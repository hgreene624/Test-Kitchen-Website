"""Document service for handling resume and cover letter uploads."""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from src.models import Document, DocumentType, Candidate
from src.lib.storage import (
    upload_document,
    delete_file,
    get_file_url,
    FileValidationError,
)
from src.config.settings import settings


class DocumentService:
    """Service for handling document operations."""

    def __init__(self, db: AsyncSession):
        """Initialize document service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def upload_candidate_document(
        self,
        candidate_id: str,
        document_type: DocumentType,
        file: UploadFile,
    ) -> Document:
        """Upload a document (resume or cover letter) for a candidate.

        If a document of this type already exists, it will be replaced.

        Args:
            candidate_id: UUID of the candidate
            document_type: Type of document (resume or cover_letter)
            file: FastAPI UploadFile object

        Returns:
            Created or updated Document object

        Raises:
            ValueError: If candidate not found
            FileValidationError: If file validation fails
        """
        # Verify candidate exists
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        # Check if document already exists
        existing_doc_result = await self.db.execute(
            select(Document).where(
                Document.candidate_id == candidate_id,
                Document.document_type == document_type,
            )
        )
        existing_doc = existing_doc_result.scalar_one_or_none()

        # If exists, delete old file from storage
        if existing_doc:
            await delete_file(existing_doc.s3_key)
            # Delete old database record
            await self.db.delete(existing_doc)
            await self.db.flush()

        # Upload new file to storage
        file_path, file_url = await upload_document(
            file=file,
            candidate_id=str(candidate_id),
            document_type=document_type.value,
        )

        # Get file size
        content = await file.read()
        file_size = len(content)
        await file.seek(0)

        # Create new document record
        document = Document(
            candidate_id=candidate_id,
            document_type=document_type,
            file_url=file_url,
            file_name=file.filename,
            file_size_bytes=file_size,
            mime_type=file.content_type,
            s3_bucket=settings.storage_bucket_name,
            s3_key=file_path,
        )

        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        return document

    async def get_candidate_documents(
        self,
        candidate_id: str,
    ) -> List[Document]:
        """Get all documents for a candidate.

        Args:
            candidate_id: UUID of the candidate

        Returns:
            List of Document objects
        """
        result = await self.db.execute(
            select(Document)
            .where(Document.candidate_id == candidate_id)
            .order_by(Document.created_at)
        )
        return list(result.scalars().all())

    async def get_document_by_id(
        self,
        document_id: str,
        candidate_id: Optional[str] = None,
    ) -> Optional[Document]:
        """Get a specific document by ID.

        Args:
            document_id: UUID of the document
            candidate_id: Optional candidate UUID to verify ownership

        Returns:
            Document object if found, None otherwise
        """
        query = select(Document).where(Document.id == document_id)

        if candidate_id:
            query = query.where(Document.candidate_id == candidate_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_document(
        self,
        document_id: str,
        candidate_id: str,
    ) -> bool:
        """Delete a document and its file from storage.

        Args:
            document_id: UUID of the document
            candidate_id: UUID of the candidate (for ownership verification)

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If candidate does not own the document
        """
        document = await self.get_document_by_id(document_id, candidate_id)

        if not document:
            return False

        if str(document.candidate_id) != str(candidate_id):
            raise ValueError("Candidate does not own this document")

        # Delete file from storage
        await delete_file(document.s3_key)

        # Delete from database
        await self.db.delete(document)
        await self.db.commit()

        return True

    async def get_document_url(
        self,
        document_id: str,
        expires_in: int = 3600,
    ) -> Optional[str]:
        """Get access URL for a document.

        Args:
            document_id: UUID of the document
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Signed URL for document access, None if document not found
        """
        document = await self.get_document_by_id(document_id)

        if not document:
            return None

        # For local storage, file_url is already accessible
        # For S3, generate signed URL
        if settings.storage_backend == "s3":
            return await get_file_url(document.s3_key, expires_in)
        else:
            return document.file_url

    async def check_candidate_documents_complete(
        self,
        candidate_id: str,
    ) -> dict:
        """Check if candidate has uploaded all required documents.

        Args:
            candidate_id: UUID of the candidate

        Returns:
            Dictionary with completion status:
            {
                "complete": bool,
                "has_resume": bool,
                "has_cover_letter": bool,
                "missing": list[str]
            }
        """
        documents = await self.get_candidate_documents(candidate_id)

        has_resume = any(doc.document_type == DocumentType.RESUME for doc in documents)
        has_cover_letter = any(
            doc.document_type == DocumentType.COVER_LETTER for doc in documents
        )

        missing = []
        if not has_resume:
            missing.append("resume")
        if not has_cover_letter:
            missing.append("cover_letter")

        return {
            "complete": has_resume and has_cover_letter,
            "has_resume": has_resume,
            "has_cover_letter": has_cover_letter,
            "missing": missing,
        }
