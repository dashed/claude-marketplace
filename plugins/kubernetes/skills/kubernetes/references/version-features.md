# Kubernetes Feature → Minimum Version

A consolidated lookup of **which Kubernetes minor version a feature this skill documents
became reliable in**, so you know what works on an older (or newer) cluster. Use it to
answer "is my cluster new enough for X?" and "what do I need to upgrade to?"

**How to read this:**

- These are **Kubernetes minor versions** (`1.MINOR`, e.g. `1.33`). Kubernetes ships a new
  minor roughly every ~4 months; patch releases (`1.33.x`) carry only fixes. The
  `1.33` form here means "the 1.33 minor and later."
- Each row is annotated by the version where a feature became **GA** (Generally
  Available) — the point at which you can rely on it unconditionally. A few rows are
  annotated by the version where the feature became **Beta-enabled-by-default**, because
  that is the practical availability point; those rows
  are **labeled clearly** (e.g. "GA 1.33 (beta-on 1.29)" or "beta-on 1.34, NOT GA"). A
  small number of rows are intentionally tracked as **not yet GA through 1.37** so you do
  not over-rely on them.
- **Alpha → Beta → GA lifecycle.** Features land as **Alpha** (off by default, may change
  or vanish — never rely on it), graduate to **Beta** (often on by default, but the gate
  can still regress), and finally reach **GA/stable** (the feature gate is eventually
  locked and removed — safe to depend on). When this table lists a beta-on version
  alongside the GA version, the beta-on version is the earliest you can *practically* use
  the feature on a default cluster, and the GA version is when it became guaranteed.
- **Sources** (one per row, cross-checked against
  kubernetes.io): the per-minor `CHANGELOG/CHANGELOG-1.x.md` files (`CL-1.x:<line>`) and
  the versioned feature-gate stage metadata in
  `pkg/features/kube_features.go` (and the apiserver mirror
  `staging/src/k8s.io/apiserver/pkg/features/kube_features.go`) (`gate:…`). CLI items at
  or below 1.28 were additionally verified empirically against the installed **kubectl
  v1.28.2** (anything that runs on 1.28.2 is available at ≤1.28).
- **Features not listed here are long-standing** — GA at or before **~1.20 (Dec 2020)**
  and treated as **bedrock**, so they carry no version tag. This includes the everyday
  surface: core resources (Pod/Deployment/ReplicaSet/StatefulSet/DaemonSet,
  Service/Ingress, ConfigMap/Secret, PV/PVC/StorageClass, Namespace/ResourceQuota/
  LimitRange, RBAC Role/RoleBinding), `startupProbe`, base `topologySpreadConstraints`,
  the bulk of `kubectl` verbs and flags, client-side apply, and so on. This file omits
  them to stay signal-rich.
- **Managed clusters lag.** Cloud-managed control planes (EKS/GKE/AKS and similar) often
  trail the newest upstream minor by one or more releases, and may keep certain feature
  gates off. Confirm against your actual server version (below), not the newest minor
  that exists.

## Contents

