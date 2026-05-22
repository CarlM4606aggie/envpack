"""Tests for envpack.crypto encryption/decryption module."""

import pytest
from envpack.crypto import encrypt, decrypt, SALT_SIZE


PASSWORD = "s3cr3t-passphrase"
SAMPLE_ENV = "DATABASE_URL=postgres://user:pass@localhost/db\nDEBUG=true\n"


def test_encrypt_returns_bytes():
    result = encrypt(SAMPLE_ENV, PASSWORD)
    assert isinstance(result, bytes)


def test_encrypted_length_greater_than_salt():
    result = encrypt(SAMPLE_ENV, PASSWORD)
    assert len(result) > SALT_SIZE


def test_round_trip():
    encrypted = encrypt(SAMPLE_ENV, PASSWORD)
    decrypted = decrypt(encrypted, PASSWORD)
    assert decrypted == SAMPLE_ENV


def test_different_passwords_produce_different_ciphertext():
    enc1 = encrypt(SAMPLE_ENV, "password1")
    enc2 = encrypt(SAMPLE_ENV, "password2")
    assert enc1 != enc2


def test_same_plaintext_produces_different_ciphertext_each_time():
    """Salt randomness ensures ciphertext differs across calls."""
    enc1 = encrypt(SAMPLE_ENV, PASSWORD)
    enc2 = encrypt(SAMPLE_ENV, PASSWORD)
    assert enc1 != enc2


def test_decrypt_wrong_password_raises():
    encrypted = encrypt(SAMPLE_ENV, PASSWORD)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(encrypted, "wrong-password")


def test_decrypt_malformed_data_raises():
    with pytest.raises(ValueError):
        decrypt(b"tooshort", PASSWORD)


def test_decrypt_corrupted_token_raises():
    encrypted = bytearray(encrypt(SAMPLE_ENV, PASSWORD))
    encrypted[SALT_SIZE + 5] ^= 0xFF  # flip a byte in the token
    with pytest.raises(ValueError):
        decrypt(bytes(encrypted), PASSWORD)


def test_empty_string_round_trip():
    encrypted = encrypt("", PASSWORD)
    assert decrypt(encrypted, PASSWORD) == ""
