---
name: kubernetes
description: Author and operate Kubernetes workloads with kubectl and YAML manifests — the kubectl CLI plus core resource authoring (Pods, Deployments, StatefulSets, Jobs/CronJobs, Services, Ingress, ConfigMaps/Secrets, PV/PVC, RBAC). Use when writing or debugging Kubernetes manifests, running kubectl (get/describe/apply/diff/rollout/logs/exec/debug/port-forward), inspecting a failing pod (CrashLoopBackOff/ImagePullBackOff/Pending/OOMKilled), managing contexts/namespaces, generating manifests with --dry-run=client, checking permissions with auth can-i, or doing server-side apply. Triggers on kubectl, kube, k8s, Pod/Deployment/Service/Ingress/ConfigMap YAML, kubeconfig, kustomize. This is the kubectl + resource/manifest layer — for installing or running a lightweight cluster use the k3s skill; cluster install/admin, client libraries, cloud-provider specifics, and Helm are out of scope.
---

# Kubernetes - kubectl + Manifest Authoring

## Overview

Kubernetes runs containerized workloads against a **declarative API**. You don't tell it *how* to run things; you declare *what* you want (a manifest's `spec`) and the system continuously works to make reality (`status`) match. `kubectl` is the CLI you use to submit that desired state and to inspect, debug, and roll out workloads against any cluster — regardless of how the cluster was built.

This skill is the **kubectl + resource/manifest layer**: authoring core API objects and driving the API with `kubectl`. It is independent of how the cluster was stood up.

> **Disambiguation:** This skill documents **`kubectl` and core-resource manifest authoring** — how to write Kubernetes objects and drive the API. It does **not** cover installing or administering a cluster. To **run a local or lightweight cluster** (install a single binary, join nodes, etcd snapshots, bundled ingress/LB/DNS, certs), use the **k3s** skill. Out of scope entirely: client libraries (client-go), cloud-provider specifics (EKS/GKE/AKS IAM, cloud LBs/CSI), and Helm (mention as a packaging option, defer).

## Mental Model

Four ideas unlock everything:

1. **Declarative desired state.** You declare *what* you want in a manifest (`spec`); the system drives reality (`status`) to match. `kubectl apply` submits desired state; controllers do the rest.
2. **Control loops (reconciliation).** Every resource type has a controller that watches and drives `status` toward `spec`. A Deployment controller creates a ReplicaSet; the ReplicaSet controller creates Pods; the scheduler binds Pods to Nodes; the kubelet runs containers. Self-healing falls out of this for free.
3. **Everything is an API object** addressed by **Group / Version / Kind (GVK)**: `apiVersion: apps/v1` + `kind: Deployment`. The empty "core" group is written as just `v1` (Pod, Service, ConfigMap, Secret, Namespace). Named groups include `apps/v1`, `batch/v1`, `networking.k8s.io/v1`, `rbac.authorization.k8s.io/v1`, `policy/v1`, `autoscaling/v2`, `storage.k8s.io/v1`. Run `kubectl api-resources` to see the live map.
4. **Namespaces** scope most resources (Pods, Deployments, Services, ConfigMaps…). Cluster-scoped resources (Nodes, PersistentVolumes, Namespaces, ClusterRoles, StorageClasses, PriorityClasses) live outside any namespace. `default` exists out of the box; `kube-system` holds control-plane add-ons.

Every object shares a shape: `apiVersion`, `kind`, `metadata` (name, namespace, labels, annotations), `spec` (desired), `status` (observed, managed by the system — **never author it**).

## When to Use This Skill

Use this skill when:
- **Writing/editing manifests** (YAML) for any core resource.
- **Driving kubectl**: deploy, inspect, debug, roll out, scale, exec/logs, port-forward, generate manifests, check RBAC.
- **Debugging a workload**: a Pod stuck Pending, CrashLoopBackOff, ImagePullBackOff, OOMKilled; reading events; describing resources.
- **Managing contexts/namespaces** across clusters via kubeconfig.

### Relationship to the k3s skill

This skill is the **kubectl + resource/manifest layer** — authoring Kubernetes objects and driving the API with `kubectl`, regardless of how the cluster was created. It does **not** cover standing up or administering a cluster. To **run a local or lightweight cluster** (install the single k3s binary, join nodes, snapshots, bundled ingress/LB/DNS/storage, certs), use the **k3s** skill. k3s hands you a working API endpoint and a kubeconfig; this skill is everything you do against it. (k3s even bundles `kubectl` — every command here works on a k3s cluster.) Out of scope: client libraries, cloud-provider specifics, and Helm.

## Prerequisites

**CRITICAL**: Before proceeding, verify kubectl is installed and check the version:

```bash
kubectl version --client     # prints e.g. "Client Version: v1.28.2"
```