- [Versioned features (ascending by Kubernetes minor)](#versioned-features-ascending-by-kubernetes-minor)
- [Checking your versions](#checking-your-versions)

## Versioned features (ascending by Kubernetes minor)

Sorted ascending by minimum Kubernetes minor; within a version, grouped by **Area**
(kubectl / workloads / networking-storage / API-machinery / security).

| Min version | Feature | Area |
|---|---|---|
| 1.21 | CronJob `batch/v1` API GA (was `batch/v1beta1`) | workloads |
| 1.21 | EndpointSlice (`discovery.k8s.io/v1`) GA | networking-storage |
| 1.21 | PodDisruptionBudget `policy/v1` API GA | networking-storage |
| 1.22 | Server-side apply (`kubectl apply --server-side`) GA | API-machinery |
| 1.23 | HorizontalPodAutoscaler `autoscaling/v2` API GA (use v2, not v1; v2beta2 deprecated) | API-machinery |
| 1.24 | Indexed Job (`completionMode: Indexed`) GA | workloads |
| 1.24 | Job `.spec.suspend` GA | workloads |
| 1.24 | `kubectl --subresource` flag (since 1.24; beta 1.27; usable in 1.28.2) | kubectl |
| 1.24 | Volume expansion (`allowVolumeExpansion`) GA | networking-storage |
| 1.25 | Ephemeral containers + `kubectl debug` GA | kubectl |
| 1.25 | Pod Security admission (PSA) GA | security |
| 1.25 | StatefulSet `.spec.minReadySeconds` GA | workloads |
| 1.26 | `kubectl events` standalone command (promoted from `kubectl alpha events` 1.23) | kubectl |
| 1.27 | CronJob `.spec.timeZone` GA | workloads |
| 1.27 | `grpc` probe handler (`GRPCContainerProbe`) GA | workloads |
| 1.27 | seccomp `RuntimeDefault` defaulting (`SeccompDefault`) GA | security |
| 1.29 | `ReadWriteOncePod` (RWOP) access mode GA (distinct from the `SELinuxMountReadWriteOncePod` gate, GA 1.36) | networking-storage |
| 1.30 | ValidatingAdmissionPolicy (CEL) GA | API-machinery |
| 1.30 | topologySpread `minDomains` GA | workloads |
| 1.30 | PodSchedulingReadiness (`schedulingGates`) GA | workloads |
| 1.31 | Job `.spec.podFailurePolicy` GA | workloads |
| 1.31 | PDB `.spec.unhealthyPodEvictionPolicy` GA | networking-storage |
| 1.31 | AppArmor structured field (`securityContext.appArmorProfile`) GA (annotation-based before) | security |
| 1.33 | Sidecar containers (`initContainers` w/ `restartPolicy: Always`) GA (beta-on 1.29) | workloads |
| 1.33 | Job `.spec.backoffLimitPerIndex` GA (beta-on 1.29) | workloads |
| 1.33 | Job `.spec.successPolicy` GA | workloads |
| 1.33 | topologySpread NodeInclusionPolicy (`nodeAffinityPolicy`/`nodeTaintsPolicy`) GA | workloads |
| 1.33 | `matchLabelKeys` in Pod (anti)affinity GA | workloads |
| 1.33 | `nftables` kube-proxy mode GA | networking-storage |
| 1.33 | MultiCIDRServiceAllocator GA | networking-storage |
| 1.34 | `lifecycle.sleep` action GA | workloads |
| 1.34 | Recover from failed volume expansion GA | networking-storage |
| 1.34 | VolumeAttributesClass GA | networking-storage |
| 1.34 | NodeSwap GA | networking-storage |
| 1.34 | Dynamic Resource Allocation (DRA, `resource.k8s.io`) GA — advanced; mention | networking-storage |
| 1.35 | Job `.spec.managedBy` GA | workloads |
| 1.35 | In-place Pod resize (`resizePolicy`, resize subresource) GA (beta-on 1.33) | workloads |
| 1.35 | SupplementalGroupsPolicy GA | security |
| 1.36 | MutatingAdmissionPolicy (CEL) GA | API-machinery |
| 1.36 | User namespaces (`hostUsers: false`) GA (beta-on 1.33) | security |
| 1.36 | ProcMountType GA | security |
| — | StatefulSet `.spec.maxUnavailable` — beta-on 1.35 only, **NOT GA through 1.37** | workloads |
| — | Pod-level resources (`spec.resources`) — beta-on 1.34, **NOT GA through 1.37** | workloads |
| — | `matchLabelKeys` in topologySpread — selector-merge beta 1.34, **NOT GA through 1.37** | workloads |

## Checking your versions

Check both the client and the server:

```bash
kubectl version            # Client Version + Server Version (and Kustomize version)
kubectl version --client   # client only (no cluster needed)
```

`kubectl version` reports the **client** (kubectl) minor and, if a cluster is reachable,
the **server** (control-plane) minor — the latter is the version this table is keyed on
for cluster features. Keep kubectl within **±1 minor** of the server (the supported
version-skew policy); a 1.28 kubectl talks happily to a 1.27–1.29 API server, but skewing
further risks missing or misrendered fields.

To see what your cluster actually exposes and which gates are on:

```bash
kubectl api-versions        # enabled API group/versions (e.g. is autoscaling/v2 served?)
kubectl api-resources       # the live GVK map for this server
```

Feature gates are not directly listed by kubectl; check the control-plane component flags
(`--feature-gates` on the API server / controller-manager / scheduler / kubelet), the
managed-provider docs, or test the field/API with `kubectl explain <type>.<path>` and a
`--dry-run=server` apply. An Alpha gate is off unless explicitly enabled, so a field that
`explain` doesn't show may simply be gated off on your cluster.

The current upstream release line documented against here is **~1.37** (development tree).
Because managed control planes commonly lag the newest minor, the "Min version" column is a
**floor**: a feature tagged GA in 1.34 is simply not guaranteed on a 1.33 server — upgrade
the cluster (not just kubectl) to pick it up.
