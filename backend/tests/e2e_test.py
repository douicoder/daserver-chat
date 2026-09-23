import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import urllib.request
import urllib.error
import json
import uuid
import subprocess

BASE = "http://localhost:5000"
passed = 0
failed = 0


def req(method, path, body=None, token=None, raw=False):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        body_out = resp.read()
        if raw:
            return resp.status, body_out
        return resp.status, json.loads(body_out)
    except urllib.error.HTTPError as e:
        body_out = e.read()
        if raw:
            return e.code, body_out
        try:
            return e.code, json.loads(body_out)
        except Exception:
            return e.code, body_out


def register_or_login(username, password):
    """Register a user; if already exists, login instead. Returns token."""
    status, data = req("POST", "/api/auth/register", {"username": username, "password": password})
    if status == 201:
        return data.get("access_token")
    # Already exists, try login
    status, data = req("POST", "/api/auth/login", {"username": username, "password": password})
    if status == 200:
        return data.get("access_token")
    return None


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name} {detail}")
    else:
        failed += 1
        print(f"  FAIL  {name} {detail}")


print("=" * 60)
print("  E2E TEST SUITE")
print("=" * 60)

# === 1. Registration ===
print("\n[1] Registration")

status, data = req("POST", "/api/auth/register", {"username": "alice", "password": "pass1234"})
if status == 201:
    check("Register alice", True, f"(status={status})")
    alice_token = data.get("access_token")
elif status == 409:
    check("Register alice (already exists, skip)", True)
    status2, data2 = req("POST", "/api/auth/login", {"username": "alice", "password": "pass1234"})
    alice_token = data2.get("access_token") if status2 == 200 else None
else:
    check("Register alice", False, f"(status={status})")
    alice_token = None

alice_user = data.get("user", {}) if isinstance(data, dict) else {}
if alice_token:
    check("alice has token", True)
    if alice_user:
        check("alice username correct", alice_user.get("username") == "alice")
        check("alice is not admin", alice_user.get("is_admin") is False)

status, data = req("POST", "/api/auth/register", {"username": "bob", "password": "pass1234"})
if status == 201:
    check("Register bob", True, f"(status={status})")
    bob_token = data.get("access_token")
elif status == 409:
    check("Register bob (already exists, skip)", True)
    status2, data2 = req("POST", "/api/auth/login", {"username": "bob", "password": "pass1234"})
    bob_token = data2.get("access_token") if status2 == 200 else None
else:
    check("Register bob", False, f"(status={status})")
    bob_token = None

status, _ = req("POST", "/api/auth/register", {"username": "alice", "password": "pass1234"})
check("Duplicate username rejected", status == 409, f"(status={status})")

status, _ = req("POST", "/api/auth/register", {"username": "", "password": "pass1234"})
check("Empty username rejected", status == 400, f"(status={status})")

status, _ = req("POST", "/api/auth/register", {"username": "short", "password": "12345"})
check("Short password rejected", status == 400, f"(status={status})")

# === 2. Login ===
print("\n[2] Login")

status, data = req("POST", "/api/auth/login", {"username": "alice", "password": "pass1234"})
check("Login alice", status == 200, f"(status={status})")
check("Login returns token", isinstance(data, dict) and "access_token" in data)

status, _ = req("POST", "/api/auth/login", {"username": "alice", "password": "wrongpass"})
check("Wrong password rejected", status == 401, f"(status={status})")

status, _ = req("POST", "/api/auth/login", {"username": "nouser", "password": "pass1234"})
check("Nonexistent user rejected", status == 401, f"(status={status})")

# === 3. JWT Auth ===
print("\n[3] JWT Authentication")

status, data = req("GET", "/api/auth/me", token=alice_token)
check("Get /me authenticated", status == 200 and isinstance(data, dict) and data.get("username") == "alice", f"(status={status})")

status, _ = req("GET", "/api/auth/me")
check("Get /me no token", status == 401, f"(status={status})")

status, _ = req("GET", "/api/auth/me", token="invalid.jwt.token")
check("Get /me invalid token", status == 401, f"(status={status})")

# === 4. Messages ===
print("\n[4] Messages")

status, data = req("GET", "/api/messages?page=1&limit=10", token=alice_token)
check("Get messages", status == 200, f"(status={status})")
check("Pagination present", isinstance(data, dict) and "pagination" in data)

status, _ = req("GET", "/api/messages")
check("Get messages unauth", status == 401, f"(status={status})")

# === 5. Attachments ===
print("\n[5] Attachments")

# Upload
boundary = str(uuid.uuid4())
file_content = b"Hello, this is a test file!"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
    f"Content-Type: text/plain\r\n\r\n"
).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()

