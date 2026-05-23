"""CLI group for the ``clone`` command."""

from __future__ import annotations

from pathlib import Path

import click

from envpack.clone import CloneError, clone_store


@click.group("clone")
def clone_group() -> None:  # pragma: no cover
    """Clone a remote envpack store."""


@clone_group.command("run")
@click.argument("source")
@click.argument("destination", type=click.Path(path_type=Path))
def run_clone(source: str, destination: Path) -> None:
    """Clone SOURCE (Git URL or local path) into DESTINATION.

    SOURCE  Git remote URL or local filesystem path of an existing store.

    DESTINATION  Local directory to clone into (must not already exist).
    """
    try:
        result = clone_store(source, destination)
    except CloneError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
