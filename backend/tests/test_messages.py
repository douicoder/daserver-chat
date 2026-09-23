import pytest
import json


class TestMessageRetrieval:
    def test_get_messages_authenticated(self, client):
        reg = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        token = reg.get_json()["access_token"]
        response = client.get("/api/messages", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "messages" in data
        assert "pagination" in data

    def test_get_messages_unauthenticated(self, client):
        response = client.get("/api/messages")
        assert response.status_code == 401

    def test_pagination(self, client):
        reg = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
        })
        token = reg.get_json()["access_token"]
        response = client.get("/api/messages?page=1&limit=10", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10
