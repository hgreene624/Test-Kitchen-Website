/**
 * Authentication service for candidate signup, login, and session management.
 */
import apiClient, { setAuthToken, clearAuthToken } from '@/lib/api-client';

export interface SignupRequest {
  email: string;
  password: string;
  full_name?: string;
  phone?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface VerifyEmailRequest {
  candidate_id: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name?: string;
    phone?: string;
    account_status: string;
    submission_status: string;
    email_verified_at?: string;
    submitted_at?: string;
    created_at?: string;
  };
}

export interface CurrentUser {
  id: string;
  email: string;
  full_name?: string;
  phone?: string;
  account_status: string;
  submission_status: string;
  email_verified_at?: string;
  submitted_at?: string;
  created_at: string;
}

/**
 * Sign up a new candidate account.
 *
 * Creates a new candidate account with UNVERIFIED status.
 * Email verification is required before the account becomes ACTIVE.
 */
export const signup = async (data: SignupRequest): Promise<AuthResponse> => {
  try {
    const response = await apiClient.post<AuthResponse>('/auth/signup', data);

    // Store token and user data
    setAuthToken(response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));

    return response.data;
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || 'Signup failed. Please try again.'
    );
  }
};

/**
 * Log in an existing candidate.
 *
 * Validates credentials and returns JWT token for authenticated requests.
 * Account must not be SUSPENDED to log in.
 */
export const login = async (data: LoginRequest): Promise<AuthResponse> => {
  try {
    const response = await apiClient.post<AuthResponse>('/auth/login', data);

    // Store token and user data
    setAuthToken(response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));

    return response.data;
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || 'Login failed. Please check your credentials.'
    );
  }
};

/**
 * Verify candidate email address.
 *
 * Marks the candidate's account as ACTIVE after email verification.
 */
export const verifyEmail = async (data: VerifyEmailRequest): Promise<{ message: string }> => {
  try {
    const response = await apiClient.post('/auth/verify-email', data);
    return response.data;
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || 'Email verification failed.'
    );
  }
};

/**
 * Log out current candidate.
 *
 * Clears JWT token from storage and calls logout endpoint.
 */
export const logout = async (): Promise<void> => {
  try {
    await apiClient.post('/auth/logout');
  } catch (error) {
    // Even if the API call fails, clear local storage
    console.error('Logout API call failed:', error);
  } finally {
    clearAuthToken();
  }
};

/**
 * Get current authenticated candidate information.
 *
 * Returns the profile of the currently authenticated candidate.
 */
export const getCurrentUser = async (): Promise<CurrentUser> => {
  try {
    const response = await apiClient.get<CurrentUser>('/auth/me');

    // Update local storage with fresh user data
    localStorage.setItem('user', JSON.stringify(response.data));

    return response.data;
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || 'Failed to fetch user data.'
    );
  }
};

/**
 * Get user data from local storage (synchronous).
 *
 * Returns cached user data without making an API call.
 */
export const getCachedUser = (): CurrentUser | null => {
  if (typeof window === 'undefined') return null;

  const userStr = localStorage.getItem('user');
  if (!userStr) return null;

  try {
    return JSON.parse(userStr) as CurrentUser;
  } catch {
    return null;
  }
};

/**
 * Check if user is authenticated (has valid token).
 */
export const isAuthenticated = (): boolean => {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('access_token');
};

/**
 * Check if user's email is verified.
 */
export const isEmailVerified = (): boolean => {
  const user = getCachedUser();
  return user?.account_status === 'active' && !!user?.email_verified_at;
};
