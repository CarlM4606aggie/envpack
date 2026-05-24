# Template Rendering

`envpack template` lets you fill `{{KEY}}` placeholders in any text file using
values decrypted from a stored snapshot.

## Quick start

```bash
# Render a template to stdout using the latest snapshot
envpack template render config/database.tmpl

# Write the result to a file
envpack template render config/database.tmpl -o config/database.conf

# Use a specific snapshot
envpack template render config/database.tmpl -s prod-2024-01-15

# Fail if any placeholder cannot be resolved
envpack template render config/database.tmpl --strict
```

## Template syntax

Placeholders follow the `{{ KEY }}` convention (whitespace around the key is
ignored). Keys must match a `KEY=VALUE` line in the referenced snapshot.

```
# config/database.tmpl
[database]
host     = {{ DB_HOST }}
port     = {{ DB_PORT }}
password = {{ DB_PASSWORD }}
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `-s / --snapshot` | `latest` | Snapshot name to source values from |
| `-o / --output` | stdout | Write rendered output to this path |
| `--strict` | off | Exit non-zero if any placeholder is unresolved |
| `--profile` | config default | Profile override |

## Missing keys

By default, unresolved `{{ KEY }}` placeholders are left as-is and a warning
is printed to stderr. Use `--strict` to treat this as a hard error.
