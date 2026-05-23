"""Tests for envpack.verify."""
from __future__ import annotations

import pytest

from envpack.store import GitStore
from envpack.crypto import encrypt
from envpack.verify import verify_snapshots, VerifyReport, VerifyResult, VerifyError


PASSWORD = "s3cr3t"
PROFILE = "default"


@pytest.fixture()
def store(tmp_path):
    s = GitStore(tmp_path / "store")
    s.init()
    return s


def _seed(store: GitStore, name: str, plaintext: bytes, password: str = PASSWORD) -> None:
    ciphertext = encrypt(plaintext, password)
    store.save(PROFILE, name, ciphertext)


def test_empty_store_returns_empty_report(store):
    report = verify_snapshots(store, PASSWORD, PROFILE)
    assert report.results == []
    assert report.all_ok is True
    assert "No snapshots" in report.summary()


def test_valid_snapshots_all_ok(store):
    _seed(store, "snap1", b"KEY=value")
    _seed(store, "snap2", b"OTHER=123")
    report = verify_snapshots(store, PASSWORD, PROFILE)
    assert len(report.results) == 2
    assert report.all_ok is True
    assert "2 snapshot(s) verified" in report.summary()


def test_wrong_password_marks_failed(store):
    _seed(store, "snap1", b"KEY=value", password=PASSWORD)
    report = verify_snapshots(store, "wrongpassword", PROFILE)
    assert len(report.results) == 1
    assert report.all_ok is False
    assert report.results[0].ok is False
    assert report.results[0].error != ""


def test_mixed_results_summary(store):
    _seed(store, "good", b"A=1", password=PASSWORD)
    # Manually corrupt a snapshot with raw bytes that won't decrypt
    store.save(PROFILE, "bad", b"not-valid-ciphertext")
    report = verify_snapshots(store, PASSWORD, PROFILE)
    assert not report.all_ok
    assert len(report.failed) == 1
    assert "1/2" in report.summary()


def test_verify_result_str_ok():
    r = VerifyResult(snapshot="snap1", ok=True)
    assert "OK" in str(r)
    assert "snap1" in str(r)


def test_verify_result_str_fail():
    r = VerifyResult(snapshot="snap2", ok=False, error="bad tag")
    assert "FAIL" in str(r)
    assert "bad tag" in str(r)


def test_failed_property_filters_correctly(store):
    _seed(store, "ok_snap", b"X=1")
    store.save(PROFILE, "broken", b"garbage")
    report = verify_snapshots(store, PASSWORD, PROFILE)
    assert len(report.failed) == 1
    assert report.failed[0].snapshot == "broken"
