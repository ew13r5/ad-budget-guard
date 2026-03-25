"""Tests for Fernet token encryption helpers."""
import pytest
from cryptography.fernet import Fernet

from app.services.crypto import encrypt_token, decrypt_token

KEY = Fernet.generate_key().decode()


class TestCrypto:
    def test_encrypt_produces_different_output(self):
        encrypted = encrypt_token("my-secret-token", KEY)
        assert encrypted != "my-secret-token"
        assert len(encrypted) > 0

    def test_round_trip(self):
        original = "fb_access_token_abc123"
        encrypted = encrypt_token(original, KEY)
        decrypted = decrypt_token(encrypted, KEY)
        assert decrypted == original

    def test_tampered_ciphertext_raises(self):
        encrypted = encrypt_token("test", KEY)
        tampered = encrypted[:-5] + "XXXXX"
        with pytest.raises(ValueError, match="tampered"):
            decrypt_token(tampered, KEY)
