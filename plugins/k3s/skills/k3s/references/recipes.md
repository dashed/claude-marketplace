# k3s Operational Recipes

Task-oriented, copy-pasteable procedures for the k3s lifecycle: HA bootstrap,
node management, airgap and private-registry installs, custom networking,
secrets encryption, etcd snapshots and restore, certificate rotation, remote
access, uninstall, and upgrades. For the conceptual overview, the subcommand
map, and the bundled components, see [SKILL.md](../SKILL.md).

> **Version note:** Long-standing flags and paths (`--token`, `--server`,
> `--cluster-init`, `--cluster-reset`, `--datastore-endpoint`, `--disable`,
> `--tls-san`, `--write-kubeconfig`/`-mode`, the core `--etcd-s3*` set, the
> `k3s etcd-snapshot` `save`/`ls`/`delete`/`prune` subcommands, and
> `k3s certificate check`/`rotate`/`rotate-ca`) are **not** annotated — they are
> present on every k3s line tracked (v1.26.0 and newer). Features added in a
> specific cycle are flagged inline as `(k3s vX.Y+)`; the marker is the **first
> minor cycle** that shipped the feature (k3s backports to all supported lines,
> so an older patch may also carry it). Documented against the k3s source at
> **v1.35.0+k3s1**. Confirm on your binary with `k3s server --help` /
> `k3s --version`.

## Table of Contents

