"""Lint .env files for common issues."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


class LintError(Exception):
    """Raised when linting cannot be performed."""


@dataclass
class LintIssue:
    line_number: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"Line {self.line_number} [{self.code}]: {self.message}"


@dataclass
class LintResult:
    path: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.ok:
            return f"{self.path}: no issues found"
        lines = [f"{self.path}: {len(self.issues)} issue(s) found"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_QUOTED_RE = re.compile(r'^(["\']).*\1$')


def lint_env_text(text: str, path: str = "<text>") -> LintResult:
    """Lint the content of a .env file and return a LintResult."""
    result = LintResult(path=path)
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            result.issues.append(LintIssue(lineno, "E001", f"Missing '=' in line: {raw!r}"))
            continue

        key, _, value = line.partition("=")
        key = key.strip()

        if not _KEY_RE.match(key):
            result.issues.append(LintIssue(lineno, "E002", f"Invalid key name: {key!r}"))

        if key in seen_keys:
            result.issues.append(
                LintIssue(lineno, "W001", f"Duplicate key '{key}' (first seen on line {seen_keys[key]})")
            )
        else:
            seen_keys[key] = lineno

        if value and not _QUOTED_RE.match(value) and " " in value:
            result.issues.append(LintIssue(lineno, "W002", f"Unquoted value with spaces for key '{key}'"))

    return result


def lint_file(path: Path) -> LintResult:
    """Lint a .env file on disk."""
    if not path.exists():
        raise LintError(f"File not found: {path}")
    return lint_env_text(path.read_text(encoding="utf-8"), path=str(path))
