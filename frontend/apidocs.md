# Chat Backend API Documentation

Base URL: `http://localhost:5000`

All request and response bodies are JSON unless otherwise noted.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Request DTOs](#request-dtos)
3. [Response DTOs](#response-dtos)
4. [REST API Endpoints](#rest-api-endpoints)
   - [Auth](#auth-endpoints)
   - [Users](#user-endpoints)
   - [Conversations](#conversation-endpoints)
   - [Messages](#message-endpoints)
   - [Attachments](#attachment-endpoints)
   - [Admin](#admin-endpoints)
5. [Socket.IO Events](#socketio-events)
6. [JWT Behavior](#jwt-behavior)
7. [Error Responses](#error-responses)
8. [Validation Requirements](#validation-requirements)
9. [Configuration](#configuration)
10. [CLI Commands](#cli-commands)

---

## Conversation Model

There are two conversation types:

- **DIRECT** — A private 1-to-1 conversation between exactly 2 users. Cannot be renamed. Has no owner.
- **GROUP** — A named conversation with 2+ members. Has an owner who controls membership and naming.

Key rules:

- Duplicate direct conversations between the same two users are resolved to the existing conversation (regardless of which user initiates).
- A user cannot create a direct conversation with themselves.
- Only the group owner can add/remove members and rename the group.
- The group owner cannot leave the group (would leave group without owner).
- Users can only access conversations they are members of. All access is verified server-side.

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

Used by Socket.IO `send_message` event and `POST /api/conversations/<id>/messages`.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| content | string or null | No* | Trimmed of leading/trailing whitespace. Max length: `MAX_MESSAGE_LENGTH` (default 5000). |
| attachment_id | string or null | No* | Must be a valid UUID of an existing attachment. |

\* At least one of `content` (non-empty after trimming) or `attachment_id` must be provided.

**Example (text only):**

```json
{
  "content": "Hello world"
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

### CreateDirectConversationRequest

Used by `POST /api/conversations/direct`.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| user_id | string | Yes | Cannot be empty. Must be a valid user ID. Cannot be the authenticated user's own ID. |

**Example:**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### CreateGroupConversationRequest

Used by `POST /api/conversations/group`.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| name | string | Yes | Cannot be empty. Max 255 characters. |
| member_ids | string[] | No | Array of user IDs to add. Duplicates are removed. Authenticated user is always added. |

**Example:**

```json
{
  "name": "Family",
  "member_ids": ["user-uuid-1", "user-uuid-2"]
}
```

---

### AddConversationMemberRequest

Used by `POST /api/conversations/<conversation_id>/members`.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| user_id | string | Yes | Cannot be empty. Must be a valid user ID. |

**Example:**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### UpdateGroupRequest

Used by `PATCH /api/conversations/<conversation_id>`.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| name | string | Yes | Cannot be empty. Max 255 characters. |

**Example:**

```json
{
  "name": "New Family Name"
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

Returned by `GET /api/conversations/<id>/messages` (inside the `messages` array) and broadcast via Socket.IO `receive_message` event.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique message identifier |
| conversation_id | string (UUID) | ID of the conversation this message belongs to |
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
  "conversation_id": "conv-uuid",
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
  "conversation_id": "conv-uuid",
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

Returned by `GET /api/conversations/<id>/messages`.

| Field | Type | Description |
|-------|------|-------------|
| messages | MessageResponse[] | Array of messages, newest first |
| pagination | PaginationInfo | Pagination metadata |

---

### PaginationInfo

| Field | Type | Description |
|-------|------|-------------|
| page | int | Current page number |
| limit | int | Items per page |
| total | int | Total number of messages |
| total_pages | int | Total number of pages |

---

### ConversationResponse

Returned by all conversation endpoints.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique conversation identifier |
| type | string | `"DIRECT"` or `"GROUP"` |
| name | string or null | Group name (null for DIRECT) |
| owner_id | string or null | Owner user ID (null for DIRECT) |
| members | ConversationMemberResponse[] | Array of conversation members |
| created_at | string (ISO 8601) | Creation timestamp |
| updated_at | string (ISO 8601) | Last update timestamp |

**Example (direct):**

```json
{
  "id": "conv-uuid",
  "type": "DIRECT",
  "name": null,
  "owner_id": null,
  "members": [
    { "id": "user-uuid-1", "username": "alice" },
    { "id": "user-uuid-2", "username": "bob" }
  ],
  "created_at": "2026-01-01T00:00:00+00:00",
  "updated_at": "2026-01-01T00:00:00+00:00"
}
```

**Example (group):**

```json
{
  "id": "conv-uuid",
  "type": "GROUP",
  "name": "Family",
  "owner_id": "user-uuid-1",
  "members": [
    { "id": "user-uuid-1", "username": "alice" },
    { "id": "user-uuid-2", "username": "bob" },
    { "id": "user-uuid-3", "username": "charlie" }
  ],
  "created_at": "2026-01-01T00:00:00+00:00",
  "updated_at": "2026-01-01T00:00:00+00:00"
}
```

---

### ConversationMemberResponse

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | User identifier |
| username | string | The user's username |

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

### Auth Endpoints

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

### User Endpoints

### GET /api/users/search

Search users by username. Returns only `id` and `username`.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** None (uses query parameters)
- **Response:** UserSearchResult[] (array)
- **Status:** 200 OK

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| q | string | "" | Username search query (case-insensitive partial match) |

**Example Response:**

```json
[
  { "id": "user-uuid", "username": "alice" },
  { "id": "user-uuid-2", "username": "alice2" }
]
```

---

### Conversation Endpoints

---

### GET /api/conversations

List all conversations the authenticated user belongs to.

- **Auth Required:** Yes (`@require_auth`)
- **Response:** ConversationResponse[] (array)
- **Status:** 200 OK

---

### GET /api/conversations/{conversation_id}

Get a single conversation by ID. Must be a member.

- **Auth Required:** Yes (`@require_auth`)
- **Response:** ConversationResponse
- **Status:** 200 OK

**Errors:**

| Status | Code | When |
|--------|------|------|
| 403 | NOT_CONVERSATION_MEMBER | User is not a member |
| 404 | CONVERSATION_NOT_FOUND | Conversation does not exist |

---

### POST /api/conversations/direct

Create a direct (1-to-1) conversation. If one already exists between the two users, returns the existing one.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** CreateDirectConversationRequest
- **Response:** ConversationResponse
- **Status:** 201 Created

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | DIRECT_CONVERSATION_WITH_SELF | Trying to chat with yourself |
| 404 | USER_NOT_FOUND | Target user does not exist |

---

### POST /api/conversations/group

Create a group conversation. The authenticated user becomes the owner and first member.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** CreateGroupConversationRequest
- **Response:** ConversationResponse
- **Status:** 201 Created

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | GROUP_NAME_REQUIRED | Empty group name |
| 400 | GROUP_TOO_SMALL | Fewer than 2 total members |
| 404 | USER_NOT_FOUND | A referenced user ID does not exist |

---

### PATCH /api/conversations/{conversation_id}

Rename a group conversation. Only the owner can do this.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** UpdateGroupRequest
- **Response:** ConversationResponse
- **Status:** 200 OK

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | INVALID_CONVERSATION_TYPE | Conversation is not a GROUP |
| 403 | NOT_GROUP_OWNER | Caller is not the owner |
| 404 | CONVERSATION_NOT_FOUND | Conversation does not exist |

---

### POST /api/conversations/{conversation_id}/members

Add a member to a group. Only the owner can do this.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** AddConversationMemberRequest
- **Response:** ConversationResponse
- **Status:** 200 OK

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | INVALID_CONVERSATION_TYPE | Conversation is not a GROUP |
| 403 | NOT_GROUP_OWNER | Caller is not the owner |
| 404 | CONVERSATION_NOT_FOUND | Conversation does not exist |
| 404 | USER_NOT_FOUND | Target user does not exist |
| 409 | USER_ALREADY_MEMBER | User is already in the group |

---

### DELETE /api/conversations/{conversation_id}/members/{user_id}

Remove a member from a group. Only the owner can do this. Cannot remove the owner.

- **Auth Required:** Yes (`@require_auth`)
- **Response:** ConversationResponse
- **Status:** 200 OK

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | INVALID_CONVERSATION_TYPE | Conversation is not a GROUP |
| 400 | CANNOT_REMOVE_OWNER | Trying to remove the owner |
| 403 | NOT_GROUP_OWNER | Caller is not the owner |
| 404 | CONVERSATION_NOT_FOUND | Conversation does not exist |
| 404 | USER_NOT_MEMBER | Target user is not a member |

---

### POST /api/conversations/{conversation_id}/leave

Leave a group conversation. The owner cannot leave.

- **Auth Required:** Yes (`@require_auth`)
- **Response:** `{ "message": "You have left the group" }`
- **Status:** 200 OK

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | INVALID_CONVERSATION_TYPE | Conversation is not a GROUP |
| 400 | CANNOT_LEAVE_AS_OWNER | Owner trying to leave |
| 403 | NOT_CONVERSATION_MEMBER | User is not a member |
| 404 | CONVERSATION_NOT_FOUND | Conversation does not exist |

---

### Message Endpoints

---

### GET /api/conversations/{conversation_id}/messages

Retrieve messages for a conversation with pagination. Must be a member.

- **Auth Required:** Yes (`@require_auth`)
- **Response:** MessageListResponse
- **Status:** 200 OK

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number (min 1) |
| limit | int | 50 | Messages per page (min 1, max 100) |

**Errors:**

| Status | Code | When |
|--------|------|------|
| 403 | NOT_CONVERSATION_MEMBER | User is not a member |
| 404 | CONVERSATION_NOT_FOUND | Conversation does not exist |

---

### POST /api/conversations/{conversation_id}/messages

Send a message to a conversation. Must be a member.

- **Auth Required:** Yes (`@require_auth`)
- **Request DTO:** SendMessageRequest
- **Response:** MessageResponse
- **Status:** 201 Created

**Errors:**

| Status | Code | When |
|--------|------|------|
| 400 | VALIDATION_ERROR | Empty message, too long, etc. |
| 403 | NOT_CONVERSATION_MEMBER | User is not a member |
| 404 | CONVERSATION_NOT_FOUND | Conversation does not exist |

---

### Attachment Endpoints

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

- If the attachment is linked to a message, only members of that conversation can download it.
- If the attachment is not yet linked to any message, any authenticated user who uploaded it can download it.
- The physical storage path is never exposed to the client.

**Errors:**

| Status | Code | When |
|--------|------|------|
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |
| 403 | NOT_CONVERSATION_MEMBER | Attachment belongs to a conversation user is not in |
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
- The server automatically joins the user to all `conversation:<id>` rooms for conversations they belong to.
- The server logs the connection and disconnection of each user.
- Uses the same JWT verification logic as REST endpoints.

---

### Client Event: send_message

Sent by the client to send a message to a specific conversation.

**Payload:**

```json
{
  "conversation_id": "conversation-uuid",
  "content": "Hello world",
  "attachment_id": null
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| conversation_id | string (UUID) | Yes | The conversation to send the message to |
| content | string or null | No* | Text content. Max length: `MAX_MESSAGE_LENGTH` (default 5000). |
| attachment_id | string or null | No* | UUID of a previously uploaded attachment. |

\* At least one of `content` or `attachment_id` must be provided.

**Behavior:**

1. Server verifies the socket is authenticated.
2. Verifies the sender is a member of the conversation.
3. Validates the payload using SendMessageRequest DTO.
4. If `attachment_id` is provided, verifies it belongs to the sender and is unused.
5. Encrypts the message content with AES-256-GCM.
6. Saves the message to the database.
7. Emits `receive_message` to the `conversation:<conversation_id>` room (only members).
8. If any step fails, sends an `error` event to the sender only.

---

### Server Event: receive_message

Emitted to the `conversation:<conversation_id>` room when a message is sent successfully. Only conversation members receive this event.

**Response DTO:** MessageResponse

**Payload:**

```json
{
  "id": "message-uuid",
  "conversation_id": "conversation-uuid",
  "sender_id": "user-uuid",
  "sender_username": "alice",
  "content": "Hello world",
  "created_at": "2026-01-01T00:00:00+00:00",
  "attachment": null
}
```

**Notes:**

- `content` is the decrypted plaintext. Empty string if attachment-only.
- `attachment` is `null` if the message has no attachment.
- Only members of the conversation receive this event.

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
| DIRECT_CONVERSATION_WITH_SELF | 400 | Cannot create a direct conversation with yourself |
| GROUP_NAME_REQUIRED | 400 | Group name is required |
| GROUP_TOO_SMALL | 400 | Group must have at least 2 members |
| CANNOT_REMOVE_OWNER | 400 | Cannot remove the group owner |
| CANNOT_LEAVE_AS_OWNER | 400 | Group owner cannot leave |
| INVALID_CONVERSATION_TYPE | 400 | Operation not valid for this conversation type |
| AUTHENTICATION_ERROR | 401 | Missing, invalid, or expired JWT token |
| INVALID_CREDENTIALS | 401 | Wrong username or password |
| AUTHORIZATION_ERROR | 403 | Authenticated but not authorized (e.g., non-admin accessing admin endpoint) |
| NOT_CONVERSATION_MEMBER | 403 | User is not a member of this conversation |
| NOT_GROUP_OWNER | 403 | Only the group owner can perform this action |
| CONVERSATION_NOT_FOUND | 404 | Conversation does not exist |
| USER_NOT_FOUND | 404 | User does not exist |
| USER_NOT_MEMBER | 404 | User is not a member of this conversation |
| ATTACHMENT_ERROR | 404 | Attachment does not exist |
| USER_ALREADY_EXISTS | 409 | Username already taken |
| USER_ALREADY_MEMBER | 409 | User is already a member of this conversation |
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
