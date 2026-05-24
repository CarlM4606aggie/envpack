"""Tests for envpack.share."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envpack.store import GitStore
from envpack.crypto import encrypt
from envpack.share import (
    ShareError,
    ShareBundle,
    export_bundle,
    import_bundle,
    read_bundle,
    write_bundle,
)


PLAINTEXT = b"API_KEY=secret123\nDB_URL=postgres://localhost/db\n"
STORE_PASS = "store-pass"
SHARE_PASS = "share-pass"


@pytest.fixture()
def store(tmp_path: Path) -> GitStore:
    s = GitStore(tmp_path / "store")
    s.init()
    return s


@pytest.fixture()
def seeded_store(store: GitStore) -> GitStore:
    ciphertext = encrypt(PLAINTEXT, STORE_PASS)
    store.save("prod", ciphertext)
    return store


def test_export_bundle_returns_share_bundle(seeded_store: GitStore) -> None:
    bundle = export_bundle(seeded_store, "prod", STORE_PASS, SHARE_PASS)
    assert isinstance(bundle, ShareBundle)
    assert bundle.snapshot_name == "prod"


def test_export_bundle_checksum_is_valid(seeded_store: GitStore) -> None:
    bundle = export_bundle(seeded_store, "prod", STORE_PASS, SHARE_PASS)
    assert bundle.verify()


def test_export_bundle_missing_snapshot_raises(store: GitStore) -> None:
    with pytest.raises(ShareError, match="not found"):
        export_bundle(store, "nonexistent", STORE_PASS, SHARE_PASS)


def test_export_bundle_wrong_password_raises(seeded_store: GitStore) -> None:
    with pytest.raises(ShareError, match="Decryption failed"):
        export_bundle(seeded_store, "prod", "wrong-pass", SHARE_PASS)


def test_write_and_read_bundle_round_trip(seeded_store: GitStore, tmp_path: Path) -> None:
    bundle = export_bundle(seeded_store, "prod", STORE_PASS, SHARE_PASS)
    dest = tmp_path / "prod.bundle.json"
    write_bundle(bundle, dest)
    loaded = read_bundle(dest)
    assert loaded.snapshot_name == bundle.snapshot_name
    assert loaded.ciphertext == bundle.ciphertext
    assert loaded.verify()


def test_read_bundle_detects_tampered_checksum(seeded_store: GitStore, tmp_path: Path) -> None:
    bundle = export_bundle(seeded_store, "prod", STORE_PASS, SHARE_PASS)
    dest = tmp_path / "prod.bundle.json"
    write_bundle(bundle, dest)
    data = json.loads(dest.read_text())
    data["checksum"] = "deadbeef"
    dest.write_text(json.dumps(data))
    with pytest.raises(ShareError, match="checksum mismatch"):
        read_bundle(dest)


def test_import_bundle_restores_plaintext(seeded_store: GitStore, tmp_path: Path) -> None:
    bundle = export_bundle(seeded_store, "prod", STORE_PASS, SHARE_PASS)
    dest = tmp_path / "prod.bundle.json"
    write_bundle(bundle, dest)
    loaded = read_bundle(dest)

    new_store = GitStore(tmp_path / "new_store")
    new_store.init()
    import_bundle(new_store, loaded, SHARE_PASS, "new-pass", snapshot_name="prod-copy")

    from envpack.crypto import decrypt
    raw = new_store.load("prod-copy")
    assert decrypt(raw, "new-pass") == PLAINTEXT


def test_import_bundle_wrong_share_password_raises(seeded_store: GitStore, tmp_path: Path) -> None:
    bundle = export_bundle(seeded_store, "prod", STORE_PASS, SHARE_PASS)
    new_store = GitStore(tmp_path / "ns")
    new_store.init()
    with pytest.raises(ShareError, match="Decryption failed"):
        import_bundle(new_store, bundle, "wrong", STORE_PASS)
