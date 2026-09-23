# DaServer Chat

Private family chat. Monorepo with Flask backend (REST + Socket.IO) and Flask frontend.

```
daserver-chat/
├── backend/    # API + Socket.IO server, port 5000
├── frontend/   # Web UI, port 3000
├── start.sh    # run both in background (nohup)
├── stop.sh     # stop background servers
└── status.sh   # check if background servers are running
```

## 1. Setup (first time only)

Requirements: Python 3.12+ (backend), Python 3.8+ (frontend).

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set:
#   JWT_SECRET_KEY=$(openssl rand -hex 32)
#   MESSAGE_ENCRYPTION_KEY=$(openssl rand -hex 32)  # 64-char hex, required
#   CORS_ALLOWED_ORIGINS=http://localhost:3000
python run.py create-admin   # create admin user
deactivate

# Frontend
cd ../frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: BACKEND_URL=http://localhost:5000
deactivate
```

## 2. Start the server (background)

`start.sh` runs both servers in the background with `nohup`, so they keep
running after you close the terminal. PIDs go in `.pids/`, output in `.logs/`.

```bash
./start.sh
./status.sh   # check RUNNING / STOPPED
tail -f .logs/backend.log .logs/frontend.log  # watch logs
```

- Backend: http://localhost:5000
- Frontend: http://localhost:3000
- Logs: `.logs/backend.log`, `.logs/frontend.log`

Or run manually in two terminals:

```bash
# Terminal 1 — backend
cd backend && source venv/bin/activate && python run.py

# Terminal 2 — frontend
cd frontend && source venv/bin/activate && python run.py
```

## 3. Stop the server

```bash
./stop.sh
```

If started manually, press `Ctrl+C` in each terminal.

## 4. Restart

```bash
./stop.sh
./start.sh
```

## Notes

- `.env`, `venv/`, `*.db`, and uploaded files in `backend/storage/attachments/` are never committed.
- Full API docs: `backend/apidocs.md`.
