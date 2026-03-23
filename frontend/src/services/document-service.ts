/**
 * Document service for uploading and managing candidate documents (resume, cover letter).
 */
import apiClient from '@/lib/api-client';

export type DocumentType = 'resume' | 'cover_letter';

export interface Document {
  id: string;
  candidate_id: string;
  document_type: string;
  file_url: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  count: number;
}

export interface DocumentCompletionStatus {
  complete: boolean;
  has_resume: boolean;
  has_cover_letter: boolean;
  missing: string[];
}

/**
 * Upload a document (resume or cover letter) for a candidate.
 *
 * If a document of this type already exists, it will be replaced.
 * Maximum file size: 10 MB.
 * Allowed formats: PDF, DOC, DOCX.
 */
export const uploadDocument = async (
  candidateId: string,
  documentType: DocumentType,
  file: File
): Promise<Document> => {
  try {
    const formData = new FormData();
    formData.append('document_type', documentType);
    formData.append('file', file);

    // Don't set Content-Type header - let axios set it automatically with the boundary
    const response = await apiClient.post<Document>(
      `/candidates/${candidateId}/documents`,
      formData
    );

    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Document upload failed.';
    throw new Error(errorMessage);
  }
};

/**
 * Get all documents for a candidate.
 *
 * Returns list of uploaded documents (resume and cover letter).
 */
export const getCandidateDocuments = async (
  candidateId: string
): Promise<DocumentListResponse> => {
  try {
    const response = await apiClient.get<DocumentListResponse>(
      `/candidates/${candidateId}/documents`
    );

    return response.data;
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || 'Failed to fetch documents.'
    );
  }
};

/**
 * Re-upload (replace) an existing document.
 *
 * Replaces an existing document with a new file. The document type
 * (resume or cover_letter) remains the same.
 */
export const reuploadDocument = async (
  candidateId: string,
  documentId: string,
  file: File
): Promise<Document> => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    // Don't set Content-Type header - let axios set it automatically with the boundary
    const response = await apiClient.put<Document>(
      `/candidates/${candidateId}/documents/${documentId}`,
      formData
    );

    return response.data;
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || 'Document re-upload failed.'
    );
  }
};

/**
 * Check if candidate has uploaded all required documents.
 *
 * Returns completion status indicating which documents are uploaded.
 */
export const getDocumentCompletionStatus = async (
  candidateId: string
): Promise<DocumentCompletionStatus> => {
  try {
    const response = await apiClient.get<DocumentCompletionStatus>(
      `/candidates/${candidateId}/documents/status`
    );

    return response.data;
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || 'Failed to fetch document status.'
    );
  }
};

/**
 * Validate file before upload.
 *
 * Checks file type and size constraints.
 */
export const validateDocumentFile = (file: File): { valid: boolean; error?: string } => {
  const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
  const ALLOWED_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ];

  if (!ALLOWED_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: 'Invalid file type. Please upload PDF, DOC, or DOCX file.',
    };
  }

  if (file.size > MAX_SIZE) {
    return {
      valid: false,
      error: `File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds maximum allowed size (10 MB).`,
    };
  }

  return { valid: true };
};

/**
 * Format file size for display.
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Get document type label for display.
 */
export const getDocumentTypeLabel = (type: DocumentType | string): string => {
  const labels: Record<string, string> = {
    resume: 'Resume',
    cover_letter: 'Cover Letter',
  };

  return labels[type] || type;
};
