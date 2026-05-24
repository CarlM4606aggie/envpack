"""CLI commands for snapshot pinning."""
from __future__ import annotations

import click

from envpack.config import Config
from envpack.pin import PinError, load_index


def _get_index(ctx: click.Context):
    cfg: Config = ctx.obj["config"]
    from pathlib import Path
    store_dir = Path(cfg.store_path)
    return load_index(store_dir)


@click.group("pin")
def pin_group() -> None:
    """Pin or unpin snapshots to protect them from pruning and rotation."""


@pin_group.command("set")
@click.argument("name")
@click.pass_context
def set_pin(ctx: click.Context, name: str) -> None:
    """Pin snapshot NAME."""
    try:
        idx = _get_index(ctx)
        idx.pin(name)
        click.echo(f"Pinned '{name}'.")
    except PinError as exc:
        raise click.ClickException(str(exc)) from exc


@pin_group.command("unset")
@click.argument("name")
@click.pass_context
def unset_pin(ctx: click.Context, name: str) -> None:
    """Unpin snapshot NAME."""
    try:
        idx = _get_index(ctx)
        idx.unpin(name)
        click.echo(f"Unpinned '{name}'.")
    except PinError as exc:
        raise click.ClickException(str(exc)) from exc


@pin_group.command("list")
@click.pass_context
def list_pins(ctx: click.Context) -> None:
    """List all pinned snapshots."""
    idx = _get_index(ctx)
    pins = idx.list_pins()
    if not pins:
        click.echo("No pinned snapshots.")
    else:
        for name in pins:
            click.echo(name)


@pin_group.command("check")
@click.argument("name")
@click.pass_context
def check_pin(ctx: click.Context, name: str) -> None:
    """Exit 0 if NAME is pinned, 1 otherwise."""
    idx = _get_index(ctx)
    if idx.is_pinned(name):
        click.echo(f"'{name}' is pinned.")
    else:
        click.echo(f"'{name}' is not pinned.")
        raise SystemExit(1)
