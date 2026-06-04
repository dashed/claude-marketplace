# ansible-core CLI Reference

Complete flag reference for the ten `ansible*` binaries, derived from the engine source
(`lib/ansible/cli/*.py` and the shared option helpers in
`lib/ansible/cli/arguments/option_helpers.py`).

> **Version annotations:** Flags marked `(ansible-core X.Y+)` carry a maintainer-declared
> `version_added` in the source. The **vast majority of CLI flags are bedrock** (present at or
> before 2.10) and are left unannotated. Deprecations the source declares are noted inline
> (e.g. *deprecated, removal 2.23*). This reference is documented against **ansible-core 2.21**
> (the reference clone is `2.22.0.dev0`; treat 2.22 items as unreleased). Confirm on your system
> with `ansible --version`, then `<binary> --help`.

## Shared flag groups

Each binary is assembled from reusable **option groups**. When a binary "has inventory options,"
it gets the whole group below. The per-binary sections list which groups apply plus that
binary's unique flags.

| Group | Flags (short / long) | Notes / default |
|-------|----------------------|-----------------|
| **base** | `--version` | prints `prog [core X]`, config file, module search path, python/jinja/pyyaml versions |
| **verbosity** | `-v`/`--verbose` (repeatable) | up to `-vvvvvv`; `-vvv` shows connection/SSH detail |
| **async** | `-P`/`--poll`, `-B`/`--background` | poll interval / run async, failing after N seconds (default 0 = not async) |
| **basedir** | `--playbook-dir` | act as if a playbook lived here (sets `roles/`, `group_vars/` relative root) for playbook-less tools |
| **check** | `-C`/`--check`, `-D`/`--diff` | dry-run (predict) / show file diffs |
| **connect** | `--private-key`/`--key-file`, `-u`/`--user`, `-c`/`--connection`, `-T`/`--timeout`, `--ssh-common-args`, `--sftp-extra-args`, `--scp-extra-args`, `--ssh-extra-args`, `-k`/`--ask-pass`, `--connection-password-file`/`--conn-pass-file` | default connection `ssh`; `-k` and `--conn-pass-file` are mutually exclusive |
| **fork** | `-f`/`--forks` | parallel hosts, default `5` |
| **inventory** | `-i`/`--inventory` (repeatable), `--list-hosts`, `-l`/`--limit`, `--flush-cache` | `-i` takes a path **or** a comma-separated host list; `--inventory-file` alias is *deprecated, removal 2.23* |
| **meta** | `--force-handlers` | run handlers even if a task fails on a host |
| **module** | `-M`/`--module-path` | prepend colon-separated local module path(s) |
| **output** | `-o`/`--one-line`, `-t`/`--tree` | *both deprecated, removal 2.23* (→ `oneline`/`tree` callbacks) |
| **runas/become** | `-b`/`--become`, `--become-method` (default `sudo`), `--become-user` | privilege escalation |
| **runas-prompt** | `-K`/`--ask-become-pass`, `--become-password-file`/`--become-pass-file` | mutually exclusive |
| **runtask** | `-e`/`--extra-vars` (repeatable; `@file` to load) | **highest** variable precedence |
| **tasknoplay** | `--task-timeout` | seconds, positive int |
| **subset/tags** | `-t`/`--tags`, `--skip-tags` | run / skip tagged plays & tasks |
| **vault** | `--vault-id` (repeatable), `-J`/`--ask-vault-password`/`--ask-vault-pass`, `--vault-password-file`/`--vault-pass-file` (repeatable) | `-J` and `--vault-password-file` are mutually exclusive |

> **Beware the overloaded short flags.** `-t` is `--tags` for `ansible`/`ansible-playbook` but
> `--type` for `ansible-doc`/`ansible-config` and `--tree` in the (deprecated) output group.
> `-o` is `--one-line` for `ansible` but `--only-if-changed` for `ansible-pull`. Always read the
> per-binary section.

## Table of Contents

