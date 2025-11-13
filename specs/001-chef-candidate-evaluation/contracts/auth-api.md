# Authentication API Contract

**Service**: Authentication & Authorization
**Technology**: FastAPI with Pydantic schemas, JWT tokens, bcrypt password hashing
**Base URL**: `/api/v1/auth`

---

## Endpoints

### POST /auth/signup

**Purpose**: Register a new candidate account with email and password

**Auth Required**: No

**Request**:
- **Headers**:
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "email": "string - valid email address (required)",
    "password": "string - min 8 chars, must include uppercase, lowercase, number, symbol (required)",
    "full_name": "string - candidate's full name (required)"
  }
  ```

**Response**:
- **Success (201 Created)**:
  ```json
  {
    "id": "string - UUID of created candidate",
    "email": "string - registered email",
    "full_name": "string - candidate name",
    "account_status": "unverified",
    "created_at": "string - ISO 8601 timestamp",
    "message": "Account created. Please check your email to verify your account."
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Validation error message",
    "code": "VALIDATION_ERROR",
    "details": {
      "field": "password",
      "message": "Password must contain at least 8 characters including uppercase, lowercase, number, and symbol"
    }
  }
  ```
- **Error (409 Conflict)**:
  ```json
  {
    "error": "An account with this email already exists",
    "code": "EMAIL_ALREADY_EXISTS"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to create account",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Email must be unique across all candidates
- Password must meet complexity requirements: min 8 chars, uppercase, lowercase, number, symbol
- Account status defaults to "unverified"
- System sends verification email after successful registration
- Password is hashed with bcrypt before storage (never stored in plaintext)

**Referenced FRs**: FR-001, FR-003

---

### POST /auth/verify-email

**Purpose**: Verify candidate email address using token from verification email

**Auth Required**: No

**Request**:
- **Headers**:
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "token": "string - email verification token sent to candidate's email (required)"
  }
  ```

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "message": "Email verified successfully. You can now log in.",
    "email": "string - verified email address",
    "account_status": "active"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Invalid or expired verification token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (409 Conflict)**:
  ```json
  {
    "error": "Email already verified",
    "code": "ALREADY_VERIFIED"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to verify email",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Verification token expires after 24 hours
- Token can only be used once
- Account status transitions from "unverified" to "active"
- Verified candidates can access interview wizard

**Referenced FRs**: FR-002

---

### POST /auth/login

**Purpose**: Authenticate candidate or admin user and issue JWT access token

**Auth Required**: No

**Request**:
- **Headers**:
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "email": "string - registered email (required)",
    "password": "string - account password (required)",
    "role": "string - 'candidate' or 'admin' (required)"
  }
  ```

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "access_token": "string - JWT token for authorization",
    "token_type": "bearer",
    "expires_in": "number - seconds until token expiration (3600 for 1 hour)",
    "user": {
      "id": "string - UUID",
      "email": "string",
      "full_name": "string",
      "role": "string - 'candidate' or 'admin'",
      "account_status": "string - 'active', 'unverified', 'rejected'"
    }
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid email or password",
    "code": "INVALID_CREDENTIALS"
  }
  ```
- **Error (403 Forbidden)**:
  ```json
  {
    "error": "Email not verified. Please check your email for verification link.",
    "code": "EMAIL_NOT_VERIFIED"
  }
  ```
