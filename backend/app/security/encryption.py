import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import Config


def encrypt(plaintext: str) -> tuple[bytes, bytes]:
    """Encrypt plaintext with AES-256-GCM. Returns (ciphertext, nonce)."""
    key = bytes.fromhex(Config.MESSAGE_ENCRYPTION_KEY)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return ciphertext, nonce


def decrypt(ciphertext: bytes, nonce: bytes) -> str:
    """Decrypt ciphertext with AES-256-GCM. Returns plaintext string."""
    key = bytes.fromhex(Config.MESSAGE_ENCRYPTION_KEY)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
