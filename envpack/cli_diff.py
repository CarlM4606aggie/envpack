"""CLI sub-commands for diffing .env snapshots."""

from __future__ import annotations

import click

from envpack.cli import _get_manager
from envpack.diff import diff_env_texts


@click.group(name="diff")
def diff_group() -> None:
    """Compare .env snapshots."""


@diff_group.command(name="snapshots")
@click.argument("snapshot_a")
@click.argument("snapshot_b")
@click.option("--profile", default=None, help="Profile to use.")
@click.pass_context
def diff_snapshots(ctx: click.Context, snapshot_a: str, snapshot_b: str, profile: str | None) -> None:
    """Show differences between two named snapshots."""
    manager = _get_manager(ctx, profile=profile)
    try:
        text_a = manager.store.load(snapshot_a)
        text_b = manager.store.load(snapshot_b)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    d = diff_env_texts(text_a, text_b)
    if not d.has_changes:
        click.echo("Snapshots are identical.")
        return

    click.echo(f"Diff: {snapshot_a} -> {snapshot_b}")
    click.echo(d.summary())


@diff_group.command(name="working")
@click.argument("snapshot_name")
@click.option("--env-file", "env_file", default=".env", show_default=True,
              help="Path to the local .env file.")
@click.option("--profile", default=None, help="Profile to use.")
@click.pass_context
def diff_working(ctx: click.Context, snapshot_name: str, env_file: str, profile: str | None) -> None:
    """Compare a snapshot against the current working .env file."""
    manager = _get_manager(ctx, profile=profile)
    try:
        snapshot_text = manager.store.load(snapshot_name)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    try:
        working_text = open(env_file).read()  # noqa: WPS515
    except FileNotFoundError:
        working_text = None

    d = diff_env_texts(snapshot_text, working_text)
    if not d.has_changes:
        click.echo("Working file matches snapshot.")
        return

    click.echo(f"Diff: {snapshot_name} -> {env_file}")
    click.echo(d.summary())