**Version note:** This skill is documented against the Kubernetes API as of **~1.37**; the empirical CLI baseline is **kubectl v1.28.2** (bundled **kustomize v5.0.4**). Long-standing features (GA at or before **1.20**) are "bedrock" and shown **unannotated**. Features added later are tagged inline as `(k8s 1.X+)` by their **GA** version — see [references/version-features.md](references/version-features.md) for the full feature → version map with source citations. **Version skew:** keep `kubectl` within **±1 minor** of the cluster.

## Install kubectl + kubeconfig/contexts

```bash
# macOS
brew install kubectl
# Linux (direct binary, matching minor)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client     # verify
```

(For a cluster to point it at, see the **k3s** skill.)

**kubeconfig** lives at `~/.kube/config` (override with `$KUBECONFIG`, which may be a `:`-separated list that gets merged). It holds three lists — **clusters** (API server URL + CA), **users** (credentials), **contexts** (a cluster+user+namespace triple) — plus a `current-context`.

```bash
kubectl config get-contexts                              # list; * marks current
kubectl config use-context <ctx>                         # switch cluster
kubectl config set-context --current --namespace=<ns>    # set default namespace
kubectl config view --minify                             # effective config for current ctx
```

(`kubectx` / `kubens` are popular third-party helpers for switching contexts/namespaces.)

## Core Workflows

### 1. Deploy + expose

```bash
kubectl create deployment web --image=nginx --replicas=3      # imperative, quick
kubectl expose deployment web --port=80 --target-port=8080    # creates a ClusterIP Service
kubectl get deploy,rs,pods,svc -l app=web
```

Prefer declarative for anything you keep: generate with `--dry-run=client -o yaml > web.yaml`, edit, then `kubectl apply -f web.yaml`.

### 2. Inspect / debug a failing pod

```bash
kubectl get pods                      # the STATUS column tells the story
kubectl describe pod <pod>            # Events at the bottom are the #1 clue
kubectl logs <pod> [-c <container>] [--previous]   # --previous = last crashed container
kubectl get events --sort-by=.lastTimestamp        # or: kubectl events
```

