"""CLI commands for browsing snapshot history."""
from __future__ import annotations

import click

from envpack.config import Config
from envpack.history import HistoryError, get_history
from envpack.store import GitStore


def _get_store(ctx: click.Context) -> GitStore:
    cfg: Config = ctx.obj["config"]
    return GitStore(cfg.store_path)


@click.group(name="history")
def history_group() -> None:
    """Browse and inspect snapshot history."""


@history_group.command(name="list")
@click.option(
    "--limit",
    "-n",
    default=None,
    type=int,
    show_default=True,
    help="Maximum number of entries to show.",
)
@click.pass_context
def list_history(ctx: click.Context, limit: int | None) -> None:
    """List all snapshots, newest first."""
    store = _get_store(ctx)
    try:
        report = get_history(store, limit=limit)
    except HistoryError as exc:
        raise click.ClickException(str(exc))

    click.echo(report.summary())


@history_group.command(name="show")
@click.argument("name")
@click.pass_context
def show_entry(ctx: click.Context, name: str) -> None:
    """Show details for a single snapshot by NAME."""
    store = _get_store(ctx)
    try:
        report = get_history(store)
    except HistoryError as exc:
        raise click.ClickException(str(exc))

    matches = [e for e in report.entries if e.name == name]
    if not matches:
        raise click.ClickException(f"Snapshot '{name}' not found.")

    entry = matches[0]
    click.echo(f"Name      : {entry.name}")
    click.echo(f"Position  : {entry.index} (0 = newest)")
    click.echo(f"Size      : {entry.size_bytes} bytes")
