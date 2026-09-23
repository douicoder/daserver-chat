import pytest
import io


class TestAttachmentUpload:
    def test_upload_authenticated(self, client):
        reg = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        token = reg.get_json()["access_token"]

        data = {
            "file": (io.BytesIO(b"hello world"), "test.txt"),
        }
        response = client.post("/api/attachments", data=data, content_type="multipart/form-data", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 201
        result = response.get_json()
        assert "id" in result
        assert result["original_filename"] == "test.txt"

    def test_upload_unauthenticated(self, client):
        data = {
            "file": (io.BytesIO(b"hello world"), "test.txt"),
        }
        response = client.post("/api/attachments", data=data, content_type="multipart/form-data")
        assert response.status_code == 401

    def test_upload_no_file(self, client):
        reg = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        token = reg.get_json()["access_token"]
        response = client.post("/api/attachments", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 400

    def test_unsupported_file_type(self, client):
        reg = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        token = reg.get_json()["access_token"]

        data = {
            "file": (io.BytesIO(b"hello world"), "malware.exe"),
        }
        response = client.post("/api/attachments", data=data, content_type="multipart/form-data", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 415


class TestAttachmentDownload:
    def test_download_authenticated(self, client):
        reg = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        token = reg.get_json()["access_token"]

        data = {
            "file": (io.BytesIO(b"hello world"), "test.txt"),
        }
        upload = client.post("/api/attachments", data=data, content_type="multipart/form-data", headers={
            "Authorization": f"Bearer {token}"
        })
        attachment_id = upload.get_json()["id"]

        response = client.get(f"/api/attachments/{attachment_id}", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200

    def test_download_unauthenticated(self, client):
        response = client.get("/api/attachments/some-id")
        assert response.status_code == 401

    def test_download_nonexistent(self, client):
        reg = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        token = reg.get_json()["access_token"]
        response = client.get("/api/attachments/nonexistent-id", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 404
