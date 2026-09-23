import pytest
from app.security.encryption import encrypt, decrypt


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "Hello, World!"
        ciphertext, nonce = encrypt(plaintext)
        decrypted = decrypt(ciphertext, nonce)
        assert decrypted == plaintext

    def test_ciphertext_differs_from_plaintext(self):
        plaintext = "Hello, World!"
        ciphertext, nonce = encrypt(plaintext)
        assert ciphertext != plaintext.encode("utf-8")

    def test_unique_nonce_per_encryption(self):
        plaintext = "Same message"
        _, nonce1 = encrypt(plaintext)
        _, nonce2 = encrypt(plaintext)
        assert nonce1 != nonce2

    def test_plaintext_not_stored(self):
        plaintext = "Sensitive data"
        ciphertext, nonce = encrypt(plaintext)
        assert plaintext.encode("utf-8") not in ciphertext

    def test_empty_string(self):
        plaintext = ""
        ciphertext, nonce = encrypt(plaintext)
        decrypted = decrypt(ciphertext, nonce)
        assert decrypted == plaintext

    def test_unicode(self):
        plaintext = "こんにちは世界 🔐"
        ciphertext, nonce = encrypt(plaintext)
        decrypted = decrypt(ciphertext, nonce)
        assert decrypted == plaintext
