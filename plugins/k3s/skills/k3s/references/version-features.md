# k3s Feature → Minimum Version

A consolidated lookup of **which k3s version introduced a flag or subcommand** this skill
documents, so you know what works on an older (or newer) k3s. Use it to answer "is my k3s new
enough for X?" and "what do I need to upgrade to?"

**How to read this:**

- These are **k3s release versions**. k3s tracks upstream **Kubernetes minor versions** — a
  release is tagged `vMAJOR.MINOR.PATCH+k3s<n>` (e.g. `v1.31.3+k3s1`). The `vX.Y+` here means
  "the v1.Y line and later."
- Versions are the **earliest k3s minor known to ship the feature**. k3s **backports features
  to all supported minor lines simultaneously**, so a flag developed in the v1.31 cycle also
  lands in later-dated patches of v1.29.x / v1.30.x. The "Min version" below is the *cycle the
  feature was developed in* (earliest by release date), matching official k3s docs — a
  lower-numbered backport may exist in an older line at a later date.
- **Caveat (source method):** versions were resolved by scanning the flag/subcommand string
  across k3s's release-tag source blobs in a **shallow clone** (the `-S` pickaxe over file
  history does not work there) and taking the earliest tag by date. Treat each as the
  **earliest-known-shipping minor**, reliable at minor granularity but not per-patch-per-line.
- **Features not listed here are long-standing** — present at or before the tracked floor
  (**v1.26.0**, 2022-12-13) and treated as bedrock. This includes the core daemon surface
  (`--token`, `--server`, `--tls-san`, `--disable`, `--node-label`/`--node-taint`,
  `--datastore-endpoint`, `--cluster-init`/`--cluster-reset`, the networking CIDR flags, the
  core `--etcd-s3*` set, `--data-dir`, `--write-kubeconfig`/`--write-kubeconfig-mode`,
  `--secrets-encryption`, `--enable-pprof` server-side, `--egress-selector-mode`,
  `--servicelb-namespace`, the `--disable-*` HA split-role flags) and the subcommands present
  at the floor (see [Subcommands at the tracked floor](#subcommands-at-the-tracked-floor)).
  This file omits them to stay signal-rich. The clone's usable tag floor is v1.26.0; anything
  "at the floor" may genuinely be older.
- This skill is documented against **k3s v1.35.0+k3s1** (working tree
  `v1.35.0+k3s1-256-g9269a8f5c3`). Always confirm on the running system: `k3s --version`.

## Contents

- [Versioned flags & subcommands](#versioned-flags--subcommands)
- [Subcommands at the tracked floor](#subcommands-at-the-tracked-floor)
- [Checking your version & install channels](#checking-your-version--install-channels)

## Versioned flags & subcommands

Sorted ascending by minimum k3s minor.

| Min version | Feature | Area |
|---|---|---|
| v1.27+ | `--helm-job-image` — default image for Helm jobs | server / helm |
| v1.27+ | `--vpn-auth` / `--vpn-auth-file` — Tailscale/VPN credentials *(Exp, deprecated-section)* | agent / networking |
| v1.27+ | `--enable-pprof` exposed on the **agent** (server-side since the v1.26.0 floor) *(Exp)* | agent / profiling |
| v1.28+ | `--embedded-registry` — embedded distributed (Spegel) registry mirror | server / registry |
| v1.28+ | `--tls-san-security` — refuse SANs unrelated to the apiserver/server nodes (default `true`) | server / tls |
| v1.28+ | `--disable-default-registry-endpoint` — disable containerd's fallback default registry endpoint (server + agent) | agent / containerd |
| v1.28+ | `--image-service-endpoint` — external CRI image-service socket | agent / runtime |
| v1.28+ | `--disable-apiserver-lb` — disable the agent client-side load-balancer *(Exp, deprecated-section)* | agent / networking |
| v1.28+ | `k3s token rotate` — rotate the server token with a new one | subcommand / token |
| v1.28+ | `k3s secrets-encrypt rotate-keys` — one-shot dynamic rotate + reencrypt | subcommand / secrets |
| v1.29+ | `--kine-tls` — TLS on the kine etcd socket *(Hidden, Exp)* | server / db |
| v1.29+ | `--default-runtime` — default runtime class in containerd | agent / runtime |
| v1.30+ | `--supervisor-metrics` — serve k3s internal metrics on the supervisor port *(Exp)* | server / metrics |
| v1.30+ | `--write-kubeconfig-group` — group owner of the written kubeconfig | server / kubeconfig |
| v1.30+ | `--etcd-s3-proxy` — proxy for S3 snapshot backups | server / etcd-s3 |
| v1.30+ | `--etcd-s3-config-secret` — `kube-system` secret that configures S3 | server / etcd-s3 |
| v1.31+ | `--nonroot-devices` — allow non-root pods device access (server + agent) | agent / containerd |
| v1.31+ | `--node-internal-dns` / `--node-external-dns` — advertise DNS names for the node *(inferred from release date; med-high confidence)* | agent / node |
| v1.32+ | `--etcd-snapshot-reconcile-interval` — snapshot reconcile interval *(inferred from release date; med-high confidence)* | server / etcd |
| v1.32+ | `--secrets-encryption-provider` — `aescbc` or `secretbox` *(Exp)* | server / secrets |
| v1.33+ | `--etcd-s3-bucket-lookup-type` — S3 bucket addressing: `auto`/`dns`/`path` | server / etcd-s3 |

## Subcommands at the tracked floor

These management subcommands already existed at the tracked floor (**v1.26.0**, 2022-12-13),
so they are unversioned in the table above — they may predate the window. Listed here because
they are commonly assumed to be newer than they are:

| Subcommand | Status |
|---|---|
| `k3s token` (`create`/`delete`/`generate`/`list`) | present at v1.26.0 (the `rotate` subcommand is v1.28+) |
| `k3s secrets-encrypt` (`status`/`enable`/`disable`/`prepare`/`rotate`/`reencrypt`) | present at v1.26.0 (`rotate-keys` is v1.28+) |
| `k3s certificate check` / `rotate` | present at v1.26.0 |
| `k3s certificate rotate-ca` | present at v1.26.0 (older than commonly assumed) |
| `k3s etcd-snapshot` (`save`/`delete`/`ls`/`prune`) | all four present at v1.26.0 — `prune` is **not** new |

## Checking your version & install channels

Check what you are running:

```
k3s --version          # e.g. k3s version v1.35.0+k3s1 (9269a8f5)
```

The installer (`https://get.k3s.io`) selects a release via `INSTALL_K3S_CHANNEL`:

| Channel | Meaning |
|---|---|
| `stable` | the recommended stable release (default) |
| `latest` | the newest release across all channels |
| `vX.Y` (e.g. `v1.31`) | the latest patch of a specific Kubernetes minor line |

```
curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=v1.31 sh -
```

Pin a specific build with `INSTALL_K3S_VERSION=v1.31.3+k3s1` instead. Because k3s backports
features across supported minor lines, upgrading to the latest **patch** of your current minor
often picks up a backported flag without a minor bump — but the "Min version" column above is
the safe floor.
