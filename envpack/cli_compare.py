"""CLI commands for comparing two snapshots."""
from __future__ import annotations

import click

from envpack.compare import compare_snapshots, CompareError
from envpack.store import GitStore
from envpack.config import Config


@click.group("compare")
def compare_group() -> None:
    """Compare two snapshots side-by-side."""


@compare_group.command("run")
@click.argument("left")
@click.argument("right")
@click.option(
    "--password",
    envvar="ENVPACK_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Decryption password.",
)
@click.option("--keys-only", is_flag=True, default=False, help="Show only changed key names.")
@click.pass_context
def run_compare(ctx: click.Context, left: str, right: str, password: str, keys_only: bool) -> None:
    """Compare snapshots LEFT and RIGHT."""
    cfg: Config = ctx.obj["config"]
    store = GitStore(cfg.store_path)

    try:
        result = compare_snapshots(store, left, right, password)
    except CompareError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())

    if result.has_differences:
        click.echo()
        for diff in result.diffs:
            if keys_only:
                click.echo(f"  {diff.status.upper():8s}  {diff.key}")
            else:
                click.echo(str(diff))
        ctx.exit(1)
