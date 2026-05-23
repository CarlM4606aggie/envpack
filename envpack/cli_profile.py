"""CLI sub-commands for managing envpack profiles."""

from __future__ import annotations

import click

from envpack.config import Config
from envpack.profile import Profile, ProfileError, ProfileManager


def _get_manager() -> ProfileManager:
    cfg = Config.load()
    return ProfileManager(store_path=cfg.store_path)


@click.group(name="profile")
def profile_group() -> None:
    """Manage environment profiles."""


@profile_group.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Short description of the profile.")
@click.option("--tag", "-t", multiple=True, help="Tag to attach (repeatable).")
def create_profile(name: str, description: str, tag: tuple) -> None:
    """Create a new profile NAME."""
    manager = _get_manager()
    try:
        manager.create(Profile(name=name, description=description, tags=list(tag)))
        click.echo(f"Profile {name!r} created.")
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command("list")
def list_profiles() -> None:
    """List all profiles."""
    manager = _get_manager()
    profiles = manager.list_profiles()
    if not profiles:
        click.echo("No profiles defined.")
        return
    for p in profiles:
        tags = f"  [{', '.join(p.tags)}]" if p.tags else ""
        desc = f"  — {p.description}" if p.description else ""
        click.echo(f"  {p.name}{tags}{desc}")


@profile_group.command("delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this profile?")
def delete_profile(name: str) -> None:
    """Delete profile NAME."""
    manager = _get_manager()
    try:
        manager.delete(name)
        click.echo(f"Profile {name!r} deleted.")
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command("show")
@click.argument("name")
def show_profile(name: str) -> None:
    """Show details of profile NAME."""
    manager = _get_manager()
    try:
        p = manager.get(name)
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Name       : {p.name}")
    click.echo(f"Description: {p.description or '(none)'}")
    click.echo(f"Tags       : {', '.join(p.tags) or '(none)'}")