- **Error (403 Forbidden)**:
  ```json
  {
    "error": "Account has been rejected",
    "code": "ACCOUNT_REJECTED"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to authenticate",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Password is compared against hashed value using bcrypt
- JWT token includes user ID, email, role, and expiration claims
- Unverified candidates cannot log in (must verify email first)
- Rejected candidates cannot log in
- Token expires after 1 hour (configurable)
- Admin and candidate accounts are separate (different tables/role check)

**Referenced FRs**: FR-001, FR-002, FR-004

---

### POST /auth/logout

**Purpose**: Invalidate current user session and JWT token

**Auth Required**: Yes | Role: both

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**: None (empty)

**Response**:
- **Success (200 OK)**:
  ```json
  {
    "message": "Logged out successfully"
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid or expired token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to log out",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Token is added to blacklist/revocation list to prevent reuse
- Client must discard token after logout
- Logged-out tokens cannot be used for subsequent requests

**Referenced FRs**: FR-004

---

### GET /auth/me

**Purpose**: Retrieve current authenticated user's profile information

**Auth Required**: Yes | Role: both

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`

**Response**:
- **Success (200 OK)** (Candidate):
  ```json
  {
    "id": "string - UUID",
    "email": "string",
    "full_name": "string",
    "role": "candidate",
    "account_status": "string - 'active', 'unverified', 'rejected'",
    "submission_status": "string - 'incomplete', 'submitted', 'reviewed', 'eliminated', 'hired'",
    "created_at": "string - ISO 8601 timestamp",
    "documents_uploaded": {
      "resume": "boolean",
      "cover_letter": "boolean"
    },
    "videos_recorded": "number - count of completed video recordings",
    "total_prompts": "number - total interview prompts",
    "feedback_submitted": "number - count of dishes with feedback"
  }
  ```
- **Success (200 OK)** (Admin):
  ```json
  {
    "id": "string - UUID",
    "email": "string",
    "full_name": "string",
    "role": "admin",
    "created_at": "string - ISO 8601 timestamp"
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid or expired token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to retrieve user information",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- User ID extracted from JWT token claims
- Candidates see submission progress metrics
- Admins see basic profile only
- Response shape differs based on user role

**Referenced FRs**: FR-004

---

### POST /auth/admin/create

**Purpose**: Create a new admin user account (admin-only operation)

**Auth Required**: Yes | Role: admin

**Request**:
- **Headers**:
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "email": "string - valid email address (required)",
    "password": "string - min 8 chars with complexity requirements (required)",
    "full_name": "string - admin's full name (required)"
  }
  ```

**Response**:
- **Success (201 Created)**:
  ```json
  {
    "id": "string - UUID of created admin",
    "email": "string",
    "full_name": "string",
    "role": "admin",
    "created_at": "string - ISO 8601 timestamp",
    "message": "Admin account created successfully"
  }
  ```
- **Error (400 Bad Request)**:
  ```json
  {
    "error": "Validation error message",
    "code": "VALIDATION_ERROR",
    "details": {
      "field": "password",
      "message": "Password must contain at least 8 characters including uppercase, lowercase, number, and symbol"
    }
  }
  ```
- **Error (401 Unauthorized)**:
  ```json
  {
    "error": "Invalid or expired token",
    "code": "INVALID_TOKEN"
  }
  ```
- **Error (403 Forbidden)**:
  ```json
  {
    "error": "Only administrators can create admin accounts",
    "code": "INSUFFICIENT_PERMISSIONS"
  }
  ```
- **Error (409 Conflict)**:
  ```json
  {
    "error": "An admin account with this email already exists",
    "code": "EMAIL_ALREADY_EXISTS"
  }
  ```
- **Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Failed to create admin account",
    "code": "INTERNAL_ERROR"
  }
  ```

**Business Rules**:
- Only existing admins can create new admin accounts
- Email must be unique across all admins
- Password complexity requirements same as candidate accounts
- Admin accounts do not require email verification
- Account status is immediately "active"
- Action is logged to audit trail

**Referenced FRs**: FR-004, FR-006

---

## Common Error Responses

All endpoints may return the following errors:

**401 Unauthorized** (for protected endpoints):
```json
{
  "error": "Authentication required",
  "code": "AUTHENTICATION_REQUIRED"
}
```

**429 Too Many Requests** (rate limiting):
```json
{
  "error": "Too many requests. Please try again later.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": "number - seconds until retry allowed"
}
```

---

## JWT Token Structure

**Token Claims**:
```json
{
  "sub": "string - user ID (UUID)",
  "email": "string - user email",
  "role": "string - 'candidate' or 'admin'",
  "iat": "number - issued at timestamp",
  "exp": "number - expiration timestamp (1 hour from iat)"
}
```

**Token Usage**:
- Include in `Authorization` header as `Bearer {token}`
- Token expires after 1 hour
- Refresh mechanism not included in MVP (user must re-login)

---

## Pydantic Schema Examples

**SignupRequest**:
```python
from pydantic import BaseModel, EmailStr, Field, validator
import re

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)

    @validator('password')
    def validate_password_complexity(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
```

**LoginRequest**:
```python
from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    CANDIDATE = "candidate"
    ADMIN = "admin"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole
```

**TokenResponse**:
```python
from pydantic import BaseModel

class UserInfo(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    account_status: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: UserInfo
```
