import pytest
from app.security.password import hash_password, verify_password


class TestPasswordHashing:
    def test_password_is_hashed(self):
        password = "mypassword123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_plaintext_not_stored(self):
        password = "mypassword123"
        hashed = hash_password(password)
        assert password not in hashed

    def test_verify_correct_password(self):
        password = "mypassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        password = "mypassword123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        password = "mypassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # Argon2id uses random salt, so hashes should differ
        assert hash1 != hash2
