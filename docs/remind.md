# Snapshot Staleness Reminders

The `remind` command group helps you keep your `.env` snapshots fresh by warning you when they haven't been updated in a configurable number of days.

## Commands

### `envpack remind check`

Checks all snapshots against the staleness threshold and exits with code **1** if any are stale.

```bash
envpack remind check --days 30
```

This is suitable for use in CI pipelines or pre-commit hooks to enforce freshness.

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | `30` | Days before a snapshot is considered stale |
| `--password` | `$ENVPACK_PASSWORD` | Master password |

**Exit codes:**
- `0` — all snapshots are within the threshold
- `1` — one or more snapshots are stale

### `envpack remind list`

Lists every snapshot with its age and a `STALE` / `ok` marker.

```bash
envpack remind list --days 14
```

Example output:

```
[STALE] prod: last updated 42.0 days ago (threshold: 14d)
[ok   ] staging: last updated 3.1 days ago (threshold: 14d)
```

## Automating reminders

Add a cron job or CI step that runs `envpack remind check` periodically:

```yaml
# .github/workflows/env-freshness.yml
- name: Check env freshness
  run: envpack remind check --days 30
  env:
    ENVPACK_PASSWORD: ${{ secrets.ENVPACK_PASSWORD }}
```

## Programmatic usage

```python
from envpack.remind import check_staleness
from envpack.store import GitStore

store = GitStore("/path/to/store")
report = check_staleness(store, threshold_days=30)
print(report.summary())
for entry in report.stale:
    print(entry)
```
