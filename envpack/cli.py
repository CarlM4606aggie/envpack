"""Entry-point CLI for envpack."""

from __future__ import annotations

import click

from envpack.cli_config import config_group
from envpack.cli_profile import profile_group
from envpack.config import Config, ConfigError
from envpack.snapshot import SnapshotManager
from envpack.store import GitStore


def _get_manager() -> SnapshotManager:
    """Build a SnapshotManager from the current config."""
    cfg = Config.load()
    store = GitStore(cfg.store_path)
    return SnapshotManager(store=store, profile=cfg.profile)


@click.group()
@click.version_option()
def cli() -> None:
    """envpack — snapshot, encrypt, and sync .env files."""


@cli.command()
def init() -> None:
    """Initialise the envpack Git store."""
    cfg = Config.load()
    store = GitStore(cfg.store_path)
    try:
        store.init()
        click.echo(f"Store initialised at {cfg.store_path}")
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc


@cli.command()
@click.argument("env_file", default=".env", type=click.Path(exists=True))
@click.password_option("--password", "-p", help="Encryption password.")
@click.option("--message", "-m", default="", help="Optional commit message.")
def push(env_file: str, password: str, message: str) -> None:
    """Encrypt and push ENV_FILE to the store."""
    manager = _get_manager()
    try:
        snapshot_id = manager.push(
            env_path=env_file,
            password=password,
            message=message or None,
        )
        click.echo(f"Snapshot {snapshot_id!r} pushed.")
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc


@cli.command()
@click.argument("snapshot_id")
@click.argument("dest", default=".env", type=click.Path())
@click.option("--password", "-p", prompt=True, hide_input=True, help="Decryption password.")
def pull(snapshot_id: str, dest: str, password: str) -> None:
    """Decrypt and restore SNAPSHOT_ID to DEST."""
    manager = _get_manager()
    try:
        manager.pull(snapshot_id=snapshot_id, dest_path=dest, password=password)
        click.echo(f"Snapshot {snapshot_id!r} restored to {dest!r}.")
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc


@cli.command(name="list")
def list_snapshots() -> None:
    """List all snapshots for the active profile."""
    manager = _get_manager()
    snapshots = manager.list_snapshots()
    if not snapshots:
        click.echo("No snapshots found.")
        return
    for snap in snapshots:
        click.echo(f"  {snap}")


cli.add_command(config_group)
cli.add_command(profile_group)
