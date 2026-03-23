"""Candidate endpoints for document upload and profile management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.services.document_service import DocumentService
from src.api.middleware.auth_middleware import get_current_candidate
from src.models import Candidate, Document, DocumentType
from src.lib.storage import FileValidationError


router = APIRouter()


# Response Models
class DocumentResponse(BaseModel):
    """Document response model."""

    id: str
    candidate_id: str
    document_type: str
    file_url: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    created_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, document: Document):
        """Create response from Document ORM object."""
        return cls(
            id=str(document.id),
            candidate_id=str(document.candidate_id),
            document_type=document.document_type.value,
            file_url=document.file_url,
            file_name=document.file_name,
            file_size_bytes=document.file_size_bytes,
            mime_type=document.mime_type,
            created_at=document.created_at.isoformat(),
            updated_at=document.updated_at.isoformat(),
        )


class DocumentListResponse(BaseModel):
    """List of documents response."""

    documents: List[DocumentResponse]
    count: int


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


# Document Upload Endpoints


@router.post(
    "/{candidate_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
)
async def upload_document(
    candidate_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate),
):
    """
    Upload a document (resume or cover letter) for a candidate.

    If a document of this type already exists, it will be replaced.
    Maximum file size: 10 MB.
    Allowed formats: PDF, DOC, DOCX.

    **Functional Requirements**: FR-007, FR-008, FR-010

    Args:
        candidate_id: UUID of the candidate
        document_type: Type of document (resume or cover_letter)
        file: File to upload
        db: Database session
        current_candidate: Authenticated candidate

    Returns:
        Uploaded document information

    Raises:
        HTTPException 403: If candidate_id doesn't match authenticated user
        HTTPException 400: If file validation fails
        HTTPException 404: If candidate not found
    """
    # Verify candidate is uploading their own documents
    if str(current_candidate.id) != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot upload documents for another candidate",
        )

    # Validate document type
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Must be 'resume' or 'cover_letter'",
        )

    document_service = DocumentService(db)

    try:
        document = await document_service.upload_candidate_document(
            candidate_id=candidate_id,
            document_type=doc_type,
            file=file,
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return DocumentResponse.from_orm(document)


@router.get(
    "/{candidate_id}/documents",
    response_model=DocumentListResponse,
    tags=["Documents"],
)
async def get_candidate_documents(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate),
):
    """
    Get all documents for a candidate.

    Returns list of uploaded documents (resume and cover letter).

    **Functional Requirements**: FR-009

    Args:
        candidate_id: UUID of the candidate
        db: Database session
        current_candidate: Authenticated candidate

    Returns:
        List of documents with metadata

    Raises:
        HTTPException 403: If candidate_id doesn't match authenticated user
    """
    # Verify candidate is accessing their own documents
    if str(current_candidate.id) != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access documents of another candidate",
        )

    document_service = DocumentService(db)
    documents = await document_service.get_candidate_documents(candidate_id)

    return DocumentListResponse(
        documents=[DocumentResponse.from_orm(doc) for doc in documents],
        count=len(documents),
    )


@router.put(
    "/{candidate_id}/documents/{document_id}",
    response_model=DocumentResponse,
    tags=["Documents"],
)
async def reupload_document(
    candidate_id: str,
    document_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate),
):
    """
    Re-upload (replace) an existing document.

    Replaces an existing document with a new file. The document type
    (resume or cover_letter) remains the same.

    **Functional Requirements**: FR-009

    Args:
        candidate_id: UUID of the candidate
        document_id: UUID of the document to replace
        file: New file to upload
        db: Database session
        current_candidate: Authenticated candidate

    Returns:
        Updated document information

    Raises:
        HTTPException 403: If candidate_id doesn't match authenticated user
        HTTPException 404: If document not found
        HTTPException 400: If file validation fails
    """
    # Verify candidate is updating their own documents
    if str(current_candidate.id) != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update documents for another candidate",
        )

    document_service = DocumentService(db)

    # Get existing document to get its type
    existing_doc = await document_service.get_document_by_id(
        document_id, candidate_id
    )

    if not existing_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Verify ownership
    if str(existing_doc.candidate_id) != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update document belonging to another candidate",
        )

    try:
        # Upload new document with same type (this will replace the old one)
        document = await document_service.upload_candidate_document(
            candidate_id=candidate_id,
            document_type=existing_doc.document_type,
            file=file,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return DocumentResponse.from_orm(document)


@router.get(
    "/{candidate_id}/documents/status",
    response_model=dict,
    tags=["Documents"],
)
async def get_documents_completion_status(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_candidate: Candidate = Depends(get_current_candidate),
):
    """
    Check if candidate has uploaded all required documents.

    Returns completion status indicating which documents are uploaded.

    Args:
        candidate_id: UUID of the candidate
        db: Database session
        current_candidate: Authenticated candidate

    Returns:
        Completion status with has_resume, has_cover_letter, and complete flags

    Raises:
        HTTPException 403: If candidate_id doesn't match authenticated user
    """
    # Verify candidate is checking their own status
    if str(current_candidate.id) != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot check status for another candidate",
        )

    document_service = DocumentService(db)
    status_info = await document_service.check_candidate_documents_complete(
        candidate_id
    )

    return status_info
