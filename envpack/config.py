"""Configuration management for envpack."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "envpack"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
DEFAULT_STORE_PATH = Path.home() / ".local" / "share" / "envpack" / "store"


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""


class Config:
    """Manages persistent envpack configuration."""

    def __init__(self, config_path: Path = DEFAULT_CONFIG_FILE) -> None:
        self._path = config_path
        self._data: dict[str, Any] = {}

    def load(self) -> None:
        """Load configuration from disk, using defaults if file is absent."""
        if self._path.exists():
            try:
                with self._path.open() as fh:
                    self._data = json.load(fh)
            except json.JSONDecodeError as exc:
                raise ConfigError(f"Invalid config file at {self._path}: {exc}") from exc
        else:
            self._data = {}

    def save(self) -> None:
        """Persist configuration to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as fh:
            json.dump(self._data, fh, indent=2)

    # ------------------------------------------------------------------
    # Typed accessors
    # ------------------------------------------------------------------

    @property
    def store_path(self) -> Path:
        raw = self._data.get("store_path")
        return Path(raw) if raw else DEFAULT_STORE_PATH

    @store_path.setter
    def store_path(self, value: Path) -> None:
        self._data["store_path"] = str(value)

    @property
    def default_profile(self) -> str:
        return self._data.get("default_profile", "default")

    @default_profile.setter
    def default_profile(self, value: str) -> None:
        self._data["default_profile"] = value

    def as_dict(self) -> dict[str, Any]:
        """Return a plain-dict view of the current configuration."""
        return {
            "store_path": str(self.store_path),
            "default_profile": self.default_profile,
        }


def load_config(config_path: Path = DEFAULT_CONFIG_FILE) -> Config:
    """Convenience helper: create, load, and return a Config instance."""
    cfg = Config(config_path)
    cfg.load()
    return cfg
