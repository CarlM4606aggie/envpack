"""CLI commands for importing .env files into the envpack store."""

from __future__ import annotations

from pathlib import Path

import click

from envpack.config import Config
from envpack.import_ import ImportError as EnvImportError
from envpack.import_ import import_env_file
from envpack.snapshot import SnapshotManager
from envpack.store import GitStore


def _get_manager(cfg: Config) -> SnapshotManager:
    store = GitStore(Path(cfg.store_path))
    return SnapshotManager(store)


@click.group(name="import")
def import_group() -> None:
    """Import .env files into the store."""


@import_group.command(name="file")
@click.argument("source", type=click.Path(exists=False))
@click.argument("snapshot_name")
@click.option(
    "--password",
    envvar="ENVPACK_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Encryption password.",
)
@click.option(
    "--profile",
    default=None,
    help="Profile to associate with the snapshot.",
)
@click.option(
    "--config",
    "config_path",
    default=None,
    type=click.Path(),
    help="Path to envpack config file.",
)
def run_import(
    source: str,
    snapshot_name: str,
    password: str,
    profile: str | None,
    config_path: str | None,
) -> None:
    """Import SOURCE .env file as SNAPSHOT_NAME into the store.

    SOURCE is the path to the .env file to import.
    SNAPSHOT_NAME is the name to assign to the imported snapshot.
    """
    cfg = Config.load(Path(config_path) if config_path else None)
    manager = _get_manager(cfg)

    try:
        result = import_env_file(
            source=Path(source),
            snapshot_name=snapshot_name,
            manager=manager,
            password=password,
            profile=profile,
        )
    except EnvImportError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
