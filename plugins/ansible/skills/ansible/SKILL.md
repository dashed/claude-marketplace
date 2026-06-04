---
name: ansible
description: ansible-core — the agentless, push-based, SSH automation engine that runs idempotent tasks from declarative YAML playbooks. Use when writing or running Ansible playbooks, issuing ad-hoc commands (`ansible -m`), managing INI/YAML inventory, authoring roles, installing collections with `ansible-galaxy`, encrypting secrets with Ansible Vault, tuning `ansible.cfg`, looking up module docs with `ansible-doc`, or provisioning/configuring hosts idempotently over SSH. Covers the ten `ansible*` CLIs, FQCN (`ansible.builtin.*`), become/privilege escalation, inventory patterns, variable precedence, check/diff mode, and strategies. Triggers on mentions of ansible, ansible-playbook, ansible-galaxy, ansible-vault, ansible-inventory, ansible.cfg, playbooks, roles, collections, or Ansible Vault. This is ansible-core (the engine + `ansible.builtin`), NOT generic configuration-management theory and NOT the bundled community `ansible` package's collection modules.
---

# ansible-core - Agentless Automation Engine

## Overview

ansible-core is the automation **engine**: you describe desired state in declarative YAML
**playbooks**, and it connects to managed hosts (by default over **SSH**, **push**-based) and
runs **modules** that converge each host to that state. It is **agentless** — nothing is
installed on the targets beyond Python and SSH; the controller pushes and executes module code,
then cleans up. Well-written modules are **idempotent**: re-running a playbook reports `changed`
only when something actually changed.

**Key characteristics:**
- **Agentless / push / SSH** — controller connects out to hosts; no daemon on the targets
- **Declarative YAML** — plays map a host pattern to an ordered list of tasks (modules + args)
- **Idempotent** — converge to desired state; safe to re-run; `--check` predicts, `--diff` shows
- **Inventory-driven** — hosts and groups come from INI/YAML inventory (or dynamic plugins)
- **FQCN-addressed** — builtin content is `ansible.builtin.<name>`; everything else ships as a
  Galaxy **collection** you install separately

> **ansible-core vs the community `ansible` package:** *ansible-core* is the engine plus the
> **`ansible.builtin`** content set (the modules/plugins bundled in this repo). The community
> **`ansible`** package (v9/10/11…) is a curated bundle of ansible-core **plus hundreds of
> collections** (`community.general`, `ansible.posix`, `community.docker`, …). When a user
> "installs ansible" they may have either. Anything beyond `ansible.builtin` requires
> `ansible-galaxy collection install <ns.coll>`. **Always FQCN non-builtin content.**

> **Disambiguation:** This skill documents **ansible-core and its `ansible*` CLIs** — playbooks,
> inventory, roles, collections, vault, config, become, and the engine's behavior. It is **not**
> a course in generic config-management theory, and it does **not** enumerate the thousands of
> collection modules — for those, use `ansible-doc -l` and `ansible-doc <fqcn>`.

## When to Use This Skill

Use this skill when:
- **Writing/running playbooks**: `ansible-playbook site.yml -i inventory.ini`
- **Ad-hoc commands**: `ansible web -m ansible.builtin.ping`, `ansible all -a 'uptime'`
- **Managing inventory**: INI or YAML hosts/groups, `group_vars/`, `host_vars/`, `--limit`
- **Authoring roles**: `tasks/`, `handlers/`, `defaults/`, `vars/`, `templates/`, `meta/`
- **Collections**: `ansible-galaxy collection install`, `requirements.yml`, FQCN resolution
- **Secrets**: Ansible Vault (`ansible-vault encrypt`/`encrypt_string`, `--vault-id`)
- **Configuration**: `ansible.cfg` discovery/precedence, `ansible-config dump`
- **Privilege escalation**: `become`, `--become-method` (sudo/su/runas), `-K`
- **Module discovery**: `ansible-doc -l`, `ansible-doc <fqcn>`, `ansible-doc -s`
- **Idempotent provisioning**: dry-run with `--check`, inspect with `--diff`

