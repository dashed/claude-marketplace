# kubectl CLI Reference

Complete reference for the `kubectl` command-line client: resource verbs, output
formats, selectors, the apply model (client- vs server-side), rollout/scale, the
exec/logs/debug family, node-maintenance verbs, RBAC/discovery commands, kubeconfig
context handling, kustomize, events/top, and the dry-run/wait/subresource flags that
matter for scripting. The CLI talks to a cluster's API server; only a handful of
`create` generators and config edits work without one (see [Offline / no-cluster
behavior](#offline--no-cluster-behavior)).

> **Verification & version annotations.** Every flag, verb, and output format below was
> confirmed against the installed **kubectl v1.28.2** (bundled **kustomize v5.0.4**) by
> reading each command's `--help` and, where possible, exercising it **client-side with
> no cluster reachable**. Anything that runs on 1.28.2 is available at **≤1.28** and is
> left unannotated (bedrock). Items newer than 1.28 could not be run here; they are
> sourced from upstream CHANGELOGs and tagged `(k8s 1.X+)`. Confirm your own build with
> `kubectl version --client`, then the relevant `kubectl <cmd> --help`. Keep kubectl
> within **±1 minor** of the cluster.

## Table of Contents

- [Resource verbs](#resource-verbs)
- [Output formats (`-o`)](#output-formats--o)
- [Selectors, fields & namespaces](#selectors-fields--namespaces)
- [Watch](#watch)
- [The apply model (client- vs server-side)](#the-apply-model-client--vs-server-side)
- [diff](#diff)
- [rollout](#rollout)
- [scale / autoscale](#scale--autoscale)
- [exec / logs / cp / port-forward / proxy / attach](#exec--logs--cp--port-forward--proxy--attach)
- [debug (ephemeral containers / node / `--copy-to`)](#debug-ephemeral-containers--node---copy-to)
- [Node maintenance: drain / cordon / taint](#node-maintenance-drain--cordon--taint)
- [label / annotate](#label--annotate)
- [auth: can-i / whoami / reconcile](#auth-can-i--whoami--reconcile)
- [Discovery: api-resources / api-versions / explain](#discovery-api-resources--api-versions--explain)
- [config (contexts / namespaces / kubeconfig)](#config-contexts--namespaces--kubeconfig)
- [kustomize (`-k`)](#kustomize--k)
- [events](#events)
- [top](#top)
- [`--dry-run` (client vs server)](#--dry-run-client-vs-server)
- [wait](#wait)
- [`--subresource`](#--subresource)
- [Offline / no-cluster behavior](#offline--no-cluster-behavior)
- [plugins / krew](#plugins--krew)
- [Agent / scripting patterns](#agent--scripting-patterns)

---

## Resource verbs

The core CRUD set. `<r>` is a resource type (`pods`, `deploy`, `svc`, …; shortnames and
`TYPE[.VERSION][.GROUP]` forms are accepted), `<name>` an object name.

| Verb | What it does |
|------|--------------|
| `get` | List/print objects (table by default; reshape with `-o`) |
| `describe` | Human-readable detail + the object's **Events** (the #1 debugging clue) |
| `create` | Create from `-f` or a generator subcommand (`create deployment …`) — errors if it already exists |
| `apply` | Declarative create-or-update (the workhorse — see [apply model](#the-apply-model-client--vs-server-side)) |
| `delete` | Delete by `-f`, `<r> <name>`, or `-l <selector>` |
| `patch` | In-place partial update |
| `edit` | Open the **live** object in `$EDITOR`, then apply the change on save |
| `replace` | Replace the whole object from `-f` |

- **patch** — `--type=strategic\|merge\|json` (the `--help` lists exactly
  `[json merge strategic]`; **default `strategic`**). Supply the patch inline with
  `-p '<patch>'` / `--patch '<patch>'` or from `--patch-file <file>`. Works on a
  `--subresource` (e.g. `--subresource=scale`).
- **edit** — edits the live object; supports `--subresource=status|scale` and
  `-o yaml|json` to pick the edit format.
- **replace** — `kubectl replace -f f.yaml`; `--force` deletes and recreates the object
  (use when an immutable field changed). Also takes `--subresource`.

## Output formats (`-o`)

`get` (and most list/print commands) accept, per `--help`:

```
json  yaml  wide  name  go-template  go-template-file  template  templatefile
jsonpath  jsonpath-as-json  jsonpath-file  custom-columns  custom-columns-file
```

| Form | Use it for |
|------|-----------|
| `-o yaml` / `-o json` | Full object — pipe `json` to `jq`, `yaml` to read |
| `-o wide` | Table plus extra columns (node, IP, …) |
| `-o name` | `resource.group/name` — ideal for piping into `xargs kubectl …` |
| `-o jsonpath='{...}'` | Extract specific fields (see [scripting](#agent--scripting-patterns)) |
| `-o jsonpath-as-json='{...}'` | Like `jsonpath` but emits valid JSON (arrays/objects) |
| `-o jsonpath-file=f` | jsonpath template read from a file |
| `-o custom-columns=NAME:.metadata.name,…` | Pick columns by jsonpath into a table |
| `-o custom-columns-file=f` | Column spec from a file |
| `-o go-template='{{…}}'` / `-o go-template-file=f` | Full Go `text/template` |

Table-shaping flags (valid on `get`; they produce a table, so they need a server that
returns a list — see [offline note](#offline--no-cluster-behavior)):

- `--show-labels` — append a LABELS column.
- `-L label1,label2` / `--label-columns` — one column per named label.
- `--sort-by='<jsonpath>'` — e.g. `--sort-by=.metadata.creationTimestamp`.
- `--no-headers` — drop the header row (script-friendly).
- `--show-kind` — prefix each row with its kind.

> **`json`/`yaml`/`name`/`jsonpath`/`go-template` work on the offline `create … --dry-run=client`
> generator; the *table* formats (`wide`, `custom-columns`, `--show-labels`, `-L`,
> `--sort-by`) do not** — `create --dry-run=client -o custom-columns=…` errors with
> `unable to match a printer suitable for the output format`. Those are list/`get`
> table printers and require a cluster.

## Selectors, fields & namespaces

- **Label selector:** `-l key=val,key2!=val2` (also set-based `key in (a,b)`,
  `key notin (c)`, `key`, `!key`). Used by `get`/`delete`/`logs`/`label`/`drain`/… .
- **Field selector:** `--field-selector status.phase=Running,metadata.namespace=foo`
  (supports `=`, `==`, `!=` only; the server allows a limited set of fields per type).
- **Namespacing:** `-n <ns>` for one namespace; `-A` / `--all-namespaces` for all.

## Watch

- `-w` / `--watch` — stream changes after the initial list (blocks).
- `--watch-only` — stream changes **without** the initial list.
- `--output-watch-events` — wrap each item in its watch event (`ADDED`/`MODIFIED`/…);
  initial objects come through as `ADDED`.

## The apply model (client- vs server-side)

`kubectl apply` converges a live object toward the manifest you give it. There are two
merge engines:

- **Client-side apply (default).** kubectl stores your last-applied manifest in the
  `kubectl.kubernetes.io/last-applied-configuration` annotation and computes a **3-way
  merge** (last-applied ↔ your file ↔ live object) locally. The field manager defaults
  to `--field-manager='kubectl-client-side-apply'`.
- **Server-side apply (SSA), `--server-side`.** The API server tracks **field ownership**
  in `metadata.managedFields`; multiple appliers (controllers, you, CI) can co-own
  different fields of one object. SSA is **GA since 1.22** (so present and stable on
  1.28.2). Set a stable `--field-manager=<name>` per actor. Prefer SSA for
  controllers/automation and any object edited by more than one actor.
  - **Conflicts:** if you try to change a field another manager owns, SSA refuses with a
    conflict. `--force-conflicts` takes ownership and overrides it. (Both
    `--server-side` and `--force-conflicts` verified on 1.28.2; the latter also exists on
    `diff`.)

Other apply flags:

- `-k <dir>` / `--kustomize <dir>` — build a kustomization, then apply (see
  [kustomize](#kustomize--k)).
- `--overwrite=true` (default) — let apply overwrite values that diverge.
- `--dry-run=client|server|none` — preview without persisting (see
  [`--dry-run`](#--dry-run-client-vs-server)).

### `--prune` (dangerous — advanced only)

`kubectl apply --prune` **deletes live objects that are no longer in the applied set** —
the historical footgun of `apply`. On 1.28.2 the `--help` still prints
`Note: --prune is still in Alpha` / *"the --prune functionality is not yet complete"*.

- Always scope it: `--prune -l app=web` plus `--prune-allowlist=<group/version/kind>`
  (repeatable) to restrict which kinds may be pruned. (The flag is `--prune-allowlist`;
  note the `diff` help text still says "whitelist" in prose but the flag is the same.)
- **Run `--dry-run=client` first** and treat `--prune` as advanced/automation-only.

```bash
kubectl apply -f web.yaml                                  # client-side, default
kubectl apply --server-side -f web.yaml                    # SSA
kubectl apply --server-side --field-manager=ci -f web.yaml # stable owner id
kubectl apply --server-side --force-conflicts -f web.yaml  # seize contested fields
kubectl apply --prune -l app=web --prune-allowlist=core/v1/ConfigMap -f manifests/
```

## diff

`kubectl diff -f f.yaml` (or `-k dir/`) shows the **server-side delta** that `apply`
would make — it sends the object to the API for a dry-run merge and prints the diff.

- Honors `--server-side` and `--force-conflicts` (same semantics as apply).
- **Exit code 1 means "differences found"** (0 = no change, >1 = error) — useful as a
  CI drift gate.

## rollout

`kubectl rollout <subcommand> <type>/<name>` for Deployments/DaemonSets/StatefulSets.
All six subcommands verified on 1.28.2:

| Subcommand | Purpose / key flags |
|------------|---------------------|
| `status` | Watch until the rollout completes — **blocks by default** (`-w/--watch=true`); pass `--watch=false` for a one-shot snapshot. `--revision=N` pins a revision; `--timeout=<dur>` |
| `history` | List revisions; `--revision=N` shows one revision's pod-template detail |
| `undo` | Roll back; `--to-revision=N` targets a specific revision (0 = previous) |
| `pause` / `resume` | Stop / restart progressing a rollout (e.g. to batch several edits) |
| `restart` | Trigger a fresh rollout with **no spec change** — the way to pick up a changed mounted ConfigMap/Secret |

```bash
kubectl rollout status deploy/web                 # good CI gate (blocks)
kubectl rollout status deploy/web --watch=false   # snapshot, don't wait
kubectl rollout history deploy/web --revision=3
kubectl rollout undo deploy/web --to-revision=2
kubectl rollout restart deploy/web
```

## scale / autoscale

- **`kubectl scale deploy/web --replicas=5`** — set replica count. Guard with
  `--current-replicas=N` (only scale if it currently has N; default `-1` = no check),
  `--resource-version=<rv>`, and `--timeout=<dur>`. Both preconditions are validated
  server-side before the scale is sent.
- **`kubectl autoscale deploy/web --min=2 --max=10 --cpu-percent=80`** — create an HPA
  for a live workload (`--name=<hpa>` to name it). This targets an existing object, so
  it **contacts the cluster** — it is not an offline generator. (For richer HPA specs —
  `autoscaling/v2` metrics/behavior — author the manifest; see references/workloads.md.)

## exec / logs / cp / port-forward / proxy / attach

- **`exec`** — `kubectl exec -it <pod> [-c <container>] -- <cmd>`. `-i/--stdin`,
  `-t/--tty`, `-c/--container`.
- **`logs`** — `kubectl logs <pod>` and:
  - `-f/--follow` stream, `-p/--previous` the previous (crashed) container instance.
  - `-c/--container <c>`, `--all-containers` (all containers in the pod).
  - `-l/--selector <sel>` logs across matching pods (`--max-log-requests=5` cap).
  - `--since=<dur>` / `--since-time=<rfc3339>`, `--tail=<n>` (`-1` = all).
  - `--prefix` (prefix each line with pod/container), `--timestamps`.
  - Accepts a controller too: `kubectl logs -f deploy/web` picks one of its pods.
- **`cp`** — `kubectl cp <pod>:/path ./local` (and the reverse). Needs `tar` in the
  container. `-c/--container`, `--no-preserve` (don't keep file mode/ownership),
  `--retries=N`.
- **`port-forward`** — `kubectl port-forward (pod|svc|deploy)/<name> [LOCAL:]REMOTE`.
  `--address=localhost` (repeatable/CSV; e.g. `0.0.0.0` to expose),
  `--pod-running-timeout=1m`.
- **`proxy`** — `kubectl proxy --port=8001` runs an authenticated reverse proxy to the
  API (`--address=127.0.0.1`, `--api-prefix=/`, `--www`/`-w` to also serve static
  files, `--www-prefix`). Then e.g. `curl localhost:8001/api/v1/namespaces`.
- **`attach`** — attach to a running container's stdio (`kubectl attach -it <pod>`); the
  lighter cousin of `exec` when you want the existing process, not a new one.

## debug (ephemeral containers / node / `--copy-to`)

`kubectl debug` is **GA since 1.25** (ephemeral containers GA 1.25). Verified on 1.28.2;
flags: `--image`, `-c/--container`, `--target`, `--copy-to`, `--replace`,
`--same-node`, `--set-image`, `--share-processes` (default `true`),
`--profile` (default `legacy`), `--env`, `--image-pull-policy`, `--attach`,
`-i/--stdin`, `-t/--tty`.

```bash
# Inject an ephemeral debug container into a running pod, sharing another container's pid ns
kubectl debug -it <pod> --image=busybox --target=<container>

# Debug a node — runs a privileged pod with the node FS mounted at /host
kubectl debug node/<node> -it --image=busybox

# Copy a crashing pod with a changed command/image so it stays up to poke at
kubectl debug <pod> -it --copy-to=<new> --container=<c> -- sh
kubectl debug <pod> --copy-to=<new> --set-image=*=busybox
```

`--replace` (with `--copy-to`) deletes the original pod; `--same-node` schedules the
copy on the original's node.

## Node maintenance: drain / cordon / taint

Adjacent to cluster admin — keep light; pairs with k3s/kubeadm node lifecycle.

- **`cordon <node>` / `uncordon <node>`** — mark a node un/schedulable (no eviction).
- **`drain <node>`** — evict pods for maintenance. Common flags:
  `--ignore-daemonsets` (required if DaemonSet pods present), `--delete-emptydir-data`
  (required if any pod uses an emptyDir), `--force` (also evict unmanaged/bare pods),
  `--grace-period=<sec>`, `--timeout=<dur>`, `--disable-eviction` (use raw DELETE
  instead of the eviction API — bypasses PDBs; dangerous), `-l/--selector`,
  `--pod-selector`.
- **`taint nodes <node> key=value:Effect`** — add/remove a taint
  (`Effect` ∈ `NoSchedule|PreferNoSchedule|NoExecute`); pairs with pod `tolerations`
  (see references/workloads.md). `--overwrite`, `--all`, `-l/--selector`. Remove with a
  trailing `-`: `kubectl taint nodes <node> key=value:NoSchedule-`.

```bash
kubectl drain node-1 --ignore-daemonsets --delete-emptydir-data
kubectl taint nodes node-1 dedicated=gpu:NoSchedule
```

## label / annotate

Same flag shape for both:

```bash
kubectl label <r> <name> key=val [key2-]            # key2- removes a label
kubectl annotate <r> <name> key='some value'
```

- `--overwrite` — required to change an existing key (otherwise it errors).
- `--all` (every object of the type), `-l/--selector`, `-A/--all-namespaces`.
- `--resource-version=<rv>` — optimistic-concurrency guard.
- `--list` — print current labels/annotations instead of changing them.
- Remove a key with a trailing `-` (`key-`).

## auth: can-i / whoami / reconcile

- **`auth can-i <verb> <resource>`** — does the current user (or impersonated subject)
  have permission?
  - `--subresource=<sub>` (e.g. `--subresource=log`), `-n <ns>`, `-A/--all-namespaces`.
  - `--list` — print **everything** you can do in the namespace.
  - `-q/--quiet` — no output; exit code only (script gate).
  - Impersonation uses the **global** flags `--as=<user>`, `--as-group=<grp>`
    (repeatable), `--as-uid=<uid>` — these live in `kubectl options`, not in
    `can-i --help`.
  - `VERB` is an API verb (`get`, `list`, `watch`, `create`, `update`, `patch`,
    `delete`); a `NONRESOURCEURL` starting with `/` is also accepted.
- **`auth whoami`** — print your resolved user/groups/extra. Marked **Experimental** in
  1.28 (`whoami` header literally says "Experimental").
- **`auth reconcile -f rbac.yaml`** — safely create/update RBAC `Role`/`ClusterRole`/
  bindings, computing the union of rules/subjects. `--remove-extra-permissions` /
  `--remove-extra-subjects` prune anything not in the input.

```bash
kubectl auth can-i create deployments
kubectl auth can-i list pods --as=system:serviceaccount:dev:foo -n prod
kubectl auth can-i get pods --subresource=log
kubectl auth can-i --list --namespace=foo
kubectl auth whoami
```

## Discovery: api-resources / api-versions / explain

- **`api-resources`** — the live GVK map (what `kind`s exist, shortnames, namespaced?,
  verbs). Flags: `--namespaced=true|false`, `--api-group=<group>`,
  `--verbs=list,get`, `--categories=<cat>`, `-o name|wide`, `--no-headers`,
  `--sort-by=name|kind`, `--cached` (use the discovery cache).
- **`api-versions`** — enabled `group/version`s on the server.
- **`explain <type>[.<path>]`** — field docs from the server's OpenAPI schema.
  `--recursive` (full tree), `--api-version=apps/v1` (pin the GVK),
  `--output=plaintext|plaintext-openapiv2`. On **1.28** the OpenAPI **v3**-backed explain
  is the default (the `KUBECTL_EXPLAIN_OPENAPIV3` toggle was removed as redundant —
  CHANGELOG-1.28); pass `--output=plaintext-openapiv2` to force the old schema source.

```bash
kubectl api-resources --namespaced=false           # cluster-scoped kinds
kubectl api-resources --api-group=apps -o name
kubectl explain deploy.spec.template.spec.containers --recursive
```

> `api-resources`/`api-versions`/`explain` all read schema **from the server** — they
> need a reachable cluster.

## config (contexts / namespaces / kubeconfig)

Edits `~/.kube/config` (or `$KUBECONFIG`, which may be a `:`-separated merge list).
**These commands edit local files and work with no cluster.** Subcommands:
`get-contexts`, `use-context`, `current-context`, `set-context`, `view`,
`get-clusters`, `set-cluster`, `set-credentials`, `rename-context`, `delete-context`,
`set`, `unset`.

```bash
kubectl config get-contexts                              # list; * marks current
kubectl config current-context
kubectl config use-context <ctx>                         # switch cluster
kubectl config set-context --current --namespace=<ns>    # change default namespace
kubectl config view --minify                             # only the current context
kubectl config view --minify --flatten -o yaml           # self-contained export
kubectl config view --raw                                # include secrets (don't paste)
```

- `set-context [NAME|--current] [--cluster=] [--user=] [--namespace=]`.
- `view` flags: `--minify` (just the current context), `--flatten` (inline file refs),
  `--raw` (un-redact credentials), `-o yaml|json|jsonpath=…`.
- `kubectx`/`kubens` are popular third-party helpers for the first two — not part of
  kubectl.

## kustomize (`-k`)

kubectl bundles **kustomize v5.0.4** (in 1.28.2).

```bash
kubectl kustomize overlays/prod/        # render the built manifests to stdout
kubectl apply -k overlays/prod/         # build, then apply
kubectl diff -k overlays/prod/          # build, then diff
```

`kubectl kustomize` flags include `-o <file>` (write instead of stdout),
`--enable-helm` (allow the Helm chart inflator), `--load-restrictor` (default
`LoadRestrictionsRootOnly`). `-k` is accepted by `apply`, `diff`, `get`, `delete`.

## events

`kubectl events` is the **standalone** events command — promoted from
`kubectl alpha events` (alpha 1.23) to `kubectl events` in **1.26** (verified present in
1.28.2). Flags: `--for <type>/<name>`, `-w/--watch`, `--types=Warning,Normal`,
`-A/--all-namespaces`, `--no-headers`, `-o json|yaml|name|jsonpath…`.

```bash
kubectl events --for pod/web-0 --watch
kubectl events --types=Warning -A
```

> **No `--sort-by` on `kubectl events`** in 1.28.2 (it has no such flag). For
> time-sorted events use the bedrock `kubectl get events --sort-by=.lastTimestamp`,
> which still works.

## top

`kubectl top pod|node` — live CPU/memory usage. **Requires metrics-server** in the
cluster (k3s bundles it).

- `top pod`: `--containers` (per-container rows), `-l/--selector`, `-A`, `--sort-by`,
  `--no-headers`.
- `top node`: `--sort-by`, `-l/--selector`, `--no-headers`.

## `--dry-run` (client vs server)

A per-command flag (`--dry-run=none|client|server`; **not** a global option):

- **`--dry-run=client`** — render/validate **locally**, print, don't submit. For pure
  generators (`create deployment …`, `create configmap …`) this needs no cluster.
- **`--dry-run=server`** — submit to the API server which runs **validation +
  admission** (including mutating webhooks) and returns the would-be object **without
  persisting**. Needs a cluster.

Available on `apply`, `create`, `patch`, `replace`, `set`, etc.

## wait

Block until a condition holds — invaluable in CI/scripts.

```bash
kubectl wait --for=condition=Available deploy/web --timeout=120s
kubectl wait --for=condition=Ready pod -l app=web --timeout=60s
kubectl wait --for=delete pod/busybox1 --timeout=60s
kubectl wait --for=jsonpath='{.status.phase}'=Running pod/web-0   # jsonpath form
```

`--for=condition=<cond>[=true|false]`, `--for=delete`, and
`--for=jsonpath='{path}'[=value]` (jsonpath form verified present in 1.28). `--all`,
`-l/--selector`, `-A`, `--timeout` (default `30s`).

## `--subresource`

`get`/`patch`/`edit`/`replace --subresource=status|scale` manipulate a subresource
directly (e.g. patch `scale` without touching the rest of the spec). The CLI flag is
**alpha 1.24, beta 1.27** — present and usable in 1.28.2.

```bash
kubectl get deploy web --subresource=scale -o yaml
kubectl patch deploy web --subresource=scale --type=merge -p '{"spec":{"replicas":2}}'
```

## Offline / no-cluster behavior

Most kubectl commands hit the API server. What works with **no cluster** (verified
client-side here):

- **kubeconfig edits:** the entire `kubectl config …` family.
- **Pure generators** with `--dry-run=client -o yaml|json|name|jsonpath|go-template`:
  | `kubectl create …` | emits |
  |---|---|
  | `deployment` | `apps/v1` |
  | `job`, `cronjob` | `batch/v1` |
  | `service …`, `configmap`, `secret …`, `serviceaccount`, `namespace`, `quota` | `v1` |
  | `rolebinding`, `clusterrolebinding` | `rbac.authorization.k8s.io/v1` |
  | `ingress` | `networking.k8s.io/v1` |
  | `poddisruptionbudget` | `policy/v1` |
  | `priorityclass` | `scheduling.k8s.io/v1` |

  Generate, redirect, edit, then apply: `kubectl create deployment web --image=nginx \
  --dry-run=client -o yaml > web.yaml`.

> **⚠️ Not offline generators — these contact the API server even under
> `--dry-run=client`** (they resolve resource/GVR mappings server-side). With no cluster
> they hang until they time out (`Unable to connect to the server: … i/o timeout`),
> verified here:
> - **`kubectl run`**
> - **`kubectl expose`**
> - **`kubectl create role --resource=…`** and **`create clusterrole --resource=…`**
>   (resolving the named resources requires discovery)
> - **`kubectl autoscale`** (targets a live workload)
>
> So for offline manifest generation, prefer `kubectl create <kind>` (the table above)
> over `run`/`expose`, and write `Pod`/`Role` manifests by hand or via the kinds that do
> generate offline.
>
> Likewise, the **table** output formats (`-o wide`, `-o custom-columns=…`,
> `--show-labels`, `-L`, `--sort-by`) are list/`get` printers that need a cluster — only
> `yaml/json/name/jsonpath/go-template` render on the offline generator.

## plugins / krew

- **`kubectl plugin list`** — list `kubectl-*` executables found on `$PATH`. Any such
  binary is callable as `kubectl <name>` (`kubectl-foo` → `kubectl foo`).
- **krew** is the community plugin **manager** (`kubectl krew install <plugin>`) — a
  third-party plugin itself. Mention it; it is not built in.

## Agent / scripting patterns

For machine consumption, prefer structured output and explicit selection over parsing
human tables.

- **jsonpath, with correct quoting.** Wrap the template in **single quotes** so the
  shell doesn't eat `{}`/`$`; use `\t`/`\n` inside; `range` to iterate:
  ```bash
  kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
  kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'
  ```
  Use `-o jsonpath-as-json` when you need valid JSON (arrays/maps) back out.
- **`-o name` → pipe.** Stable `resource.group/name` lines feed `xargs`/loops:
  ```bash
  kubectl get pods -l app=web -o name | xargs -I{} kubectl logs {} --tail=20
  kubectl get pods --field-selector=status.phase=Failed -o name | xargs kubectl delete
  ```
- **`--no-headers`** for clean column extraction:
  ```bash
  kubectl get pods --no-headers -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName
  ```
- **`-o json | jq`** when jsonpath gets awkward:
  ```bash
  kubectl get pods -o json | jq -r '.items[] | select(.status.phase!="Running") | .metadata.name'
  ```
- **Exit codes as gates.** `auth can-i -q` (0 = allowed), `diff` (1 = drift found),
  `wait`/`rollout status` (non-zero on timeout) all script cleanly.
- **Always pin the namespace/context** in automation: pass `-n <ns>` and
  `--context <ctx>` explicitly rather than relying on the current-context, and prefer
  SSA with a stable `--field-manager` so ownership is attributable.
- **`--dry-run=client` + `diff`/`wait`** before mutating: render → `diff` → `apply` →
  `rollout status`/`wait` is the safe CI cycle.
