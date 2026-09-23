# Chat Backend API Documentation

Base URL: `http://localhost:5000`

All request and response bodies are JSON unless otherwise noted.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Request DTOs](#request-dtos)
3. [Response DTOs](#response-dtos)
4. [REST API Endpoints](#rest-api-endpoints)
5. [Socket.IO Events](#socketio-events)
6. [JWT Behavior](#jwt-behavior)
7. [Error Responses](#error-responses)
8. [Validation Requirements](#validation-requirements)
9. [Configuration](#configuration)
10. [CLI Commands](#cli-commands)

---

## Authentication

### REST API Authentication

All protected REST endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens are obtained from `POST /api/auth/register` or `POST /api/auth/login`.

### Socket.IO Authentication

Socket.IO connections authenticate via the JWT token passed as a query parameter during the handshake:

```javascript
const socket = io("http://localhost:5000", {
  query: { token: "your-jwt-token" }
});
```

- If the token is missing or invalid, the connection is rejected.
- If the token is valid, the user is tracked as an authenticated connection.
- The same JWT verification logic is reused for both REST and Socket.IO.
- The sender identity is always derived from the token, never from the client payload.

### Authentication Flow

```
Client
  ↓ sends credentials
POST /api/auth/login
  ↓ verifies password with Argon2id
  ↓ generates JWT containing sub, username, is_admin, iat, exp
  ↓ returns access_token
Client
  ↓ includes token in Authorization header or Socket.IO query
Protected Endpoint / Socket.IO
  ↓ verifies JWT signature and expiration
  ↓ loads user from database
  ↓ attaches user to request context
```

---

## Request DTOs

### RegisterRequest

Used by `POST /api/auth/register`.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| username | string | Yes | Cannot be empty. Trimmed of leading/trailing whitespace. |
| password | string | Yes | Minimum 6 characters. |

**Example:**

```json
{
  "username": "alice",
  "password": "securepass123"
}
```

---

### LoginRequest

Used by `POST /api/auth/login`.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| username | string | Yes | Cannot be empty. Trimmed of whitespace. |
| password | string | Yes | Cannot be empty. |

**Example:**

```json
{
  "username": "alice",
  "password": "securepass123"
}
```

---

### SendMessageRequest

Used by Socket.IO `send_message` event.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| content | string or null | No* | Trimmed of leading/trailing whitespace. Max length: `MAX_MESSAGE_LENGTH` (default 5000). |
| attachment_id | string or null | No* | Must be a valid UUID of an existing attachment. |

\* At least one of `content` (non-empty after trimming) or `attachment_id` must be provided.

**Example (text only):**

```json
{
  "content": "Hello world",
  "attachment_id": null
}
```

**Example (attachment only):**

```json
{
  "content": null,
  "attachment_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Example (text + attachment):**

```json
{
  "content": "Check this out",
  "attachment_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### ChangePasswordRequest

Used by `POST /api/admin/users/{user_id}/password`.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| new_password | string | Yes | Minimum 6 characters. |

**Example:**

```json
{
  "new_password": "newsecurepass"
}
```

---

### Attachment Upload (multipart/form-data)

Used by `POST /api/attachments`. Not JSON — sent as `multipart/form-data`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | The file to upload. |

**Example (curl):**

```bash
curl -X POST http://localhost:5000/api/attachments \
  -H "Authorization: Bearer <token>" \
  -F "file=@photo.jpg"
```

---

## Response DTOs

### UserResponse

Returned by `GET /api/auth/me`, `GET /api/users/me`.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique user identifier |
| username | string | The user's username |
| is_admin | boolean | Whether the user has admin privileges |

**Never exposes:** `password_hash`

**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice",
  "is_admin": false
}
```

---

### AuthResponse

Returned by `POST /api/auth/register` and `POST /api/auth/login`.

| Field | Type | Description |
|-------|------|-------------|
| access_token | string | JWT token for authentication |
| expires_at | string (ISO 8601) | Token expiration timestamp |
| user | UserResponse | The authenticated user's profile |

**Example:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_at": "2026-01-01T01:00:00+00:00",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice",
    "is_admin": false
  }
}
```

---

### MessageResponse

Returned by `GET /api/messages` (inside the `messages` array) and broadcast via Socket.IO `receive_message` event.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique message identifier |
| sender_id | string (UUID) | ID of the user who sent the message |
| sender_username | string | Username of the sender |
| content | string or null | Decrypted plaintext content. Empty string if attachment-only. |
| created_at | string (ISO 8601) | Message timestamp (UTC) |
| attachment | AttachmentInfo or null | Attachment data if the message has one |

**Never exposes:** `encrypted_content`, `nonce`, `storage_path`

**Example (text message):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sender_id": "user-uuid",
  "sender_username": "alice",
  "content": "Hello world",
  "created_at": "2026-01-01T00:00:00+00:00",
  "attachment": null
}
```

**Example (attachment message):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sender_id": "user-uuid",
  "sender_username": "alice",
  "content": "",
  "created_at": "2026-01-01T00:00:00+00:00",
  "attachment": {
    "id": "attachment-uuid",
    "original_filename": "photo.jpg",
    "mime_type": "image/jpeg",
    "size": 102400
  }
}
```

---

### MessageListResponse

Returned by `GET /api/messages`.

| Field | Type | Description |
|-------|------|-------------|
| messages | MessageResponse[] | Array of messages, newest first |
| pagination | PaginationInfo | Pagination metadata |

**Example:**

```json
{
  "messages": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "sender_id": "user-uuid",
      "sender_username": "alice",
      "content": "Hello world",
      "created_at": "2026-01-01T00:00:00+00:00",
      "attachment": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 120,
    "total_pages": 3
  }
}
```

---

### PaginationInfo

| Field | Type | Description |
|-------|------|-------------|
| page | int | Current page number |
| limit | int | Items per page |
| total | int | Total number of messages |
| total_pages | int | Total number of pages |

---

### AttachmentResponse

Returned by `POST /api/attachments`.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique attachment identifier |
| original_filename | string | Sanitized original filename |
| mime_type | string | Detected MIME type |
| size | int | File size in bytes |
| created_at | string (ISO 8601) | Upload timestamp (UTC) |
| download_url | string | Relative URL to download the file |

**Never exposes:** `stored_filename`, `storage_path`, `uploader_id`

**Example:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "holiday.jpg",
  "mime_type": "image/jpeg",
  "size": 482931,
  "created_at": "2026-01-01T00:00:00+00:00",
  "download_url": "/api/attachments/550e8400-e29b-41d4-a716-446655440000"
}
```

---

### AttachmentInfo (nested in MessageResponse)

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Attachment identifier |
| original_filename | string | Sanitized original filename |
| mime_type | string | Detected MIME type |
| size | int | File size in bytes |

---

### AdminUserResponse

Returned by `GET /api/admin/users` (array of these).

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | User identifier |
| username | string | The user's username |
| is_admin | boolean | Whether the user has admin privileges |
| created_at | string (ISO 8601) | Account creation timestamp |

**Example:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice",
    "is_admin": false,
    "created_at": "2026-01-01T00:00:00+00:00"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "is_admin": true,
    "created_at": "2026-01-01T00:00:00+00:00"
  }
]
```

---

### AdminPasswordChangeResponse

Returned by `POST /api/admin/users/{user_id}/password`.

| Field | Type | Description |
|-------|------|-------------|
| message | string | Confirmation message |

**Example:**

```json
{
  "message": "Password updated successfully"
}
```

---

## REST API Endpoints

---

### POST /api/auth/register

Register a new user account.

- **Auth Required:** No
- **Request DTO:** RegisterRequest
- **Response DTO:** AuthResponse
- **Status:** 201 Created

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | VALIDATION_ERROR | Empty username, password < 6 chars, missing fields |
| 409 | USER_ALREADY_EXISTS | Username already taken |

---

### POST /api/auth/login

Authenticate and receive a JWT token.

- **Auth Required:** No
- **Request DTO:** LoginRequest
- **Response DTO:** AuthResponse
- **Status:** 200 OK

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | INVALID_CREDENTIALS | Wrong username or password |

---

### GET /api/auth/me

Get the currently authenticated user's profile.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** None
- **Response DTO:** UserResponse
- **Status:** 200 OK

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | AUTHENTICATION_ERROR | Missing, invalid, or expired token |

---

### GET /api/users/me

Identical to `GET /api/auth/me`. Returns the currently authenticated user.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** None
- **Response DTO:** UserResponse
- **Status:** 200 OK

---

### GET /api/messages

Retrieve chat message history with pagination. Messages are returned newest-first.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** None (uses query parameters)
- **Response DTO:** MessageListResponse
- **Status:** 200 OK

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number (min 1) |
| limit | int | 50 | Messages per page (min 1, max 100) |

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |

---

### POST /api/attachments

Upload a file. Returns metadata and a download URL.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** Attachment Upload (multipart/form-data)
- **Response DTO:** AttachmentResponse
- **Status:** 201 Created

**Validation Rules:**

- File size must not exceed `MAX_FILE_SIZE_MB` (default 25 MB).
- File extension must be in the allowed list: `jpg`, `jpeg`, `png`, `gif`, `webp`, `pdf`, `txt`, `zip`.
- MIME type is detected from file content signatures, not just the client-provided type.
- Original filename is sanitized with `secure_filename()`.
- Server-side filename is a random hex string (e.g., `9f31b8c4e2a74f...`).

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | VALIDATION_ERROR | No file provided, empty filename |
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |
| 413 | FILE_TOO_LARGE | File exceeds max size |
| 415 | UNSUPPORTED_FILE_TYPE | File extension not in allowed list |

---

### GET /api/attachments/{attachment_id}

Download a previously uploaded file. The file is streamed as a binary download.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** None
- **Response:** Binary file stream

**Response Headers:**

| Header | Value |
|--------|-------|
| Content-Type | Detected MIME type of the file |
| Content-Disposition | `attachment; filename="<original_filename>"` |

**Notes:**

- Any authenticated user can download any attachment.
- The physical storage path is never exposed to the client.

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |
| 404 | ATTACHMENT_ERROR | Attachment ID does not exist |

---

### GET /api/admin/users

List all registered users. Admin only.

- **Auth Required:** Yes (`@require_admin`)
- **Request DTO:** None
- **Response DTO:** AdminUserResponse[] (array)
- **Status:** 200 OK

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |
| 403 | AUTHORIZATION_ERROR | Token is valid but user is not an admin |

---

### POST /api/admin/users/{user_id}/password

Change another user's password. Admin only. The admin cannot see the existing password.

- **Auth Required:** Yes (`@require_admin`)
- **Request DTO:** ChangePasswordRequest
- **Response DTO:** AdminPasswordChangeResponse
- **Status:** 200 OK

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | VALIDATION_ERROR | Password < 6 characters |
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |
| 403 | AUTHORIZATION_ERROR | Token is valid but user is not an admin |
| 404 | USER_NOT_FOUND | User ID does not exist |

---

## Socket.IO Events

Connect to the Socket.IO server at `http://localhost:5000`.

---

### Connection

The client must provide the JWT token as a query parameter during the Socket.IO handshake:

```javascript
const socket = io("http://localhost:5000", {
  query: { token: "your-jwt-token" }
});
```

**Behavior:**

- If the token is missing or invalid, the connection is rejected (returns `false`).
- If the token is valid, the user is tracked as an authenticated connection.
- The server logs the connection and disconnection of each user.
- Uses the same JWT verification logic as REST endpoints.

---

### Client Event: send_message

Sent by the client to broadcast a message to all connected users.

**Request DTO:** SendMessageRequest

**Payload:**

```json
{
  "content": "Hello world",
  "attachment_id": null
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | string or null | No* | Text content of the message. Stripped of leading/trailing whitespace. Max length: `MAX_MESSAGE_LENGTH` (default 5000). |
| attachment_id | string or null | No* | UUID of a previously uploaded attachment. Must belong to the sender and not already be attached to another message. |

\* At least one of `content` or `attachment_id` must be provided.

**Behavior:**

1. Server verifies the socket is authenticated.
2. Validates the payload using SendMessageRequest DTO.
3. If `attachment_id` is provided, verifies:
   - Attachment exists
   - Attachment belongs to the authenticated sender
   - Attachment has not already been attached to another message
4. Encrypts the message content with AES-256-GCM (unique nonce per message).
5. Saves the message to the database.
6. Broadcasts `receive_message` to all connected clients.
7. If any step fails, sends an `error` event to the sender only.

---

### Server Event: receive_message

Broadcast to all connected clients (including the sender) when a message is sent successfully.

**Response DTO:** MessageResponse

**Payload:**

```json
{
  "id": "uuid",
  "sender_id": "uuid",
  "sender_username": "alice",
  "content": "Hello world",
  "created_at": "2026-01-01T00:00:00+00:00",
  "attachment": {
    "id": "uuid",
    "original_filename": "photo.jpg",
    "mime_type": "image/jpeg",
    "size": 102400
  }
}
```

**Notes:**

- `content` is the decrypted plaintext. Empty string if attachment-only.
- `attachment` is `null` if the message has no attachment.

---

### Server Event: error

Sent to the client that triggered the error. Not broadcast.

**Payload:**

```json
{
  "code": "VALIDATION_ERROR",
  "message": "A message must contain content, an attachment, or both"
}
```

**Possible error codes:**

| Code | When |
|------|------|
| AUTHENTICATION_ERROR | Socket connection is not authenticated |
| VALIDATION_ERROR | Invalid payload format, empty message, content too long |
| ATTACHMENT_ERROR | Attachment not found, not owned by sender, or already used |
| MESSAGE_ERROR | General message processing failure |

---

### Disconnect

When a client disconnects, the server removes them from the authenticated connections map and logs the event. No payload is sent.

---

## JWT Behavior

### Token Generation

JWT tokens are generated upon successful registration or login.

**Algorithm:** HS256

**Claims:**

| Claim | Type | Description |
|-------|------|-------------|
| sub | string (UUID) | The user's unique ID |
| username | string | The user's username |
| is_admin | boolean | Whether the user has admin privileges |
| iat | int (Unix timestamp) | Token issued-at time |
| exp | int (Unix timestamp) | Token expiration time |

**Expiration:** Configurable via `JWT_EXPIRATION_MINUTES` (default 60 minutes).

**Example token payload (decoded):**

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice",
  "is_admin": false,
  "iat": 1700000000,
  "exp": 1700003600
}
```

### Token Verification

1. Extract token from `Authorization: Bearer <token>` header (REST) or `?token=` query parameter (Socket.IO).
2. Decode and verify the JWT signature using `JWT_SECRET_KEY`.
3. Check expiration — reject with `AUTHENTICATION_ERROR` if expired.
4. Load the user from the database using the `sub` claim.
5. Reject if the user no longer exists.
6. Attach the user object to the request context (`g.current_user` for REST, `connected_users[sid]` for Socket.IO).

### Security Rules

- The sender ID is always derived from the JWT token, never from the client payload.
- Clients cannot impersonate other users.
- Tokens with invalid signatures are rejected.
- Tokens past their `exp` claim are rejected.
- The `JWT_SECRET_KEY` must be a strong random string, never hardcoded.

---

## Error Responses

### REST API Error Format

All REST API errors follow a consistent JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description"
  }
}
```

### Error Code Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request body, missing fields, or parameter out of range |
| MESSAGE_ERROR | 400 | General message processing failure |
| AUTHENTICATION_ERROR | 401 | Missing, invalid, or expired JWT token |
| INVALID_CREDENTIALS | 401 | Wrong username or password |
| AUTHORIZATION_ERROR | 403 | Authenticated but not authorized (e.g., non-admin accessing admin endpoint) |
| USER_NOT_FOUND | 404 | User does not exist |
| ATTACHMENT_ERROR | 404 | Attachment does not exist |
| USER_ALREADY_EXISTS | 409 | Username already taken |
| FILE_TOO_LARGE | 413 | Uploaded file exceeds max size |
| UNSUPPORTED_FILE_TYPE | 415 | File extension not in allowed list |

### Socket.IO Error Format

Socket.IO errors are sent as an `error` event to the requesting client only:

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable description"
}
```

---

## Validation Requirements

### Username

- Required on registration.
- Cannot be empty or whitespace-only.
- Must be unique across all users.
- Trimmed of leading/trailing whitespace before storage.

### Password

- Required on registration and password change.
- Minimum 6 characters.
- Stored as an Argon2id hash — plaintext is never stored.
- Never returned in any API response.

### Message Content

- At least one of `content` or `attachment_id` must be provided.
- If `content` is provided, it must be non-empty after trimming whitespace.
- Maximum length: `MAX_MESSAGE_LENGTH` (default 5000 characters).
- Leading and trailing whitespace is stripped.
- Content is encrypted with AES-256-GCM before storage — plaintext is never stored in the database.

### Attachment ID (in messages)

- Must be a valid UUID.
- Must reference an existing attachment in the database.
- Must belong to the authenticated user (the uploader).
- Must not already be attached to another message.
- An attachment cannot exist indefinitely without being attached to a message.

### File Upload

- A file must be provided in the `file` form field.
- Filename must not be empty after sanitization.
- File size must not exceed `MAX_FILE_SIZE_MB` (default 25 MB).
- File extension must be in the allowed list: `jpg`, `jpeg`, `png`, `gif`, `webp`, `pdf`, `txt`, `zip`.
- MIME type is detected from file content signatures (magic bytes), not just the client-provided Content-Type.
- Original filename is sanitized with `secure_filename()`.
- Server-side filename is a cryptographically random hex string — the original filename is never used for storage.
- Files are stored outside executable application directories.
- Path traversal is prevented by validating the resolved storage path.

### File Type Detection

The server detects MIME types from file content signatures:

| Magic Bytes | Detected Type |
|-------------|---------------|
| `FF D8 FF` | image/jpeg |
| `89 50 4E 47` | image/png |
| `47 49 46 38` | image/gif |
| `52 49 46 46` ... `57 45 42 50` | image/webp |
| `25 50 44 46` | application/pdf |
| `50 4B 03 04` | application/zip |

### Query Parameters (GET /api/messages)

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| page | int | 1 | 1 | unlimited | Page number |
| limit | int | 50 | 1 | 100 | Items per page |

Values below the minimum are clamped to the minimum. Values above the maximum are clamped to the maximum.

### Admin Endpoints

- Require a valid JWT token.
- Require `is_admin == true` in the JWT claims.
- Non-admin users receive a 403 AUTHORIZATION_ERROR.
- Admins cannot retrieve existing passwords.
- Admins can only change passwords, not perform other user modifications.

---

## Configuration

All configuration is loaded from environment variables (`.env` file).

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| FLASK_ENV | development | No | Flask environment |
| DATABASE_URL | sqlite:///chat.db | No | SQLAlchemy database URL |
| JWT_SECRET_KEY | — | Yes | Secret key for signing JWT tokens (strong random string) |
| JWT_EXPIRATION_MINUTES | 60 | No | Token expiration time in minutes |
| MESSAGE_ENCRYPTION_KEY | — | Yes | 64-char hex string (32 bytes) for AES-256-GCM encryption |
| FILE_STORAGE_PATH | ./storage/attachments | No | Directory for storing uploaded files |
| MAX_FILE_SIZE_MB | 25 | No | Maximum upload file size in MB |
| MAX_MESSAGE_LENGTH | 5000 | No | Maximum message text length in characters |
| CORS_ALLOWED_ORIGINS | http://localhost:3000 | No | Comma-separated list of allowed CORS origins |

**Startup validation:** The server validates that `JWT_SECRET_KEY` and `MESSAGE_ENCRYPTION_KEY` are set and that the encryption key is exactly 64 hex characters. The server will not start if these are missing or invalid.

---

## CLI Commands

### Create Admin User

```bash
python run.py create-admin
```

Securely prompts for username and password. Creates an admin user in the database.

### Run Server

```bash
python run.py
```

Starts the server on `http://0.0.0.0:5000`.

### Run Tests

```bash
pytest tests/ -v
```
