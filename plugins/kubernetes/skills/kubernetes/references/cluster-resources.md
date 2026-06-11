# Kubernetes Cluster Resources Reference

The resources that surround and support workloads: networking (Service, Ingress,
NetworkPolicy), configuration (ConfigMap, Secret), storage (PV/PVC/StorageClass),
isolation/limits (Namespace, ResourceQuota, LimitRange), access control (RBAC,
ServiceAccount), plus DNS conventions, the downward API, and kubeconfig structure.
For the Pod/controller side (Deployments, Jobs, scheduling), see
[workloads.md](workloads.md); for the `kubectl` CLI, see [kubectl.md](kubectl.md);
for the source-cited version table, see [version-features.md](version-features.md).

> **Version note:** documented against Kubernetes **~1.37**. Features carry an inline
> `(k8s 1.X+)` tag **only** where [version-features.md](version-features.md) sources
> a GA (or practical beta-on) boundary; everything else is bedrock (GA at/before 1.20)
> and unannotated. Confirm the live API map with `kubectl api-resources` and any field
> with `kubectl explain <type>.<path>`.

## Table of Contents

- [Service (v1)](#service-v1)
- [Ingress (networking.k8s.io/v1)](#ingress-networkingk8siov1)
- [NetworkPolicy (networking.k8s.io/v1)](#networkpolicy-networkingk8siov1)
- [ConfigMap & Secret (v1)](#configmap--secret-v1)
- [Storage: PV / PVC / StorageClass](#storage-pv--pvc--storageclass)
- [Namespace / ResourceQuota / LimitRange (v1)](#namespace--resourcequota--limitrange-v1)
- [RBAC (rbac.authorization.k8s.io/v1)](#rbac-rbacauthorizationk8siov1)
- [ServiceAccount (v1) & bound tokens](#serviceaccount-v1--bound-tokens)
- [DNS naming conventions](#dns-naming-conventions)
- [Downward API](#downward-api)
- [kubeconfig file structure](#kubeconfig-file-structure)

## Service (v1)

A Service gives a stable virtual IP (and DNS name) that load-balances over the Pods
matched by `.spec.selector`. The `.spec.type` field picks the exposure model:

- **ClusterIP** (default) — in-cluster virtual IP only.
- **NodePort** — opens a port (default range 30000–32767) on every node, on top of a
  ClusterIP.
- **LoadBalancer** — provisions an external load balancer (cloud provider, or a
  bare-metal implementation like k3s ServiceLB), on top of a NodePort.
- **ExternalName** — a CNAME alias to `.spec.externalName`; no selector, no proxying,
  no cluster IP.
- **Headless** (`clusterIP: None`) — no virtual IP; DNS returns the Pod IPs directly.
  Used by StatefulSets and any client that wants to talk to individual Pods.

Endpoints behind a Service are tracked by the controller as **EndpointSlice**
objects (`discovery.k8s.io/v1`, GA 1.21).

### ClusterIP with named ports and session affinity

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: ClusterIP            # the default; may be omitted
  selector:
    app: web                 # matches Pod labels
  ports:
    - name: http             # naming ports lets targetPort reference them by name
      port: 80               # the Service's port
      targetPort: http       # container port name (or a number)
      protocol: TCP          # TCP (default), UDP, or SCTP
  sessionAffinity: ClientIP  # ClientIP or None (default); pins a client to a backend
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800  # sticky window; >0 and <=86400, default 10800 (3h)
```

A container exposing a named port (referenced by `targetPort: http` above):

```yaml
# inside the Pod template:
containers:
  - name: web
    image: nginx
    ports:
      - name: http
        containerPort: 8080
```

### NodePort

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080        # optional; auto-assigned from the node-port range if omitted
  externalTrafficPolicy: Local   # Local preserves client source IP (no second hop);
                                 # Cluster (default) spreads across all endpoints
```

### LoadBalancer

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-lb
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
    - port: 443
      targetPort: 8443
  # externalTrafficPolicy: Local also applies here, to preserve source IP
```

The cloud/bare-metal LB implementation fills in `.status.loadBalancer.ingress` with
the external IP/hostname once provisioned.

### ExternalName

```yaml
apiVersion: v1
kind: Service
metadata:
  name: db
spec:
  type: ExternalName
  externalName: db.prod.example.com   # DNS returns a CNAME to this; no selector/ports needed
```

### Headless

```yaml
apiVersion: v1
kind: Service
metadata:
  name: db          # a StatefulSet references this via .spec.serviceName
spec:
  clusterIP: None   # headless — DNS resolves to each ready Pod IP, no VIP
  selector:
    app: db
  ports:
    - port: 5432
      targetPort: 5432
  # publishNotReadyAddresses: true   # also publish DNS for not-yet-ready Pods
```

## Ingress (networking.k8s.io/v1)

HTTP(S) routing into Services from outside the cluster. An Ingress is inert without an
**IngressController** running in the cluster (k3s ships Traefik); the controller reads
Ingress objects and configures the actual proxy. `.spec.ingressClassName` selects which
controller handles this Ingress by naming an **IngressClass** object.

`networking.k8s.io/v1` is bedrock (GA 1.19).

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
spec:
  ingressClassName: traefik          # names an IngressClass; picks the controller
  tls:
    - hosts:
        - app.example.com
      secretName: app-tls            # a kubernetes.io/tls Secret (tls.crt + tls.key)
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix         # Prefix | Exact | ImplementationSpecific
            backend:
              service:
                name: api
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  name: http         # may reference a Service port by name instead of number
```

`pathType` values: **Prefix** (match by URL path segments), **Exact** (exact match),
**ImplementationSpecific** (controller decides). A default backend (no host/path) can be
set via `.spec.defaultBackend`.

> **Gateway API is the successor.** Gateway API (`gateway.networking.k8s.io`, with
> `GatewayClass`/`Gateway`/`HTTPRoute`) is the modern, more expressive replacement for
> Ingress and the direction of travel for L4/L7 routing. It is a **separate project
> shipped as CRDs**, not part of core Kubernetes — install it before use. It is out of
> scope here; defer to the Gateway API documentation.

## NetworkPolicy (networking.k8s.io/v1)

A namespaced, label-selected firewall for Pods. The key rule to internalize:

- A Pod is **default-allow** until *some* NetworkPolicy selects it.
- Once any policy with a given `policyType` selects a Pod, that direction becomes
  **default-deny** — only traffic matching an `ingress`/`egress` rule is permitted.

Enforcement requires a CNI that implements NetworkPolicy (k3s enforces them unless
started with `--disable-network-policy`).

### Default-deny all ingress in a namespace

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: prod
spec:
  podSelector: {}            # empty selector = all Pods in the namespace
  policyTypes:
    - Ingress               # selecting Ingress with no ingress rules denies all inbound
```

A default-deny for **both** directions adds `Egress` to `policyTypes` (still with no
`ingress`/`egress` rules).

### Allow specific ingress and egress

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-allow
  namespace: prod
spec:
  podSelector:
    matchLabels:
      app: web              # this policy governs Pods labeled app=web
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend         # Pods in THIS namespace labeled app=frontend
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring   # all Pods in the monitoring ns
        - ipBlock:
            cidr: 10.0.0.0/16
            except:
              - 10.0.5.0/24
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: db
      ports:
        - protocol: TCP
          port: 5432
    - to: []                # an empty `to` with only ports = allow to anywhere on these ports
      ports:
        - protocol: UDP
          port: 53          # DNS — commonly required once egress is locked down
```

> A `from`/`to` entry combining `podSelector` **and** `namespaceSelector` in one list
> item is an AND (Pods matching both); separate list items are OR'd. An `ipBlock` peer
> cannot be combined with selectors in the same item.

## ConfigMap & Secret (v1)

Both hold key/value data and are consumed the same ways — as environment variables, as
mounted files, or referenced from other fields. ConfigMap is for non-secret config;
Secret is for sensitive data.

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: info                 # string key/values
  app.conf: |                     # a whole config file
    server.port=8080
    server.host=0.0.0.0
binaryData:                       # base64-encoded binary values (optional)
  cert.der: aGVsbG8=
immutable: true                   # optional: locks the object; can't be edited, only
                                  # deleted+recreated (k8s 1.21+); improves performance
```

### Secret

A Secret stores values base64-encoded in `data`. **Base64 is encoding, not
encryption** — Secrets are not encrypted at rest unless the cluster enables
encryption-at-rest (and RBAC controls who can read them). `stringData` lets you write
plaintext that the API server encodes for you on write; it is write-only (never echoed
back).

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque                      # the default
stringData:                       # plaintext in, base64 stored; convenient for authoring
  DB_PASSWORD: s3cr3t
  config.json: |
    {"token": "abc123"}
data:                             # alternatively, pre-base64-encoded values
  API_KEY: YWJjMTIz
immutable: true                   # (k8s 1.21+) — same semantics as ConfigMap
```

**Secret `type` values** drive validation and how components consume them:

| `type` | Required keys | Used for |
|---|---|---|
| `Opaque` | (any) | arbitrary user data (the default) |
| `kubernetes.io/dockerconfigjson` | `.dockerconfigjson` | image pull secrets (`imagePullSecrets`) |
| `kubernetes.io/tls` | `tls.crt`, `tls.key` | TLS certs (Ingress `tls`, etc.) |
| `kubernetes.io/basic-auth` | `username`, `password` | basic-auth credentials |
| `kubernetes.io/service-account-token` | — | legacy long-lived SA token (prefer bound tokens) |

### Consuming: envFrom vs. valueFrom vs. volume mount

```yaml
# inside a Pod template's container:
containers:
  - name: app
    image: myapp
    envFrom:
      - configMapRef:
          name: app-config       # imports every key as an env var
      - secretRef:
          name: app-secret       # likewise for the Secret's keys
    env:
      - name: LOG                 # OR cherry-pick a single key
        valueFrom:
          configMapKeyRef:
            name: app-config
            key: LOG_LEVEL
      - name: DB_PASSWORD
        valueFrom:
          secretKeyRef:
            name: app-secret
            key: DB_PASSWORD
    volumeMounts:
      - name: config-vol
        mountPath: /etc/app       # each key becomes a file under this dir
        readOnly: true
volumes:
  - name: config-vol
    configMap:
      name: app-config
      items:                      # optional: project only selected keys, rename paths
        - key: app.conf
          path: app.conf
  # - name: secret-vol
  #   secret:
  #     secretName: app-secret
  #     defaultMode: 0400
```

**Update propagation caveats:**

- **Mounted** ConfigMaps/Secrets update **live** (eventually consistent — the kubelet
  refreshes on a sync interval; can take ~1 minute). A mount that uses `subPath` does
  **not** receive updates.
- **Environment variables** (from `envFrom`/`valueFrom`) are captured at Pod start and
  **never** update. Restart the Pods (`kubectl rollout restart deploy/<name>`) to pick
  up env changes.
- An **immutable** ConfigMap/Secret cannot be updated at all — delete and recreate (and
  re-roll consumers).

## Storage: PV / PVC / StorageClass

Three objects implement persistence:

- **PersistentVolume (PV)** — a cluster-scoped piece of storage, either pre-provisioned
  by an admin or created dynamically by a provisioner.
- **PersistentVolumeClaim (PVC)** — a namespaced *request* for storage that binds to a
  PV. Pods reference a PVC, never a PV directly.
- **StorageClass** (`storage.k8s.io/v1`) — names a provisioner for **dynamic**
  provisioning (k3s ships `local-path`). A PVC that names a StorageClass gets a PV made
  on demand.

### StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: rancher.io/local-path        # the CSI/in-tree provisioner driver
reclaimPolicy: Delete                      # Delete (default) | Retain — fate of the PV when its PVC is deleted
volumeBindingMode: WaitForFirstConsumer    # Immediate | WaitForFirstConsumer
                                           # (latter delays binding until a Pod is scheduled — topology-aware)
allowVolumeExpansion: true                 # permit growing PVCs bound to this class (k8s 1.24+)
parameters:                                # provisioner-specific
  type: ssd
```

### PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data
spec:
  accessModes:
    - ReadWriteOnce          # see access modes below
  storageClassName: fast     # omit to use the cluster default class; "" disables dynamic provisioning
  resources:
    requests:
      storage: 10Gi
  # volumeName: pv-0         # optional: bind to a specific pre-provisioned PV
```

A PVC consumed by a Pod:

```yaml
volumes:
  - name: data
    persistentVolumeClaim:
      claimName: data
```

(StatefulSets generate one PVC per replica via `.spec.volumeClaimTemplates`; see
[workloads.md](workloads.md).)

### Statically-provisioned PV (admin-authored)

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-0
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain    # Retain | Delete | Recycle (deprecated)
  storageClassName: fast
  hostPath:                                # one of many volume sources (csi, nfs, etc.)
    path: /mnt/data
```

**Access modes:**

| Mode | Short | Meaning |
|---|---|---|
| `ReadWriteOnce` | RWO | read-write by a single **node** |
| `ReadOnlyMany` | ROX | read-only by many nodes |
| `ReadWriteMany` | RWX | read-write by many nodes |
| `ReadWriteOncePod` | RWOP | read-write by a single **Pod** (k8s 1.29+) |

**Resizing:** to grow a volume, edit the PVC's `spec.resources.requests.storage`
upward (the StorageClass must have `allowVolumeExpansion: true`); online expansion is
GA 1.24. Recovery from a failed expansion (shrinking the request back down after a
provisioner rejects it) is GA 1.34.

**VolumeAttributesClass** (`storage.k8s.io/v1`, GA 1.34) lets you change mutable volume
parameters (e.g. IOPS/throughput) of an existing volume by referencing a
`VolumeAttributesClass` from the PVC — without recreating it.

## Namespace / ResourceQuota / LimitRange (v1)

A **Namespace** is the scope and isolation boundary for most resources (Pods,
Services, ConfigMaps, etc.). `ResourceQuota` and `LimitRange` are namespaced
governance objects.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: team-a
```

**ResourceQuota** caps the *aggregate* resource use and object counts in a namespace.
If a quota for a compute resource exists, every Pod in the namespace must set the
corresponding request/limit (often supplied by a LimitRange default).

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-a-quota
  namespace: team-a
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
    persistentvolumeclaims: "10"
    services.loadbalancers: "2"
```

**LimitRange** sets default / min / max per-container (or per-Pod) requests and limits
within a namespace, and supplies defaults when a container omits them.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: team-a-limits
  namespace: team-a
spec:
  limits:
    - type: Container
      default:                 # applied as the limit if the container omits one
        cpu: 500m
        memory: 512Mi
      defaultRequest:          # applied as the request if omitted
        cpu: 100m
        memory: 128Mi
      max:
        cpu: "2"
        memory: 2Gi
      min:
        cpu: 50m
        memory: 64Mi
```

## RBAC (rbac.authorization.k8s.io/v1)

RBAC grants permissions by binding a **role** (a set of rules) to **subjects** (users,
groups, ServiceAccounts). `rbac.authorization.k8s.io/v1` is bedrock.

- **Role** — namespaced; its rules apply within one namespace.
- **ClusterRole** — cluster-scoped; can grant access to cluster-scoped resources
  (Nodes, PVs), to namespaced resources across **all** namespaces, or to non-resource
  URLs.
- **RoleBinding** — grants a Role (or a ClusterRole) **within one namespace**.
- **ClusterRoleBinding** — grants a ClusterRole **cluster-wide**.

A RoleBinding may reference a **ClusterRole**, which grants that ClusterRole's rules
only inside the RoleBinding's namespace — the common way to reuse a shared role
definition per-namespace.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: team-a
rules:
  - apiGroups: [""]                 # "" is the core group (Pods, Services, ConfigMaps…)
    resources: ["pods", "pods/log"] # subresources use a slash
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    resourceNames: ["web"]          # optional: restrict to named objects (no list/watch)
    verbs: ["get", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: team-a
subjects:
  - kind: ServiceAccount
    name: ci
    namespace: team-a
  - kind: User
    name: alice@example.com         # authenticator-provided identity
    apiGroup: rbac.authorization.k8s.io
  - kind: Group
    name: team-a-devs
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role                        # Role or ClusterRole
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

A ClusterRole + ClusterRoleBinding granting read across all namespaces:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: secret-reader
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-secrets-global
subjects:
  - kind: Group
    name: system:authenticated
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: secret-reader
  apiGroup: rbac.authorization.k8s.io
```

**Aggregated ClusterRoles** — a ClusterRole with an `aggregationRule` has its `rules`
managed automatically (leave them empty); the controller unions in the rules of every
ClusterRole whose labels match the selector. This is how the built-in `admin`/`edit`/
`view` roles are extended by add-ons.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring
aggregationRule:
  clusterRoleSelectors:
    - matchLabels:
        rbac.example.com/aggregate-to-monitoring: "true"
rules: []   # filled in by the aggregation controller — do not author by hand
# A contributing ClusterRole simply carries the matching label:
#   metadata.labels: { rbac.example.com/aggregate-to-monitoring: "true" }
```

**Common verbs:**

| Verb | Applies to |
|---|---|
| `get` | read a single named object |
| `list` | list a collection (can return all object data — treat like read-all) |
| `watch` | stream changes to a collection |
| `create` | create new objects |
| `update` | replace an object (full) |
| `patch` | partially modify an object |
| `delete` | delete a single object |
| `deletecollection` | delete a whole collection |
| `*` | all verbs (use sparingly) |

> `list` effectively exposes the contents of every object in the collection, so
> granting `list` on `secrets` is as powerful as `get` on each — scope it carefully.

**Check effective permissions** without trial-and-error:

```bash
kubectl auth can-i create deployments -n team-a
kubectl auth can-i get pods --as=system:serviceaccount:team-a:ci   # impersonate a subject
kubectl auth can-i --list -n team-a                                # everything the caller can do
kubectl auth reconcile -f rbac.yaml                                # safely apply/merge RBAC objects
```

## ServiceAccount (v1) & bound tokens

A ServiceAccount is a namespaced identity used by Pods (and automation) to authenticate
to the API server. Every namespace has a `default` SA.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ci
  namespace: team-a
automountServiceAccountToken: false   # opt out of auto-mounting the token into Pods
imagePullSecrets:                     # registry creds used for Pods running as this SA
  - name: regcred                     # a kubernetes.io/dockerconfigjson Secret
```

A Pod selects its identity with `spec.serviceAccountName: ci`. The same
`automountServiceAccountToken` field exists on the Pod spec and overrides the SA-level
setting.

**Bound, projected tokens (the modern model).** Pods no longer rely on a forever-living
token Secret. The kubelet mounts a short-lived, audience-scoped token via a *projected
volume* that it auto-rotates; the token is bound to the Pod's lifetime and a specific
audience. To mint one manually:

```bash
kubectl create token ci -n team-a --audience=api --duration=1h
```

A projected token volume, made explicit (this is what the kubelet injects by default):

```yaml
volumes:
  - name: kube-api-access
    projected:
      sources:
        - serviceAccountToken:
            path: token
            audience: api
            expirationSeconds: 3600   # min 600; kubelet rotates before expiry
```

> Several token-binding refinements (binding the token to the node, a JTI claim, Pod/Node
> info in the token) GA'd in the 1.32–1.33 range; the bound-token model itself is the
> default well before that. For a Secret-backed legacy token, create a Secret of type
> `kubernetes.io/service-account-token` annotated with the SA name — but prefer
> `kubectl create token` / projection.

## DNS naming conventions

CoreDNS (bundled by k3s) serves cluster DNS under the cluster domain
`cluster.local`:

| What | DNS name |
|---|---|
| Service (any type with a ClusterIP) | `<svc>.<ns>.svc.cluster.local` |
| Service, short forms within the same namespace | `<svc>` or `<svc>.<ns>` |
| Headless Service Pod (e.g. StatefulSet) | `<pod>.<svc>.<ns>.svc.cluster.local` |
| Named SRV port | `_<port-name>._<proto>.<svc>.<ns>.svc.cluster.local` |
| A Pod by IP (rarely used) | `<pod-ipv4-dashed>.<ns>.pod.cluster.local` |

A headless Service returns an A/AAAA record per ready Pod IP (rather than one VIP),
which is what gives StatefulSet members stable, individually-addressable names.

## Downward API

Expose Pod/container metadata to a container as environment variables or files, without
the app calling the API server.

- **`fieldRef`** — Pod object fields: `metadata.name`, `metadata.namespace`,
  `metadata.uid`, `metadata.labels['<key>']`, `metadata.annotations['<key>']`,
  `status.podIP`, `status.hostIP`, `spec.nodeName`, `spec.serviceAccountName`.
- **`resourceFieldRef`** — the container's own resource requests/limits (e.g.
  `limits.memory`, `requests.cpu`).

```yaml
containers:
  - name: app
    image: myapp
    env:
      - name: POD_NAME
        valueFrom:
          fieldRef:
            fieldPath: metadata.name
      - name: POD_IP
        valueFrom:
          fieldRef:
            fieldPath: status.podIP
      - name: MEM_LIMIT
        valueFrom:
          resourceFieldRef:
            containerName: app
            resource: limits.memory
            divisor: 1Mi
    volumeMounts:
      - name: podinfo
        mountPath: /etc/podinfo
volumes:
  - name: podinfo
    downwardAPI:
      items:
        - path: labels                # each becomes a file
          fieldRef:
            fieldPath: metadata.labels
        - path: cpu_request
          resourceFieldRef:
            containerName: app
            resource: requests.cpu
```

> Only labels and annotations can be projected as a downwardAPI **volume** *and* update
> live when they change; field/resource env vars are captured at start.

## kubeconfig file structure

kubeconfig (default `~/.kube/config`, overridable with `$KUBECONFIG` — which may be a
`:`-separated list that gets merged) is three independent lists plus a pointer to the
current context:

- **clusters** — an API server URL + its CA (how to reach and trust a cluster).
- **users** — credentials (client cert, token, exec plugin, etc.).
- **contexts** — a `{cluster, user, namespace}` triple; a name you switch between.
- **current-context** — the context used when `--context` is not given.

```yaml
apiVersion: v1
kind: Config
current-context: dev
clusters:
  - name: dev-cluster
    cluster:
      server: https://10.0.0.1:6443
      certificate-authority-data: <base64 CA>   # or certificate-authority: /path/ca.crt
users:
  - name: dev-user
    user:
      client-certificate-data: <base64 cert>    # or token:, or an exec: credential plugin
      client-key-data: <base64 key>
contexts:
  - name: dev
    context:
      cluster: dev-cluster
      user: dev-user
      namespace: team-a            # default namespace for this context
```

Manage it with `kubectl config` rather than editing by hand:

```bash
kubectl config get-contexts                              # list; * marks current
kubectl config use-context dev                           # switch cluster
kubectl config set-context --current --namespace=team-a  # change default namespace
kubectl config view --minify --flatten                   # effective config for current ctx, inlined
```

(See [kubectl.md](kubectl.md) for the full `kubectl config` surface.)
