# Snapshot Copy

The `copy` command duplicates an existing snapshot under a new name within the
same profile. The encrypted bytes are transferred verbatim — **no
re-encryption** is performed, so the same password works for both the original
and the copy.

## Usage

```bash
envpack copy run <source> <destination> [--profile PROFILE] [--password PASSWORD]
```

### Arguments

| Argument | Description |
|---|---|
| `source` | Name of the snapshot to copy from |
| `destination` | Name of the new snapshot |

### Options

| Option | Default | Description |
|---|---|---|
| `--profile` | `default` | Profile that owns both snapshots |
| `--password` | prompt / `ENVPACK_PASSWORD` | Encryption password |

## Examples

```bash
# Duplicate the current production snapshot before making changes
envpack copy run prod-2024-01-15 prod-2024-01-15-backup

# Copy within a named profile
envpack copy run latest latest-bak --profile staging
```

## Notes

- The destination name must not already exist in the profile. Use
  `envpack rename` if you want to move a snapshot instead.
- Because the raw ciphertext is copied directly, you do not need to supply the
  correct password for the operation to succeed — the password option is
  accepted for API consistency but is not used during the copy itself.
- To re-encrypt snapshots under a new password, use `envpack rotate` instead.