Map STATUS → cause in [Troubleshooting](#troubleshooting) below.

### 3. Apply / diff / rollout cycle

```bash
kubectl diff -f web.yaml              # preview what apply would change
kubectl apply -f web.yaml             # converge to desired state
kubectl rollout status deploy/web     # wait for the rollout to finish
kubectl rollout history deploy/web
kubectl rollout undo deploy/web       # roll back to previous revision
kubectl rollout restart deploy/web    # re-roll pods (e.g. to pick up a changed Secret)
```

### 4. Exec / logs / port-forward

```bash
kubectl exec -it <pod> -- sh                       # shell in a running container
kubectl logs -f deploy/web                         # stream logs (Deployment → a pod)
kubectl port-forward svc/web 8080:80               # localhost:8080 → Service:80
```

### 5. Generate manifests with `--dry-run=client` (offline, no cluster)

```bash
kubectl create deployment web --image=nginx --dry-run=client -o yaml
kubectl create configmap app-cfg --from-literal=LOG=info --dry-run=client -o yaml
kubectl create cronjob nightly --image=busybox --schedule="0 2 * * *" --dry-run=client -o yaml
```

These emit clean starter YAML you then edit (verified emitting on 1.28.2: deployment→`apps/v1`, job/cronjob→`batch/v1`, service/cm/secret→`v1`, rolebinding→`rbac.authorization.k8s.io/v1`, ingress→`networking.k8s.io/v1`, pdb→`policy/v1`, priorityclass→`scheduling.k8s.io/v1`).

> **Not offline generators.** `kubectl run`, `kubectl expose`, `kubectl autoscale`, and `kubectl create role --resource=…` consult the API server **even under `--dry-run=client`** (for resource/GVR resolution), so they need a reachable cluster. Don't expect them to render YAML with no cluster.

### 6. RBAC quick-check with `auth can-i`

```bash
kubectl auth can-i create deployments                          # for yourself
kubectl auth can-i get pods --as=system:serviceaccount:ns:sa   # impersonate
kubectl auth can-i --list                                      # everything you can do
kubectl auth whoami                                            # who am I (Experimental in 1.28)
```

## Quick Reference

| Task | Command |
|------|---------|
| List / wide / labels | `kubectl get <r> [-o wide] [--show-labels] [-A]` |
| Full detail + events | `kubectl describe <r> <name>` |
| Apply / preview | `kubectl apply -f f.yaml` · `kubectl diff -f f.yaml` |
| Server-side apply | `kubectl apply --server-side -f f.yaml` (k8s 1.22+) |
| Delete | `kubectl delete -f f.yaml` / `kubectl delete <r> <name>` |
| Logs / follow / prev | `kubectl logs [-f] [--previous] [-c c] <pod>` |
| Shell in | `kubectl exec -it <pod> -- sh` |
| Port-forward | `kubectl port-forward svc/<s> L:R` |
| Rollout | `kubectl rollout status\|history\|undo\|restart <deploy>` |
| Scale | `kubectl scale deploy/<d> --replicas=N` |
| Debug pod | `kubectl debug -it <pod> --image=busybox --target=<c>` (k8s 1.25+) |
| Explain a field | `kubectl explain deploy.spec.template.spec.containers` |
| Switch namespace | `kubectl config set-context --current --namespace=<ns>` |
| Can I…? | `kubectl auth can-i <verb> <resource>` |
| Resource map | `kubectl api-resources` |
| Output as jsonpath | `kubectl get pods -o jsonpath='{.items[*].metadata.name}'` |
| Wait for condition | `kubectl wait --for=condition=Available deploy/web --timeout=120s` |
| Build + apply kustomize | `kubectl apply -k overlays/prod/` |

## Troubleshooting

A failing Pod's STATUS column is the fastest diagnostic. Map it to a cause, then confirm with `kubectl describe pod <pod>` (read the **Events** at the bottom).

| STATUS / symptom | Likely cause | First moves |
|------------------|--------------|-------------|
| **ImagePullBackOff / ErrImagePull** | bad image name/tag, private registry without `imagePullSecrets`, rate-limit | `describe pod` → Events; fix image or add a pull secret |
| **CrashLoopBackOff** | container starts then exits/errors repeatedly | `logs --previous`; check command/args, config, a failing probe, missing env/secret |
| **Pending** | no node fits: insufficient CPU/mem, unschedulable taints, no matching nodeSelector/affinity, unbound PVC | `describe pod` → Events ("FailedScheduling"); `kubectl get pvc`; check requests vs node capacity |
| **OOMKilled** (in `describe`/last state) | container exceeded its memory **limit** | raise `resources.limits.memory`, or fix the leak; check `requests` too |
| **Init:… / PodInitializing stuck** | an init container is failing/looping | `logs <pod> -c <init-container>` |
| **CreateContainerConfigError** | referenced ConfigMap/Secret/key missing | `describe pod`; create/fix the referenced object |
| **Terminating (stuck)** | finalizers, or graceful shutdown hanging | check `metadata.finalizers`; `--grace-period=0 --force` as a last resort |

**Common kubectl errors:**
- `The connection to the server <host> was refused` → wrong/empty context or cluster down. Check `kubectl config current-context` and your kubeconfig.
- `error: You must be logged in to the server (Unauthorized)` → bad/expired credentials.
- `Error from server (Forbidden)` → RBAC; confirm what you can do with `kubectl auth can-i`.
- `Error from server (NotFound)` → wrong namespace (try `-n <ns>` / `-A`) or the object is truly absent.
- `no matches for kind "X" in version "Y"` → a CRD isn't installed, or the wrong apiVersion.

## References

For exhaustive detail, see the bundled reference files:

- [references/kubectl.md](references/kubectl.md) — the full `kubectl` CLI: verbs, output formats (`-o jsonpath`/`custom-columns`/`go-template`), selectors, the apply model (client- vs server-side, `--prune`), `diff`, `rollout`, `scale`/`autoscale`, `exec`/`logs`/`cp`/`port-forward`/`proxy`, `debug`, node ops (`drain`/`cordon`/`taint`), `auth can-i`, `api-resources`/`explain`, `config`, kustomize (`-k`), `events`, `top`, `--dry-run`, `wait`, `--subresource`, and plugins/krew.
- [references/workloads.md](references/workloads.md) — manifest authoring for workloads: Pod spec essentials (env, resources, probes, securityContext, init/sidecar containers, volumes), Deployment, ReplicaSet, StatefulSet, DaemonSet, Job, CronJob, HorizontalPodAutoscaler, PodDisruptionBudget, and scheduling controls (affinity, topology spread, tolerations, priority).
- [references/cluster-resources.md](references/cluster-resources.md) — Service (incl. headless), Ingress/IngressClass, NetworkPolicy, ConfigMap/Secret, storage (PV/PVC/StorageClass, access modes), Namespace/ResourceQuota/LimitRange, RBAC (Role/ClusterRole/bindings/aggregation), ServiceAccount + bound tokens, DNS conventions, and the Downward API.
- [references/version-features.md](references/version-features.md) — source-cited feature → minimum-version map (what's bedrock vs. added later), so you know when each `(k8s 1.X+)` annotation applies.

## Resources

- **Help**: `kubectl help`, `kubectl <verb> --help`, `kubectl explain <type>[.<path>]`
- **Official docs**: https://kubernetes.io/docs/
- **Reference**: https://kubernetes.io/docs/reference/kubectl/
- **API reference**: https://kubernetes.io/docs/reference/kubernetes-api/
