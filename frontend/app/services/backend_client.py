import requests
from flask import current_app


class BackendClient:
    """Centralized HTTP client for communicating with the DaServer Chat backend."""

    def __init__(self, base_url=None):
        self.base_url = base_url or current_app.config["BACKEND_URL"]

    def _url(self, path):
        return f"{self.base_url}{path}"

    def _headers(self, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _handle_response(self, resp):
        """Return (status_code, json_body) tuple."""
        try:
            body = resp.json()
        except ValueError:
            body = None
        return resp.status_code, body

    # ── Auth ──────────────────────────────────────────────────────────

    def register(self, username, password):
        resp = requests.post(
            self._url("/api/auth/register"),
            json={"username": username, "password": password},
            timeout=10,
        )
        return self._handle_response(resp)

    def login(self, username, password):
        resp = requests.post(
            self._url("/api/auth/login"),
            json={"username": username, "password": password},
            timeout=10,
        )
        return self._handle_response(resp)

    def get_me(self, token):
        resp = requests.get(
            self._url("/api/auth/me"),
            headers=self._headers(token),
            timeout=10,
        )
        return self._handle_response(resp)

    # ── Users ─────────────────────────────────────────────────────────

    def search_users(self, token, query=""):
        resp = requests.get(
            self._url("/api/users/search"),
            headers=self._headers(token),
            params={"q": query},
            timeout=10,
        )
        return self._handle_response(resp)

    # ── Conversations ─────────────────────────────────────────────────

    def get_conversations(self, token):
        resp = requests.get(
            self._url("/api/conversations"),
            headers=self._headers(token),
            timeout=10,
        )
        return self._handle_response(resp)

    def get_conversation(self, token, conversation_id):
        resp = requests.get(
            self._url(f"/api/conversations/{conversation_id}"),
            headers=self._headers(token),
            timeout=10,
        )
        return self._handle_response(resp)

    def create_direct_conversation(self, token, user_id):
        resp = requests.post(
            self._url("/api/conversations/direct"),
            headers=self._headers(token),
            json={"user_id": user_id},
            timeout=10,
        )
        return self._handle_response(resp)

    def create_group_conversation(self, token, name, member_ids):
        resp = requests.post(
            self._url("/api/conversations/group"),
            headers=self._headers(token),
            json={"name": name, "member_ids": member_ids},
            timeout=10,
        )
        return self._handle_response(resp)

    def rename_group(self, token, conversation_id, name):
        resp = requests.patch(
            self._url(f"/api/conversations/{conversation_id}"),
            headers=self._headers(token),
            json={"name": name},
            timeout=10,
        )
        return self._handle_response(resp)

    def add_member(self, token, conversation_id, user_id):
        resp = requests.post(
            self._url(f"/api/conversations/{conversation_id}/members"),
            headers=self._headers(token),
            json={"user_id": user_id},
            timeout=10,
        )
        return self._handle_response(resp)

    def remove_member(self, token, conversation_id, user_id):
        resp = requests.delete(
            self._url(f"/api/conversations/{conversation_id}/members/{user_id}"),
            headers=self._headers(token),
            timeout=10,
        )
        return self._handle_response(resp)

    def leave_group(self, token, conversation_id):
        resp = requests.post(
            self._url(f"/api/conversations/{conversation_id}/leave"),
            headers=self._headers(token),
            timeout=10,
        )
        return self._handle_response(resp)

    # ── Messages ──────────────────────────────────────────────────────

    def get_messages(self, token, conversation_id, page=1, limit=50):
        resp = requests.get(
            self._url(f"/api/conversations/{conversation_id}/messages"),
            headers=self._headers(token),
            params={"page": page, "limit": limit},
            timeout=10,
        )
        return self._handle_response(resp)

    def send_message(self, token, conversation_id, content=None, attachment_id=None):
        payload = {}
        if content is not None:
            payload["content"] = content
        if attachment_id is not None:
            payload["attachment_id"] = attachment_id
        resp = requests.post(
            self._url(f"/api/conversations/{conversation_id}/messages"),
            headers=self._headers(token),
            json=payload,
            timeout=10,
        )
        return self._handle_response(resp)

    # ── Attachments ───────────────────────────────────────────────────

    def upload_attachment(self, token, file):
        resp = requests.post(
            self._url("/api/attachments"),
            headers={"Authorization": f"Bearer {token}"},
            files={"file": file},
            timeout=30,
        )
        return self._handle_response(resp)

    def get_attachment_url(self, attachment_id):
        return self._url(f"/api/attachments/{attachment_id}")

    # ── Admin ─────────────────────────────────────────────────────────

    def admin_get_users(self, token):
        resp = requests.get(
            self._url("/api/admin/users"),
            headers=self._headers(token),
            timeout=10,
        )
        return self._handle_response(resp)

    def admin_change_password(self, token, user_id, new_password):
        resp = requests.post(
            self._url(f"/api/admin/users/{user_id}/password"),
            headers=self._headers(token),
            json={"new_password": new_password},
            timeout=10,
        )
        return self._handle_response(resp)
