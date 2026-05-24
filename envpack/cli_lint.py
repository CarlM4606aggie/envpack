"""CLI commands for linting .env files."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envpack.lint import LintError, lint_env_text, lint_file
from envpack.snapshot import SnapshotManager
from envpack.config import Config


@click.group("lint")
def lint_group() -> None:
    """Lint .env files for common issues."""


@lint_group.command("file")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def lint_file_cmd(env_file: Path) -> None:
    """Lint a local .env FILE."""
    try:
        result = lint_file(env_file)
    except LintError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(result.summary())
    if not result.ok:
        sys.exit(1)


@lint_group.command("snapshot")
@click.argument("name")
@click.option("--password", prompt=True, hide_input=True, help="Decryption password.")
@click.pass_context
def lint_snapshot(ctx: click.Context, name: str, password: str) -> None:
    """Lint a stored snapshot by NAME."""
    cfg: Config = ctx.obj["config"]
    manager = SnapshotManager(
        store_path=Path(cfg.store_path),
        password=password,
        profile=cfg.profile,
    )
    try:
        content = manager.store.load(name)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error loading snapshot: {exc}", err=True)
        sys.exit(1)

    from envpack.crypto import decrypt

    try:
        plaintext = decrypt(content, password).decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error decrypting snapshot: {exc}", err=True)
        sys.exit(1)

    result = lint_env_text(plaintext, path=f"snapshot:{name}")
    click.echo(result.summary())
    if not result.ok:
        sys.exit(1)
