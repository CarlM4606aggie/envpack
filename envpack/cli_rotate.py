"""CLI sub-command: envpack rotate."""

from __future__ import annotations

import click

from envpack.config import Config
from envpack.rotate import RotateError, rotate_snapshots
from envpack.store import GitStore


@click.group("rotate")
def rotate_group() -> None:
    """Password rotation commands."""


@rotate_group.command("run")
@click.option("--store-path", default=None, help="Override store path.")
@click.option("--profile", default=None, help="Profile to rotate (default: active profile).")
@click.password_option(
    "--old-password",
    prompt="Current password",
    confirmation_prompt=False,
    help="Existing encryption password.",
)
@click.password_option(
    "--new-password",
    prompt="New password",
    help="Replacement encryption password.",
)
def run_rotation(
    store_path: str | None,
    profile: str | None,
    old_password: str,
    new_password: str,
) -> None:
    """Re-encrypt all snapshots with a new password."""
    cfg = Config.load()
    resolved_store = store_path or cfg.store_path
    resolved_profile = profile or cfg.profile

    store = GitStore(resolved_store)
    try:
        result = rotate_snapshots(store, old_password, new_password, resolved_profile)
    except RotateError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
    if not result.success:
        raise click.ClickException("Some snapshots could not be rotated.")
