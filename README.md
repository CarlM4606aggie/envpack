# envpack

> A shell utility to snapshot, encrypt, and sync `.env` files across machines using a Git-backed store.

---

## Installation

```bash
pip install envpack
```

Or install from source:

```bash
git clone https://github.com/yourname/envpack.git && cd envpack && pip install .
```

---

## Usage

**Snapshot and encrypt your current `.env` file:**

```bash
envpack push --env .env --store ~/dotenv-store
```

**Pull and decrypt on another machine:**

```bash
envpack pull --store ~/dotenv-store --out .env
```

**List stored snapshots:**

```bash
envpack list --store ~/dotenv-store
```

Encryption is handled via a passphrase or key file. The backing store is a plain Git repository you control — local or remote (e.g. a private GitHub repo).

```bash
# Initialize a new Git-backed store
envpack init --store ~/dotenv-store --remote git@github.com:yourname/env-store.git
```

---

## How It Works

1. `envpack push` encrypts your `.env` file and commits the snapshot to the Git store.
2. `envpack pull` fetches the latest snapshot, decrypts it, and writes it to disk.
3. All secrets stay encrypted at rest — only the passphrase holder can read them.

---

## Requirements

- Python 3.8+
- Git installed and available on `PATH`

---

## License

MIT © 2024 [yourname](https://github.com/yourname)