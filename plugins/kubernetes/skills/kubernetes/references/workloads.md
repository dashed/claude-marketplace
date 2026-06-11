# Kubernetes Workload Manifest Authoring

The practical reference for writing **workload** manifests: the Pod spec and the
controllers that wrap it — Deployment, StatefulSet, DaemonSet, Job, CronJob —
plus autoscaling (HPA), disruption budgets (PDB), and the scheduling controls
(affinity, topology spread, tolerations, priority) that live in every Pod
template. For the kubectl CLI that drives these objects (`apply`, `rollout`,
`scale`, `diff`), see [kubectl.md](kubectl.md). For Services, ConfigMaps/Secrets,
storage (PV/PVC), RBAC, and networking, see
[cluster-resources.md](cluster-resources.md). For the conceptual overview and
core workflows, see [SKILL.md](../SKILL.md).

> **Version annotations.** Fields are flagged inline as `(k8s 1.X+)` **only**
> where they reach **GA** (the point you can rely on them unconditionally). Where
> a long beta-default-on window is the practical availability point, both are
> noted (e.g. "beta-on 1.29, GA 1.33"). Anything GA at or before **1.20** is
> *bedrock* and left unannotated. A handful of features are flagged **not yet
> GA** — treat those as "available behind a gate, don't rely on it in portable
> manifests". Documented against the Kubernetes source tree at **~1.37**; field
> shapes verified against `staging/src/k8s.io/api/`. Confirm any field on your
> cluster with `kubectl explain <type>.<path>` and your server version with
> `kubectl version`.

## Table of Contents

