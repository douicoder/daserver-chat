import pytest


class TestAdminAuthorization:
    def test_normal_user_cannot_list_users(self, client):
        reg = client.post("/api/auth/register", json={
            "username": "normaluser",
            "password": "password123",
        })
        token = reg.get_json()["access_token"]
        response = client.get("/api/admin/users", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 403

    def test_admin_can_list_users(self, client):
        from app.database.database import SessionLocal
        from app.models.user import User
        from app.security.password import hash_password

        db = SessionLocal()
        admin = User(username="admin", password_hash=hash_password("admin123"), is_admin=True)
        db.add(admin)
        db.commit()
        db.close()

        login = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        token = login.get_json()["access_token"]
        response = client.get("/api/admin/users", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        users = response.get_json()
        assert len(users) >= 1

    def test_admin_can_change_password(self, client):
        from app.database.database import SessionLocal
        from app.models.user import User
        from app.security.password import hash_password

        db = SessionLocal()
        admin = User(username="admin", password_hash=hash_password("admin123"), is_admin=True)
        target = User(username="target", password_hash=hash_password("oldpass123"), is_admin=False)
        db.add(admin)
        db.add(target)
        db.commit()
        target_id = target.id
        db.close()

        login = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        token = login.get_json()["access_token"]

        response = client.post(f"/api/admin/users/{target_id}/password", json={
            "new_password": "newpass123",
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200

        # Verify new password works
        login2 = client.post("/api/auth/login", json={
            "username": "target",
            "password": "newpass123",
        })
        assert login2.status_code == 200

        # Verify old password no longer works
        login3 = client.post("/api/auth/login", json={
            "username": "target",
            "password": "oldpass123",
        })
        assert login3.status_code == 401
