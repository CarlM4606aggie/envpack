# Watch Mode

`envpack watch start` monitors a `.env` file for changes and automatically pushes a new encrypted snapshot whenever the file is modified.

## Usage

```bash
envpack watch start .env --password mysecret
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--password` | *(prompted)* | Encryption password used for the snapshot. |
| `--interval` | `2.0` | Polling interval in seconds. |
| `--snapshot` | filename stem | Override the snapshot name. |

## How It Works

1. On startup, `envpack` records the SHA-256 hash of the target file.
2. Every `--interval` seconds the file is re-hashed.
3. When the hash differs from the last known value, a new snapshot is pushed via `SnapshotManager.push`.
4. Press **Ctrl-C** to stop watching.

## Example Workflow

```bash
# Terminal 1 — start watcher
envpack watch start .env --password $ENVPACK_PASS --interval 5

# Terminal 2 — edit the file; the watcher will push automatically
echo 'NEW_KEY=hello' >> .env
```

## Notes

- The watcher uses **polling**, not filesystem events, to remain cross-platform.
- Each detected change creates a **separate snapshot**; use `envpack prune` to limit history.
- The watcher does **not** detect file deletions as a change to push — it simply records the absence.
