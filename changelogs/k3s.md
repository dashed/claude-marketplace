# Changelog - k3s

All notable changes to the k3s skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-04

### Added
- Initial addition to the marketplace — a skill for the **k3s** lightweight, CNCF-certified Kubernetes distribution (`k3s` single-binary multicall tool), authored against the k3s **v1.35.0+k3s1** source.
- `SKILL.md`: overview of the single-binary distro and its bundled components (containerd, flannel, CoreDNS, Traefik, ServiceLB/Klipper, local-path-provisioner, metrics-server); when-to-use + prerequisites/path table; install (`curl -sfL https://get.k3s.io | sh -`, `INSTALL_K3S_*` env vars, stable/latest/`vX.Y` channels); the `k3s` subcommand map; six core workflows (single-server + kubeconfig, HA embedded etcd, external SQL datastore, agent join, `--disable` components, day-2 one-liners); token semantics; config file + `.d` drop-ins + `+`-append; quick-reference table; troubleshooting.
- `references/options.md`: exhaustive flag reference — `server` flags grouped by area (listener/apiserver, networking/CNI, kubeconfig, cluster/token, datastore/etcd, etcd snapshots/S3, components/disables, extra-args passthrough, storage/registry/runtime, node registration, security/misc/experimental), `agent` flags, one section per subcommand (`token`, `etcd-snapshot`, `secrets-encrypt`, `certificate`, `check-config`, `completion`) plus the `kubectl`/`crictl`/`ctr` passthrough note. Each flag carries its aliases, type/default, `K3S_*` env equivalent, and **Hidden**/**Exp**/**Dep** markers.
- `references/recipes.md`: task-oriented recipes — HA 3-server embedded-etcd bootstrap, external datastore, add/remove nodes, airgap install, `registries.yaml` mirrors, custom CNI / disable flannel, disable Traefik + ServiceLB, secrets-encryption (one-shot `rotate-keys` and staged), etcd snapshot save/list/prune + full `cluster-reset --cluster-reset-restore-path` restore, certificate rotation + `rotate-ca`, remote kubeconfig (`--tls-san` / `--write-kubeconfig-mode`), uninstall, and upgrades (install-script re-run + System Upgrade Controller note).
- `references/version-features.md`: 21 source-verified `feature → minimum k3s version` rows (ascending v1.27→v1.33), mirroring the git/fzf/fd/ripgrep skills' version-features pattern. Floor-version subcommands (v1.26.0) are noted separately since the shallow clone cannot prove a pre-1.26 origin.
- Inline `(k3s vX.Y+)` version annotations across all files for source-verified versioned features; long-standing bedrock flags left unannotated ("unlisted = long-standing").
