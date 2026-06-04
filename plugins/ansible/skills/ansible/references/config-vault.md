# Ansible Configuration & Vault Reference

Two operational topics for **ansible-core**: how `ansible.cfg` is discovered and
the settings that matter, and how Ansible **Vault** encrypts secrets. For the
authoring model (inventory, plays, variables, roles), see
[playbooks.md](playbooks.md); for the CLI binaries, see [SKILL.md](../SKILL.md).

> **Scope & version note:** ansible-core only. Every setting below traces to the
> source `lib/ansible/config/base.yml` and `lib/ansible/config/manager.py`. A
> setting generally has **three bindings** — an ini key (in a section), an
> `ANSIBLE_*` env var, and a default; **env overrides ini**. Features with a
> real maintainer-declared `version_added` are flagged `(ansible-core X.Y+)`;
> unmarked settings are long-standing. Documented against ansible-core
> **2.22.0.dev0** (latest released line **2.21**). Confirm on your install with
> `ansible-config dump` and `ansible-config list`.

## Table of Contents

- [ansible.cfg Discovery Order](#ansiblecfg-discovery-order)
- [Generating a Config Template](#generating-a-config-template)
- [Config Sections & Key Settings](#config-sections--key-settings)
- [Inspecting Configuration](#inspecting-configuration)
- [Ansible Vault](#ansible-vault)
  - [Encrypting Whole Files](#encrypting-whole-files)
  - [Encrypting a Single Value (encrypt_string)](#encrypting-a-single-value-encrypt_string)
  - [Password Sources](#password-sources)
  - [Vault IDs & Labels](#vault-ids--labels)
  - [Multiple Vaults](#multiple-vaults)
  - [Rekey, View, Edit](#rekey-view-edit)
  - [Using Vaulted Vars in Playbooks & Inventory](#using-vaulted-vars-in-playbooks--inventory)

## ansible.cfg Discovery Order

Ansible loads the **first** config file it finds, in this order (it does **not**
merge multiple files):

| # | Location | Notes |
|---|---|---|
| 1 | **`$ANSIBLE_CONFIG`** | a file path, or a directory containing `ansible.cfg` |
| 2 | **`./ansible.cfg`** | current working directory — *skipped with a warning if the cwd is world-writable* |
| 3 | **`~/.ansible.cfg`** | the invoking user's home directory |
| 4 | **`/etc/ansible/ansible.cfg`** | system-wide fallback |

The mnemonic from the source docstring is **"ENV, CWD, HOME, /etc/ansible."**
Because `./ansible.cfg` wins over home and system files, keeping a project-local
`ansible.cfg` next to your playbooks is the standard way to pin per-project
behavior. Confirm which file is active:

```bash
ansible --version          # prints "config file = ..."
ansible-config view        # show the active config file's contents
```

## Generating a Config Template

`ansible-config init` writes a starter file documenting every option. Use
`--disabled` to emit it fully commented out (enable only what you change):

```bash
ansible-config init --disabled > ansible.cfg          # ini, all options commented
ansible-config init --disabled -t all > ansible.cfg   # include plugin options too
ansible-config init --format env --disabled           # emit as ANSIBLE_* env vars
```

`ansible-config validate` (`-f ini|env`) checks a config for unknown/invalid
settings.

## Config Sections & Key Settings

An `ansible.cfg` is INI-style with `[sections]`. The settings below are the
authoring-relevant subset of `config/base.yml` (ini key · `ANSIBLE_*` env ·
default).

### [defaults]

| Setting | ini key | env | default |
|---|---|---|---|
| Inventory source | `inventory` | `ANSIBLE_INVENTORY` | `/etc/ansible/hosts` |
| Parallel hosts | `forks` | `ANSIBLE_FORKS` | `5` |
| Remote login user | `remote_user` | `ANSIBLE_REMOTE_USER` | (current user) |
| Execution strategy | `strategy` | `ANSIBLE_STRATEGY` | `linear` |
| Fact gathering | `gathering` | `ANSIBLE_GATHERING` | `implicit` |
| SSH host-key checking | `host_key_checking` | `ANSIBLE_HOST_KEY_CHECKING` | `True` |
| Dict merge behavior | `hash_behaviour` | `ANSIBLE_HASH_BEHAVIOUR` | `replace` |
| Connection timeout | `timeout` | `ANSIBLE_TIMEOUT` | `10` |
| Role search path | `roles_path` | `ANSIBLE_ROLES_PATH` | `~/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles` |
| Collection search path | `collections_path` | `ANSIBLE_COLLECTIONS_PATH` | `~/.ansible/collections:/usr/share/ansible/collections` |
| Module library path | `library` | `ANSIBLE_LIBRARY` | `~/.ansible/plugins/modules:/usr/share/ansible/plugins/modules` |
| Log file | `log_path` | `ANSIBLE_LOG_PATH` | (none) |
| `.retry` files | `retry_files_enabled` | `ANSIBLE_RETRY_FILES_ENABLED` | `False` |
| Invalid group chars | `force_valid_group_names` | `ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS` | `never` |
| Ansible home dir | `home` | `ANSIBLE_HOME` | `~/.ansible` |
| Connection pipelining | `pipelining` | `ANSIBLE_PIPELINING` | `False` |

> `host_key_checking = True` rejects unknown SSH host keys — disable it
> deliberately (and only for ephemeral/test hosts). `pipelining = True` is a
> notable speed win but requires `requiretty` to be off in sudoers.
> `{{ANSIBLE_HOME}}` (default `~/.ansible`, **ansible-core 2.15** made it a
> first-class `home` setting) is the base for the default role/collection paths.

### [privilege_escalation]

| Setting | ini key | env | default |
|---|---|---|---|
| Escalate by default | `become` | `ANSIBLE_BECOME` | `False` |
| Escalation method | `become_method` | `ANSIBLE_BECOME_METHOD` | `sudo` |
| Become target user | `become_user` | `ANSIBLE_BECOME_USER` | `root` |
| Prompt for password | `become_ask_pass` | `ANSIBLE_BECOME_ASK_PASS` | `False` |

Builtin become methods are **`sudo`** (default), **`su`**, and **`runas`**
(Windows) — `doas`, `pbrun`, etc. moved to collections. Prompt for the become
password at runtime with `-K`/`--ask-become-pass`.

### [ssh_connection]

Transport tuning lives on the `ssh` connection plugin (`plugins/connection/ssh.py`),
not `base.yml`: `ssh_args`, `control_path`, `control_path_dir`, `pipelining`,
`scp_if_ssh`, and connection retries. **ansible-core 2.19** added ssh-agent
management (`SSH_AGENT`, `SSH_AGENT_EXECUTABLE`, `SSH_AGENT_KEY_LIFETIME`) and
the `ssh` options `private_key`, `private_key_passphrase`, and
`password_mechanism`.

### [inventory]

| Setting | ini key | env | default |
|---|---|---|---|
| Enabled plugins | `enable_plugins` | `ANSIBLE_INVENTORY_ENABLED` | `host_list, script, auto, yaml, ini, toml` |
| Unmatched host pattern | `host_pattern_mismatch` | — | `warning` |

### [galaxy]

| Setting | ini key | env | default |
|---|---|---|---|
| Galaxy server | `server` | `ANSIBLE_GALAXY_SERVER` | `https://galaxy.ansible.com` |
| Server list | `server_list` | — | (none) |

### [persistent_connection]

| Setting | ini key | default |
|---|---|---|
| Connect timeout | `connect_timeout` | `30` |
| Control path dir | `control_path_dir` | `~/.ansible/pc` |

### A minimal project ansible.cfg

```ini
# ansible.cfg  (next to your playbooks → wins over ~ and /etc)
[defaults]
inventory      = ./inventory.yml
roles_path     = ./roles
collections_path = ./collections
host_key_checking = False        # ephemeral lab hosts only
forks          = 20
gathering      = smart

[privilege_escalation]
become         = True
become_method  = sudo

[ssh_connection]
pipelining     = True
```

## Inspecting Configuration

```bash
ansible-config list                 # every setting, its default, ini/env bindings
ansible-config dump                 # effective values (defaults + your overrides)
ansible-config dump --only-changed  # just what differs from defaults — great for audits
ansible-config view                 # print the active config file
```

`ansible-config dump --only-changed` is the fastest way to see exactly what your
environment has customized.

## Ansible Vault

Vault encrypts secrets at rest (variables files, single values, or any file)
with **AES256**; ansible decrypts them transparently at runtime when you supply
the password. The CLI is `ansible-vault` with subcommands `create`, `edit`,
`view`, `encrypt`, `decrypt`, `rekey`, and `encrypt_string`.

### Encrypting Whole Files

Encrypt a vars file (or any file ansible loads — `group_vars/`, `host_vars/`):

```bash
ansible-vault create  group_vars/prod/secrets.yml      # new file, opens $EDITOR
ansible-vault encrypt group_vars/prod/secrets.yml      # encrypt an existing file
ansible-vault view    group_vars/prod/secrets.yml      # read without decrypting to disk
ansible-vault edit    group_vars/prod/secrets.yml      # decrypt → edit → re-encrypt
ansible-vault decrypt group_vars/prod/secrets.yml      # permanently decrypt (careful)
```

A vault-encrypted vars file is loaded exactly like a plaintext one — the
variables inside are usable normally once the password is provided to the
playbook run.

### Encrypting a Single Value (encrypt_string)

When you want **one secret inside an otherwise plaintext vars file**, use
`encrypt_string` to produce an inline `!vault` blob:

```bash
ansible-vault encrypt_string 's3cr3t-token' --name 'api_token'
```

```yaml
# vars.yml — a normal, readable file with one encrypted value
api_token: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          66386439653...   (encrypted blob)
db_host: db1.example.com          # plaintext alongside it
```

Useful flags: `-n`/`--name` (repeatable — name several at once), `-p`/`--prompt`
(prompt for the secret rather than passing it on the command line),
`--stdin-name`, and `--output -` to write to stdout.
`VAULT_ENCRYPT_SALT` (**ansible-core 2.15**) pins the salt for deterministic
output (e.g. reproducible diffs).

### Password Sources

Per invocation the password comes from **one** source (these are mutually
exclusive):

| Source | Flag | Behavior |
|---|---|---|
| Interactive prompt | `-J` / `--ask-vault-pass` | ask on the terminal |
| Password file | `--vault-password-file FILE` | read the secret from a file (**repeatable**); the file may be an **executable script** that prints the password |
| Vault id + source | `--vault-id LABEL@SOURCE` | label a secret and bind it to a source (see below) |

```bash
ansible-playbook site.yml --ask-vault-pass
ansible-playbook site.yml --vault-password-file ~/.vault_pass.txt
ansible-playbook site.yml --vault-password-file ./bin/get-vault-pass.sh   # script
```

### Vault IDs & Labels

A **vault id** ties a *label* to a *source* with `--vault-id LABEL@SOURCE`. The
source is `prompt` (ask interactively), a file path, or an executable script:

```bash
ansible-playbook site.yml --vault-id prod@prompt
ansible-playbook site.yml --vault-id dev@~/.dev-vault-pass
ansible-vault encrypt --encrypt-vault-id prod group_vars/prod/secrets.yml
```

When encrypting, the chosen label is stamped into the file header so ansible
knows which secret decrypts it. `--encrypt-vault-id LABEL` selects which id to
encrypt with when several are configured.

Two related settings:

- `DEFAULT_VAULT_IDENTITY_LIST` (`[defaults] vault_identity_list`) — default list
  of `label@source` ids, so you can omit `--vault-id` on every command.
- `DEFAULT_VAULT_ID_MATCH` (`[defaults] vault_id_match`, default `False`) — when
  `True`, ansible only tries the secret whose **label matches** the file's
  header, instead of trying every configured secret.

### Multiple Vaults

Supply several `--vault-id` flags to decrypt content protected by different
secrets in the same run — e.g. a shared `dev` secret plus a tightly held `prod`
secret:

```bash
ansible-playbook site.yml \
  --vault-id dev@~/.dev-vault-pass \
  --vault-id prod@prompt
```

Set the common ones in `[defaults] vault_identity_list` so day-to-day runs need
no flags. With `vault_id_match = True`, each file is decrypted only by its
matching label (faster and avoids trying the wrong key).

### Rekey, View, Edit

Rotate the password on already-encrypted files with `rekey`:

```bash
ansible-vault rekey group_vars/prod/secrets.yml
ansible-vault rekey --new-vault-password-file ~/.new-pass.txt secrets.yml
ansible-vault rekey --new-vault-id prod@~/.new-prod-pass secrets.yml
```

`view`/`edit` decrypt only in memory (or via a temp file for `edit`) — prefer
them over `decrypt`, which writes plaintext to disk permanently.

### Using Vaulted Vars in Playbooks & Inventory

Vaulted content is decrypted automatically wherever ansible loads variables —
**no special syntax in the playbook**. Just supply the password at run time:

```bash
# group_vars/prod/secrets.yml is vault-encrypted; this "just works":
ansible-playbook -i inventory.yml site.yml --vault-id prod@prompt
```

```yaml
# A task referencing a vaulted variable looks completely ordinary:
- name: Configure the API client
  ansible.builtin.template:
    src: client.conf.j2
    dest: /etc/app/client.conf
  vars:
    token: "{{ api_token }}"      # api_token came from a vaulted vars file
```

**In inventory:** vault works at every variable layer — encrypt entire
`group_vars/`/`host_vars/` files, or embed `!vault` inline values in them. Test
that a path is encrypted with the `vaulted_file` test (**ansible-core 2.18**):

```yaml
when: 'group_vars/prod/secrets.yml' is vaulted_file
```

> Tip: keep vault passwords out of shell history — use
> `--vault-password-file` pointing at a `0600` file or a script that fetches the
> secret from your secrets manager, and set `vault_identity_list` so routine
> commands need no flags at all.
