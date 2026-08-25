"""AES-256-GCM + PBKDF2-HMAC-SHA256 vault cryptography.

KDF parameters (study project, documented in one place):
    ALGORITHM  = PBKDF2-HMAC-SHA256
    ITERATIONS = 200_000
    SALT_LEN   = 16 bytes
    KEY_LEN    = 32 bytes (AES-256)
    NONCE_LEN  = 12 bytes (GCM)
"""

from __future__ import annotations

import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITERATIONS = 200_000
SALT_LEN = 16
KEY_LEN = 32
NONCE_LEN = 12


class CryptoError(Exception):
    pass


def new_salt() -> bytes:
    return os.urandom(SALT_LEN)


def derive_key(password: str, salt: bytes) -> bytes:
    if not password:
        raise CryptoError("Master password is required.")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt(plaintext: bytes, key: bytes) -> bytes:
    nonce = os.urandom(NONCE_LEN)
    ct = AESGCM(key).encrypt(nonce, plaintext, None)
    return nonce + ct


def decrypt(blob: bytes, key: bytes) -> bytes:
    if len(blob) < NONCE_LEN + 16:
        raise CryptoError("Ciphertext is truncated.")
    nonce, ct = blob[:NONCE_LEN], blob[NONCE_LEN:]
    try:
        return AESGCM(key).decrypt(nonce, ct, None)
    except InvalidTag as exc:
        raise CryptoError("Incorrect master password or corrupted data.") from exc
