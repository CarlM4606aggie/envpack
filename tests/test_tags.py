"""Tests for envpack.tags module."""
import pytest
from pathlib import Path

from envpack.tags import TagIndex, TagError, _validate_tag


@pytest.fixture
def index(tmp_path):
    return TagIndex.load(tmp_path / "tags.json")


# --- _validate_tag ---

def test_valid_tag_passes():
    _validate_tag("production")
    _validate_tag("v1.0.0")
    _validate_tag("my-env_tag")


def test_empty_tag_raises():
    with pytest.raises(TagError):
        _validate_tag("")


def test_tag_with_spaces_raises():
    with pytest.raises(TagError):
        _validate_tag("bad tag")


def test_tag_too_long_raises():
    with pytest.raises(TagError):
        _validate_tag("a" * 65)


# --- TagIndex ---

def test_set_and_get_round_trip(index):
    index.set("prod", "snap-abc123")
    assert index.get("prod") == "snap-abc123"


def test_get_missing_returns_none(index):
    assert index.get("nonexistent") is None


def test_set_persists_to_disk(tmp_path):
    path = tmp_path / "tags.json"
    idx1 = TagIndex.load(path)
    idx1.set("staging", "snap-xyz")

    idx2 = TagIndex.load(path)
    assert idx2.get("staging") == "snap-xyz"


def test_delete_removes_tag(index):
    index.set("v1", "snap-001")
    index.delete("v1")
    assert index.get("v1") is None


def test_delete_missing_tag_raises(index):
    with pytest.raises(TagError, match="does not exist"):
        index.delete("ghost")


def test_list_tags_returns_sorted(index):
    index.set("beta", "snap-b")
    index.set("alpha", "snap-a")
    index.set("gamma", "snap-g")
    result = index.list_tags()
    assert [t for t, _ in result] == ["alpha", "beta", "gamma"]


def test_overwrite_existing_tag(index):
    index.set("env", "snap-old")
    index.set("env", "snap-new")
    assert index.get("env") == "snap-new"


def test_list_tags_empty(index):
    assert index.list_tags() == []
