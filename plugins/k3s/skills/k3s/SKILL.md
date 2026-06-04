---
name: k3s
description: The k3s lightweight CNCF-certified Kubernetes distribution shipped as a single binary that bundles containerd, flannel, CoreDNS, Traefik, ServiceLB (Klipper), local-path-provisioner, and metrics-server. Use when installing or running a lightweight Kubernetes cluster, bootstrapping a single-node or HA k3s control plane, joining agent (worker) nodes, choosing embedded etcd vs an external SQL datastore, managing cluster/agent tokens, rotating certificates, taking or restoring etcd snapshots, enabling secrets encryption, doing airgap or private-registry installs, disabling bundled components (Traefik/ServiceLB/CoreDNS), or upgrading k3s. Triggers on mentions of k3s, `k3s server`, `k3s agent`, the `curl -sfL https://get.k3s.io | sh -` installer, `/etc/rancher/k3s/`, or Rancher's lightweight Kubernetes. This is the k3s CLI/distribution, NOT generic Kubernetes/kubectl.
---

# k3s - Lightweight Kubernetes Distribution

## Overview

k3s is a fully CNCF-certified Kubernetes distribution packaged as a **single self-contained binary** (≈70 MB). One executable is the control plane, the kubelet, the container runtime supervisor, and a multicall wrapper for `kubectl`/`crictl`/`ctr`. You run `k3s server` to start a control-plane node and `k3s agent` to start a worker; everything else (etcd or SQLite, networking, DNS, ingress, load balancing, storage) is bundled and started for you.

**What k3s bundles (and manages for you):**
- **containerd** — the embedded CRI runtime (no Docker needed; `--docker` to opt into cri-dockerd is deprecated)
- **flannel** — the default CNI (`--flannel-backend`: `vxlan` default, `host-gw`, `wireguard-native`, or `none`)
- **CoreDNS** — cluster DNS (deployed component `coredns`)
- **Traefik** — ingress controller (deployed component `traefik`)
- **ServiceLB / Klipper** — a built-in `LoadBalancer` service implementation (component `servicelb`)
- **local-path-provisioner** — default `local-path` StorageClass (component `local-storage`)
- **metrics-server** — resource metrics (component `metrics-server`)
- **SQLite by default**, with **embedded etcd** (for HA) or an **external datastore** (MySQL/Postgres/etcd/NATS) as alternatives

**Key characteristics:**
- **Single binary, single process tree** — `k3s server`/`k3s agent` supervise all components
- **Batteries-included** — a working cluster (ingress, LB, DNS, storage) right after install
- **Config in one place** — `/etc/rancher/k3s/`: `config.yaml`, `k3s.yaml` (kubeconfig), `registries.yaml`
- **Easy to slim down** — `--disable` any bundled component to bring your own

> **Disambiguation:** This skill is about the **k3s distribution and its `k3s` CLI** — installation, the `server`/`agent` lifecycle, bundled components, tokens, etcd snapshots, certs. It does **not** teach generic Kubernetes or `kubectl` usage; for that, use Kubernetes documentation. Anything k3s-specific (what it adds, bundles, or changes) belongs here.

## When to Use This Skill

Use this skill when:
- **Installing k3s**: the `curl -sfL https://get.k3s.io | sh -` installer and `INSTALL_K3S_*` env vars
- **Bootstrapping a cluster**: single-server, HA with embedded etcd, or an external datastore
- **Joining nodes**: agents (workers) or additional servers via `K3S_URL` + `K3S_TOKEN`
- **Slimming the stack**: `--disable traefik`, `--disable servicelb`, `--flannel-backend=none`, etc.
- **Day-2 operations**: etcd snapshots, certificate rotation, secrets encryption, token rotation
- **Restricted environments**: airgap installs, private/mirror registries (`registries.yaml`)
- **Remote API access**: adding SANs (`--tls-san`) and a readable kubeconfig (`--write-kubeconfig-mode`)
- **Upgrading / uninstalling**: re-running the installer, channels, the bundled uninstall scripts

## Prerequisites

**CRITICAL**: Before proceeding, verify k3s is installed and check the version:

```bash
k3s --version          # prints e.g. "k3s version v1.32.1+k3s1 (…)"
```

**Version note:** This skill is documented against the k3s source at **v1.35.0+k3s1**. Long-standing flags and paths work on any recent k3s; features added in a specific release are annotated inline as `(k3s vX.Y+)`. The "Since" marker is the **first minor cycle** a feature shipped in (k3s backports features to all supported minor lines, so an older patch release may also have it). Always confirm flags on the running version with `k3s server --help` / `k3s agent --help`.

**If k3s is not installed:** do **NOT** silently auto-install on someone's machine. k3s installs a systemd service and modifies the host — confirm intent first, then use the official installer (see [Install](#install)). The canonical install is:

