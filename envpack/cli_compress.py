"""CLI commands for inspecting compression stats on stored snapshots."""

import click

from envpack.compress import compress_text, CompressResult
from envpack.config import Config
from envpack.store import GitStore


def _get_store(config: Config) -> GitStore:
    return GitStore(config.store_path)


@click.group("compress")
def compress_group() -> None:
    """Compression utilities for snapshot payloads."""


@compress_group.command("stats")
@click.argument("snapshot_name")
@click.option("--password", prompt=True, hide_input=True, help="Decryption password.")
@click.pass_context
def compress_stats(ctx: click.Context, snapshot_name: str, password: str) -> None:
    """Show compression stats for a stored snapshot."""
    cfg: Config = ctx.obj["config"]
    store = _get_store(cfg)
    try:
        raw_bytes = store.load(snapshot_name)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    from envpack.crypto import decrypt

    try:
        plaintext = decrypt(raw_bytes, password)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(f"Decryption failed: {exc}") from exc

    compressed = compress_text(plaintext.decode("utf-8"))
    result = CompressResult(
        original_size=len(plaintext),
        compressed_size=len(compressed),
    )
    click.echo(f"Snapshot : {snapshot_name}")
    click.echo(f"Stats    : {result.summary()}")


@compress_group.command("estimate")
@click.argument("env_file", type=click.Path(exists=True))
def estimate(env_file: str) -> None:
    """Estimate compression savings for a local .env file."""
    with open(env_file, "r", encoding="utf-8") as fh:
        text = fh.read()

    compressed = compress_text(text)
    result = CompressResult(
        original_size=len(text.encode("utf-8")),
        compressed_size=len(compressed),
    )
    click.echo(f"File  : {env_file}")
    click.echo(f"Stats : {result.summary()}")
