"""CLI sub-commands for managing envpack configuration."""

from __future__ import annotations

from pathlib import Path

import click

from envpack.config import ConfigError, load_config


@click.group("config")
def config_group() -> None:
    """View and edit envpack configuration."""


@config_group.command("show")
def show_config() -> None:
    """Print the current configuration."""
    try:
        cfg = load_config()
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    for key, value in cfg.as_dict().items():
        click.echo(f"{key} = {value}")


@config_group.command("set-store")
@click.argument("path", type=click.Path(path_type=Path))
def set_store(path: Path) -> None:
    """Set the path to the local Git-backed store."""
    try:
        cfg = load_config()
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    cfg.store_path = path.expanduser().resolve()
    cfg.save()
    click.echo(f"Store path updated to: {cfg.store_path}")


@config_group.command("set-profile")
@click.argument("profile")
def set_profile(profile: str) -> None:
    """Set the default snapshot profile name."""
    if not profile.strip():
        raise click.ClickException("Profile name must not be empty.")

    try:
        cfg = load_config()
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    cfg.default_profile = profile
    cfg.save()
    click.echo(f"Default profile updated to: {cfg.default_profile}")


@config_group.command("reset")
@click.confirmation_option(prompt="Reset configuration to defaults?")
def reset_config() -> None:
    """Reset configuration to built-in defaults."""
    from envpack.config import DEFAULT_CONFIG_FILE, Config

    cfg = Config(DEFAULT_CONFIG_FILE)
    # Do NOT load existing data — write fresh defaults.
    cfg.save()
    click.echo("Configuration reset to defaults.")
