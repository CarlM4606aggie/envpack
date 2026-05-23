"""Tests for envpack.rotate."""

from __future__ import annotations

import pytest

from envpack.crypto import decrypt, encrypt
from envpack.rotate import RotateError, RotationResult, rotate_snapshots
from envpack.store import GitStore


OLD_PASS = "old-secret"
NEW_PASS = "new-secret"
PROFILE = "default"


@pytest.fixture()
def store(tmp_path):
    s = GitStore(tmp_path / "store")
    s.init()
    return s


def _seed(store: GitStore, name: str, plaintext: bytes) -> None:
    ct = encrypt(plaintext, OLD_PASS)
    store.save(PROFILE, name, ct, message=f"seed {name}")


def test_rotate_re_encrypts_all_snapshots(store):
    _seed(store, "snap1", b"KEY=value1")
    _seed(store, "snap2", b"KEY=value2")

    result = rotate_snapshots(store, OLD_PASS, NEW_PASS, PROFILE)

    assert result.success
    assert set(result.rotated) == {"snap1", "snap2"}
    assert result.failed == []


def test_rotated_data_decryptable_with_new_password(store):
    _seed(store, "snap1", b"SECRET=hello")

    rotate_snapshots(store, OLD_PASS, NEW_PASS, PROFILE)

    ct = store.load(PROFILE, "snap1")
    assert decrypt(ct, NEW_PASS) == b"SECRET=hello"


def test_rotated_data_not_decryptable_with_old_password(store):
    from envpack.crypto import decrypt as _decrypt
    from cryptography.fernet import InvalidToken

    _seed(store, "snap1", b"SECRET=hello")
    rotate_snapshots(store, OLD_PASS, NEW_PASS, PROFILE)

    ct = store.load(PROFILE, "snap1")
    with pytest.raises(Exception):
        _decrypt(ct, OLD_PASS)


def test_rotate_empty_store_returns_empty_result(store):
    result = rotate_snapshots(store, OLD_PASS, NEW_PASS, PROFILE)
    assert result.rotated == []
    assert result.failed == []
    assert result.success


def test_rotation_result_summary_contains_names(store):
    _seed(store, "alpha", b"A=1")
    result = rotate_snapshots(store, OLD_PASS, NEW_PASS, PROFILE)
    summary = result.summary()
    assert "alpha" in summary
    assert "Rotated: 1" in summary


def test_wrong_old_password_records_failure(store):
    _seed(store, "snap1", b"X=1")
    result = rotate_snapshots(store, "wrong-password", NEW_PASS, PROFILE)
    assert "snap1" in result.failed
    assert result.rotated == []
    assert not result.success