## Prerequisites

**CRITICAL**: Before proceeding, verify ansible-core is installed and check the version:

```bash
ansible --version        # prints "ansible [core 2.21.x]", config file, python/jinja versions
```

**Version note:** This skill is documented against **ansible-core 2.21** (the latest released
core; the reference clone is a `2.22.0.dev0` development checkout, so 2.22 features are treated
as unreleased). Long-standing flags work on any recent core; features added in a specific
release are annotated inline as `(ansible-core X.Y+)` **only where the source declares a
`version_added`**. Bedrock flags (the bulk of the CLI) are left unannotated. Confirm on the
running system with `ansible --version` and `<binary> --help`.

**If ansible-core is not installed:** do **NOT** silently auto-install. Recommend a user-scoped
install and let the user choose engine-only vs the full bundle:

```bash
# Just the engine + ansible.builtin (recommended for CI / lean controllers)
pipx install ansible-core          # or: pip install --user ansible-core

# The full community bundle (ansible-core + curated collections)
pipx install ansible               # or: pip install --user ansible

# System packages also exist (apt/dnf "ansible" or "ansible-core"); versions lag pip
```

`pipx` keeps ansible in an isolated venv with the `ansible*` shims on `PATH` — preferred over a
global `pip install`.

## The `ansible*` Binaries

Ten executables ship in `bin/`; each is a thin launcher over `lib/ansible/cli/<name>.py`.

| Binary | Purpose |
|--------|---------|
| `ansible` | **Ad-hoc** — run a single module against a host pattern (`-m`/`-a`) |
| `ansible-playbook` | Run **playbooks** (the primary workhorse) |
| `ansible-inventory` | Inspect/validate inventory: `--list`, `--graph`, `--host` |
| `ansible-galaxy` | Install/manage **collections** and **roles** (`requirements.yml`) |
| `ansible-vault` | Encrypt/decrypt secrets: `create`, `encrypt`, `encrypt_string`, `view`, `rekey` |
| `ansible-doc` | Plugin/module documentation: `-l` (list), `-s` (snippet), `-t TYPE` |
| `ansible-config` | View/dump/generate config: `list`, `dump`, `view`, `init`, `validate` |
| `ansible-console` | Interactive REPL that runs modules against a host pattern |
| `ansible-pull` | **Pull** mode — host clones a repo and runs a playbook on itself (cron/scale) |
| `ansible-test` | Dev/CI test runner for collections (shipped separately; out of scope here) |

Every binary shares flag groups (verbosity `-v`…`-vvvvvv`, inventory, connection, become,
vault, …). For the exhaustive per-binary flag set, see **[references/cli.md](references/cli.md)**.

## Mental Model

```
inventory ──> playbook ──> plays ──> tasks ──> modules (FQCN) ──> managed hosts (SSH)
   hosts        YAML        hosts:    name:     ansible.builtin.*    idempotent change
   & groups               + tasks    module:                        (check/diff preview)
```

1. **Inventory** names your hosts and arranges them into **groups** (`all` and `ungrouped` are
   implicit). INI and YAML are the two hand-written formats.
2. A **playbook** is a list of **plays**; each play binds a **host pattern** (`hosts:`) to an
   ordered list of **tasks** (plus `pre_tasks`, `roles`, `post_tasks`, `handlers`).
3. Each **task** invokes one **module** by **FQCN** (`ansible.builtin.copy`) with arguments.
4. **Idempotency**: modules converge to desired state and report `changed` only on real change.
   **`--check`** predicts changes without applying; **`--diff`** shows what would change.
5. **FQCN**: builtin content is `ansible.builtin.<name>`; bare names resolve via `ansible.legacy`
   (local `library/` overrides, then builtin). Non-builtin content needs its collection installed.

