# ansible-core Feature → Minimum Version

A consolidated lookup of **which ansible-core version introduced a config option, plugin, module, or module option** this skill documents, so you know what works on an older (or newer) engine. Use it to answer "is my ansible-core new enough for X?" and "what do I need to upgrade to?"

**How to read this:**

- These are **ansible-core** minor versions — the engine (`ansible.builtin` content), **not** the community **`ansible`** package. Each version is the `version_added:` value declared in ansible-core source (`lib/ansible/config/base.yml`, `lib/ansible/plugins/**`, `lib/ansible/modules/*.py`). These are **maintainer-declared metadata harvested verbatim — never inferred**.
- **ansible-core vs the community `ansible` package.** Since the **2.10 "great collection split"**, the monolithic `ansible` was divided into **`ansible-core`** (the engine + `ansible.builtin`) and the umbrella **`ansible`** package (a curated bundle of `ansible-core` plus hundreds of Galaxy collections like `community.general`, `ansible.posix`). The two version schemes differ — community `ansible` 11.x bundles roughly `ansible-core` 2.18 — but the exact bundle↔core mapping is **not** verifiable from the engine source; **see the ansible community package release notes** (ansible-build-data / the porting guides) for the authoritative matrix. When you "install ansible" you may have either just `ansible-core` or the full bundle.
- The version below is the **earliest ansible-core minor** in which the feature carries its `version_added`. `2.15`→`2.21` are released; `2.22` is the current development tree (`2.22.0.dev0`) and its features are unreleased — none are listed here.
- **Features not listed here are long-standing** — present at or before ~ansible-core **2.10** (the base/core split point) or carrying no `version_added` at all: the bulk of `ssh`/`winrm` connection options (2.7), most lookups/filters (0.9–2.12), the `sudo`/`su`/`runas` become methods, the `linear`/`free` strategies, and essentially every playbook keyword. **Per-playbook-keyword "since version X" facts are not derivable from ansible-core source** (`keyword_desc.yml` and `playbook/*.py` carry no version metadata), so this file does not annotate keywords. Treat anything unlisted as "always available."
- This file is documented against **ansible-core 2.21** (the latest released minor; source tree `2.22.0.dev0`). Always confirm on the running system — see [Checking your versions](#checking-your-versions).

Every row below traces to a `version_added:` value read directly from ansible-core source. Non-builtin (collection) content is **not** covered here — collection modules carry their own `version_added` in the collection's own versioning (see the closing note). The private internal `ansible._protomatter` collection (all `2.19`, underscore namespace) is **not** a public API and is deliberately omitted.

## Contents

- [Versioned features (ascending by ansible-core minor)](#versioned-features-ascending-by-ansible-core-minor)
- [Checking your versions](#checking-your-versions)

## Versioned features (ascending by ansible-core minor)

Sorted ascending by minimum ansible-core minor. "Area" follows the engine subsystem the feature lives in.

| Min version | Feature | Area |
|---|---|---|
| 2.15+ | `VAULT_ENCRYPT_SALT` — pin the vault salt for deterministic encryption output | config / vault |
| 2.15+ | `EDITOR`, `PAGER` — configurable editor/pager for the CLIs | config |
| 2.15+ | `commonpath` filter — new builtin filter (longest common sub-path) | filter plugin (new) |
| 2.15+ | `normpath` filter — new builtin filter (normalize a path) | filter plugin (new) |
| 2.15+ | `deb822_repository` module — manage `deb822`-format APT sources | module (new) |
| 2.15+ | `dnf5` module — package management via the libdnf5 backend | module (new) |
| 2.15+ | `apt_repository`: `sources_added` / `sources_removed`; `dnf`: `use_backend`; `group`: `force`; `iptables`: `numeric` | module options |
| 2.16+ | `GALAXY_COLLECTIONS_PATH_WARNING` — warn on non-standard collections path | config / galaxy |
| 2.16+ | `config` lookup: `show_origin` option — report where a setting came from | lookup plugin |
| 2.16+ | `command`: `expand_argument_vars` — control env-var expansion in argv | module option |
| 2.16+ | `blockinfile`: `append_newline` / `prepend_newline`; `find`: `exact_mode` / `mode`; `user`: `password_expire_warn` | module options |
| 2.17+ | `LOG_VERBOSITY`, `TARGET_LOG_INFO` — independent log verbosity / target-side log detail | config / logging |
| 2.17+ | `csvfile` lookup: `keycol`; `regex_replace` filter: `count` / `mandatory_count` | lookup / filter plugins |
| 2.17+ | `import_role`: `public` — export the imported role's vars/handlers to the play | module option |
| 2.17+ | `pip`: `break_system_packages`; `dnf`/`dnf5`: `best`; `async_status`: `check_mode`; `find`: `encoding` | module options |
| 2.18+ | `COLOR_DOC_*` (constant/deprecated/link/module/plugin/reference) + `COLOR_INCLUDED` — ansible-doc / output colors | config / color |
| 2.18+ | `GALAXY_COLLECTION_IMPORT_POLL_FACTOR` / `GALAXY_COLLECTION_IMPORT_POLL_INTERVAL` — tune collection-import polling | config / galaxy |
| 2.18+ | `vaulted_file` test — new builtin test (is a file vault-encrypted) | test plugin (new) |
| 2.18+ | `timedout` test — new builtin test (did a task time out) | test plugin (new) |
| 2.18+ | `ini` lookup: `interpolation` option | lookup plugin |
| 2.18+ | `mount_facts` module — gather mount-point facts | module (new) |
| 2.18+ | `find`: `limit`; `group`: `gid_max` / `gid_min`; `user`: `uid_max` / `uid_min` / `password_expire_account_disable`; `yum_repository`: `countme` | module options |
| 2.19+ | `SSH_AGENT`, `SSH_AGENT_EXECUTABLE`, `SSH_AGENT_KEY_LIFETIME` — ansible-core can manage an ssh-agent | config / ssh |
| 2.19+ | `ALLOW_BROKEN_CONDITIONALS`, `ALLOW_EMBEDDED_TEMPLATES` — conditional/templating strictness toggles (leave at defaults) | config / templating |
| 2.19+ | `DISPLAY_TRACEBACK` — control traceback display | config / output |
| 2.19+ | `ssh` connection: `password_mechanism`, `private_key`, `private_key_passphrase`, `verbosity` (pairs with the new ssh-agent support) | connection plugin |
| 2.19+ | `local` connection: `become_strip_preamble`, `become_success_timeout` | connection plugin |
| 2.19+ | `sudo` become: `sudo_chdir`; `template` lookup: `trim_blocks`; `b64encode`/`b64decode` filter: `urlsafe` | become / lookup / filter plugins |
| 2.19+ | `apt`: `auto_install_module_deps`; `dnf5`: `auto_install_module_deps`; `find`: `checksum_algorithm` | module options |
| 2.20+ | `blockinfile`: `encoding`; `lineinfile`: `encoding`; `deb822_repository`: `install_python_debian`; `stat`: `get_selinux_context` / `selinux_context` | module options |
| 2.21+ | `INJECT_INVOCATION`, `WORKER_SESSION_ISOLATION` — worker invocation / session-isolation controls | config |
| 2.21+ | `psrp` connection: `certificate_key_password`, `no_profile` | connection plugin |
| 2.21+ | `generator` inventory: `use_extra_vars` option | inventory plugin |
| 2.21+ | `to_yaml` filter: `vault_behavior` option | filter plugin |
| 2.21+ | `include_role`: `rescuable` — allow a dynamically-included role to be rescued by a `block`/`rescue` | module option |
| 2.21+ | `deb822_repository`: `exclude` / `include`; `slurp`: `armor`; `stat`: `disk_usage_bytes` | module options |

## Checking your versions

Check what you are running:

```
ansible --version            # ansible-core (engine) version, config file in use, module search path, python/jinja/pyyaml versions
ansible-community --version  # the community "ansible" package version (only present if the bundle is installed)
ansible-galaxy collection list   # every installed collection and its version (incl. ansible.builtin)
```

`ansible --version` reports the **ansible-core** number (e.g. `core 2.21`) — that is the version this table is keyed on. `ansible-community --version` reports the **umbrella package** number (e.g. `11.x`), which bundles a specific ansible-core plus many collections; map the two via the ansible community package release notes, not by guessing.

> **Collection content versions separately.** Anything beyond `ansible.builtin` (e.g. `community.general.*`, `ansible.posix.*`) carries its **own** `version_added` tied to the **collection's** version, not to ansible-core. A module option marked `version_added: 5.0.0` in `community.general` refers to that collection's 5.0.0 — install/upgrade it with `ansible-galaxy collection install <ns.coll>` and check `ansible-galaxy collection list`. This file covers builtin (ansible-core) content only.
