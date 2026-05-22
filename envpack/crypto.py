"""Encryption and decryption utilities for .env file contents."""

import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet


SALT_SIZE = 16
ITERATIONS = 390000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt(plaintext: str, password: str) -> bytes:
    """Encrypt plaintext string using a password.

    Returns raw bytes: [salt (16 bytes)] + [fernet token].
    """
    salt = os.urandom(SALT_SIZE)
    key = _derive_key(password, salt)
    token = Fernet(key).encrypt(plaintext.encode())
    return salt + token


def decrypt(data: bytes, password: str) -> str:
    """Decrypt bytes produced by :func:`encrypt` using a password.

    Raises:
        ValueError: If decryption fails (wrong password or corrupted data).
    """
    if len(data) <= SALT_SIZE:
        raise ValueError("Encrypted data is too short or malformed.")
    salt, token = data[:SALT_SIZE], data[SALT_SIZE:]
    key = _derive_key(password, salt)
    try:
        return Fernet(key).decrypt(token).decode()
    except Exception as exc:
        raise ValueError("Decryption failed: wrong password or corrupted data.") from exc
