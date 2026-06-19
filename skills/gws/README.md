# gws skill — notes

Companion to `SKILL.md`. The skill body covers day-to-day usage; this file
covers setup details, mainly **multi-account switching**.

## Where credentials live

`~/.config/gws/`:
- `client_secret.json` — OAuth client (client_id/secret/project_id), not the user token
- `credentials.enc` — your refresh token, **AES-256-GCM encrypted**
- `token_cache.json` — cached short-lived access tokens

The encryption key is stored in the **OS keychain** (service `gws-cli`), not on
disk. So `credentials.enc` alone is useless on another machine — the key doesn't
travel with it.

## Multi-account switching

gws stores **one login at a time** — `gws auth login` overwrites the previous
account's `credentials.enc`. There's no native `--account` flag. Switch by
keeping each account in its own config dir.

### Method 1 — per-account config dir (recommended; stays encrypted)

`GOOGLE_WORKSPACE_CLI_CONFIG_DIR` points gws at a different config dir, each with
its own encrypted `credentials.enc`. They don't overwrite each other, and the
keychain key (`gws-cli` + username) decrypts all of them.

One-time setup:
```bash
# account 1 (frank): wrap the existing default dir
cp -r ~/.config/gws ~/.config/gws-frank

# account 2 (other): fresh dir, reuse the same client, log in as that account
mkdir -p ~/.config/gws-other
cp ~/.config/gws/client_secret.json ~/.config/gws-other/
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-other gws auth login
```

Daily use — add aliases to your shell profile:
```bash
alias gws-frank='GOOGLE_WORKSPACE_CLI_CONFIG_DIR=$HOME/.config/gws-frank gws'
alias gws-other='GOOGLE_WORKSPACE_CLI_CONFIG_DIR=$HOME/.config/gws-other gws'

gws-frank gmail +send --to ...
gws-other drive files list ...
```

### Method 2 — exported plaintext file (quicker, less safe)

```bash
gws auth login && gws auth export --unmasked > ~/.gws/frank.json   # after logging in as frank
gws auth login && gws auth export --unmasked > ~/.gws/other.json   # after logging in as other
# select per call:
GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=~/.gws/frank.json gws gmail +send ...
```
The exported file is a **plaintext refresh token** — lock down its permissions.
Prefer Method 1.

## Prerequisite for each account

gws attaches a quota project, so every account must be able to use the project's
quota — i.e. hold **`roles/serviceUsageConsumer`** (or higher) on the OAuth
client's GCP project (`agent-mcp-495904`).

The login/consent gate (test-user list) no longer applies: the consent screen is
published to **In production**, so any account can authenticate — and its refresh
token no longer expires after 7 days.

## Reference

Upstream project: <https://github.com/googleworkspace/cli>

- Install: `brew install googleworkspace-cli` or `npm i -g @googleworkspace/cli`
- Discover any command at runtime: `gws <service> --help`, `gws schema <service>.<resource>.<method>`
- Full skill/recipe index: the repo's `docs/skills.md` (or run `gws generate-skills`)
