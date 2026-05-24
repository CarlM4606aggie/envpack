"""CLI commands for the watch feature."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envpack.cli import _get_manager
from envpack.config import Config
from envpack.watch import WatchError, WatchEvent, watch_file


@click.group("watch")
def watch_group() -> None:
    """Watch a .env file and auto-push on changes."""


@watch_group.command("start")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--password", prompt=True, hide_input=True, help="Encryption password.")
@click.option("--interval", default=2.0, show_default=True, help="Poll interval in seconds.")
@click.option("--snapshot", "snapshot_name", default=None, help="Snapshot name (default: filename stem).")
def start_watch(
    env_file: str,
    password: str,
    interval: float,
    snapshot_name: str | None,
) -> None:
    """Watch ENV_FILE and push a new snapshot whenever it changes."""
    path = Path(env_file)
    name = snapshot_name or path.stem

    try:
        cfg = Config.load()
    except Exception as exc:  # pragma: no cover
        click.echo(f"Config error: {exc}", err=True)
        sys.exit(1)

    manager = _get_manager(cfg)

    click.echo(f"Watching {path} every {interval}s — press Ctrl+C to stop.")

    def _on_change(event: WatchEvent) -> None:
        label = "first push" if event.is_first_seen else "change detected"
        click.echo(f"  [{label}] pushing snapshot '{name}'…")
        try:
            manager.push(path, password, name)
            click.echo(f"  snapshot '{name}' saved.")
        except Exception as exc:
            click.echo(f"  push failed: {exc}", err=True)

    try:
        watch_file(path, _on_change, interval=interval)
    except WatchError as exc:
        click.echo(f"Watch error: {exc}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nWatcher stopped.")
