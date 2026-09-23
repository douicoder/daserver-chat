# Chat Backend

A small, clean, secure, real-time chat backend with authentication and file sharing.

## Technology Stack

- Python 3.12+
- Flask + Flask-SocketIO
- SQLAlchemy + SQLite
- Pydantic (DTO validation)
- Argon2id (password hashing)
- JWT (authentication)
- AES-256-GCM (message encryption at rest)

## Architecture

```
Controller → Service → Repository → Database
Controller → AttachmentService → FileStorage
```

### Project Structure

```
chat-backend/
├── app/
│   ├── api/            # REST controllers
│   ├── sockets/        # Socket.IO handlers
│   ├── dto/            # Pydantic DTOs
│   ├── models/         # SQLAlchemy models
│   ├── repositories/   # Database operations
│   ├── services/       # Business logic
│   ├── security/       # Password, JWT, encryption
│   ├── storage/        # File storage
│   ├── database/       # DB engine/session
│   └── exceptions/     # Custom exceptions
├── tests/
├── storage/attachments/
├── .env
├── requirements.txt
└── run.py
```

## Installation

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

## Environment Configuration

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

Required secrets:
- `JWT_SECRET_KEY` — Random string for signing JWTs
- `MESSAGE_ENCRYPTION_KEY` — 64-character hex string (32 bytes) for AES-256-GCM

## File Storage Configuration

Ensure the storage directory exists:

```bash
mkdir -p storage/attachments
```

## Running the Server

```bash
python run.py
```

Server starts on `http://0.0.0.0:5000`.

## Create Admin User

```bash
python run.py create-admin
```

## Running Tests

```bash
pytest tests/ -v
```

## REST API

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register` | Register a new user | No |
| POST | `/api/auth/login` | Login | No |
| GET | `/api/auth/me` | Get current user | Yes |

**Register / Login Request:**
```json
{ "username": "string", "password": "string" }
```

**Response:**
```json
{
  "access_token": "jwt-token",
  "expires_at": "2026-01-01T00:00:00",
  "user": { "id": "...", "username": "...", "is_admin": false }
}
```

### Users

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/users/me` | Get current user | Yes |

### Messages

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/messages?page=1&limit=50` | Get message history (paginated) | Yes |

### Attachments

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/attachments` | Upload a file (multipart/form-data) | Yes |
| GET | `/api/attachments/<id>` | Download a file | Yes |

### Admin

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/admin/users` | List all users | Admin |
| POST | `/api/admin/users/<user_id>/password` | Change user password | Admin |

**Change Password Request:**
```json
{ "new_password": "string" }
```

## Socket.IO

### Connection

Connect with JWT as query parameter:

```javascript
const socket = io("http://localhost:5000", {
  query: { token: "your-jwt-token" }
});
```

### Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client → Server | Authenticate via query token |
| `disconnect` | Client → Server | User disconnected |
| `send_message` | Client → Server | Send a message |
| `receive_message` | Server → Client | Broadcast received message |
| `error` | Server → Client | Error response |

**send_message payload:**
```json
{
  "content": "Hello!",
  "attachment_id": null
}
```

**receive_message payload:**
```json
{
  "id": "message-id",
  "sender_id": "user-id",
  "sender_username": "username",
  "content": "Hello!",
  "created_at": "2026-01-01T00:00:00",
  "attachment": null
}
```

## Authentication

All protected endpoints require the `Authorization` header:

```
Authorization: Bearer <jwt-token>
```

JWT contains: `sub` (user ID), `username`, `is_admin`, `iat`, `exp`.

## Security Notes

- Passwords are hashed with Argon2id (never stored in plaintext)
- Messages are encrypted with AES-256-GCM before storage
- Each message uses a unique 96-bit nonce
- Encryption key is loaded from environment variable (never hardcoded)
- File uploads are validated by size, extension, and content signature
- Random filenames prevent path traversal
- CORS is configurable per environment
- Admin endpoints require `is_admin` claim in JWT
