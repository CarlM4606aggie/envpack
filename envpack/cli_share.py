"""CLI commands for sharing snapshots via encrypted bundles."""

from __future__ import annotations

from pathlib import Path

import click

from envpack.config import Config
from envpack.store import GitStore
from envpack.share import (
    ShareError,
    export_bundle,
    import_bundle,
    read_bundle,
    write_bundle,
)


@click.group("share")
def share_group() -> None:
    """Share snapshots with other users via encrypted bundles."""


@share_group.command("export")
@click.argument("snapshot")
@click.argument("dest", type=click.Path())
@click.password_option("--password", prompt="Store password", confirmation_prompt=False)
@click.option("--share-password", prompt=True, hide_input=True, help="Password for the bundle.")
@click.pass_context
def export_cmd(ctx: click.Context, snapshot: str, dest: str, password: str, share_password: str) -> None:
    """Export SNAPSHOT to a shareable encrypted bundle at DEST."""
    cfg: Config = ctx.obj["config"]
    store = GitStore(Path(cfg.store_path))
    try:
        bundle = export_bundle(store, snapshot, password, share_password)
    except ShareError as exc:
        raise click.ClickException(str(exc))

    dest_path = Path(dest)
    write_bundle(bundle, dest_path)
    click.echo(f"Bundle written to {dest_path} (snapshot: {snapshot})")


@share_group.command("import")
@click.argument("src", type=click.Path(exists=True))
@click.option("--name", default=None, help="Override the snapshot name.")
@click.option("--share-password", prompt=True, hide_input=True, help="Password used to encrypt the bundle.")
@click.password_option("--password", prompt="Store password", confirmation_prompt=False)
@click.pass_context
def import_cmd(ctx: click.Context, src: str, name: str | None, share_password: str, password: str) -> None:
    """Import a shared bundle from SRC into the store."""
    cfg: Config = ctx.obj["config"]
    store = GitStore(Path(cfg.store_path))
    try:
        bundle = read_bundle(Path(src))
        saved_name = import_bundle(store, bundle, share_password, password, snapshot_name=name)
    except ShareError as exc:
        raise click.ClickException(str(exc))

    click.echo(f"Imported snapshot '{saved_name}' from {src}")


@share_group.command("inspect")
@click.argument("src", type=click.Path(exists=True))
def inspect_cmd(src: str) -> None:
    """Inspect metadata of a shared bundle without decrypting it."""
    import datetime

    try:
        bundle = read_bundle(Path(src))
    except ShareError as exc:
        raise click.ClickException(str(exc))

    created = datetime.datetime.fromtimestamp(bundle.created_at).isoformat()
    click.echo(f"Snapshot : {bundle.snapshot_name}")
    click.echo(f"Created  : {created}")
    click.echo(f"Checksum : {bundle.checksum}")
    click.echo(f"Size     : {len(bundle.ciphertext)} bytes (encrypted)")
