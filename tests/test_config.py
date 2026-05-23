"""Tests for envpack.config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envpack.config import (
    DEFAULT_STORE_PATH,
    Config,
    ConfigError,
    load_config,
)


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    return tmp_path / "config.json"


@pytest.fixture()
def cfg(config_path: Path) -> Config:
    c = Config(config_path)
    c.load()
    return c


class TestDefaults:
    def test_default_store_path(self, cfg: Config) -> None:
        assert cfg.store_path == DEFAULT_STORE_PATH

    def test_default_profile(self, cfg: Config) -> None:
        assert cfg.default_profile == "default"


class TestPersistence:
    def test_save_creates_file(self, cfg: Config, config_path: Path) -> None:
        cfg.save()
        assert config_path.exists()

    def test_save_and_load_round_trip(self, config_path: Path, tmp_path: Path) -> None:
        cfg = Config(config_path)
        cfg.load()
        cfg.store_path = tmp_path / "my_store"
        cfg.default_profile = "work"
        cfg.save()

        cfg2 = Config(config_path)
        cfg2.load()
        assert cfg2.store_path == tmp_path / "my_store"
        assert cfg2.default_profile == "work"

    def test_save_creates_parent_directories(self, tmp_path: Path) -> None:
        deep_path = tmp_path / "a" / "b" / "config.json"
        cfg = Config(deep_path)
        cfg.load()
        cfg.save()
        assert deep_path.exists()


class TestErrorHandling:
    def test_invalid_json_raises_config_error(self, config_path: Path) -> None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("not valid json")
        cfg = Config(config_path)
        with pytest.raises(ConfigError, match="Invalid config file"):
            cfg.load()


class TestHelpers:
    def test_load_config_returns_config(self, config_path: Path) -> None:
        result = load_config(config_path)
        assert isinstance(result, Config)

    def test_as_dict_contains_expected_keys(self, cfg: Config) -> None:
        d = cfg.as_dict()
        assert "store_path" in d
        assert "default_profile" in d

    def test_as_dict_values_are_strings(self, cfg: Config) -> None:
        d = cfg.as_dict()
        assert all(isinstance(v, str) for v in d.values())
