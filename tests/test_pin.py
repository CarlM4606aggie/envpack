"""Tests for envpack.pin."""
from __future__ import annotations

import pytest
from pathlib import Path

from envpack.pin import PinError, PinIndex, load_index


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# PinIndex unit tests
# ---------------------------------------------------------------------------

def test_empty_index_has_no_pins(store):
    idx = load_index(store)
    assert idx.list_pins() == []


def test_pin_adds_name(store):
    idx = load_index(store)
    idx.pin("v1")
    assert "v1" in idx.list_pins()


def test_pin_is_idempotent(store):
    idx = load_index(store)
    idx.pin("v1")
    idx.pin("v1")
    assert idx.list_pins().count("v1") == 1


def test_pin_empty_name_raises(store):
    idx = load_index(store)
    with pytest.raises(PinError):
        idx.pin("")


def test_unpin_removes_name(store):
    idx = load_index(store)
    idx.pin("v1")
    idx.unpin("v1")
    assert "v1" not in idx.list_pins()


def test_unpin_nonexistent_is_noop(store):
    idx = load_index(store)
    idx.unpin("ghost")  # should not raise


def test_is_pinned_true(store):
    idx = load_index(store)
    idx.pin("snap")
    assert idx.is_pinned("snap") is True


def test_is_pinned_false(store):
    idx = load_index(store)
    assert idx.is_pinned("snap") is False


def test_persistence_across_loads(store):
    idx = load_index(store)
    idx.pin("persistent")

    idx2 = load_index(store)
    assert idx2.is_pinned("persistent")


def test_multiple_pins(store):
    idx = load_index(store)
    for name in ["a", "b", "c"]:
        idx.pin(name)
    assert set(idx.list_pins()) == {"a", "b", "c"}