```bash
curl -sfL https://get.k3s.io | sh -
```

**Where things live (memorize these):**
| Path | What |
|------|------|
| `/etc/rancher/k3s/k3s.yaml` | Admin kubeconfig written by the server (root-owned `0600` by default) |
| `/etc/rancher/k3s/config.yaml` | Server/agent config file (see [Configuration File](#configuration-file)) |
| `/etc/rancher/k3s/registries.yaml` | Private/mirror registry config |
| `/var/lib/rancher/k3s` | Data dir (`--data-dir`/`-d`); `${HOME}/.rancher/k3s` when run non-root |
| `/var/lib/rancher/k3s/server/db/` | Datastore (SQLite/etcd) |
| `/var/lib/rancher/k3s/server/db/snapshots/` | Default etcd snapshot directory |
| `/var/lib/rancher/k3s/server/node-token` | Token agents use to join (read on the first server) |

## Install

The installer script detects systemd/openrc, installs the binary, writes a service, and starts it. Configure it entirely through **environment variables** (set them before the pipe):

```bash
# Latest stable, server (control-plane) node — default behavior
curl -sfL https://get.k3s.io | sh -

# Pin a channel or exact version
curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=latest sh -
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.32.1+k3s1 sh -

# Pass server flags through INSTALL_K3S_EXEC
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik --tls-san k8s.example.com" sh -

# Install an AGENT and join an existing server
curl -sfL https://get.k3s.io | K3S_URL=https://myserver:6443 K3S_TOKEN=<node-token> sh -
```

**Key installer variables** (all verified in `install.sh`):
| Variable | Purpose |
|----------|---------|
| `INSTALL_K3S_EXEC` | Args/subcommand passed to the k3s service (e.g. `server --disable traefik`) |
| `INSTALL_K3S_CHANNEL` | Release channel: `stable` (default), `latest`, `testing` |
| `INSTALL_K3S_VERSION` | Exact version to install (e.g. `v1.32.1+k3s1`) |
| `INSTALL_K3S_SKIP_DOWNLOAD` | `true` = don't fetch the binary (airgap — you stage it yourself) |
| `INSTALL_K3S_SKIP_START` | `true` = install but don't start the service |
| `INSTALL_K3S_SKIP_ENABLE` | `true` = don't enable the service at boot |
| `INSTALL_K3S_BIN_DIR` | Install dir for the binary, links, and uninstall script |
| `INSTALL_K3S_SYMLINK` | `skip` to avoid the `kubectl`/`crictl`/`ctr` symlinks |
| `INSTALL_K3S_NAME` | Suffix for the service name (run multiple k3s instances) |

`K3S_URL` + `K3S_TOKEN` make the installer set up an **agent** by default; without `K3S_URL` it installs a **server**.

> The installer also creates uninstall scripts: **`/usr/local/bin/k3s-uninstall.sh`** (server) and **`/usr/local/bin/k3s-agent-uninstall.sh`** (agent). See [recipes.md](references/recipes.md#uninstall) for upgrade and uninstall flows.

## The `k3s` Binary: Subcommand Map

`k3s` is a multicall binary — symlinks named `kubectl`/`crictl`/`ctr` invoke those passthroughs directly.

| Subcommand | Purpose |
|------------|---------|
| `k3s server` | Run a control-plane node (also runs an agent unless `--disable-agent`) |
| `k3s agent` | Run a worker node; needs `K3S_URL` + a token |
| `k3s kubectl` | Bundled kubectl (args forwarded verbatim) |
| `k3s crictl` | Bundled crictl (CRI debugging) |
| `k3s ctr` | Bundled containerd `ctr` |
| `k3s token` | Manage join tokens: `create`, `delete`, `generate`, `list`, `rotate` |
| `k3s etcd-snapshot` | Manage embedded-etcd snapshots: `save`, `ls`, `delete`, `prune` |
| `k3s secrets-encrypt` | Secrets-at-rest encryption: `status`, `enable`, `disable`, `prepare`, `rotate`, `reencrypt`, `rotate-keys` |
| `k3s certificate` | Component certs: `check`, `rotate`, `rotate-ca` |
| `k3s check-config` | Validate the host's kernel/config for k3s |
| `k3s completion` | Shell completion (`bash`/`zsh`, `-i` to install) |

Global flags on the root app: `--debug` (env `K3S_DEBUG`) and `--data-dir`/`-d` (env `K3S_DATA_DIR`).

## Core Workflows

### 1. Single-server cluster + get the kubeconfig

```bash
# Start a server (the installer does this; here's the equivalent direct invocation)
k3s server

# The admin kubeconfig is written here:
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
k3s kubectl get nodes
```

The kubeconfig is root-owned `0600` by default. To make it readable by your user, or to write it elsewhere:

```bash
k3s server --write-kubeconfig-mode 0644
k3s server --write-kubeconfig /home/me/.kube/config   # -o, env K3S_KUBECONFIG_OUTPUT
```

### 2. HA with embedded etcd

Embedded etcd needs an **odd number of servers** (3 or 5) for quorum (`floor(n/2)+1`). Use `--cluster-init` on the **first server only**; everyone else joins with `--server` + `--token`.

```bash
# First server — initializes a new embedded-etcd cluster
k3s server --cluster-init --token <SECRET>

# Second & third servers — JOIN (no --cluster-init!)
k3s server --server https://<first-server>:6443 --token <SECRET>
```

> `--cluster-init` is **only** for the first node. Re-using it on joiners is wrong. Losing quorum (e.g. 2 of 3 servers down) requires `--cluster-reset` — see [recipes.md](references/recipes.md#etcd-snapshots--restore).

### 3. External datastore (no embedded etcd)

Pass `--datastore-endpoint` to **every** server; do **not** combine with `--cluster-init`. SQLite is the single-node default; MySQL/MariaDB, Postgres, etcd, and NATS are supported DSNs.

```bash
k3s server \
  --datastore-endpoint='postgres://user:pass@db.example.com:5432/k3s' \
  --token <SECRET>
# TLS to the datastore: --datastore-cafile / --datastore-certfile / --datastore-keyfile
```

### 4. Join agent (worker) nodes

Agents authenticate with `K3S_URL` (the server) + `K3S_TOKEN`. The token is the cluster token, or an **agent-only** token (`--agent-token`, which cannot add servers).

```bash
# On a server, read the node token:
sudo cat /var/lib/rancher/k3s/server/node-token

# On the worker (env vars are the idiomatic form for agents):
K3S_URL=https://<server>:6443 K3S_TOKEN=<node-token> k3s agent
# equivalently: k3s agent --server https://<server>:6443 --token <node-token>
```

### 5. Disabling bundled components

`--disable` (a repeatable/comma-list of **packaged components**) accepts exactly: **`coredns`, `servicelb`, `traefik`, `local-storage`, `metrics-server`, `runtimes`** (on Linux; Windows/`nostage` builds allow only `coredns, servicelb`).

```bash
k3s server --disable traefik --disable servicelb        # drop ingress + LoadBalancer
k3s server --disable traefik,servicelb,metrics-server   # comma-list also works
```

> **`coredns` IS disable-able** via `--disable` (you'd then run your own DNS). Other subsystems have **dedicated bool flags**, not `--disable` values: `--disable-scheduler`, `--disable-cloud-controller`, `--disable-kube-proxy`, `--disable-network-policy`, `--disable-helm-controller`.

Bring your own CNI by disabling flannel: `--flannel-backend=none` (then apply your CNI manifests).

### 6. Common day-2 one-liners

```bash
# Take an on-demand etcd snapshot (embedded etcd only)
k3s etcd-snapshot save --name pre-upgrade

# List / prune snapshots
k3s etcd-snapshot ls
k3s etcd-snapshot prune --snapshot-retention 5

# Check / rotate component certificates (restart k3s after a rotate)
k3s certificate check
k3s certificate rotate

# Secrets-encryption status and one-shot key rotation
k3s secrets-encrypt status
k3s secrets-encrypt rotate-keys         # (k3s v1.28+) modern one-shot rotate+reencrypt

# Rotate the server token, then restart other nodes with the new value
k3s token rotate --token <old> --new-token <new>    # (k3s v1.28+)
```

## Tokens (get these right)

- **`--token`** (env `K3S_TOKEN`) is the cluster join secret — it joins **both servers and agents**.
- **`--agent-token`** (env `K3S_AGENT_TOKEN`) joins **agents only** — hand it to workers so they cannot be used to add control-plane servers.
- `--token-file` / `--agent-token-file` read the secret from a file.
- Every non-first node presents the token via `--token` + `--server https://<first-server>:6443`.

## Configuration File

Instead of long flag lists, put settings in **`/etc/rancher/k3s/config.yaml`** (override with `--config`/`-c` or env `K3S_CONFIG_FILE`). Each top-level YAML key maps to the same-named flag; list values become repeated flags; bools map to bool flags.

```yaml
# /etc/rancher/k3s/config.yaml
write-kubeconfig-mode: "0644"
tls-san:
  - k8s.example.com
  - 10.0.0.10
disable:
  - traefik
  - servicelb
node-label:
  - "topology.kubernetes.io/region=us-east"
```

- **Drop-ins**: files in `/etc/rancher/k3s/config.yaml.d/*.yaml` load in lexical order **after** the base file.
- **List-append `+`**: a key suffixed with `+` (e.g. `node-label+:`) **appends** to earlier values instead of replacing them.
- **Precedence**: command-line flags override (or, for list flags, append to) config-file values.
- **Unknown keys** are logged and skipped (warning, not fatal). The config is **optional** unless you pass `--config` to a missing path.

## Quick Reference

| Flag / item | Purpose |
|-------------|---------|
| `--token` / `-t` (env `K3S_TOKEN`) | Cluster join secret (servers + agents) |
| `--server` / `-s` (env `K3S_URL`) | URL of an existing server to join |
| `--cluster-init` | Bootstrap embedded etcd on the **first** server |
| `--cluster-reset` (+ `--cluster-reset-restore-path`) | Reduce to one member / restore a snapshot |
| `--datastore-endpoint` | External datastore DSN (no `--cluster-init`) |
| `--disable` | Drop packaged components: `coredns,servicelb,traefik,local-storage,metrics-server,runtimes` |
| `--flannel-backend` | `vxlan` (default), `host-gw`, `wireguard-native`, `none` |
| `--tls-san` | Extra hostnames/IPs on the apiserver cert (for LB/VIP/public DNS access) |
| `--write-kubeconfig` / `-o`, `--write-kubeconfig-mode` | Where/with what mode to write the admin kubeconfig |
| `--node-label`, `--node-taint` | Repeatable labels/taints set at node registration |
| `--secrets-encryption` | Enable secrets-at-rest encryption |
| `--embedded-registry` | Enable the embedded Spegel distributed registry mirror (k3s v1.28+) |
| `--data-dir` / `-d` (env `K3S_DATA_DIR`) | State directory (default `/var/lib/rancher/k3s`) |

## Advanced Usage

For copy-pasteable, task-oriented procedures, see **[references/recipes.md](references/recipes.md)**:

- HA embedded-etcd 3-server bootstrap; external SQL datastore
- Adding/removing agent and server nodes
- Airgap install (image tarball + `INSTALL_K3S_SKIP_DOWNLOAD`)
- Private/mirror registry via `registries.yaml`
- Custom CNI (`--flannel-backend=none`); disabling Traefik + ServiceLB
- Secrets encryption enable + key-rotation flow
- etcd snapshot save/list/prune **and the full restore procedure** (`--cluster-reset --cluster-reset-restore-path`)
- Certificate rotation and `rotate-ca` flow
- Remote-access kubeconfig (`--tls-san`, `--write-kubeconfig-mode`)
- Uninstall scripts and upgrade flows (installer re-run, channels, System Upgrade Controller)

## Troubleshooting

**"Command not found: k3s"** — k3s isn't installed, or the `kubectl`/`crictl` symlinks were skipped (`INSTALL_K3S_SYMLINK=skip`). Use `k3s kubectl …` directly, or check `/usr/local/bin`.

**"kubectl can't connect" / permission denied on kubeconfig** — the kubeconfig at `/etc/rancher/k3s/k3s.yaml` is root-owned `0600`. `export KUBECONFIG=/etc/rancher/k3s/k3s.yaml` (and run as root), or restart the server with `--write-kubeconfig-mode 0644`.

**"x509 / certificate is not valid for the requested name"** — you're reaching the API via a name/IP not on the cert. Add it with `--tls-san <name>` and restart. `--tls-san-security` defaults **true** and rejects SANs unrelated to the apiserver service or server nodes unless listed in `--tls-san`.

**Agent won't join** — verify `K3S_URL` points at `https://<server>:6443`, the token matches (`/var/lib/rancher/k3s/server/node-token`), and the supervisor port is reachable. An agent-only token (`--agent-token`) cannot join servers.

**Embedded-etcd cluster won't form a quorum** — you need an **odd** number of servers, and only the first uses `--cluster-init`. To recover a lost quorum, see the `--cluster-reset` procedure in [recipes.md](references/recipes.md#etcd-snapshots--restore).

**A flag from older docs is missing** — features carry a minimum version. Confirm with `k3s server --help` on the running binary, or see [references/version-features.md](references/version-features.md) for the feature → first-version map.

## References

For exhaustive detail, see the bundled reference files:

- [references/recipes.md](references/recipes.md) — task-oriented, copy-pasteable procedures (HA bootstrap, airgap, registries, snapshots & restore, cert/secrets rotation, uninstall, upgrades)
- [references/options.md](references/options.md) — complete `k3s server`/`k3s agent`/subcommand flag reference, grouped by area
- [references/version-features.md](references/version-features.md) — which k3s version introduced each flag/feature (minimum-version lookup)

## Resources

- **Help**: `k3s server --help`, `k3s agent --help`, `k3s <subcommand> --help`
- **Official docs**: https://docs.k3s.io
- **Installer & repo**: https://get.k3s.io · https://github.com/k3s-io/k3s
- **Recipes**: [references/recipes.md](references/recipes.md)
