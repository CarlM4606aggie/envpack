"""CLI commands for snapshot integrity verification."""
from __future__ import annotations

import click

from envpack.cli import _get_manager
from envpack.config import Config
from envpack.store import GitStore
from envpack.verify import verify_snapshots, VerifyError


@click.group(name="verify")
def verify_group() -> None:
    """Verify integrity of stored snapshots."""


@verify_group.command(name="run")
@click.option("--profile", default=None, help="Profile to verify (default: active profile).")
@click.option("--password", prompt=True, hide_input=True, help="Encryption password.")
@click.pass_context
def run_verify(ctx: click.Context, profile: str | None, password: str) -> None:
    """Decrypt and verify all snapshots for a profile."""
    cfg: Config = ctx.obj["config"]
    active_profile = profile or cfg.profile
    store = GitStore(cfg.store_path)

    try:
        report = verify_snapshots(store, password, active_profile)
    except VerifyError as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)
        return

    for result in report.results:
        icon = click.style("✓", fg="green") if result.ok else click.style("✗", fg="red")
        click.echo(f"  {icon}  {result}")

    click.echo()
    click.echo(report.summary())

    if not report.all_ok:
        ctx.exit(1)
