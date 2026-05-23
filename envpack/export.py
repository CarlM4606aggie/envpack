"""Export snapshots to portable formats (dotenv, JSON, shell)."""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Dict


class ExportFormat(str, Enum):
    DOTENV = "dotenv"
    JSON = "json"
    SHELL = "shell"


class ExportError(Exception):
    """Raised when an export operation fails."""


def _parse_env(text: str) -> Dict[str, str]:
    """Parse a .env file text into a key/value mapping."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def export_snapshot(
    plaintext: str,
    fmt: ExportFormat = ExportFormat.DOTENV,
    output_path: Path | None = None,
) -> str:
    """Convert decrypted snapshot text to the requested format.

    Args:
        plaintext: Raw .env file contents.
        fmt: Target export format.
        output_path: If provided, write the result to this file.

    Returns:
        The formatted string.
    """
    pairs = _parse_env(plaintext)

    if fmt == ExportFormat.DOTENV:
        lines = [f"{k}={v}" for k, v in pairs.items()]
        output = "\n".join(lines) + ("\n" if lines else "")
    elif fmt == ExportFormat.JSON:
        output = json.dumps(pairs, indent=2) + "\n"
    elif fmt == ExportFormat.SHELL:
        lines = [f"export {k}={v}" for k, v in pairs.items()]
        output = "\n".join(lines) + ("\n" if lines else "")
    else:
        raise ExportError(f"Unknown export format: {fmt}")

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")

    return output
