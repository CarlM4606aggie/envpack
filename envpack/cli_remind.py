"""CLI commands for snapshot staleness reminders."""

from __future__ import annotations

import click

from envpack.cli import _get_manager
from envpack.remind import RemindError, check_staleness


@click.group("remind")
def remind_group() -> None:
    """Check for stale snapshots that haven't been updated recently."""


@remind_group.command("check")
@click.option(
    "--days",
    default=30,
    show_default=True,
    type=click.IntRange(min=1),
    help="Number of days before a snapshot is considered stale.",
)
@click.option(
    "--password",
    envvar="ENVPACK_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Master password (used to access the store).",
)
@click.pass_context
def run_check(ctx: click.Context, days: int, password: str) -> None:
    """List snapshots that are older than DAYS days."""
    manager = _get_manager(ctx, password)
    try:
        report = check_staleness(manager.store, threshold_days=days)
    except RemindError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(report.summary())

    stale = report.stale
    if stale:
        ctx.exit(1)


@remind_group.command("list")
@click.option(
    "--days",
    default=30,
    show_default=True,
    type=click.IntRange(min=1),
    help="Staleness threshold in days.",
)
@click.option(
    "--password",
    envvar="ENVPACK_PASSWORD",
    prompt=True,
    hide_input=True,
)
@click.pass_context
def list_stale(ctx: click.Context, days: int, password: str) -> None:
    """Print each snapshot with its age."""
    manager = _get_manager(ctx, password)
    try:
        report = check_staleness(manager.store, threshold_days=days)
    except RemindError as exc:
        raise click.ClickException(str(exc)) from exc

    if not report.entries:
        click.echo("No snapshots found.")
        return

    for entry in report.entries:
        marker = "STALE" if entry.age_days >= days else "ok"
        click.echo(f"[{marker:5s}] {entry}")