## Core Workflows

### 1. Ad-hoc command (one module, no playbook)

```bash
# Default module is `command`; -a passes its args
ansible all -i inventory.ini -m ansible.builtin.ping
ansible web -i inventory.ini -m ansible.builtin.shell -a 'systemctl status nginx'
ansible all -i inventory.ini -a 'uptime'                 # implicit -m command

# With privilege escalation (prompt for the sudo password with -K)
ansible db -i inventory.ini -b -K -m ansible.builtin.apt -a 'name=htop state=present'
```

`-i` accepts a path **or** a comma-separated host list (note the trailing comma):
`ansible all -i 'host1.example.com,' -m ping`.

### 2. Inventory basics (INI and YAML)

```ini
# inventory.ini
[web]
web1.example.com
web2.example.com ansible_host=10.0.0.12

[db]
db1.example.com

[prod:children]      # a group of groups
web
db

[web:vars]
ansible_user=deploy
```

```yaml
# inventory.yml  (auto-detected by the `auto` plugin via the top-level groups)
all:
  children:
    web:
      hosts:
        web1.example.com:
        web2.example.com:
          ansible_host: 10.0.0.12
      vars:
        ansible_user: deploy
    db:
      hosts:
        db1.example.com:
```

Variables also live in **`group_vars/<group>.yml`** and **`host_vars/<host>.yml`** beside the
inventory or the playbook. Inspect what Ansible parsed:

```bash
ansible-inventory -i inventory.yml --list          # full JSON
ansible-inventory -i inventory.yml --graph --vars   # tree view with vars
ansible-inventory -i inventory.yml --host web1.example.com
```

### 3. First playbook + the common run flags

```yaml
# site.yml
- name: Configure web servers
  hosts: web
  become: true                      # privilege-escalate for the whole play
  tasks:
    - name: Install nginx
      ansible.builtin.package:
        name: nginx
        state: present
    - name: Deploy config
      ansible.builtin.template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: restart nginx          # fires the handler only if this task changed
  handlers:
    - name: restart nginx
      ansible.builtin.service:
        name: nginx
        state: restarted
```

```bash
ansible-playbook site.yml -i inventory.yml            # run it
ansible-playbook site.yml -i inventory.yml --syntax-check   # parse only
ansible-playbook site.yml -i inventory.yml --check --diff   # dry-run + show diffs
ansible-playbook site.yml -i inventory.yml --limit web1     # subset of hosts
ansible-playbook site.yml -i inventory.yml --tags deploy    # only tagged tasks
ansible-playbook site.yml -i inventory.yml -b -K            # become + prompt sudo pass
ansible-playbook site.yml -i inventory.yml -e env=prod      # extra vars (highest precedence)
ansible-playbook site.yml -i inventory.yml -e @vars.yml     # extra vars from a file
ansible-playbook site.yml -i inventory.yml -vvv             # verbose (repeat up to -vvvvvv)
```

### 4. Privilege escalation (become)

```bash
ansible-playbook site.yml -b                       # become: true on the CLI
ansible-playbook site.yml -b --become-user postgres   # escalate to a specific user
ansible-playbook site.yml -b --become-method su -K    # use su instead of sudo, prompt pass
```

Builtin become methods are **`sudo`** (default), **`su`**, and **`runas`** (Windows). Others
(`doas`, `pbrun`, …) live in collections. Prompt for the password with **`-K`**/`--ask-become-pass`.

### 5. Collections via ansible-galaxy + requirements.yml

```yaml
# requirements.yml
collections:
  - name: community.general
  - name: ansible.posix
    version: ">=1.5.0"
roles:
  - src: geerlingguy.nginx
```

