"""CLI commands for managing snapshot tags."""
from __future__ import annotations

import click
from pathlib import Path

from envpack.config import Config
from envpack.tags import TagIndex, TagError


def _get_index(config: Config) -> TagIndex:
    store_path = Path(config.store_path)
    return TagIndex.load(store_path / "tags.json")


@click.group("tag")
def tag_group() -> None:
    """Manage snapshot tags."""


@tag_group.command("set")
@click.argument("tag")
@click.argument("snapshot_id")
@click.pass_context
def set_tag(ctx: click.Context, tag: str, snapshot_id: str) -> None:
    """Assign TAG to a SNAPSHOT_ID."""
    config: Config = ctx.obj["config"]
    try:
        index = _get_index(config)
        index.set(tag, snapshot_id)
        click.echo(f"Tag '{tag}' -> '{snapshot_id}'")
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc


@tag_group.command("get")
@click.argument("tag")
@click.pass_context
def get_tag(ctx: click.Context, tag: str) -> None:
    """Resolve TAG to its snapshot ID."""
    config: Config = ctx.obj["config"]
    index = _get_index(config)
    snapshot_id = index.get(tag)
    if snapshot_id is None:
        raise click.ClickException(f"Tag '{tag}' not found.")
    click.echo(snapshot_id)


@tag_group.command("delete")
@click.argument("tag")
@click.pass_context
def delete_tag(ctx: click.Context, tag: str) -> None:
    """Remove TAG from the index."""
    config: Config = ctx.obj["config"]
    try:
        index = _get_index(config)
        index.delete(tag)
        click.echo(f"Tag '{tag}' deleted.")
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc


@tag_group.command("list")
@click.pass_context
def list_tags(ctx: click.Context) -> None:
    """List all tags and their snapshot IDs."""
    config: Config = ctx.obj["config"]
    index = _get_index(config)
    tags = index.list_tags()
    if not tags:
        click.echo("No tags defined.")
        return
    for tag, snapshot_id in tags:
        click.echo(f"{tag:<24} {snapshot_id}")
