import pytest
import json


class TestRegistration:
    def test_register_success(self, client):
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        assert response.status_code == 201
        data = response.get_json()
        assert "access_token" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["is_admin"] is False

    def test_register_duplicate_username(self, client):
        client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password456",
        })
        assert response.status_code == 409

    def test_register_empty_username(self, client):
        response = client.post("/api/auth/register", json={
            "username": "",
            "password": "password123",
        })
        assert response.status_code == 400

    def test_register_short_password(self, client):
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "12345",
        })
        assert response.status_code == 400


class TestLogin:
    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/auth/login", json={
            "username": "nouser",
            "password": "password123",
        })
        assert response.status_code == 401


class TestJWTAuth:
    def test_get_me_authenticated(self, client):
        reg = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        token = reg.get_json()["access_token"]
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        assert response.get_json()["username"] == "testuser"

    def test_get_me_no_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalidtoken123"
        })
        assert response.status_code == 401