- [HA Embedded-etcd: 3-Server Bootstrap](#ha-embedded-etcd-3-server-bootstrap)
- [External SQL Datastore](#external-sql-datastore)
- [Add / Remove Nodes](#add--remove-nodes)
- [Airgap Install](#airgap-install)
- [Private / Mirror Registry](#private--mirror-registry)
- [Custom CNI / Disable Flannel](#custom-cni--disable-flannel)
- [Disable Traefik + ServiceLB](#disable-traefik--servicelb)
- [Secrets Encryption + Key Rotation](#secrets-encryption--key-rotation)
- [etcd Snapshots & Restore](#etcd-snapshots--restore)
- [Certificate Rotation](#certificate-rotation)
- [Remote-Access kubeconfig](#remote-access-kubeconfig)
- [Uninstall](#uninstall)
- [Upgrades](#upgrades)

## HA Embedded-etcd: 3-Server Bootstrap

Embedded etcd needs an **odd number of servers** (3 or 5). Quorum is
`floor(n/2)+1` (2 of 3). Only the **first** server uses `--cluster-init`.

```bash
# === Server 1 (initialize the cluster) ===
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --cluster-init \
  --tls-san k8s.example.com" \
  K3S_TOKEN=<SHARED_SECRET> sh -

# === Servers 2 and 3 (JOIN — no --cluster-init) ===
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --server https://<server-1>:6443 \
  --tls-san k8s.example.com" \
  K3S_TOKEN=<SHARED_SECRET> sh -
```

Verify all three control-plane nodes:

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
k3s kubectl get nodes -o wide
```

> Behind a fixed VIP / load balancer, give every server the LB name in
> `--tls-san` and point agents at the LB instead of a single server. Keep an
> odd server count; adding a 4th server does not improve quorum tolerance.

## External SQL Datastore

A non-etcd HA topology: every server shares one external datastore. Do **not**
combine with `--cluster-init`. Supported: MySQL/MariaDB, Postgres, etcd, NATS
(SQLite is the single-node default).

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --datastore-endpoint='mysql://user:pass@tcp(db.example.com:3306)/k3s' \
  --tls-san k8s.example.com" \
  K3S_TOKEN=<SHARED_SECRET> sh -
```

TLS to the datastore:

```bash
k3s server --datastore-endpoint='postgres://…' \
  --datastore-cafile=/etc/k3s/db-ca.pem \
  --datastore-certfile=/etc/k3s/db-cert.pem \
  --datastore-keyfile=/etc/k3s/db-key.pem
```

Connection-string forms: `mysql://…`, `postgres://…`, `https://etcd:2379`,
`nats://…`. Front the servers with a load balancer for the API; agents join the
LB or any server.

## Add / Remove Nodes

**Read the join token on a server:**

```bash
sudo cat /var/lib/rancher/k3s/server/node-token
```

**Add an agent (worker):**

```bash
curl -sfL https://get.k3s.io | \
  K3S_URL=https://<server>:6443 K3S_TOKEN=<node-token> sh -
```

**Add a server (HA):** join with `--server` + `--token` (embedded etcd) or the
same `--datastore-endpoint` (external DB) — never `--cluster-init` on a joiner.

**Hand agents a restricted token** so they can't add control-plane servers:

```bash
k3s server --agent-token <AGENT_ONLY_SECRET>      # on the server(s)
# workers then use K3S_TOKEN=<AGENT_ONLY_SECRET>
```

**Remove a node** — uninstall on the node, then delete it from the cluster:

```bash
# On the departing node:
/usr/local/bin/k3s-agent-uninstall.sh      # or k3s-uninstall.sh for a server
# From a remaining server:
k3s kubectl delete node <node-name>
```

> Removing an **etcd server** member also needs the member removed from etcd
> (k3s prunes the member when the node is deleted cleanly); always keep the
> remaining server count odd.

## Airgap Install

No internet on the target host. Stage the binary and the images tarball, then
tell the installer to skip the download.

```bash
# 1) On a connected machine, download for your arch from the k3s release page:
#    - k3s                              (the binary)
#    - k3s-airgap-images-<arch>.tar.zst (or .tar)   (the images tarball)
#    - install.sh

# 2) On the target host, stage the images where k3s imports them at startup:
sudo mkdir -p /var/lib/rancher/k3s/agent/images/
sudo cp k3s-airgap-images-amd64.tar.zst /var/lib/rancher/k3s/agent/images/

# 3) Install the binary and run the installer WITHOUT downloading:
sudo cp k3s /usr/local/bin/ && sudo chmod +x /usr/local/bin/k3s
INSTALL_K3S_SKIP_DOWNLOAD=true ./install.sh

# Agent (worker) airgap install:
INSTALL_K3S_SKIP_DOWNLOAD=true K3S_URL=https://<server>:6443 \
  K3S_TOKEN=<node-token> ./install.sh
```

`INSTALL_K3S_SKIP_DOWNLOAD=true` makes the installer use the binary and images
you staged instead of fetching them. Combine with a private registry (below) for
your own workload images.

## Private / Mirror Registry

Configure registry mirrors and credentials in **`/etc/rancher/k3s/registries.yaml`**
(read by the embedded containerd; create it before/at start, then restart k3s).

```yaml
# /etc/rancher/k3s/registries.yaml
mirrors:
  docker.io:
    endpoint:
      - "https://registry.internal:5000"
  registry.internal:5000:
    endpoint:
      - "https://registry.internal:5000"
configs:
  registry.internal:5000:
    auth:
      username: myuser
      password: mypass
    tls:
      ca_file: /etc/ssl/certs/internal-ca.pem
      # insecure_skip_verify: true   # for self-signed without a CA
```

```bash
sudo systemctl restart k3s        # or k3s-agent on workers
```

Related flags: `--system-default-registry` rewrites **system** image references
to a private registry; `--embedded-registry` (k3s v1.28+) turns on the embedded
Spegel distributed mirror across nodes; `--disable-default-registry-endpoint`
(k3s v1.28+) stops containerd's fallback to the default endpoint when a mirror
is configured.

## Custom CNI / Disable Flannel

Disable the bundled flannel CNI and apply your own (Calico, Cilium, Multus, …).

```bash
k3s server --flannel-backend=none --disable-network-policy
# then apply your CNI's manifests with kubectl
```

`--flannel-backend` values: `vxlan` (default), `host-gw`, `wireguard-native`
(encrypted node-to-node), and `none` (bring your own). The older
`wireguard`/`ipsec` backends are gone. `--disable-network-policy` is needed
because the bundled policy controller assumes flannel.

```bash
# WireGuard-encrypted flannel (no external CNI needed):
k3s server --flannel-backend=wireguard-native
```

## Disable Traefik + ServiceLB

`--disable` takes packaged-component names:
`coredns, servicelb, traefik, local-storage, metrics-server, runtimes`.

```bash
# Drop the bundled ingress and the built-in LoadBalancer
k3s server --disable traefik --disable servicelb

# Equivalent comma-list
k3s server --disable traefik,servicelb
```

In `config.yaml`:

```yaml
disable:
  - traefik
  - servicelb
```

> `coredns` is in the `--disable` list (you'd supply your own DNS). Subsystems
> with **dedicated** flags — not `--disable` values — include
> `--disable-scheduler`, `--disable-cloud-controller`, `--disable-kube-proxy`,
> `--disable-network-policy`, and `--disable-helm-controller`.

## Secrets Encryption + Key Rotation

Enable encryption-at-rest for Secrets, then manage keys at runtime.

```bash
# Enable at start (provider default is aescbc):
k3s server --secrets-encryption
# secretbox provider (k3s v1.32+):
k3s server --secrets-encryption --secrets-encryption-provider secretbox
```

**Check status** any time:

```bash
k3s secrets-encrypt status
```

**Modern one-shot rotation** (k3s v1.28+) — rotates the key and re-encrypts all
secrets in one command:

```bash
k3s secrets-encrypt rotate-keys
```

**Manual staged rotation** (the older 3-step dance, still supported). Run on the
servers in order; on multi-server clusters restart each server between stages:

```bash
k3s secrets-encrypt prepare       # stage 1: add a new key (stop using it yet)
# restart k3s on all servers
k3s secrets-encrypt rotate         # stage 2: start encrypting with the new key
# restart k3s on all servers
k3s secrets-encrypt reencrypt      # stage 3: re-encrypt existing data, drop old key
```

## etcd Snapshots & Restore

**Embedded etcd only.** Snapshots default to
`/var/lib/rancher/k3s/server/db/snapshots/`. Scheduled snapshots run on a cron
(`--etcd-snapshot-schedule-cron`, default `0 */12 * * *`) with retention
(`--etcd-snapshot-retention`, default 5).

```bash
# On-demand snapshot
k3s etcd-snapshot save --name pre-upgrade

# List / prune / delete
k3s etcd-snapshot ls
k3s etcd-snapshot ls -o json
k3s etcd-snapshot prune --snapshot-retention 5
k3s etcd-snapshot delete <snapshot-name>
```

**Snapshot to S3** (works for `save` and scheduled snapshots):

```bash
k3s etcd-snapshot save \
  --s3 --s3-bucket my-bucket --s3-region us-east-1 \
  --s3-access-key "$AWS_ACCESS_KEY_ID" --s3-secret-key "$AWS_SECRET_ACCESS_KEY"
# --s3-bucket-lookup-type auto|dns|path  (k3s v1.33+)
```

### Restore procedure (embedded etcd)

This is destructive and must be done with the other servers **stopped**:

```bash
# 1) Stop k3s on ALL servers
sudo systemctl stop k3s            # on every server node

# 2) On ONE server, reset the cluster and restore the snapshot:
k3s server \
  --cluster-reset \
  --cluster-reset-restore-path=/var/lib/rancher/k3s/server/db/snapshots/<snapshot>

# 3) When it reports the reset/restore is complete, stop that process,
#    then start k3s normally on this restored server:
sudo systemctl start k3s

# 4) On the OTHER servers, delete the stale datastore and rejoin:
sudo rm -rf /var/lib/rancher/k3s/server/db
sudo systemctl start k3s
```

`--cluster-reset` alone (no restore path) forgets all peers and makes the node
the sole member of a new cluster — the recovery path when you've **lost
quorum**. Restoring an S3 snapshot uses the same `--cluster-reset-restore-path`
plus the `--etcd-s3*` flags to locate it.

## Certificate Rotation

k3s component certificates are valid for one year and **auto-rotate** when the
service restarts within ~90 days of expiry. To force it:

```bash
k3s certificate check                       # inspect cert expiry on disk
sudo systemctl stop k3s
k3s certificate rotate                       # rotate component certs on disk
sudo systemctl start k3s                     # restart to pick up new certs
```

Rotate only specific components with `--service` (repeatable; valid values:
`admin, api-server, controller-manager, scheduler, supervisor, k3s-controller,
k3s-server, cloud-controller, etcd, auth-proxy, kubelet, kube-proxy`).

**Rotate the cluster CA** (`rotate-ca`) — write updated CA certs into the
datastore (needs a prepared CA bundle at `--path`):

```bash
k3s certificate rotate-ca --path /opt/k3s/server/rotate-ca
# --force to bypass the validation checks
```

## Remote-Access kubeconfig

To reach the API from your laptop or through a load balancer:

```bash
# 1) Add the external name/IP to the apiserver cert and make the kubeconfig readable:
k3s server --tls-san k8s.example.com --write-kubeconfig-mode 0644

# 2) Copy /etc/rancher/k3s/k3s.yaml to your machine and edit the `server:` URL:
#    https://127.0.0.1:6443  ->  https://k8s.example.com:6443
scp root@server:/etc/rancher/k3s/k3s.yaml ~/.kube/k3s-remote.yaml
export KUBECONFIG=~/.kube/k3s-remote.yaml
```

`--tls-san-security` defaults **true** — SANs unrelated to the apiserver service
or server nodes are rejected unless explicitly listed in `--tls-san`.
`--write-kubeconfig-group` (k3s v1.30+) sets the kubeconfig's group owner.

## Uninstall

The installer drops uninstall scripts next to the binary:

```bash
# Server node:
/usr/local/bin/k3s-uninstall.sh

# Agent (worker) node:
/usr/local/bin/k3s-agent-uninstall.sh
```

These stop and remove the service, the binary, the `kubectl`/`crictl`/`ctr`
symlinks, and `/var/lib/rancher/k3s` data. From a surviving server, also
`k3s kubectl delete node <name>` for a node you removed.

## Upgrades

**Re-run the installer** to upgrade in place (it replaces the binary and
restarts the service). Pin a channel or version:

```bash
# Latest stable
curl -sfL https://get.k3s.io | sh -

# Track a channel or pin a version
curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=latest sh -
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.32.1+k3s1 sh -
```

Channels: `stable` (default), `latest`, `testing`. **Take an etcd snapshot
before upgrading** an embedded-etcd cluster (`k3s etcd-snapshot save`), and
upgrade **servers before agents**, one node at a time.

> **Automated rolling upgrades:** for hands-off cluster upgrades, k3s integrates
> with the **System Upgrade Controller** (Rancher's `Plan` CRD) — install the
> controller, then apply server/agent upgrade `Plan` objects that cordon, drain,
> and upgrade nodes in a controlled order. See https://docs.k3s.io for the
> current manifests; the CLI re-run above is the manual equivalent.