req_up = urllib.request.Request(
    f"{BASE}/api/attachments", data=body,
    headers={"Authorization": f"Bearer {alice_token}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST",
)
try:
    resp = urllib.request.urlopen(req_up)
    attach_data = json.loads(resp.read())
    attach_status = resp.status
except urllib.error.HTTPError as e:
    attach_data = json.loads(e.read())
    attach_status = e.code

check("Upload file", attach_status == 201, f"(status={attach_status})")
attachment_id = attach_data.get("id") if isinstance(attach_data, dict) else None
check("Upload returns id", attachment_id is not None)
check("Upload returns original_filename", isinstance(attach_data, dict) and attach_data.get("original_filename") == "test.txt")
check("Upload returns mime_type", isinstance(attach_data, dict) and "text" in (attach_data.get("mime_type") or ""))

# Download
if attachment_id:
    status, file_data = req("GET", f"/api/attachments/{attachment_id}", token=alice_token, raw=True)
    check("Download file", status == 200 and file_data == file_content, f"(status={status})")
else:
    check("Download file", False, "(no attachment_id)")

# Download unauth
status, _ = req("GET", f"/api/attachments/{attachment_id or 'fake'}", raw=True)
check("Download unauth", status == 401, f"(status={status})")

# Download nonexistent
status, _ = req("GET", "/api/attachments/fake-id-123", token=alice_token, raw=True)
check("Download nonexistent", status == 404, f"(status={status})")

# Unsupported file type
boundary2 = str(uuid.uuid4())
bad_body = (
    f"--{boundary2}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="malware.exe"\r\n'
    f"Content-Type: application/octet-stream\r\n\r\n"
).encode() + b"not a virus" + f"\r\n--{boundary2}--\r\n".encode()

req_bad = urllib.request.Request(
    f"{BASE}/api/attachments", data=bad_body,
    headers={"Authorization": f"Bearer {alice_token}", "Content-Type": f"multipart/form-data; boundary={boundary2}"},
    method="POST",
)
try:
    resp = urllib.request.urlopen(req_bad)
    bad_status = resp.status
except urllib.error.HTTPError as e:
    bad_status = e.code
check("Unsupported file type rejected", bad_status == 415, f"(status={bad_status})")

# Upload unauth
boundary3 = str(uuid.uuid4())
unauth_body = (
    f"--{boundary3}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
    f"Content-Type: text/plain\r\n\r\n"
).encode() + b"content" + f"\r\n--{boundary3}--\r\n".encode()

req_unauth = urllib.request.Request(
    f"{BASE}/api/attachments", data=unauth_body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary3}"},
    method="POST",
)
try:
    resp = urllib.request.urlopen(req_unauth)
    unauth_status = resp.status
except urllib.error.HTTPError as e:
    unauth_status = e.code
check("Upload unauth rejected", unauth_status == 401, f"(status={unauth_status})")

# === 6. Admin ===
print("\n[6] Admin")

# Create admin user directly
result = subprocess.run([
    os.path.join(os.getcwd(), "venv", "Scripts", "python"),
    os.path.join(os.getcwd(), "tests", "create_test_admin.py"),
], capture_output=True, text=True)
print(f"    (admin setup: {result.stdout.strip()} {result.stderr.strip()})")

status, data = req("POST", "/api/auth/login", {"username": "admin_e2e", "password": "admin123"})
admin_token = data.get("access_token") if isinstance(data, dict) else None
check("Login as admin", status == 200 and admin_token is not None, f"(status={status})")

status, _ = req("GET", "/api/admin/users", token=alice_token)
check("Normal user -> admin denied", status == 403, f"(status={status})")

status, data = req("GET", "/api/admin/users", token=admin_token)
user_count = len(data) if isinstance(data, list) else 0
check("Admin lists users", status == 200 and user_count >= 3, f"(status={status}, count={user_count})")

# Change bob's password
bob_id = None
if isinstance(data, list):
    for u in data:
        if u["username"] == "bob":
            bob_id = u["id"]
            break

if bob_id:
    status, _ = req("POST", f"/api/admin/users/{bob_id}/password", {"new_password": "newpass999"}, token=admin_token)
    check("Admin changes password", status == 200, f"(status={status})")

    status, _ = req("POST", "/api/auth/login", {"username": "bob", "password": "newpass999"})
    check("New password works", status == 200, f"(status={status})")

    status, _ = req("POST", "/api/auth/login", {"username": "bob", "password": "pass1234"})
    check("Old password fails", status == 401, f"(status={status})")
else:
    check("Admin changes password", False, "(bob not found in user list)")

# === Summary ===
print("\n" + "=" * 60)
total = passed + failed
print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    sys.exit(1)
