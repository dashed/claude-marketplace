# Authentication — gogcli

gogcli accepts credentials from four sources. Precedence (highest first):

1. **Direct access token** via `--access-token <token>` or `GOG_ACCESS_TOKEN=<token>`. Bypasses the keyring entirely. ~1h TTL with no auto-refresh. Good for CI.
2. **Application Default Credentials (ADC)** when `GOG_AUTH_MODE=adc`. Works with Workload Identity, Cloud Run, and `gcloud auth application-default login`. Added in 0.12.0.
3. **Service account + Domain-Wide Delegation (DWD)**. Workspace only. Takes precedence over OAuth refresh tokens for that account. Required for `keep` and `admin`.
4. **OAuth refresh token** (Desktop OAuth 2.0 flow). Tokens stored in the OS keyring.

## Table of contents

- [OAuth setup](#oauth-setup)
- [Multiple OAuth clients](#multiple-oauth-clients)
- [Headless / remote flows](#headless--remote-flows)
- [Least-privilege scope flags](#least-privilege-scope-flags)
- [Application Default Credentials (ADC)](#application-default-credentials-adc)
- [Direct access token](#direct-access-token)
- [Service account + Domain-Wide Delegation](#service-account--domain-wide-delegation)
- [Account selection and aliases](#account-selection-and-aliases)
- [Credential storage and keyring backends](#credential-storage-and-keyring-backends)
- [Re-auth and extra scopes](#re-auth-and-extra-scopes)

## OAuth setup

```bash
# 1. Store the Desktop OAuth client JSON. Only required once per client.
gog auth credentials /path/to/client_secret.json

# 2. Launch the browser OAuth flow; persists a refresh token in the keyring.
gog auth add you@example.com

# 3. Verify.
gog auth status
gog auth list --check
```

`gog auth credentials` copies the client JSON to `$(os.UserConfigDir())/gogcli/credentials.json` (mode `0600`). Refresh tokens are stored in the OS keyring under service name `gogcli`, key `token:<client>:<email>`.

Remove an account:

```bash
gog auth remove you@example.com   # aliases: logout
```

## Multiple OAuth clients

Use `--client <name>` to maintain credentials for more than one OAuth app (e.g. personal vs work):

```bash
gog --client work auth credentials /path/to/work-client.json
gog --client work auth add you@company.com

gog --client personal auth credentials /path/to/personal-client.json
gog --client personal auth add you@gmail.com
```

Auto-selection is also possible via `account_clients` or `client_domains` in `config.json` — map accounts or domains to a client name, and `gog` will pick it automatically when you pass `--account`.

Per-client credentials live at `$(os.UserConfigDir())/gogcli/credentials-<client>.json`; tokens are keyed `token:<client>:<email>`.

## Headless / remote flows

For servers, containers, or SSH sessions where the browser can't open locally:

| Flag | Purpose |
|---|---|
| `--manual` | Print the auth URL, then paste the Google redirect URL back into the prompt. |
| `--remote --step 1 ...` | Print the auth URL and cache state for ~10 minutes. |
| `--remote --step 2 --auth-url <url>` | Exchange the redirect URL from step 1 on another machine. |
| `--listen-addr <host[:port]>` | Bind OAuth callback listener behind a proxy/tunnel. |
| `--redirect-host <host>` | Override the redirect host announced to Google. |
| `--redirect-uri <url>` | Full custom callback URI. Reused across printed URL, state cache, and exchange. |
| `--force-consent` | Force Google to re-prompt and re-issue a refresh token. |

Remote step-2 replay preserves scope-shaping flags (0.12) so `--remote --step 2` asks for the same token set as step 1 did.

## Least-privilege scope flags

Pass these on `auth add` to narrow the OAuth scope set:

| Flag | Meaning |
|---|---|
| `--services <csv>` | Comma-separated service set. Default `user` = user-facing services. Other values: `all`, `gmail`, `calendar`, `drive`, `docs`, `contacts`, `tasks`, `sheets`, `people`, `groups`, `keep`, `admin`, etc. |
| `--readonly` | Request readonly scopes where supported. |
| `--drive-scope <full\|readonly\|file>` | `file` = write-limited to files opened/created by this app. Can't combine with `--readonly`. |
| `--gmail-scope <full\|readonly>` | `readonly` = `gmail.readonly` only. |
| `--extra-scopes <csv>` | Append additional OAuth scope URIs (e.g. `https://www.googleapis.com/auth/gmail.labels`). |

For any limited/readonly flag, `gogcli` passes `include_granted_scopes=false` to prevent older broad grants from silently accumulating.

Print the full resolved scope list for a service set with:

```bash
gog auth services
```

## Application Default Credentials (ADC)

Added in 0.12.0. Uses the standard Google ADC chain (Workload Identity, Cloud Run, `gcloud auth application-default login`, `GOOGLE_APPLICATION_CREDENTIALS`).

```bash
export GOG_AUTH_MODE=adc
gog drive ls --json
```

No keyring involvement; tokens are fetched via the metadata server or the ADC file directly.

## Direct access token

```bash
# Flag form.
gog --access-token "ya29.a0Af..." drive ls --json

# Env form (good for CI).
export GOG_ACCESS_TOKEN="ya29.a0Af..."
gog drive ls --json
```

This path bypasses the keyring entirely. Typical TTL is ~1 hour; `gogcli` does **not** auto-refresh. Provision the token upstream (e.g. `gcloud auth print-access-token`, a short-lived IAM-minted token, or a just-in-time CI step).

## Service account + Domain-Wide Delegation

Workspace only. Required for `keep` (all commands) and `admin`.

### Cloud Console

1. Create a service account.
2. Enable **Domain-wide delegation** on the account.
3. Create and download a JSON key.

### Workspace Admin

Security → API controls → Domain-wide delegation → Register the service account's Client ID with the comma-separated list of scopes you need. `gog auth services` prints the exact list.

### Configure gogcli

```bash
gog auth service-account set you@company.com --key /path/to/sa.json
gog auth service-account list
gog auth service-account get you@company.com
gog auth service-account unset you@company.com
```

Once set, the SA takes precedence over any stored OAuth refresh token for that subject. If the configured subject matches the SA itself (no impersonation), pure service-account mode works (0.12 fix).

**Common failures**

- Token mint fails or API returns 403 "insufficient permissions": a required scope isn't registered in Workspace Admin's DWD allowlist. Add it and retry.
- Keep service-account fallback is isolated to Keep commands since 0.12 — it won't leak into Gmail, Drive, etc.

## Account selection and aliases

```bash
gog --account you@example.com events --today
gog --account work drive ls --max 20
export GOG_ACCOUNT=work-alias
```

`auto` = the default account (or the sole stored account). Reserved words: `auto`, `default`.

Aliases:

```bash
gog auth alias set work you@company.com
gog auth alias list
gog auth alias unset work
```

Or declare aliases in `config.json` under `account_aliases`.

## Credential storage and keyring backends

| Item | Location |
|---|---|
| Client credentials | `$(os.UserConfigDir())/gogcli/credentials[-<client>].json` (`0600`) |
| Refresh tokens | OS keyring (`github.com/99designs/keyring`), service `gogcli`, key `token:<client>:<email>`. Legacy `token:<email>` is migrated on read. |
| File-backend tokens | `$(os.UserConfigDir())/gogcli/keyring/` (encrypted blobs) |

Choose a backend:

```bash
gog auth keyring auto       # Platform default.
gog auth keyring keychain   # macOS Keychain.
gog auth keyring file       # Encrypted file backend.
```

Or set `GOG_KEYRING_BACKEND=<auto|keychain|file>` — the env var wins over the configured value.

For non-interactive `file` backend use:

```bash
export GOG_KEYRING_BACKEND=file
export GOG_KEYRING_PASSWORD='<passphrase>'
```

Without `GOG_KEYRING_PASSWORD`, `--no-input` will fail to unlock the file backend.

**macOS tip.** Keychain treats different binary paths as different apps (so `go run`, `./bin/gog`, and `/opt/homebrew/bin/gog` each trigger fresh prompts). Pick one stable path or use the file backend.

## Re-auth and extra scopes

Use `--extra-scopes` to append scope URIs beyond the built-in service set:

```bash
gog auth add you@example.com \
    --services gmail \
    --extra-scopes "https://www.googleapis.com/auth/gmail.labels,https://www.googleapis.com/auth/gmail.settings.basic"
```

If Google doesn't return a refresh token (because consent was previously granted), force a fresh one:

```bash
gog auth add you@example.com --force-consent
```

Remote step-2 replay (`--remote --step 2`) preserves scope-shaping flags from step 1, so the same token set is issued.

## Inspecting auth state

```bash
gog auth status              # Current account, client, and auth mode.
gog auth list                # All stored accounts with mode and scopes.
gog auth list --check        # Also validates each refresh token.
gog auth tokens              # Print stored token metadata (no secrets by default).
gog auth services            # Resolved scope URIs for a service set.
```
