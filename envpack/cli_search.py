"""CLI commands for searching snapshots."""
from __future__ import annotations

import click
from envpack.config import Config
from envpack.store import GitStore
from envpack.search import search_snapshots


@click.group("search")
def search_group() -> None:
    """Search snapshots for keys or values."""


@search_group.command("run")
@click.option("--key", "-k", default=None, help="Key pattern (glob or regex).")
@click.option("--value", "-v", default=None, help="Value pattern (glob or regex).")
@click.option("--snapshot", "-s", default=None, help="Snapshot name glob filter.")
@click.option("--show-values", is_flag=True, default=False, help="Show matched values.")
@click.password_option("--password", "-p", confirmation_prompt=False, help="Decryption password.")
def run_search(
    key: str | None,
    value: str | None,
    snapshot: str | None,
    show_values: bool,
    password: str,
) -> None:
    """Search snapshots by key and/or value pattern."""
    if not key and not value:
        raise click.UsageError("Provide at least --key or --value.")

    cfg = Config.load()
    store = GitStore(cfg.store_path)

    result = search_snapshots(
        store=store,
        password=password,
        key_pattern=key,
        value_pattern=value,
        snapshot_glob=snapshot,
    )

    if not result.has_matches:
        click.echo("No matches found.")
        return

    for match in result.matches:
        if show_values:
            click.echo(f"{match.snapshot}: {match.key}={match.value}")
        else:
            click.echo(f"{match.snapshot}: {match.key}")

    click.echo(f"\n{len(result.matches)} match(es) found.")
