"""Fernet encryption helpers for Facebook access tokens."""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


def encrypt_token(plaintext: str, key: str) -> str:
    """Encrypt a plaintext token. Returns base64-encoded ciphertext string."""
    f = Fernet(key.encode() if isinstance(key, str) else key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str, key: str) -> str:
    """Decrypt a Fernet-encrypted token. Raises ValueError on tampered data."""
    f = Fernet(key.encode() if isinstance(key, str) else key)
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt token: invalid or tampered ciphertext")
