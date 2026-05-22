"""Command-line interface for envpack snapshot commands."""

import sys
import getpass
from pathlib import Path

import click

from envpack.store import GitStore, StoreError
from envpack.snapshot import SnapshotManager


def _get_manager(store_dir: str | None) -> SnapshotManager:
    store = GitStore(store_dir=Path(store_dir) if store_dir else None)
    return SnapshotManager(store=store)


@click.group()
def cli() -> None:
    """envpack — snapshot, encrypt, and sync .env files."""


@cli.command()
@click.option("--store", default=None, help="Path to the envpack store directory.")
def init(store: str | None) -> None:
    """Initialize the envpack Git store."""
    try:
        GitStore(store_dir=Path(store) if store else None).init()
        click.echo("Store initialized.")
    except StoreError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--file", "env_file", default=".env", show_default=True)
@click.option("--store", default=None)
def push(name: str, env_file: str, store: str | None) -> None:
    """Encrypt and push a .env file to the store."""
    password = getpass.getpass("Password: ")
    try:
        _get_manager(store).push(Path(env_file), name, password)
        click.echo(f"Snapshot '{name}' saved.")
    except (StoreError, FileNotFoundError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--out", default=".env", show_default=True)
@click.option("--store", default=None)
def pull(name: str, out: str, store: str | None) -> None:
    """Decrypt and pull a snapshot from the store."""
    password = getpass.getpass("Password: ")
    try:
        _get_manager(store).pull(name, password, Path(out))
        click.echo(f"Snapshot '{name}' written to {out}.")
    except (StoreError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command(name="list")
@click.option("--store", default=None)
def list_cmd(store: str | None) -> None:
    """List all stored snapshots."""
    try:
        names = _get_manager(store).list_snapshots()
        if names:
            click.echo("\n".join(names))
        else:
            click.echo("No snapshots found.")
    except StoreError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--store", default=None)
def delete(name: str, store: str | None) -> None:
    """Delete a snapshot from the store."""
    try:
        _get_manager(store).delete(name)
        click.echo(f"Snapshot '{name}' deleted.")
    except StoreError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
