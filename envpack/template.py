"""Template rendering for .env files — fill placeholders from a snapshot."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""


@dataclass
class RenderResult:
    rendered: str
    filled: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    def summary(self) -> str:
        parts = [f"filled={len(self.filled)}"]
        if self.missing:
            parts.append(f"missing={len(self.missing)} ({', '.join(self.missing)})")
        return "RenderResult(" + ", ".join(parts) + ")"


def _parse_env(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines from env text, skipping comments and blanks."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def render_template(template_text: str, env_text: str, strict: bool = False) -> RenderResult:
    """Replace {{KEY}} placeholders in *template_text* using values from *env_text*.

    Args:
        template_text: Template string containing ``{{KEY}}`` placeholders.
        env_text: Raw .env file content used as the value source.
        strict: If True, raise :class:`TemplateError` when any placeholder is missing.

    Returns:
        :class:`RenderResult` with the rendered string and fill/missing lists.
    """
    env = _parse_env(env_text)
    filled: List[str] = []
    missing: List[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key in env:
            filled.append(key)
            return env[key]
        missing.append(key)
        return match.group(0)

    rendered = _PLACEHOLDER_RE.sub(_replace, template_text)

    if strict and missing:
        raise TemplateError(f"Missing keys in env: {', '.join(sorted(set(missing)))}")

    return RenderResult(rendered=rendered, filled=filled, missing=list(set(missing)))


def render_template_file(
    template_path: Path,
    env_text: str,
    output_path: Path | None = None,
    strict: bool = False,
) -> RenderResult:
    """Render a template file and optionally write the result to *output_path*."""
    if not template_path.exists():
        raise TemplateError(f"Template file not found: {template_path}")
    result = render_template(template_path.read_text(), env_text, strict=strict)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.rendered)
    return result
