"""CLI commands for exporting snapshots to portable formats."""
from __future__ import annotations

from pathlib import Path

import click

from envpack.config import Config
from envpack.crypto import decrypt
from envpack.export import ExportFormat, ExportError, export_snapshot
from envpack.store import GitStore, StoreError


@click.group(name="export")
def export_group() -> None:
    """Export a snapshot to dotenv, JSON, or shell format."""


@export_group.command("run")
@click.argument("snapshot_name")
@click.option(
    "--format",
    "fmt",
    type=click.Choice([f.value for f in ExportFormat], case_sensitive=False),
    default=ExportFormat.DOTENV.value,
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Write output to this file instead of stdout.",
)
@click.option("--password", prompt=True, hide_input=True, help="Decryption password.")
def run_export(
    snapshot_name: str,
    fmt: str,
    output: Path | None,
    password: str,
) -> None:
    """Decrypt SNAPSHOT_NAME and export it in the chosen format."""
    try:
        cfg = Config.load()
        store = GitStore(Path(cfg.store_path))
        ciphertext = store.load(snapshot_name)
    except StoreError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        plaintext = decrypt(ciphertext, password)
    except Exception as exc:
        raise click.ClickException(f"Decryption failed: {exc}") from exc

    try:
        result = export_snapshot(
            plaintext.decode("utf-8"),
            ExportFormat(fmt),
            output_path=output,
        )
    except ExportError as exc:
        raise click.ClickException(str(exc)) from exc

    if output:
        click.echo(f"Exported '{snapshot_name}' to {output} [{fmt}]")
    else:
        click.echo(result, nl=False)
