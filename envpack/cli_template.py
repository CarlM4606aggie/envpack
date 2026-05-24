"""CLI commands for the template rendering feature."""

from __future__ import annotations

from pathlib import Path

import click

from envpack.config import Config
from envpack.crypto import decrypt
from envpack.snapshot import SnapshotManager
from envpack.store import GitStore
from envpack.template import TemplateError, render_template_file


def _get_manager(cfg: Config) -> SnapshotManager:
    store = GitStore(Path(cfg.store_path))
    return SnapshotManager(store=store, password=cfg.password or "")


@click.group(name="template")
def template_group() -> None:
    """Render config templates using values from a snapshot."""


@template_group.command("render")
@click.argument("template_file", type=click.Path(exists=True, path_type=Path))
@click.option("-s", "--snapshot", default="latest", show_default=True, help="Snapshot name to source values from.")
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None, help="Output file path. Defaults to stdout.")
@click.option("--strict", is_flag=True, default=False, help="Fail if any placeholder is unresolved.")
@click.option("--profile", default=None, help="Profile override.")
@click.pass_context
def render_template_cmd(
    ctx: click.Context,
    template_file: Path,
    snapshot: str,
    output: Path | None,
    strict: bool,
    profile: str | None,
) -> None:
    """Render TEMPLATE_FILE filling {{KEY}} placeholders from a snapshot."""
    cfg: Config = ctx.obj["config"]
    if profile:
        cfg.profile = profile

    store = GitStore(Path(cfg.store_path))
    try:
        if snapshot == "latest":
            names = store.list_snapshots()
            if not names:
                raise click.ClickException("No snapshots found in store.")
            snapshot = names[-1]
        env_bytes = store.load(snapshot)
        password = cfg.password or click.prompt("Password", hide_input=True)
        env_text = decrypt(env_bytes, password).decode()
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    try:
        result = render_template_file(template_file, env_text, output_path=output, strict=strict)
    except TemplateError as exc:
        raise click.ClickException(str(exc)) from exc

    if output is None:
        click.echo(result.rendered)
    else:
        click.echo(f"Rendered to {output} ({len(result.filled)} keys filled)")

    if result.missing:
        click.echo(f"Warning: unresolved placeholders: {', '.join(result.missing)}", err=True)
