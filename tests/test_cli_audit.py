"""Tests for the audit CLI commands."""
import pytest
from click.testing import CliRunner
from pathlib import Path

from envpack.audit import AuditEntry, AuditLog
from envpack.cli_audit import audit_group
from envpack.config import Config


@pytest.fixture
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    store_path = tmp_path / "store"
    store_path.mkdir()
    cfg = Config(store_path=str(store_path), profile="default")
    cfg.save(tmp_path / "config.toml")
    monkeypatch.setattr(
        "envpack.cli_audit.Config",
        type("FakeCfg", (), {"load": staticmethod(lambda: cfg)}),
    )
    return store_path


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_log_empty(runner: CliRunner, isolated_config: Path) -> None:
    result = runner.invoke(audit_group, ["log"])
    assert result.exit_code == 0
    assert "No audit log entries" in result.output


def test_log_shows_entries(runner: CliRunner, isolated_config: Path) -> None:
    log = AuditLog(isolated_config)
    log.record(AuditEntry.now("push", "default", "my-app", ".env"))
    result = runner.invoke(audit_group, ["log"])
    assert result.exit_code == 0
    assert "PUSH" in result.output
    assert "my-app" in result.output


def test_log_filter_by_action(runner: CliRunner, isolated_config: Path) -> None:
    log = AuditLog(isolated_config)
    log.record(AuditEntry.now("push", "default", "snap-push", ".env"))
    log.record(AuditEntry.now("pull", "default", "snap-pull", ".env"))
    result = runner.invoke(audit_group, ["log", "--action", "pull"])
    assert result.exit_code == 0
    assert "snap-pull" in result.output
    assert "snap-push" not in result.output


def test_log_filter_by_profile(runner: CliRunner, isolated_config: Path) -> None:
    log = AuditLog(isolated_config)
    log.record(AuditEntry.now("push", "prod", "prod-snap", ".env"))
    log.record(AuditEntry.now("push", "dev", "dev-snap", ".env"))
    result = runner.invoke(audit_group, ["log", "--profile", "prod"])
    assert result.exit_code == 0
    assert "prod-snap" in result.output
    assert "dev-snap" not in result.output


def test_log_limit(runner: CliRunner, isolated_config: Path) -> None:
    log = AuditLog(isolated_config)
    for i in range(5):
        log.record(AuditEntry.now("push", "default", f"snap-{i}", ".env"))
    result = runner.invoke(audit_group, ["log", "-n", "2"])
    assert result.exit_code == 0
    assert result.output.count("PUSH") == 2


def test_clear_log(runner: CliRunner, isolated_config: Path) -> None:
    log = AuditLog(isolated_config)
    log.record(AuditEntry.now("push", "default", "snap", ".env"))
    result = runner.invoke(audit_group, ["clear"], input="y\n")
    assert result.exit_code == 0
    assert log.entries() == []
