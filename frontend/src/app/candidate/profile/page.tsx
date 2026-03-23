/**
 * Candidate Profile Page
 *
 * Displays candidate information and allows document upload (resume, cover letter).
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getCurrentUser, logout, isAuthenticated, type CurrentUser } from '@/services/auth-service';
import {
  getCandidateDocuments,
  getDocumentCompletionStatus,
  type Document,
  type DocumentCompletionStatus,
} from '@/services/document-service';
import DocumentUpload from '@/components/DocumentUpload';

export default function CandidateProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [documents, setDocuments] = useState<{ resume?: Document; cover_letter?: Document }>({});
  const [completionStatus, setCompletionStatus] = useState<DocumentCompletionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check authentication
    if (!isAuthenticated()) {
      router.push('/candidate/login');
      return;
    }

    loadUserData();
  }, []);

  const loadUserData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch user data
      const userData = await getCurrentUser();
      setUser(userData);

      // Fetch documents
      const docsResponse = await getCandidateDocuments(userData.id);
      const docsMap: { resume?: Document; cover_letter?: Document } = {};

      docsResponse.documents.forEach((doc) => {
        if (doc.document_type === 'resume') {
          docsMap.resume = doc;
        } else if (doc.document_type === 'cover_letter') {
          docsMap.cover_letter = doc;
        }
      });

      setDocuments(docsMap);

      // Fetch completion status
      const status = await getDocumentCompletionStatus(userData.id);
      setCompletionStatus(status);
    } catch (err: any) {
      setError(err.message || 'Failed to load profile data.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      router.push('/candidate/login');
    } catch (err) {
      console.error('Logout error:', err);
      router.push('/candidate/login');
    }
  };

  const handleDocumentUploadSuccess = () => {
    // Reload documents and completion status
    loadUserData();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full"></div>
          <p className="mt-4 text-gray-600">Loading your profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white shadow-md rounded-lg p-6">
          <div className="text-center">
            <div className="text-red-600 text-5xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Profile</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={loadUserData}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {user.full_name || 'Candidate Profile'}
              </h1>
              <p className="text-gray-600 mt-1">{user.email}</p>
              <div className="mt-2 flex items-center space-x-4">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    user.account_status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : user.account_status === 'unverified'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {user.account_status === 'active'
                    ? '✓ Email Verified'
                    : user.account_status === 'unverified'
                    ? '⚠ Email Not Verified'
                    : '✗ Suspended'}
                </span>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    user.submission_status === 'submitted'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {user.submission_status === 'submitted'
                    ? 'Application Submitted'
                    : 'Application Incomplete'}
                </span>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>

        {/* Completion Status */}
        {completionStatus && !completionStatus.complete && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-yellow-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Profile Incomplete
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>Please upload the following documents to complete your profile:</p>
                  <ul className="list-disc list-inside mt-1">
                    {completionStatus.missing.map((doc) => (
                      <li key={doc}>{doc === 'resume' ? 'Resume' : 'Cover Letter'}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {completionStatus?.complete && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <svg
                className="h-5 w-5 text-green-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="ml-3 text-sm font-medium text-green-800">
                Profile Complete! All required documents have been uploaded.
              </p>
            </div>
          </div>
        )}

        {/* Document Upload Section */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">
            Application Documents
          </h2>

          <div className="space-y-6">
            {/* Resume Upload */}
            <DocumentUpload
              candidateId={user.id}
              documentType="resume"
              existingDocument={documents.resume}
              onUploadSuccess={handleDocumentUploadSuccess}
              onUploadError={(error) => console.error('Resume upload error:', error)}
            />

            {/* Cover Letter Upload */}
            <DocumentUpload
              candidateId={user.id}
              documentType="cover_letter"
              existingDocument={documents.cover_letter}
              onUploadSuccess={handleDocumentUploadSuccess}
              onUploadError={(error) => console.error('Cover letter upload error:', error)}
            />
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-6 bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Information</h3>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Phone Number</dt>
              <dd className="mt-1 text-sm text-gray-900">{user.phone || 'Not provided'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Member Since</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(user.created_at).toLocaleDateString()}
              </dd>
            </div>
            {user.email_verified_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Email Verified</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(user.email_verified_at).toLocaleDateString()}
                </dd>
              </div>
            )}
            {user.submitted_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Application Submitted</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(user.submitted_at).toLocaleDateString()}
                </dd>
              </div>
            )}
          </dl>
        </div>
      </div>
    </div>
  );
}
