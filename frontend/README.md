# DaServer Chat Frontend

A private family chat frontend built with Flask, Jinja2, vanilla JavaScript, and Socket.IO.

## Requirements

- Python 3.8+
- A running DaServer Chat backend

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env and set BACKEND_URL to your backend address

# Run the frontend
python run.py
```

The frontend runs at `http://localhost:3000`.

## Features

- Authentication (login, register, logout)
- Direct conversations
- Group conversations
- Real-time messaging via Socket.IO
- File attachments (upload, display, download)
- Group management (rename, add/remove members, leave)
- Admin panel (user list, password management)
- Responsive design (desktop + mobile)
- Dark, flat, minimal UI

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://localhost:5000` | Backend API URL |
| `FLASK_SECRET_KEY` | `dev-secret-change-in-production` | Flask session secret |

## Structure

```
app/            Flask application (routes, services)
templates/      Jinja2 HTML templates
static/css/     Styles
static/js/      Client-side JavaScript
```

## API Contract

All backend API behavior is defined in `apidocs.md`. The frontend does not modify or extend the backend API.
