# Password Rotation

envpack supports rotating the encryption password used to protect your `.env` snapshots. This is useful when:

- A team member with access to the old password leaves.
- You want to periodically refresh credentials.
- A password may have been compromised.

## How it works

Rotation decrypts every snapshot stored under a profile using the **old password**, then immediately re-encrypts each one with the **new password**. Each re-encrypted snapshot is committed to the Git-backed store so the full history is preserved.

## CLI usage

```bash
# Interactive prompts for both passwords
envpack rotate run

# Explicit flags (useful in scripts — prefer prompts for security)
envpack rotate run --old-password OLD --new-password NEW

# Rotate a specific profile
envpack rotate run --profile production

# Use a custom store path
envpack rotate run --store-path /path/to/store
```

## Python API

```python
from envpack.store import GitStore
from envpack.rotate import rotate_snapshots

store = GitStore("/path/to/store")
result = rotate_snapshots(store, old_password="old", new_password="new", profile="default")

print(result.summary())
if not result.success:
    print("Some snapshots failed:", result.failed)
```

## Failure handling

If a snapshot cannot be decrypted with the old password (e.g. it was encrypted with a different key), it is recorded in `result.failed` and the CLI exits with a non-zero status. Successfully rotated snapshots are **not** rolled back — inspect the failed list and re-run after correcting the issue.

## Audit log

Each rotated snapshot produces a Git commit with the message `rotate: <profile>/<name>`, providing a clear audit trail in the store repository.
