"""CLI commands for the restore feature."""

from __future__ import annotations

from pathlib import Path

import click

from envpack.config import Config
from envpack.store import GitStore
from envpack.restore import restore_snapshot, RestoreError


@click.group("restore")
def restore_group() -> None:
    """Restore a snapshot to disk."""


@restore_group.command("run")
@click.argument("snapshot_name")
@click.argument("target", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "--password",
    envvar="ENVPACK_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Decryption password (or set ENVPACK_PASSWORD).",
)
@click.option(
    "--no-backup",
    is_flag=True,
    default=False,
    help="Skip creating a backup of an existing target file.",
)
def run_restore(
    snapshot_name: str,
    target: Path,
    password: str,
    no_backup: bool,
) -> None:
    """Decrypt SNAPSHOT_NAME and write it to TARGET."""
    cfg = Config.load()
    store = GitStore(Path(cfg.store_path))

    try:
        result = restore_snapshot(
            store,
            snapshot_name,
            password,
            target,
            backup=not no_backup,
        )
    except RestoreError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