```bash
ansible-galaxy collection install -r requirements.yml      # install collections + roles…
ansible-galaxy install -r requirements.yml                 # …(role-file form)
ansible-galaxy collection install community.general --upgrade
ansible-galaxy collection list                             # what's installed + where
ansible-galaxy collection init my_namespace.my_collection  # scaffold a new collection
ansible-galaxy role init my_role                           # scaffold a new role
```

Collections install under `COLLECTIONS_PATHS` (default `~/.ansible/collections:/usr/share/...`).

### 6. Ansible Vault (secrets)

```bash
ansible-vault create secrets.yml                  # new encrypted file (opens $EDITOR)
ansible-vault encrypt existing.yml                # encrypt in place
ansible-vault view secrets.yml                    # read without decrypting to disk
ansible-vault edit secrets.yml                    # edit in place
ansible-vault rekey secrets.yml                   # change the password
ansible-vault encrypt_string 's3cr3t' -n db_pass  # inline !vault blob for one variable

# Run a playbook that uses vaulted data
ansible-playbook site.yml --ask-vault-pass                       # -J, prompt interactively
ansible-playbook site.yml --vault-password-file ~/.vault-pass    # password file (or script)
ansible-playbook site.yml --vault-id prod@prompt --vault-id dev@~/.dev-pass   # labeled vaults
```

Whole files **or** single inline variables (`encrypt_string`) can be vaulted and are loaded
transparently at runtime. `--ask-vault-pass` and `--vault-password-file` are mutually exclusive
per invocation. `VAULT_ENCRYPT_SALT` (ansible-core 2.15+) pins the salt for deterministic output.

### 7. Discover modules and plugins with ansible-doc

```bash
ansible-doc -l                            # list all modules (defer to this — do NOT memorize)
ansible-doc -l -t become                  # list plugins of a type (become/callback/lookup/…)
ansible-doc ansible.builtin.copy          # full docs for one module
ansible-doc -s ansible.builtin.copy       # short "playbook snippet" form
ansible-doc -t lookup ansible.builtin.env # docs for a non-module plugin
```

## ansible.cfg Essentials

Settings live in `ansible.cfg`. **Discovery order — first found wins** (it does **not** merge):

1. **`$ANSIBLE_CONFIG`** (a file, or a dir containing `ansible.cfg`)
2. **`./ansible.cfg`** (cwd — *skipped with a warning if cwd is world-writable*)
3. **`~/.ansible.cfg`**
4. **`/etc/ansible/ansible.cfg`**

Every option also has an **environment variable** (env overrides the ini file). Generate a fully
commented starter file:

```bash
ansible-config init --disabled > ansible.cfg     # all options, commented out
ansible-config dump --only-changed               # show settings that differ from defaults
ansible-config list                              # every option with its ini key/env/default
```

```ini
# ansible.cfg
[defaults]
inventory = ./inventory.yml
remote_user = deploy
host_key_checking = True
forks = 5
strategy = linear

[privilege_escalation]
become = True
become_method = sudo
```

> **Variable precedence (low → high), abbreviated:** role `defaults/` (weakest) → group_vars →
> host_vars → host facts → play vars → `vars_files` → role `vars/` → block/task vars →
> `include_vars` → `set_fact`/registered → role/include params → **`-e` extra vars (always win)**.
> Key rules to remember: **`-e` overrides everything; role `defaults/` are the weakest.** The
> canonical 22-tier list is in the official docs; see [references/cli.md](references/cli.md) and
> the config/vault reference for the source-verified backbone.

## Quick Reference