- [Pod Spec Essentials](#pod-spec-essentials)
- [Deployment](#deployment)
- [StatefulSet](#statefulset)
- [DaemonSet](#daemonset)
- [Job](#job)
- [CronJob](#cronjob)
- [HorizontalPodAutoscaler](#horizontalpodautoscaler)
- [PodDisruptionBudget](#poddisruptionbudget)
- [Scheduling Controls](#scheduling-controls)

## Pod Spec Essentials

A **Pod** is one or more co-scheduled containers that share a network namespace
(one IP, one port space) and, optionally, volumes. You rarely author a bare Pod —
almost always it lives inside a controller's `.spec.template`. The Pod template
is the heart of every workload below, so master it once and reuse it everywhere.

Every field shown here is part of the Pod template the controllers embed.

### Containers, command/args, ports

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
    - name: app
      image: nginx:1.27
      command: ["nginx"]            # overrides the image ENTRYPOINT
      args: ["-g", "daemon off;"]   # overrides the image CMD
      workingDir: /usr/share/nginx
      ports:
        - name: http                # named — referenceable from a Service/probe
          containerPort: 8080
          protocol: TCP
```

`command`/`args` map to ENTRYPOINT/CMD: set `command` to replace the entrypoint,
`args` to replace the arguments. `containerPort` is documentation/naming — it
does not publish the port (a Service does that); naming it lets probes and
Services target it by name.

### env / envFrom

Three ways to inject configuration, lowest ceremony first:

```yaml
      env:
        - name: LOG_LEVEL
          value: "info"                       # literal
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef: { name: db, key: password }
        - name: APP_CONFIG
          valueFrom:
            configMapKeyRef: { name: app-cfg, key: config.json }
        - name: POD_IP
          valueFrom:
            fieldRef: { fieldPath: status.podIP }        # downward API
        - name: CPU_LIMIT
          valueFrom:
            resourceFieldRef: { resource: limits.cpu }   # downward API
      envFrom:
        - configMapRef: { name: app-cfg }     # import ALL keys as env vars
        - secretRef: { name: app-secrets }
          prefix: APP_                          # optional key prefix
```

`env` sets one variable at a time (and can pull from ConfigMap/Secret keys, Pod
fields via `fieldRef`, or resource values via `resourceFieldRef`). `envFrom`
bulk-imports every key from a ConfigMap or Secret. **Env vars are captured at
container start — they do NOT update live**; change a referenced ConfigMap/Secret
and you must restart the pods (`kubectl rollout restart`) to pick it up.

### resources and QoS classes

```yaml
      resources:
        requests:                   # scheduling guarantee (used to place the pod)
          cpu: "250m"
          memory: "256Mi"
        limits:                     # hard cap
          cpu: "500m"
          memory: "512Mi"
```

- **requests** are what the scheduler reserves on a node; **limits** are the
  ceiling the kubelet enforces. Exceeding the **memory** limit ⇒ the container is
  **OOMKilled**; exceeding the **CPU** limit ⇒ the container is **throttled** (not
  killed).
- Always set both in production. The relationship between them determines the
  Pod's **Quality of Service (QoS) class**, which decides eviction order under
  node pressure:

  | QoS class | Condition | Eviction priority |
  |---|---|---|
  | **Guaranteed** | every container sets requests == limits for both cpu and memory | evicted **last** |
  | **Burstable** | at least one request/limit set, but not Guaranteed | evicted in the middle |
  | **BestEffort** | no requests or limits anywhere | evicted **first** |

  QoS is computed, not declared — you get a class by how you set requests/limits.

> **In-place pod resize** `(k8s 1.35+, beta-on 1.33)` — `resources` on a running
> container can be changed without recreating the pod, via the `resize`
> subresource. Control per-resource restart behavior with `resizePolicy`:
> ```yaml
>       resizePolicy:
>         - resourceName: cpu
>           restartPolicy: NotRequired      # or RestartContainer
>         - resourceName: memory
>           restartPolicy: RestartContainer
> ```

> **Pod-level resources** (`spec.resources`, sharing a budget across all
> containers) is **beta-on 1.34 and not GA as of 1.37** — do not rely on it in
> portable manifests.

### Probes: liveness, readiness, startup

Three independent health checks, each using one handler — `httpGet`,
`tcpSocket`, `exec`, or `grpc` `(k8s 1.27+ for grpc)`:

```yaml
      livenessProbe:                # FAIL → kubelet restarts the container
        httpGet: { path: /healthz, port: http }
        initialDelaySeconds: 10
        periodSeconds: 10
        failureThreshold: 3
      readinessProbe:               # FAIL → pod removed from Service endpoints
        httpGet: { path: /ready, port: http }
        periodSeconds: 5
      startupProbe:                 # gates the other two until the app has started
        httpGet: { path: /healthz, port: http }
        failureThreshold: 30        # allow 30 × periodSeconds for slow boot
        periodSeconds: 10
```

- **livenessProbe** — on failure, the container is **restarted**. Use for
  deadlock detection, not for slow startup.
- **readinessProbe** — on failure, the pod is **removed from Service endpoints**
  (no traffic) but not restarted. Use for "temporarily can't serve".
- **startupProbe** — while it is failing, liveness/readiness are suspended; once
  it succeeds the others take over. This is how you give a slow-starting app a
  long grace period without loosening liveness. (Bedrock — GA 1.20.)

Common timing fields on each probe: `initialDelaySeconds`, `periodSeconds`,
`timeoutSeconds`, `successThreshold`, `failureThreshold`.

### lifecycle hooks

```yaml
      lifecycle:
        postStart:
          exec: { command: ["/bin/sh", "-c", "echo started > /tmp/ready"] }
        preStop:
          httpGet: { path: /drain, port: http }
```

`postStart` runs right after the container starts; `preStop` runs before the
container is sent SIGTERM (use it to drain connections gracefully). A
`lifecycle.sleep` action `(k8s 1.34+)` lets `preStop` simply pause for N seconds
without shipping a shell:

```yaml
        preStop:
          sleep: { seconds: 15 }    # k8s 1.34+
```

### securityContext (pod- and container-level)

Security settings exist at both the **pod** level (`spec.securityContext`,
applies to all containers) and the **container** level (overrides the pod
setting for that container):

```yaml
spec:
  securityContext:                  # pod-level
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000                   # group owner applied to mounted volumes
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: nginx:1.27
      securityContext:              # container-level
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
          add: ["NET_BIND_SERVICE"]
```

Key fields: `runAsNonRoot`, `runAsUser`/`runAsGroup`, `readOnlyRootFilesystem`,
`allowPrivilegeEscalation`, `capabilities` (add/drop), and
`seccompProfile: {type: RuntimeDefault}`. `fsGroup` is pod-level only. The
structured **AppArmor** field `securityContext.appArmorProfile`
`(k8s 1.31+)` replaces the older `container.apparmor.security.beta.kubernetes.io/<name>`
annotation:

```yaml
      securityContext:
        appArmorProfile:
          type: RuntimeDefault      # structured field — k8s 1.31+
```

### serviceAccountName

```yaml
spec:
  serviceAccountName: app-sa        # identity the pod uses for API access
  automountServiceAccountToken: true
```

Names the ServiceAccount whose (bound, time-limited) token the pod presents to
the API server. See [cluster-resources.md](cluster-resources.md) for
ServiceAccounts and modern bound tokens.

### initContainers

Init containers run **to completion, in order, before** any app container starts.
Use them for setup, migrations, or waiting on a dependency:

```yaml
spec:
  initContainers:
    - name: wait-for-db
      image: busybox:1.36
      command: ["sh", "-c", "until nc -z db 5432; do sleep 1; done"]
  containers:
    - name: app
      image: myapp:1.0
```

### Sidecar containers `(k8s 1.33+, beta-on 1.29)`

A **sidecar** is a long-running helper (log shipper, proxy, config reloader) that
must live for the whole Pod lifetime. The native pattern is an **init container
with `restartPolicy: Always`** — it starts before the app containers, but unlike
a normal init container it keeps running alongside them:

```yaml
spec:
  initContainers:
    - name: log-shipper
      image: fluent/fluent-bit:3.0
      restartPolicy: Always         # ← this makes it a SIDECAR (k8s 1.33+; beta-on 1.29)
      volumeMounts:
        - { name: logs, mountPath: /var/log/app }
  containers:
    - name: app
      image: myapp:1.0
      volumeMounts:
        - { name: logs, mountPath: /var/log/app }
  volumes:
    - name: logs
      emptyDir: {}
```

Sidecars defined this way start before the app, are ready before app containers
start, and terminate after them — solving the ordering problems of putting a
helper in `containers[]`. Rely on it from **1.29** (beta-on) and unconditionally
from **1.33**.

### volumes and volumeMounts

Declare volumes at the Pod level, then mount them per container:

```yaml
spec:
  volumes:
    - name: cache
      emptyDir: {}                              # scratch space, dies with the pod
    - name: config
      configMap: { name: app-cfg }
    - name: secrets
      secret: { secretName: app-secrets }
    - name: data
      persistentVolumeClaim: { claimName: app-data }
    - name: meta
      downwardAPI:
        items:
          - path: labels
            fieldRef: { fieldPath: metadata.labels }
  containers:
    - name: app
      image: myapp:1.0
      volumeMounts:
        - { name: config, mountPath: /etc/app, readOnly: true }
        - { name: data, mountPath: /var/lib/app }
        - { name: cache, mountPath: /tmp/cache }
        - { name: config, mountPath: /etc/app/log.conf, subPath: log.conf }
```

Common volume sources: `emptyDir`, `hostPath`, `configMap`, `secret`,
`persistentVolumeClaim`, `projected`, `downwardAPI`, `csi`. `volumeMounts` fields:
`name`, `mountPath`, `readOnly`, and `subPath` (mount a single file/key rather
than the whole volume). **Mounted** ConfigMaps/Secrets update live (eventually);
env vars sourced from them do not.

## Deployment

`apps/v1`. The workhorse for **stateless** apps. A Deployment owns a ReplicaSet
per revision (which is what enables rollback), and the ReplicaSet owns the Pods.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels: { app: web }       # IMMUTABLE — must match template labels
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%                 # extra pods allowed above replicas during roll
      maxUnavailable: 25%           # pods allowed to be down during roll
  minReadySeconds: 10               # pod must stay ready this long to count
  revisionHistoryLimit: 10          # old ReplicaSets kept for rollback
  progressDeadlineSeconds: 600      # mark rollout failed if stuck this long
  template:                         # ← the Pod template (see above)
    metadata:
      labels: { app: web }
    spec:
      containers:
        - name: app
          image: nginx:1.27
          ports: [{ containerPort: 80 }]
```

**Strategy interplay:**

- `RollingUpdate` (default) replaces pods gradually. `maxSurge` and
  `maxUnavailable` (each a count or percentage) bound how fast: e.g.
  `maxUnavailable: 0` + `maxSurge: 1` does a strict "add one new, then remove one
  old" zero-downtime roll. Both being `0` is invalid.
- `Recreate` kills all old pods *before* creating new ones — accepts downtime,
  needed when two versions can't run at once (e.g. exclusive DB lock).
- `.spec.selector` is immutable after creation; it must match `template.metadata.labels`.

Drive rollouts with `kubectl rollout status|history|undo|restart deploy/web`
(see [kubectl.md](kubectl.md)).

> **ReplicaSet** (`apps/v1`) maintains N replicas and is what a Deployment creates
> underneath. You almost never author one directly — let the Deployment manage it.

## StatefulSet

`apps/v1`. For **stateful**, identity-sensitive workloads (databases, queues):
each pod gets a **stable name**, **stable network identity**, and its **own
persistent storage**.

```yaml
apiVersion: v1
kind: Service                       # the REQUIRED headless Service
metadata:
  name: db
spec:
  clusterIP: None                   # ← headless: no VIP, DNS returns pod IPs
  selector: { app: db }
  ports: [{ port: 5432, name: pg }]
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db                   # ← must name the headless Service above
  replicas: 3
  selector:
    matchLabels: { app: db }
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0                  # only ordinals >= partition are updated
  minReadySeconds: 10               # k8s 1.25+
  template:
    metadata:
      labels: { app: db }
    spec:
      containers:
        - name: postgres
          image: postgres:16
          ports: [{ containerPort: 5432 }]
          volumeMounts:
            - { name: data, mountPath: /var/lib/postgresql/data }
  volumeClaimTemplates:             # ← each pod gets its OWN PVC
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
```

- **Headless Service** (`clusterIP: None`) named in `.spec.serviceName` gives each
  pod a stable DNS name: `<sts>-<ordinal>.<svc>.<ns>.svc.cluster.local`.
- Pods are named `<sts>-0`, `<sts>-1`, … and created/deleted **in order**.
- **`volumeClaimTemplates`** mints a PVC per pod, named `<claim>-<sts>-<ordinal>`
  (e.g. `data-db-0`). These PVCs **survive** pod rescheduling and (by default)
  StatefulSet deletion.
- **Update strategies:** `RollingUpdate` updates pods in reverse ordinal order;
  `partition: N` updates only ordinals ≥ N (staged/canary rollouts). `OnDelete`
  updates a pod only when you manually delete it.
- `.spec.minReadySeconds` `(k8s 1.25+)`.

> `.spec.persistentVolumeClaimRetentionPolicy` controls whether the per-pod PVCs
> are deleted when the StatefulSet is scaled down or deleted. `maxUnavailable`
> for a StatefulSet rolling update is **beta-on as of 1.35 and not GA through
> 1.37** (gate `MaxUnavailableStatefulSet`) — do not rely on it in portable
> manifests.

## DaemonSet

`apps/v1`. Runs **one pod per (matching) node** — log shippers, node monitoring
agents, CNI plugins, storage daemons. As nodes join the cluster they get the
pod; as they leave it is garbage-collected.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
spec:
  selector:
    matchLabels: { app: node-exporter }
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1             # also: maxSurge
  template:
    metadata:
      labels: { app: node-exporter }
    spec:
      tolerations:                  # usually needed to land on control-plane / tainted nodes
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: node-exporter
          image: prom/node-exporter:latest
```

- `updateStrategy`: `RollingUpdate` (with `maxUnavailable`/`maxSurge`) or
  `OnDelete`.
- DaemonSets typically need **tolerations** (see
  [Scheduling Controls](#scheduling-controls)) to land on tainted/control-plane
  nodes, and often a `nodeSelector` to target a node subset.

## Job

`batch/v1`. **Run-to-completion** work — batch processing, migrations, one-off
tasks. The Job controller creates pods until the success criteria are met.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: import
spec:
  completions: 5                    # total successful pods required
  parallelism: 2                    # how many run at once
  backoffLimit: 4                   # pod retries before the Job is marked Failed
  activeDeadlineSeconds: 600        # hard wall-clock cap for the whole Job
  ttlSecondsAfterFinished: 3600     # auto-delete this long after finishing
  completionMode: Indexed           # k8s 1.24+ (see below)
  template:
    spec:
      restartPolicy: Never          # Jobs use Never or OnFailure (NOT Always)
      containers:
        - name: worker
          image: myapp:1.0
          command: ["./import.sh"]
```

Core knobs:

- **`completions`** / **`parallelism`** — total successes needed, and concurrency.
  Omit both for a single run-once pod.
- **`backoffLimit`** — number of pod-level retries before the Job fails (default
  6).
- **`activeDeadlineSeconds`** — overall time limit; **`ttlSecondsAfterFinished`**
  — auto-cleanup of a finished Job and its pods.
- The pod template's `restartPolicy` must be `Never` or `OnFailure` (never
  `Always`).

**Indexed Jobs** `(k8s 1.24+)` — `completionMode: Indexed` gives each pod a unique
index (`0..completions-1`), exposed as `JOB_COMPLETION_INDEX` in the env and in
the pod's hostname/annotation. Use it to statically partition work.

**`.spec.suspend`** `(k8s 1.24+)` — set `true` to create the Job suspended (no
pods) and flip to `false` later; the basis for queueing systems.

### podFailurePolicy `(k8s 1.31+)`

React to **specific** failures instead of blindly retrying — fail fast on
non-retryable exit codes, or ignore infrastructure disruptions:

```yaml
spec:
  backoffLimit: 6
  podFailurePolicy:
    rules:
      - action: FailJob             # don't retry — software bug exit codes
        onExitCodes:
          operator: In
          values: [1, 2, 42]
      - action: Ignore              # don't count disruptions against backoffLimit
        onPodConditions:
          - type: DisruptionTarget
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: worker
          image: myapp:1.0
```

`action` is one of `FailJob`, `Ignore`, `Count` (the default behavior), or
`FailIndex` (Indexed Jobs only). Each rule matches on **either** `onExitCodes`
(operator `In`/`NotIn` + values) **or** `onPodConditions`, not both.

### Per-index backoff and success policy `(k8s 1.33+)`

For Indexed Jobs:

```yaml
spec:
  completionMode: Indexed
  completions: 10
  parallelism: 10
  backoffLimitPerIndex: 1           # k8s 1.33+ — retry budget PER index
  maxFailedIndexes: 3               # k8s 1.33+ — fail the Job after N bad indexes
  successPolicy:                    # k8s 1.33+ — succeed early on a subset
    rules:
      - succeededIndexes: "0,2-4"
      - succeededCount: 6
```

- **`backoffLimitPerIndex`** + **`maxFailedIndexes`** `(k8s 1.33+)` — give each
  index its own retry budget and bound how many indexes may fail before the whole
  Job fails (so one poison index doesn't burn the global `backoffLimit`).
- **`successPolicy`** `(k8s 1.33+)` — declare the Job successful once a subset of
  indexes (`succeededIndexes`) or a count (`succeededCount`) succeed, terminating
  the rest.

> **`.spec.managedBy`** `(k8s 1.35+)` — hands reconciliation to an external/
> multi-cluster controller instead of the built-in Job controller. Advanced;
> mention only.

## CronJob

`batch/v1`. Runs a **Job on a schedule** (cron syntax).

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: nightly-backup
spec:
  schedule: "0 2 * * *"             # standard 5-field cron
  timeZone: "America/New_York"      # k8s 1.27+ (else schedule is in kube-controller-manager's TZ)
  concurrencyPolicy: Forbid         # Allow (default) | Forbid | Replace
  startingDeadlineSeconds: 200      # skip a run if it can't start within this window
  successfulJobsHistoryLimit: 3     # finished Jobs to retain
  failedJobsHistoryLimit: 1
  suspend: false                    # pause scheduling without deleting
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: backup
              image: myapp:1.0
              command: ["./backup.sh"]
```

- **`schedule`** — standard 5-field cron. **`timeZone`** `(k8s 1.27+)` interprets
  it in a named IANA zone; without it the schedule uses the controller manager's
  time zone.
- **`concurrencyPolicy`** — `Allow` (default, overlapping runs OK), `Forbid` (skip
  a new run if the previous is still going), or `Replace` (kill the running one,
  start fresh).
- **`startingDeadlineSeconds`** — if a scheduled run is delayed past this, skip it.
- **History limits** — how many finished Jobs to keep for inspection.
- **`jobTemplate`** is a full Job spec, so everything in [Job](#job) applies.

> The `batch/v1` CronJob API is GA as of **1.21**; on clusters older than that it
> was `batch/v1beta1`. Use `batch/v1`.

## HorizontalPodAutoscaler

`autoscaling/v2`. Automatically scales a workload's **replica count** based on
observed metrics. **Use `autoscaling/v2`** `(k8s 1.23+)` — the legacy
`autoscaling/v1` is CPU-only.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource                # built-in cpu/memory
      resource:
        name: cpu
        target:
          type: Utilization         # % of the pods' requests
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: AverageValue        # absolute per-pod value
          averageValue: 500Mi
    - type: Pods                    # custom per-pod metric
      pods:
        metric: { name: requests_per_second }
        target:
          type: AverageValue
          averageValue: "100"
    - type: External                # metric from outside the cluster (queue depth, etc.)
      external:
        metric: { name: queue_depth }
        target:
          type: Value
          value: "30"
  behavior:                         # tune scale velocity & flapping
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - { type: Percent, value: 50, periodSeconds: 60 }
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - { type: Pods, value: 4, periodSeconds: 30 }
        - { type: Percent, value: 100, periodSeconds: 30 }
      selectPolicy: Max
```

- **`metrics[]`** — each entry has a `type`: `Resource` (built-in cpu/memory),
  `Pods` (a custom per-pod metric, averaged), `Object` (a metric describing a
  single in-cluster object), or `External` (a metric from outside the cluster).
- **`target.type`** is `Utilization` (percentage of resource requests — Resource
  only), `AverageValue` (per-pod absolute), or `Value` (raw total).
- **`behavior`** — separate `scaleUp`/`scaleDown` rules with
  `stabilizationWindowSeconds` (smooths flapping; the controller picks the most
  conservative recommendation within the window) and `policies` (rate limits),
  combined by `selectPolicy` (`Max`/`Min`/`Disabled`).
- Resource metrics require **metrics-server**; Pods/Object/External require a
  custom/external metrics adapter. `kubectl autoscale` creates a basic HPA
  imperatively (see [kubectl.md](kubectl.md)).

## PodDisruptionBudget

`policy/v1`. Caps **voluntary** disruptions (node drains, cluster upgrades) so a
workload keeps a minimum number of pods running. It does **not** protect against
involuntary loss (a node crashing).

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web
spec:
  minAvailable: 2                   # OR maxUnavailable — not both
  selector:
    matchLabels: { app: web }
  unhealthyPodEvictionPolicy: IfHealthyBudget   # k8s 1.31+
```

- Set **exactly one** of `minAvailable` or `maxUnavailable` (a count or
  percentage), plus a `selector` matching the pods.
- A drain (`kubectl drain`) blocks rather than violate the budget — pair PDBs with
  `kubectl drain` for safe maintenance.
- **`unhealthyPodEvictionPolicy`** `(k8s 1.31+)` — `IfHealthyBudget` (default,
  only evict unhealthy pods when the budget is otherwise met) vs
  `AlwaysAllow` (let already-unhealthy pods be evicted even when the budget is at
  its limit — avoids deadlocks where broken pods can never be replaced).
- The `policy/v1` API is GA as of **1.21** (was `policy/v1beta1` before).

## Scheduling Controls

These fields live in the Pod template (`spec`) and steer **where** the scheduler
places pods.

### nodeSelector

The simplest constraint — schedule only onto nodes carrying all the listed
labels:

```yaml
spec:
  nodeSelector:
    disktype: ssd
    kubernetes.io/os: linux
```

### affinity / anti-affinity

Richer placement rules. Two flavors of each constraint: **`requiredDuringScheduling
IgnoredDuringExecution`** (hard — must be satisfied to schedule) and
**`preferredDuringSchedulingIgnoredDuringExecution`** (soft — weighted
preference).

```yaml
spec:
  affinity:
    nodeAffinity:                   # constrain to nodes by label expressions
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - { key: topology.kubernetes.io/zone, operator: In, values: ["us-east-1a", "us-east-1b"] }
    podAntiAffinity:                # spread replicas off the same node
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchLabels: { app: web }
            topologyKey: kubernetes.io/hostname
    podAffinity:                    # co-locate with pods matching a selector
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels: { app: cache }
          topologyKey: kubernetes.io/hostname
```

- **`nodeAffinity`** selects nodes by label expressions (a superset of
  `nodeSelector`).
- **`podAffinity`** / **`podAntiAffinity`** schedule relative to *other pods* — the
  `topologyKey` defines the domain (e.g. `kubernetes.io/hostname` = per node,
  `topology.kubernetes.io/zone` = per zone). Anti-affinity on the hostname key is
  the classic "spread my replicas across nodes" rule.
- **`matchLabelKeys`** in pod (anti)affinity `(k8s 1.33+)` scopes a term to pods
  sharing the same value of a label (e.g. only count pods of the *same rollout
  revision*).

### topologySpreadConstraints

Evenly spread pods across failure domains (zones, nodes) — more declarative than
anti-affinity for "balance" goals. The base feature is bedrock (default-on since
1.18).

```yaml
spec:
  topologySpreadConstraints:
    - maxSkew: 1                    # max difference in pod count between domains
      topologyKey: topology.kubernetes.io/zone
      whenUnsatisfiable: DoNotSchedule    # or ScheduleAnyway (soft)
      labelSelector:
        matchLabels: { app: web }
      minDomains: 3                 # k8s 1.30+ — require at least N domains
```

- **`maxSkew`** — the allowed imbalance; **`topologyKey`** — the domain label;
  **`whenUnsatisfiable`** — `DoNotSchedule` (hard) or `ScheduleAnyway` (best
  effort).
- **`minDomains`** `(k8s 1.30+)` — force spreading across at least N domains.
- **`nodeAffinityPolicy`** / **`nodeTaintsPolicy`** (NodeInclusionPolicy)
  `(k8s 1.33+)` — control whether node affinity/taints are honored when computing
  spread.

> `matchLabelKeys` in topology spread is **not GA through 1.37** (selector-merge
> beta 1.34) — do not rely on it as GA.

### tolerations

Taints (`kubectl taint nodes …`) repel pods from nodes; a matching **toleration**
lets a pod schedule there anyway. The counterpart to taints (covered in
[kubectl.md](kubectl.md)).

```yaml
spec:
  tolerations:
    - key: dedicated
      operator: Equal
      value: gpu
      effect: NoSchedule
    - key: node.kubernetes.io/not-ready
      operator: Exists
      effect: NoExecute
      tolerationSeconds: 300        # tolerate the taint for 5 min, then evict
```

`effect` is `NoSchedule`, `PreferNoSchedule`, or `NoExecute` (the last also evicts
already-running pods that don't tolerate it). `operator: Exists` matches any
value for the key.

### priorityClassName

Reference a **PriorityClass** (`scheduling.k8s.io/v1`) to set a pod's scheduling
priority; higher-priority pending pods can **preempt** (evict) lower-priority ones
to make room.

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
preemptionPolicy: PreemptLowerPriority    # or Never (no preemption)
description: "Critical workloads"
---
apiVersion: v1
kind: Pod
metadata:
  name: critical
spec:
  priorityClassName: high-priority
  containers:
    - { name: app, image: myapp:1.0 }
```

PriorityClass is cluster-scoped and bedrock. `preemptionPolicy: Never` makes a
high-priority pod jump the scheduling queue without evicting anyone.
