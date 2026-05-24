"""CLI commands for copying snapshots."""
from __future__ import annotations

import sys

import click

from envpack.cli import _get_manager
from envpack.copy import CopyError, copy_snapshot


@click.group("copy")
def copy_group() -> None:
    """Copy snapshots within the store."""


@copy_group.command("run")
@click.argument("source")
@click.argument("destination")
@click.option("--profile", default="default", show_default=True, help="Profile to use.")
@click.option(
    "--password",
    envvar="ENVPACK_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Encryption password.",
)
@click.pass_context
def run_copy(ctx: click.Context, source: str, destination: str, profile: str, password: str) -> None:
    """Copy SOURCE snapshot to DESTINATION within the store."""
    manager = _get_manager(ctx)
    try:
        result = copy_snapshot(
            store=manager.store,
            source=source,
            destination=destination,
            profile=profile,
            password=password,
        )
    except CopyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(result.summary())
