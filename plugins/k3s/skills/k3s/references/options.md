# k3s Options Reference

Complete reference for the `k3s` CLI: the `server` and `agent` daemon flags (grouped by
k3s's own help categories — listener, networking, db, agent/runtime, etc.) and every
management subcommand (`token`, `etcd-snapshot`, `secrets-encrypt`, `certificate`,
`check-config`, `completion`) plus the `kubectl`/`crictl`/`ctr` passthroughs.

> **Version annotations:** Flags marked `(k3s vX.Y+)` were first shipped in that k3s minor
> (k3s releases track upstream Kubernetes minors, e.g. `v1.31.3+k3s1`). Unmarked flags are
> long-standing — present at or before the tracked floor (**v1.26.0**, 2022-12-13) and treated
> as bedrock. For the consolidated feature→version lookup see
> [references/version-features.md](version-features.md). This reference is documented against
> **k3s v1.35.0+k3s1**, verified against the Go source (`pkg/cli/cmds/*.go`, `cmd/k3s/main.go`,
> `pkg/configfilearg/`). Confirm on your system with `k3s --version`, then `k3s server --help`
> / `k3s agent --help`.
>
> ⚠️ k3s sets `app.DisableSliceFlagSeparator = true`, so **list flags do NOT split on commas**
> at the CLI. Repeat the flag (`--tls-san a --tls-san b`) or use the config file's `+`-append
> form. See [Config file & environment](#config-file--environment).

## Legend

- **Type** — Go CLI flag type: `bool`, `string`, `int`, `duration` (e.g. `10m`, `5m`),
  `stringSlice` (repeatable; comma-splitting is disabled — see above).
- **`K3S_*` env** — the environment variable that sets the same value, if any. CLI flags
  override env, which overrides the config file.
- **Markers** in the Description: **Hidden** (works but omitted from `--help`), **Exp**
  (usage text marks it experimental), **Dep** (source groups it under deprecated/hidden). A
  flag may carry more than one.
- A leading `(group)` in a description is k3s's own help category (e.g. `(agent/networking)`).

## Usage

```
k3s server   [OPTIONS]              # run a control-plane (server) node
k3s agent    [OPTIONS]              # run a worker (agent) node — needs --server + --token
k3s <subcommand> [OPTIONS]         # token | etcd-snapshot | secrets-encrypt | certificate | …
k3s kubectl  [KUBECTL ARGS...]     # passthrough to bundled kubectl
k3s --version
```

`k3s` is a **multicall binary**: symlinks named `kubectl`, `crictl`, or `ctr` invoke those
passthroughs directly. `server` runs an embedded `agent` (kubelet) unless `--disable-agent`,
so **a server accepts all agent flags too**.

## Table of Contents

- [Global / logging / config (server & agent)](#global--logging--config-server--agent)
- [Server flags](#server-flags)
  - [Listener & apiserver](#listener--apiserver)
  - [Networking & CNI (flannel)](#networking--cni-flannel)
  - [Client / kubeconfig](#client--kubeconfig)
  - [Cluster & token](#cluster--token)
  - [Datastore & etcd](#datastore--etcd)
  - [etcd snapshots & S3](#etcd-snapshots--s3)
  - [Components & disables](#components--disables)
  - [Extra-args passthrough](#extra-args-passthrough)
  - [Storage / registry / runtime](#storage--registry--runtime)
  - [Node registration](#node-registration)
  - [Security / misc / experimental](#security--misc--experimental)
- [Agent flags](#agent-flags)
- [Subcommands](#subcommands)
  - [k3s token](#k3s-token)
  - [k3s etcd-snapshot](#k3s-etcd-snapshot)
  - [k3s secrets-encrypt](#k3s-secrets-encrypt)
  - [k3s certificate](#k3s-certificate)
  - [k3s check-config](#k3s-check-config)
  - [k3s completion](#k3s-completion)
  - [kubectl / crictl / ctr passthrough](#kubectl--crictl--ctr-passthrough)
- [Config file & environment](#config-file--environment)
- [Deprecated, experimental & hidden flags](#deprecated-experimental--hidden-flags)

## Global / logging / config (server & agent)

Shared by both daemons (`root.go`, `config.go`, `log.go`). At the bare `k3s` root only
`--debug` and `--data-dir`/`-d` apply.

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--config`, `-c` | string | `/etc/rancher/k3s/config.yaml` | `K3S_CONFIG_FILE` | Load configuration from FILE (processed before flag parsing; see [Config file](#config-file--environment)) |
| `--debug` | bool | `false` | `K3S_DEBUG` | Turn on debug logs |
| `--v` | int | `0` | | Log-level verbosity number |
| `--vmodule` | string | | | Comma-list `FILE_PATTERN=LOG_LEVEL` for file-filtered logging |
| `--log`, `-l` | string | | | Log to FILE |
| `--alsologtostderr` | bool | `false` | | Log to stderr as well as the log file |
| `--data-dir`, `-d` | string | `/var/lib/rancher/k3s` (root) · `~/.rancher/k3s` (non-root) | `K3S_DATA_DIR` | State folder. etcd data + snapshots live under `${data-dir}/server/db/` |
| `--bind-address` | string | `0.0.0.0` | | k3s bind address |

## Server flags

Defined in `pkg/cli/cmds/server.go` (`ServerFlags`). ≈85 visible + hidden. All
[agent flags](#agent-flags) are also valid on `server`.

### Listener & apiserver

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--https-listen-port` | int | `6443` | | HTTPS (apiserver/supervisor) listen port |
| `--advertise-address` | string | node-external-ip / node-ip | | IP the apiserver advertises to the cluster |
| `--advertise-port` | int | https-listen-port | | Port the apiserver advertises |
| `--tls-san` | stringSlice | | | Add hostnames/IPs as Subject-Alternative-Names on the server TLS cert (for VIP / LB / public DNS access) |
| `--tls-san-security` (k3s v1.28+) | bool | **`true`** | | Refuse SANs not tied to the apiserver service / server nodes / `--tls-san` values |
| `--supervisor-port` | int | | `K3S_SUPERVISOR_PORT` | **Hidden, Exp.** Supervisor port override |
| `--apiserver-port` | int | | `K3S_APISERVER_PORT` | **Hidden, Exp.** apiserver internal port override |
| `--apiserver-bind-address` | string | | `K3S_APISERVER_BIND_ADDRESS` | **Hidden, Exp.** apiserver internal bind override |

### Networking & CNI (flannel)

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--cluster-cidr` | stringSlice | `10.42.0.0/16` | | Pod IP CIDRs (IPv4/IPv6 dual-stack) |
| `--service-cidr` | stringSlice | `10.43.0.0/16` | | Service IP CIDRs |
| `--service-node-port-range` | string | `30000-32767` | | NodePort range |
| `--cluster-dns` | stringSlice | `10.43.0.10` | | CoreDNS service ClusterIP (must fall inside `--service-cidr`) |
| `--cluster-domain` | string | `cluster.local` | | Cluster domain |
| `--flannel-backend` | string | **`vxlan`** | | One of `none`, `vxlan`, `host-gw`, `wireguard-native`. Use `none` to bring your own CNI |
| `--flannel-ipv6-masq` | bool | `false` | | Enable IPv6 masquerading for pods |
| `--flannel-external-ip` | bool | `false` | | Use node external IPs for flannel traffic |
| `--flannel-iface` | string | | | (agent/networking) Override the flannel interface |
| `--flannel-conf` | string | | | (agent/networking) Override the flannel config file |
| `--flannel-cni-conf` | string | | | (agent/networking) Override the flannel CNI config file |
| `--egress-selector-mode` | string | **`agent`** | | One of `agent`, `cluster`, `pod`, `disabled` |
| `--servicelb-namespace` | string | `kube-system` | | Namespace for the ServiceLB (Klipper LB) pods |

### Client / kubeconfig

The server writes an admin kubeconfig to `/etc/rancher/k3s/k3s.yaml` (mode `0600`) by default.

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--write-kubeconfig`, `-o` | string | (`/etc/rancher/k3s/k3s.yaml`) | `K3S_KUBECONFIG_OUTPUT` | Write the admin kubeconfig to this file instead |
| `--write-kubeconfig-mode` | string | | `K3S_KUBECONFIG_MODE` | File mode for the kubeconfig (e.g. `0644` to make it readable by non-root) |
| `--write-kubeconfig-group` (k3s v1.30+) | string | | `K3S_KUBECONFIG_GROUP` | Group owner of the written kubeconfig |

### Cluster & token

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--token`, `-t` | string | | `K3S_TOKEN` | Shared secret to join the cluster — joins **both servers and agents** |
| `--token-file` | string | | `K3S_TOKEN_FILE` | File containing the token |
| `--agent-token` | string | | `K3S_AGENT_TOKEN` | Secret that joins **agents only**, not control-plane servers |
| `--agent-token-file` | string | | `K3S_AGENT_TOKEN_FILE` | File containing the agent token |
| `--server`, `-s` | string | | `K3S_URL` | Server URL to join an existing cluster |
| `--cluster-init` | bool | `false` | `K3S_CLUSTER_INIT` | Initialize a **new** cluster with embedded etcd (first server only) |
| `--cluster-reset` | bool | `false` | `K3S_CLUSTER_RESET` | Forget all peers and become the sole member of a new cluster |
| `--cluster-reset-restore-path` | string | | | Path to a snapshot file to restore (used with `--cluster-reset`) |

### Datastore & etcd

Pick **one** datastore strategy: embedded SQLite (default, single node), embedded etcd
(`--cluster-init`), or an external `--datastore-endpoint`. Do not combine etcd with an
external endpoint.

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--datastore-endpoint` | string | (SQLite) | `K3S_DATASTORE_ENDPOINT` | External datastore DSN: etcd, NATS, MySQL, or Postgres |
| `--datastore-cafile` | string | | `K3S_DATASTORE_CAFILE` | TLS CA file for the datastore |
| `--datastore-certfile` | string | | `K3S_DATASTORE_CERTFILE` | TLS cert file for the datastore |
| `--datastore-keyfile` | string | | `K3S_DATASTORE_KEYFILE` | TLS key file for the datastore |
| `--kine-tls` (k3s v1.29+) | bool | `false` | | **Hidden, Exp.** (db) Enable TLS on the kine etcd socket |
| `--etcd-expose-metrics` | bool | `false` | | Expose etcd metrics on the client interface |
| `--etcd-disable-snapshots` | bool | `false` | | Disable automatic etcd snapshots |
| `--etcd-snapshot-name` | string | `etcd-snapshot` | | Base name of scheduled snapshots (a UNIX timestamp is appended) |
| `--etcd-snapshot-schedule-cron` | string | `0 */12 * * *` | | Snapshot cron schedule |
| `--etcd-snapshot-reconcile-interval` (k3s v1.32+) | duration | `10m` | | Snapshot reconcile interval |
| `--etcd-snapshot-retention` | int | `5` | | Number of snapshots to retain |
| `--etcd-snapshot-dir` | string | `${data-dir}/server/db/snapshots` | | Snapshot directory |
| `--etcd-snapshot-compress` | bool | `false` | | Compress etcd snapshots |

### etcd snapshots & S3

Backup scheduled snapshots to S3-compatible storage. (For on-demand snapshots use the
[`k3s etcd-snapshot`](#k3s-etcd-snapshot) subcommand.)

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--etcd-s3` | bool | `false` | | Enable snapshot backup to S3 |
| `--etcd-s3-endpoint` | string | `s3.amazonaws.com` | | S3 endpoint URL |
| `--etcd-s3-endpoint-ca` | string | | | Custom CA for the S3 endpoint |
| `--etcd-s3-skip-ssl-verify` | bool | `false` | | Disable S3 SSL certificate validation |
| `--etcd-s3-access-key` | string | | `AWS_ACCESS_KEY_ID` | S3 access key |
| `--etcd-s3-secret-key` | string | | `AWS_SECRET_ACCESS_KEY` | S3 secret key |
| `--etcd-s3-session-token` | string | | `AWS_SESSION_TOKEN` | S3 session token |
| `--etcd-s3-bucket` | string | | | S3 bucket name |
| `--etcd-s3-bucket-lookup-type` (k3s v1.33+) | string | `auto` | | Bucket addressing: `auto`, `dns`, or `path` |
| `--etcd-s3-region` | string | `us-east-1` | | S3 region |
| `--etcd-s3-folder` | string | | | S3 folder / key prefix |
| `--etcd-s3-retention` | int | `5` | | S3 retention limit |
| `--etcd-s3-proxy` (k3s v1.30+) | string | | | Proxy for S3 (overrides proxy env vars) |
| `--etcd-s3-config-secret` (k3s v1.30+) | string | | | `kube-system` secret name that configures S3 |
| `--etcd-s3-insecure` | bool | `false` | | Disable S3 over HTTPS |
| `--etcd-s3-timeout` | duration | `5m` | | S3 operation timeout |

### Components & disables

`--disable` removes packaged components; the individual `--disable-*` bools toggle
control-plane pieces.

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--disable` | stringSlice | | | Do not deploy (and delete) packaged components. Valid values (Linux): `coredns`, `servicelb`, `traefik`, `local-storage`, `metrics-server`, `runtimes`. **`coredns` IS disable-able.** On the Windows/`nostage` build only `coredns`, `servicelb` |
| `--disable-scheduler` | bool | `false` | | Disable the default kube-scheduler |
| `--disable-cloud-controller` | bool | `false` | | Disable the k3s default cloud-controller-manager |
| `--disable-kube-proxy` | bool | `false` | | Disable kube-proxy |
| `--disable-network-policy` | bool | `false` | | Disable the k3s default network-policy controller |
| `--disable-helm-controller` | bool | `false` | | Disable the Helm controller |
| `--disable-apiserver` | bool | `false` | | **Hidden, Exp.** Disable the apiserver on this node (HA split-role) |
| `--disable-controller-manager` | bool | `false` | | **Hidden, Exp.** Disable kube-controller-manager (HA split-role) |
| `--disable-etcd` | bool | `false` | | **Hidden, Exp.** Disable etcd on this node (HA split-role) |
| `--embedded-registry` (k3s v1.28+) | bool | `false` | | Enable the embedded distributed (Spegel) registry mirror; requires embedded containerd |
| `--supervisor-metrics` (k3s v1.30+) | bool | `false` | | **Exp.** Serve k3s internal metrics on the supervisor port |
| `--disable-agent` | bool | `false` | | **Hidden, Dep.** Do not run a local agent/kubelet on this server |

### Extra-args passthrough

Append/override flags on the underlying Kubernetes components. Repeatable; values are
`flag=value`.

| Flag | Type | Description |
|------|------|-------------|
| `--kube-apiserver-arg` | stringSlice | Customized flag for kube-apiserver |
| `--etcd-arg` | stringSlice | Customized flag for etcd |
| `--kube-scheduler-arg` | stringSlice | Customized flag for kube-scheduler |
| `--kube-controller-manager-arg` | stringSlice | Customized flag for kube-controller-manager |
| `--kube-cloud-controller-manager-arg` | stringSlice | Customized flag for the cloud-controller-manager |
| `--kubelet-arg` | stringSlice | (agent/flags) Customized flag for kubelet |
| `--kube-proxy-arg` | stringSlice | (agent/flags) Customized flag for kube-proxy |
| `--kube-controller-arg` | stringSlice | **Hidden, Dep.** Old alias of `--kube-controller-manager-arg` |
| `--kube-cloud-controller-arg` | stringSlice | **Hidden, Dep.** Old alias of `--kube-cloud-controller-manager-arg` |

### Storage / registry / runtime

Shared agent flags, also valid on `server`.

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--default-local-storage-path` | string | | | Path for the local-path provisioner storage class |
| `--system-default-registry` | string | | `K3S_SYSTEM_DEFAULT_REGISTRY` | Private registry for all system images |
| `--private-registry` | string | `/etc/rancher/k3s/registries.yaml` | | Private registry config file |
| `--pause-image` | string | `rancher/mirrored-pause:3.6` | | Pause (sandbox) image for containerd |
| `--snapshotter` | string | `overlayfs` (Linux) / `windows` | | containerd snapshotter |
| `--container-runtime-endpoint` | string | | | Use an external CRI socket instead of embedded containerd |
| `--default-runtime` (k3s v1.29+) | string | | | Default runtime class in containerd |
| `--image-service-endpoint` (k3s v1.28+) | string | | | External CRI image-service socket |
| `--disable-default-registry-endpoint` (k3s v1.28+) | bool | `false` | | (agent/containerd) Disable containerd's fallback default registry endpoint when a mirror is configured |
| `--nonroot-devices` (k3s v1.31+) | bool | `false` | | (agent/containerd) Allow non-root pods device access (`device_ownership_from_security_context=true`) |
| `--image-credential-provider-bin-dir` | string | `/var/lib/rancher/credentialprovider/bin` | | Credential-provider plugin bin dir |
| `--image-credential-provider-config` | string | `/var/lib/rancher/credentialprovider/config.yaml` | | Credential-provider config file |
| `--resolv-conf` | string | | `K3S_RESOLV_CONF` | kubelet `resolv.conf` |
| `--airgap-extra-registry` | stringSlice | | | **Hidden.** Extra registry to tag airgap images from |
| `--docker` | bool | `false` | | **Exp, Dep.** Use cri-dockerd instead of containerd |

### Node registration

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--node-name` | string | | `K3S_NODE_NAME` | Node name |
| `--with-node-id` | bool | `false` | | Append a generated id to the node name |
| `--node-label` | stringSlice | | | Labels to register the node / start kubelet with |
| `--node-taint` | stringSlice | | | Taints to register kubelet with (e.g. `key=value:NoExecute`) |
| `--node-ip`, `-i` | stringSlice | | | IPs to advertise for the node |
| `--node-external-ip` | stringSlice | | | External IPs to advertise |
| `--node-internal-dns` (k3s v1.31+) | stringSlice | | | Internal DNS names to advertise |
| `--node-external-dns` (k3s v1.31+) | stringSlice | | | External DNS names to advertise |
| `--protect-kernel-defaults` | bool | `false` | | Error if kernel tunables differ from kubelet defaults |
| `--selinux` | bool | `false` | `K3S_SELINUX` | Enable SELinux in containerd |
| `--lb-server-port` | int | `6444` | `K3S_LB_SERVER_PORT` | Local supervisor client load-balancer port |

### Security / misc / experimental

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--secrets-encryption` | bool | `false` | | Enable secret encryption at rest |
| `--secrets-encryption-provider` (k3s v1.32+) | string | `aescbc` | | **Exp.** Encryption provider: `aescbc` or `secretbox` |
| `--enable-pprof` | bool | `false` | | **Exp.** Enable the pprof endpoint on the supervisor port |
| `--rootless` | bool | `false` | | **Exp.** Run rootless |
| `--prefer-bundled-bin` | bool | `false` | | **Exp.** Prefer bundled userspace binaries over host binaries |
| `--helm-job-image` (k3s v1.27+) | string | | | Default image for Helm jobs |

## Agent flags

Defined in `NewAgentCommand` (`pkg/cli/cmds/agent.go`). ≈40 flags. The agent shares most
node/runtime/networking flags with `server` (same flag variables); it has **no**
apiserver/datastore/etcd/disable-component/tls-san flags. `--data-dir` here defaults to
`/var/lib/rancher/k3s` with no root/non-root switch. An agent **requires** `--server` +
`--token`.

| Flag | Type | Default | `K3S_*` env | Description |
|------|------|---------|-------------|-------------|
| `--config`, `-c` | string | `/etc/rancher/k3s/config.yaml` | `K3S_CONFIG_FILE` | Config file |
| `--debug` | bool | `false` | `K3S_DEBUG` | Debug logs |
| `--v` | int | `0` | | Log verbosity |
| `--vmodule` | string | | | File-filtered logging |
| `--log`, `-l` | string | | | Log to file |
| `--alsologtostderr` | bool | `false` | | Log to stderr too |
| `--token`, `-t` | string | | `K3S_TOKEN` | Token to use for authentication |
| `--token-file` | string | | `K3S_TOKEN_FILE` | Token file |
| `--server`, `-s` | string | | `K3S_URL` | Server to connect to (**required**) |
| `--data-dir`, `-d` | string | `/var/lib/rancher/k3s` | `K3S_DATA_DIR` | State folder |
| `--node-name` | string | | `K3S_NODE_NAME` | Node name |
| `--with-node-id` | bool | `false` | | Append a generated id to the node name |
| `--node-label` | stringSlice | | | kubelet registration labels |
| `--node-taint` | stringSlice | | | kubelet registration taints |
| `--node-ip`, `-i` | stringSlice | | | IPs to advertise for the node |
| `--node-external-ip` | stringSlice | | | External IPs to advertise |
| `--node-internal-dns` (k3s v1.31+) | stringSlice | | | Internal DNS names to advertise |
| `--node-external-dns` (k3s v1.31+) | stringSlice | | | External DNS names to advertise |
| `--bind-address` | string | `0.0.0.0` | | Bind address |
| `--selinux` | bool | `false` | `K3S_SELINUX` | Enable SELinux in containerd |
| `--lb-server-port` | int | `6444` | `K3S_LB_SERVER_PORT` | Supervisor client load-balancer port |
| `--protect-kernel-defaults` | bool | `false` | | Error if kernel tunables differ from kubelet defaults |
| `--resolv-conf` | string | | `K3S_RESOLV_CONF` | kubelet `resolv.conf` |
| `--pause-image` | string | `rancher/mirrored-pause:3.6` | | Pause (sandbox) image |
| `--snapshotter` | string | `overlayfs` | | containerd snapshotter |
| `--private-registry` | string | `/etc/rancher/k3s/registries.yaml` | | Private registry config file |
| `--container-runtime-endpoint` | string | | | External CRI socket |
| `--default-runtime` (k3s v1.29+) | string | | | Default runtime class in containerd |
| `--image-service-endpoint` (k3s v1.28+) | string | | | External CRI image-service socket |
| `--disable-default-registry-endpoint` (k3s v1.28+) | bool | `false` | | (agent/containerd) Disable containerd's fallback default registry endpoint |
| `--nonroot-devices` (k3s v1.31+) | bool | `false` | | (agent/containerd) Allow non-root pods device access |
| `--image-credential-provider-bin-dir` | string | `/var/lib/rancher/credentialprovider/bin` | | Credential-provider bin dir |
| `--image-credential-provider-config` | string | `/var/lib/rancher/credentialprovider/config.yaml` | | Credential-provider config file |
| `--airgap-extra-registry` | stringSlice | | | **Hidden.** Extra airgap registry to tag images from |
| `--flannel-iface` | string | | | flannel interface override |
| `--flannel-conf` | string | | | flannel config override |
| `--flannel-cni-conf` | string | | | flannel CNI config override |
| `--kubelet-arg` | stringSlice | | | Customized flag for kubelet |
| `--kube-proxy-arg` | stringSlice | | | Customized flag for kube-proxy |
| `--enable-pprof` (k3s v1.27+) | bool | `false` | | **Exp.** pprof endpoint on the supervisor port (server-side since the v1.26.0 floor) |
| `--rootless` | bool | `false` | | **Exp.** Run rootless |
| `--prefer-bundled-bin` | bool | `false` | | **Exp.** Prefer bundled binaries over host binaries |
| `--docker` | bool | `false` | | **Exp, Dep.** Use cri-dockerd instead of containerd |
| `--vpn-auth` (k3s v1.27+) | string | | `K3S_VPN_AUTH` | **Exp, Dep-section.** VPN creds `name=<provider>,joinKey=<key>[,controlServerURL=<url>][,extraArgs=<args>]` |
| `--vpn-auth-file` (k3s v1.27+) | string | | `K3S_VPN_AUTH_FILE` | **Exp, Dep-section.** File with VPN creds |
| `--disable-apiserver-lb` (k3s v1.28+) | bool | `false` | | **Exp, Dep-section.** Disable the agent client-side load-balancer; connect directly to the configured server |

## Subcommands

Wired in `cmd/k3s/main.go`; constructors in `pkg/cli/cmds/`.

### k3s token

Manage bootstrap/server tokens (`token.go`). Available since **k3s v1.26+**. Common flags on
every subcommand: `--data-dir`/`-d`, `--kubeconfig` (env `KUBECONFIG`).

| Subcommand | Extra flags | Purpose |
|------------|-------------|---------|
| `create` | `--description`, `--groups` (stringSlice), `--ttl` (duration, default `24h`; `0` = never expire), `--usages` (stringSlice) | Create a bootstrap token on the server |
| `delete` | (common only) | Delete bootstrap tokens |
| `generate` | (common only) | Generate and print a token without creating it on the server |
| `list` | `--output`/`-o` (default `text`) | List bootstrap tokens |
| `rotate` (k3s v1.28+) | `--token`/`-t` (`K3S_TOKEN`), `--server`/`-s` (`K3S_URL`, default `https://127.0.0.1:6443`), `--new-token` | Rotate the original **server** token with a new one |

### k3s etcd-snapshot

Manage on-demand etcd snapshots (`etcd_snapshot.go`). Subcommands `save`, `delete`, `ls`
(aliases `list`, `l`), `prune` — all present since **k3s v1.26+**. These use short flag names
with `etcd-*` aliases (distinct from the server-side scheduling flags).

| Flag | Aliases | Type | Default | Description |
|------|---------|------|---------|-------------|
| `--debug` | | bool | `false` | Debug logs |
| `--config` | `-c` | string | `/etc/rancher/k3s/config.yaml` | Config file |
| `--log` | | string | | Log to file |
| `--alsologtostderr` | | bool | `false` | Log to stderr too |
| `--node-name` | | string | (env `K3S_NODE_NAME`) | Node name |
| `--data-dir` | `-d` | string | | State folder |
| `--etcd-token` | `-t` | string | | etcd token |
| `--etcd-server` | `-s` | string | `https://127.0.0.1:6443` | Server URL |
| `--dir` | `--etcd-snapshot-dir` | string | `${data-dir}/server/db/snapshots` | Snapshot directory |
| `--name` | | string | `on-demand` | Snapshot base name |
| `--snapshot-compress` | `--etcd-snapshot-compress` | bool | `false` | Compress the snapshot |
| `--snapshot-retention` | `--etcd-snapshot-retention` | int | `5` | Snapshots to retain |
| `--s3` … `--s3-timeout` | `--etcd-s3-*` aliases | (see S3 set) | | Full S3 set: `--s3`, `--s3-endpoint`, `--s3-endpoint-ca`, `--s3-skip-ssl-verify`, `--s3-access-key`, `--s3-secret-key`, `--s3-session-token`, `--s3-bucket`, `--s3-bucket-lookup-type`, `--s3-region`, `--s3-retention`, `--s3-folder`, `--s3-proxy`, `--s3-config-secret`, `--s3-insecure`, `--s3-timeout` |
| `--output` | `-o` | string | `standard` | (`ls` only) `standard` or `json` |

> ⚠️ **Upstream quirk:** the retention flag is declared `snapshot-retention,` with a trailing
> comma in the source. Use the canonical `--etcd-snapshot-retention` (or `--snapshot-retention`).

### k3s secrets-encrypt

Control secrets encryption and key rotation (`secrets_encrypt.go`). Available since
**k3s v1.26+**. Common flags: `--data-dir`, `--token`/`-t` (`K3S_TOKEN`), `--server`/`-s`
(`K3S_URL`, default `https://127.0.0.1:6443`).

| Subcommand | Extra flags | Purpose |
|------------|-------------|---------|
| `status` | `--output`/`-o` (`text`/`json`, default `text`) | Print the current encryption status |
| `enable` | | Enable secrets encryption |
| `disable` | | Disable secrets encryption |
| `prepare` | `--force`/`-f` | Prepare for key rotation (stage 1) |
| `rotate` | `--force`/`-f` | Rotate encryption keys (stage 2) |
| `reencrypt` | `--force`/`-f`, `--skip` (skip removing the old key) | Re-encrypt all data with the new key (stage 3) |
| `rotate-keys` (k3s v1.28+) | | One-shot dynamic rotate + reencrypt (supersedes the manual prepare/rotate/reencrypt dance) |

### k3s certificate

Manage k3s certificates (`certs.go`; the command name is `certificate`). `check`/`rotate`
since **k3s v1.26+**; `rotate-ca` since **k3s v1.26+** (older than commonly assumed).

| Subcommand | Flags | Purpose |
|------------|-------|---------|
| `check` | `--debug`, `--config`/`-c`, `--log`, `--alsologtostderr`, `--data-dir`, `--service`/`-s` (stringSlice), `--output`/`-o` (`text`/`table`/`json`/`yaml`, default `text`) | Check component certs on disk |
| `rotate` | same as `check` minus `--output` | Rotate component certs on disk (restart required afterward) |
| `rotate-ca` | `--data-dir`, `--server`/`-s` (`K3S_URL`, default `https://127.0.0.1:6443`), `--path` (**required**), `--force` | Write updated CA certs to the datastore |

`--service` valid values: `admin`, `api-server`, `controller-manager`, `scheduler`,
`supervisor`, `k3s-controller`, `k3s-server`, `cloud-controller`, `etcd`, `auth-proxy`,
`kubelet`, `kube-proxy`.

### k3s check-config

Runs the bundled config-check script (`check-config.go`). Declared `SkipFlagParsing: true` —
all arguments are forwarded verbatim to the script. Verifies the host kernel/modules are
suitable for k3s.

### k3s completion

Generate shell completion (`completion.go`). Subcommands `bash` and `zsh`, each with `-i` to
install the source line into the shell rc file.

```
k3s completion bash        # print the completion script
k3s completion bash -i     # install it into ~/.bashrc
```

### kubectl / crictl / ctr passthrough

Declared `SkipFlagParsing: true` — every argument after the subcommand is forwarded verbatim
to the bundled tool. Because `k3s` is a multicall binary, symlinks named `kubectl`, `crictl`,
or `ctr` invoke these directly.

| Subcommand | Wraps | Notes |
|------------|-------|-------|
| `k3s kubectl` | bundled kubectl | Uses the server's admin kubeconfig automatically on a server node |
| `k3s crictl` | bundled crictl | Talks to the embedded containerd CRI socket |
| `k3s ctr` | bundled containerd `ctr` | Low-level containerd client |

## Config file & environment

(`pkg/configfilearg/`.) The daemon reads `--config`/`K3S_CONFIG_FILE` (default
`/etc/rancher/k3s/config.yaml`) **before** flag parsing.

- **Optional by default:** a missing *default* config is fine; only an explicitly-given
  missing path is an error.
- **Drop-ins:** files in `<configfile>.d/` (e.g. `/etc/rancher/k3s/config.yaml.d/`) matching
  `*.yaml`/`*.yml` are loaded in lexical order, **after** the base `config.yaml`.
- **Mapping:** each top-level key `k: v` becomes `--k=v`; list values become repeated flags;
  bool keys (e.g. `cluster-init: true`) map to the bool flag.
- **`+`-append:** a key suffixed with `+` (e.g. `node-label+:`, `tls-san+:`) **appends** to
  earlier values instead of replacing them. This is the way to add to slice flags given that
  CLI comma-splitting is disabled.
- **Precedence:** CLI flags are applied after config-derived args, so **CLI overrides config**
  (or appends, for slice flags). Env vars sit between.
- **Unknown keys** are logged and skipped (warning, not fatal).

## Deprecated, experimental & hidden flags

| Flag | Status | Use instead / note |
|------|--------|--------------------|
| `--docker` | **Exp, Dep** | Use the default embedded containerd, or `--container-runtime-endpoint` for an external CRI |
| `--disable-agent` | **Hidden, Dep** | Run a dedicated agent process, or use HA split-role flags |
| `--kube-controller-arg` | **Hidden, Dep** | `--kube-controller-manager-arg` |
| `--kube-cloud-controller-arg` | **Hidden, Dep** | `--kube-cloud-controller-manager-arg` |
| `--vpn-auth` / `--vpn-auth-file` | **Exp, Dep-section** | Tailscale/VPN integration; pin a specific version if you depend on it |
| `--disable-apiserver-lb` | **Exp, Dep-section** | Only when an external LB fronts the servers |
| `--kine-tls` | **Hidden, Exp** | TLS on the kine socket; not stabilized |
| `--supervisor-port` / `--apiserver-port` / `--apiserver-bind-address` | **Hidden, Exp** | Internal port/bind overrides; avoid unless directed |
| `--disable-apiserver` / `--disable-controller-manager` / `--disable-etcd` | **Hidden, Exp** | HA split-role topologies only |
| `--secrets-encryption-provider` | **Exp** | `aescbc` (default) or `secretbox` |
| `--supervisor-metrics` / `--enable-pprof` / `--rootless` / `--prefer-bundled-bin` | **Exp** | Experimental; behavior may change |

> Older `--flannel-backend` values `wireguard` and `ipsec` have been removed from the current
> usage string — use `wireguard-native`, or `none` + a manual CNI.
