"""CLI commands for viewing the envpack audit log."""
import click
from pathlib import Path

from envpack.audit import AuditLog
from envpack.config import Config


def _get_log() -> AuditLog:
    cfg = Config.load()
    return AuditLog(Path(cfg.store_path))


@click.group("audit")
def audit_group() -> None:
    """View the audit log of push/pull operations."""


@audit_group.command("log")
@click.option("-n", "--limit", default=20, show_default=True, help="Number of entries to show.")
@click.option("--action", type=click.Choice(["push", "pull"]), default=None, help="Filter by action.")
@click.option("--profile", default=None, help="Filter by profile name.")
def show_log(limit: int, action: str | None, profile: str | None) -> None:
    """Display recent audit log entries."""
    audit = _get_log()
    entries = audit.entries()

    if action:
        entries = [e for e in entries if e.action == action]
    if profile:
        entries = [e for e in entries if e.profile == profile]

    entries = entries[:limit]

    if not entries:
        click.echo("No audit log entries found.")
        return

    for e in entries:
        note_str = f"  [{e.note}]" if e.note else ""
        click.echo(
            f"{e.timestamp}  {e.action.upper():4s}  profile={e.profile}  "
            f"snapshot={e.snapshot_name}  path={e.env_path}{note_str}"
        )


@audit_group.command("clear")
@click.confirmation_option(prompt="Clear the entire audit log?")
def clear_log() -> None:
    """Delete all audit log entries."""
    audit = _get_log()
    audit.clear()
    click.echo("Audit log cleared.")
