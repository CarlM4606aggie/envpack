"""Tests for envpack.profile."""

from __future__ import annotations

import pytest

from envpack.profile import Profile, ProfileError, ProfileManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def manager(tmp_path):
    return ProfileManager(store_path=tmp_path / "store")


# ---------------------------------------------------------------------------
# Profile dataclass
# ---------------------------------------------------------------------------


def test_profile_valid_name():
    p = Profile(name="production")
    assert p.name == "production"


def test_profile_invalid_name_raises():
    with pytest.raises(ProfileError, match="valid identifier"):
        Profile(name="my-profile")


def test_profile_matches_tag():
    p = Profile(name="staging", tags=["cloud", "aws"])
    assert p.matches_tag("aws")
    assert not p.matches_tag("gcp")


# ---------------------------------------------------------------------------
# ProfileManager.create / get
# ---------------------------------------------------------------------------


def test_create_and_get_round_trip(manager):
    p = Profile(name="dev", description="Development env", tags=["local"])
    manager.create(p)
    retrieved = manager.get("dev")
    assert retrieved.name == "dev"
    assert retrieved.description == "Development env"
    assert retrieved.tags == ["local"]


def test_create_duplicate_raises(manager):
    manager.create(Profile(name="dev"))
    with pytest.raises(ProfileError, match="already exists"):
        manager.create(Profile(name="dev"))


def test_get_missing_raises(manager):
    with pytest.raises(ProfileError, match="not found"):
        manager.get("nonexistent")


# ---------------------------------------------------------------------------
# ProfileManager.list_profiles
# ---------------------------------------------------------------------------


def test_list_profiles_empty(manager):
    assert manager.list_profiles() == []


def test_list_profiles_returns_all(manager):
    manager.create(Profile(name="dev"))
    manager.create(Profile(name="prod"))
    names = {p.name for p in manager.list_profiles()}
    assert names == {"dev", "prod"}


# ---------------------------------------------------------------------------
# ProfileManager.delete
# ---------------------------------------------------------------------------


def test_delete_removes_profile(manager):
    manager.create(Profile(name="staging"))
    manager.delete("staging")
    assert not manager.exists("staging")


def test_delete_missing_raises(manager):
    with pytest.raises(ProfileError, match="not found"):
        manager.delete("ghost")


# ---------------------------------------------------------------------------
# ProfileManager.exists
# ---------------------------------------------------------------------------


def test_exists_true(manager):
    manager.create(Profile(name="ci"))
    assert manager.exists("ci")


def test_exists_false(manager):
    assert not manager.exists("ci")