- [ansible (ad-hoc)](#ansible-ad-hoc)
- [ansible-playbook](#ansible-playbook)
- [ansible-galaxy](#ansible-galaxy)
- [ansible-vault](#ansible-vault)
- [ansible-inventory](#ansible-inventory)
- [ansible-doc](#ansible-doc)
- [ansible-config](#ansible-config)
- [ansible-console](#ansible-console)
- [ansible-pull](#ansible-pull)
- [ansible-test (note)](#ansible-test-note)

---

## `ansible` (ad-hoc)

Run a single module against a host pattern — no playbook. Source: `lib/ansible/cli/adhoc.py`.
**Groups:** runas/become, inventory, async, output, connect, check, runtask, vault, fork,
module, basedir, tasknoplay.

```
ansible <pattern> -m <module> -a <args> [options]
```

**Unique flags:**

| Flag | Description |
|------|-------------|
| `<pattern>` | Host pattern (**required** positional): a group, host, `all`, glob, or union/intersection/exclusion expression |
| `-m`/`--module-name` | Module to run (**default `command`**) |
| `-a`/`--args` | Module args as `k=v k=v` or a JSON string (default none) |

**Most-used inherited flags:** `-i`, `-b`/`-K`, `-u`, `-e`, `-f`, `-o`/`--one-line` (*dep 2.23*),
`-B`/`-P` (async), `--check`/`--diff`.

```bash
ansible all -i inv.ini -m ansible.builtin.ping
ansible web -i inv.ini -m ansible.builtin.service -a 'name=nginx state=restarted' -b -K
ansible all -i inv.ini -a 'uptime' -o                  # implicit command module, one line/host
ansible all -i inv.ini -m ansible.builtin.shell -a 'sleep 30' -B 60 -P 5   # async, poll every 5s
```

---

## `ansible-playbook`

Run one or more playbooks. Source: `lib/ansible/cli/playbook.py`. **Groups:** connect, meta,
runas/become, subset/tags, check, inventory, runtask, vault, fork, module.

```
ansible-playbook playbook.yml [playbook2.yml ...] [options]
```

**Unique flags:**

| Flag | Description |
|------|-------------|
| `playbook` | One or more playbook files (positional, `nargs='+'`) |
| `--syntax-check` | Parse the playbook(s) and exit — no execution |
| `--list-tasks` | List the tasks that would run (respects tags) |
| `--list-tags` | List all tags defined in the playbook |
| `--list-hosts` | List the hosts a run would target (from the inventory group) |
| `--step` | Confirm `(Y/n/c)` before running each task |
| `--start-at-task <NAME>` | Begin execution at the task matching NAME |

**Key inherited flags (the common run set):**

| Flag | Group | Description |
|------|-------|-------------|
| `-i`/`--inventory` | inventory | Inventory source (path or `host,` list); repeatable |
| `-l`/`--limit` | inventory | Restrict to a host subset/pattern |
| `--flush-cache` | inventory | Clear the fact cache before the run |
| `-t`/`--tags`, `--skip-tags` | subset/tags | Run / skip tagged plays & tasks |
| `-C`/`--check`, `-D`/`--diff` | check | Dry-run / show file diffs |
| `-b`/`--become`, `--become-method`, `--become-user` | runas | Privilege escalation (sudo/su/runas) |
| `-K`/`--ask-become-pass` | runas-prompt | Prompt for the become password |
| `-e`/`--extra-vars` | runtask | Extra vars (`@file`); highest precedence; repeatable |
| `-f`/`--forks` | fork | Parallelism (default 5) |
| `-u`/`--user`, `-c`/`--connection`, `-k`/`--ask-pass`, `--private-key` | connect | Remote user / transport / SSH auth |
| `-T`/`--timeout`, `--ssh-extra-args`, `--ssh-common-args` | connect | Connection tuning |
| `--force-handlers` | meta | Run handlers even after a host fails |
| `-M`/`--module-path` | module | Prepend a local module path |
| `-v` … `-vvvvvv` | verbosity | Increasing verbosity |
| `--vault-id`, `-J`/`--ask-vault-pass`, `--vault-password-file` | vault | Vault secret sources |

```bash
ansible-playbook site.yml -i inv.yml --check --diff
ansible-playbook site.yml -i inv.yml --limit 'web:&prod' --tags deploy
ansible-playbook site.yml -i inv.yml --list-tasks            # preview without running
ansible-playbook site.yml -i inv.yml --start-at-task 'Deploy config' --step
ansible-playbook site.yml -i inv.yml -e @prod-vars.yml --vault-id prod@prompt
```

---

## `ansible-galaxy`

Install and manage **collections** and **roles**. Source: `lib/ansible/cli/galaxy.py`. Two
**required** top-level TYPE subparsers: **`collection`** and **`role`**.

**Common server options (all subcommands):**

| Flag | Description |
|------|-------------|
| `-s`/`--server` | Galaxy API server URL |
| `--token`/`--api-key` | API auth token |
| `-c`/`--ignore-certs` | Skip TLS certificate validation |
| `--timeout` | API call timeout (seconds) |

**Cache options (download/install):** `--clear-response-cache`, `--no-cache`.

### `ansible-galaxy collection <action>`

Actions: **`download`**, **`init`**, **`build`**, **`publish`**, **`install`**, **`list`**, **`verify`**.

**`collection install`:**

| Flag | Description |
|------|-------------|
| `<names>` | Positional collection names (`ns.coll[:version]`), or paths/URLs/tarballs |
| `-r`/`--requirements-file` | Install from a `requirements.yml` |
| `-p`/`--collections-path` | Target install path |
| `--pre` | Allow pre-release versions |
| `-U`/`--upgrade` | Upgrade to the latest allowed version |
| `-i`/`--ignore-errors` | Continue past per-collection failures |
| `-n`/`--no-deps` | Do not install dependencies |
| `--force-with-deps` | Force reinstall including dependencies |
| `-f`/`--force` | Force overwrite of an existing install |
| `--offline` | Resolve only from local sources (no Galaxy) |
| `--keyring`, `--signature`, `--required-valid-signature-count`, `--ignore-signature-status-code(s)`, `--disable-gpg-verify` | GPG signature verification controls |

**`collection build`:** positional path(s) (default `.`); `--output-path` (default `./`); `-f`/`--force`.
**`collection publish`:** positional tarball; `--no-wait`.
**`collection download`:** `-n`/`--no-deps`, `-p`/`--download-path` (default `./collections`), `-r`, `--pre`.
**`collection init`:** positional `ns.coll`; `--init-path`, `--collection-skeleton`, `-f`/`--force`.
**`collection verify`:** positional names; `-r`, `-p`, `--offline`, plus the GPG flags.

### `ansible-galaxy role <action>`

Actions: **`init`**, **`install`**, **`remove`**, **`delete`**, **`list`**, **`search`**, **`import`**, **`setup`**, **`info`**.

**`role install`:**

| Flag | Description |
|------|-------------|
| `<names>` | Positional role names or SCM/URL sources |
| `-r`/`--role-file` | Install from a requirements file |
| `-p`/`--roles-path` | Target roles path |
| `-g`/`--keep-scm-meta` | Keep the SCM metadata after install |
| `-n`/`--no-deps` | Do not install role dependencies |
| `-f`/`--force` | Force overwrite of an existing role |

**`role init`:** positional name; `--init-path`, `--role-skeleton`, `--type`, `-f`/`--force`.
**`role delete`/`role import`:** positional `github_user github_repo`.

```bash
ansible-galaxy collection install -r requirements.yml
ansible-galaxy collection install community.general:>=8.0.0 --upgrade
ansible-galaxy collection list
ansible-galaxy collection init my_ns.my_coll
ansible-galaxy collection build && ansible-galaxy collection publish my_ns-my_coll-1.0.0.tar.gz
ansible-galaxy role install geerlingguy.nginx -p ./roles
```

---

## `ansible-vault`

Encrypt/decrypt Vault secrets. Source: `lib/ansible/cli/vault.py`. All subcommands inherit the
vault + verbosity options; `--vault-id LABEL@SOURCE` is the identity selector.

**Subcommands:** `create`, `decrypt`, `edit`, `view`, `encrypt`, `encrypt_string`, `rekey`.

| Subcommand | Purpose | Notable flags |
|------------|---------|---------------|
| `create FILE` | Create a new encrypted file (opens `$EDITOR`) | `--skip-tty-check`, `--encrypt-vault-id LABEL` |
| `edit FILE` | Decrypt-edit-re-encrypt in place | `--encrypt-vault-id LABEL` |
| `view FILE` | Print decrypted contents (no decrypt to disk) | — |
| `encrypt FILE…` | Encrypt existing plaintext file(s) | `--output FILE` (`-` = stdout), `--encrypt-vault-id LABEL` |
| `decrypt FILE…` | Decrypt to plaintext | `--output FILE` (`-` = stdout) |
| `encrypt_string` | Produce an inline `!vault \| …` blob for one variable | `-p`/`--prompt`, `--show-input`, `-n`/`--name` (repeatable), `--stdin-name`, `--output`, `--encrypt-vault-id` |
| `rekey FILE…` | Change the encryption password | `--new-vault-password-file`, `--new-vault-id` |

**Password sources (mutually exclusive per invocation):** `-J`/`--ask-vault-pass` (interactive)
vs `--vault-password-file FILE` (repeatable; the file may be an executable that prints the
password). `--encrypt-vault-id LABEL` chooses which configured id to encrypt with.

```bash
ansible-vault create secrets.yml
ansible-vault encrypt_string 's3cr3t' -n db_password        # paste output into a vars file
ansible-vault view secrets.yml --vault-password-file ~/.vp
ansible-vault rekey secrets.yml --new-vault-password-file ~/.vp.new
ansible-vault encrypt plain.yml --output - > secrets.yml    # encrypt to stdout
```

---

## `ansible-inventory`

Inspect, validate, and export inventory. Source: `lib/ansible/cli/inventory.py`. **Groups:**
inventory, vault, basedir, runtask. Positional `group` (used with `--graph`).

**Actions (exactly one required):**

| Flag | Description |
|------|-------------|
| `--list` | Dump all hosts and vars as JSON (inventory-script form) |
| `--host HOST` | Print the variables for a single host |
| `--graph` | Print a tree of groups and hosts |

**Output / format options:**

| Flag | Description |
|------|-------------|
| `-y`/`--yaml` | YAML output instead of JSON (for `--list`) |
| `--toml` | TOML output |
| `--vars` | Include host/group vars in `--graph` / `--list` |
| `--export` | Render as the inventory would be exported (group structure) |
| `--output FILE` | Write to a file instead of stdout |

```bash
ansible-inventory -i inv.yml --list
ansible-inventory -i inv.yml --graph --vars
ansible-inventory -i inv.yml --host web1.example.com
ansible-inventory -i inv.yml --list -y --output rendered.yml
```

---

## `ansible-doc`

Show plugin/module documentation. Source: `lib/ansible/cli/doc.py`. **Groups:** module, basedir.
Positional `plugin` (`nargs='*'`).

| Flag | Description |
|------|-------------|
| `-t`/`--type` | Plugin type (**default `module`**). Choices: `become, cache, callback, cliconf, connection, httpapi, inventory, lookup, netconf, shell, vars, module, strategy, test, filter, role, keyword` |
| `-l`/`--list` | List available plugins of the type (**use this instead of memorizing modules**) |
| `-s`/`--snippet` | Print a ready-to-paste playbook task snippet |
| `-j`/`--json` | Emit docs as JSON |
| `-F`/`--list_files` | List plugin names with their source file paths |
| `-r`/`--roles-path` | Where to look for roles (with `-t role`) |
| `-e`/`--entry-point` | Role entry point to document (with `-t role`) |
| `--metadata-dump` | Dump the full plugin-doc metadata set |
| `--no-fail-on-errors` | Continue past plugins that fail to load (with `--metadata-dump`) |

```bash
ansible-doc -l                              # every module
ansible-doc -l -t lookup                    # every lookup plugin
ansible-doc ansible.builtin.copy            # full docs
ansible-doc -s ansible.builtin.copy         # snippet form
ansible-doc -t become -l                    # become plugins (sudo/su/runas/…)
```

---

## `ansible-config`

View, dump, generate, and validate configuration. Source: `lib/ansible/cli/config.py`.

**Common options:** `-c`/`--config FILE`, `-t`/`--type` (`all` | `base` | `<plugin type>`,
default `base`).

| Subcommand | Purpose | Notable flags |
|------------|---------|---------------|
| `list` | List all config options with ini key / env / default | `-f`/`--format json\|yaml` |
| `dump` | Show current effective config | `--only-changed`/`--changed-only`, `-f`/`--format json\|yaml\|display` |
| `view` | Print the active config file | — |
| `init` | Generate a starter config | `-f`/`--format ini\|env\|vars`, `--disabled` (emit options commented out) |
| `validate` | Check config for invalid/deprecated settings | `-f`/`--format ini\|env` |

```bash
ansible-config init --disabled > ansible.cfg     # commented starter file
ansible-config dump --only-changed               # non-default settings
ansible-config list -f yaml                       # all options, YAML
ansible-config validate                           # lint the active config
```

---

## `ansible-console`

Interactive REPL that runs modules against a host pattern. Source: `lib/ansible/cli/console.py`.
**Groups:** runas/become, inventory, connect, check, vault, fork, module, basedir, runtask,
tasknoplay.

| Flag | Description |
|------|-------------|
| `<pattern>` | Host pattern to target (positional, **default `all`**) |
| `--step` | Confirm before each task |

At the prompt, type a module + args like an ad-hoc command (`copy src=… dest=…`); built-in REPL
commands switch the target group, become, forks, etc. Inherits `-i`, `-b`/`-K`, `--check`, etc.

```bash
ansible-console web -i inv.yml -b
# web# ping
# web# command uptime
```

---

## `ansible-pull`

**Pull mode**: the managed host clones a repo and runs a playbook **on itself** — inverts the
usual push model (good for scale/cron). Source: `lib/ansible/cli/pull.py`. **Groups:** connect,
vault, runtask, subset/tags, inventory, module, runas-prompt — plus its own `--check`/`--diff`.

| Flag | Description |
|------|-------------|
| `playbook.yml` | Playbook(s) to run after checkout (positional, `nargs='*'`) |
| `-U`/`--url` | Repository URL to clone |
| `-C`/`--checkout` | Branch/tag/commit to check out |
| `-d`/`--directory` | Destination directory for the checkout |
| `-i`/`--inventory` | Inventory source |
| `-f`/`--force` | Run the playbook even if the repo checkout fails |
| `-o`/`--only-if-changed` | **Only run if the repo changed** (note: `-o` here ≠ ad-hoc `--one-line`) |
| `-s`/`--sleep` | Sleep a random interval (≤ N s) before starting (stagger a fleet) |
| `--purge` | Delete the checkout directory after the run |
| `--full` | Full clone instead of a shallow one |
| `-m`/`--module-name` | SCM type to use (**default `git`**) |
| `--accept-host-key` | Add the SCM host key to known_hosts automatically |
| `--verify-commit` | Verify the GPG signature on the checked-out commit |
| `--clean` | Revert local modifications to the checkout before running |
| `--track-subs` | Track and update git submodules |

```bash
ansible-pull -U https://github.com/me/infra.git -C main local.yml
ansible-pull -U https://github.com/me/infra.git -o -i localhost, site.yml   # only if changed
```

---

## `ansible-test` (note)

`ansible-test` is the **collection dev/CI test runner** (sanity / unit / integration). It ships
separately under `test/lib/ansible_test/` and has **no module under `lib/ansible/cli/`**, so its
flags are out of scope for this reference. Run `ansible-test --help` inside a collection checkout
for its sanity/units/integration subcommands.