| Flag / item | Purpose |
|-------------|---------|
| `-i`/`--inventory` | Inventory path **or** comma-host-list (repeatable) |
| `-m`/`--module-name`, `-a`/`--args` | (ad-hoc) module + its `k=v`/JSON args |
| `-l`/`--limit` | Restrict the run to a host subset/pattern |
| `-t`/`--tags`, `--skip-tags` | Run / skip tagged plays & tasks |
| `-C`/`--check`, `-D`/`--diff` | Dry-run (predict) / show file diffs |
| `-b`/`--become`, `--become-method`, `--become-user` | Privilege escalation (sudo/su/runas) |
| `-K`/`--ask-become-pass` | Prompt for the become (sudo) password |
| `-e`/`--extra-vars` | Extra vars (`@file` to load); **highest precedence** |
| `-f`/`--forks` | Parallelism (default 5) |
| `-u`/`--user`, `-c`/`--connection`, `-k`/`--ask-pass` | Remote user / transport / prompt SSH pass |
| `--syntax-check`, `--list-tasks`, `--list-hosts`, `--list-tags` | Inspect a playbook without running |
| `--start-at-task`, `--step` | Resume at a task / confirm each task |
| `-J`/`--ask-vault-pass`, `--vault-password-file`, `--vault-id` | Vault secret sources |
| `-v` … `-vvvvvv` | Increasing verbosity (`-vvv` shows the SSH/connection detail) |

## Advanced Usage

For exhaustive, source-verified detail, see the bundled reference files:

- **[references/cli.md](references/cli.md)** — complete per-binary flag reference (every
  `ansible*` CLI, grouped by shared flag groups + unique flags)
- **[references/playbooks.md](references/playbooks.md)** — playbook anatomy: plays, tasks,
  handlers/`notify`/`listen`, blocks/`rescue`/`always`, roles, loops, conditionals, delegation,
  strategies (`linear`/`free`/`host_pinned`/`debug`)
- **[references/config-vault.md](references/config-vault.md)** — `ansible.cfg` keys, full
  variable-precedence list, FQCN/`ansible.legacy`, inventory plugins/patterns, Vault mechanics
- **[references/version-features.md](references/version-features.md)** — which ansible-core
  version introduced each annotated feature (minimum-version lookup)

## Troubleshooting

**"Command not found: ansible"** — ansible-core isn't installed or its venv isn't on `PATH`.
See Prerequisites. Do **NOT** auto-install on someone's machine.

**SSH / connection failures** — re-run with **`-vvv`** to see the exact SSH command and error.
Common causes: wrong `ansible_user` / `remote_user`, missing key (`--private-key`), unknown host
key (`host_key_checking = True` by default — add the key to `known_hosts` rather than disabling).

**`become`/sudo failures** — a password is needed: add **`-K`**/`--ask-become-pass`. Check
`--become-method` (sudo/su/runas) and `--become-user`. Verify the remote user may escalate.

**"couldn't resolve module/action" / FQCN not found** — the content's **collection isn't
installed**. Builtin is `ansible.builtin.<name>`; everything else needs
`ansible-galaxy collection install <ns.coll>`. List installed collections with
`ansible-galaxy collection list`, and confirm the module exists with `ansible-doc -l | grep <name>`.

**Task always reports `changed`** — the module call isn't idempotent (often `command`/`shell`
with no `creates:`/`removes:` guard, or `changed_when:`). Prefer a purpose-built module; predict
with `--check` and inspect with `--diff`.

**Vault errors ("Attempting to decrypt … no vault secrets")** — supply a password source:
`--ask-vault-pass` (`-J`), `--vault-password-file FILE`, or a matching `--vault-id LABEL@SOURCE`.

**A flag from older docs is missing** — features carry a minimum version. Confirm with
`<binary> --help` on the running version, or see
[references/version-features.md](references/version-features.md).

## Resources

- **Help**: `ansible --help`, `ansible-playbook --help`, `<binary> --help`
- **Module/plugin docs**: `ansible-doc -l`, `ansible-doc <fqcn>`, `ansible-doc -s <fqcn>`
- **Config introspection**: `ansible-config list` / `dump` / `init --disabled`
- **Official docs**: https://docs.ansible.com/ansible-core/
- **Galaxy (collections/roles)**: https://galaxy.ansible.com
- **Source**: https://github.com/ansible/ansible
