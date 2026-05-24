"""CLI command group for renaming snapshots."""
from __future__ import annotations

import click

from envpack.cli import _get_manager
from envpack.rename import RenameError, rename_snapshot


@click.group("rename")
def rename_group() -> None:
    """Rename a stored snapshot."""


@rename_group.command("run")
@click.argument("old_name")
@click.argument("new_name")
@click.password_option(
    "--password",
    "-p",
    prompt="Store password",
    confirmation_prompt=False,
    help="Password used to encrypt/decrypt the store.",
)
@click.pass_context
def run_rename(ctx: click.Context, old_name: str, new_name: str, password: str) -> None:
    """Rename snapshot OLD_NAME to NEW_NAME."""
    manager = _get_manager(ctx)
    try:
        result = rename_snapshot(
            store=manager.store,
            old_name=old_name,
            new_name=new_name,
            password=password,
        )
    except RenameError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
