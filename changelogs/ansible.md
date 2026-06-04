# Changelog - ansible

All notable changes to the ansible skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-04

### Added
- Initial addition to the marketplace — a skill for **ansible-core**, the agentless, push-based SSH automation engine, authored against the ansible-core **2.22.0.dev0** source (latest released 2.21).
- `SKILL.md`: overview (agentless/push/SSH/idempotent; ansible-core vs the community `ansible` package); when-to-use; install (`pipx`/`pip` `ansible` vs `ansible-core`); the ten-binary CLI map (`ansible`, `ansible-playbook`, `ansible-galaxy`, `ansible-vault`, `ansible-inventory`, `ansible-doc`, `ansible-config`, `ansible-console`, `ansible-pull`, plus an `ansible-test` scope note); mental model (inventory → playbook → modules → FQCN → idempotency); seven core workflows (ad-hoc command, inventory INI+YAML, first playbook + run flags, become, `ansible-galaxy` + `requirements.yml`, vault, `ansible-doc`); ansible.cfg discovery/precedence; quick-reference table; troubleshooting.
- `references/cli.md`: the shared option-group table (`option_helpers.py`) plus a per-binary flag reference for every CLI, including `ansible-galaxy` collection/role actions and `ansible-vault` subcommands; documents overloaded short-flag gotchas (`-t`, `-o` differ per binary) and the 2.23 deprecations (`--inventory-file`, `-o`, `-t`).
- `references/playbooks.md`: inventory (INI + YAML, `group_vars`/`host_vars`, patterns/`--limit`, dynamic inventory), playbook anatomy (plays/tasks/handlers, blocks/rescue/always), the **source-verified 12-step variable-precedence backbone** (from `lib/ansible/vars/manager.py`; the canonical 22-level doc list explicitly flagged as docs-only), loops (`loop`/`loop_control` + legacy `with_*`), conditionals, templating (filters/tests/lookups vs `query`), roles, collections & FQCN, delegation/`run_once`, strategies/parallelism, handlers (`notify`/`listen`/`flush_handlers`), tags, and check/diff/idempotency.
- `references/config-vault.md`: ansible.cfg discovery order (`ANSIBLE_CONFIG` → `./ansible.cfg` → `~/.ansible.cfg` → `/etc/ansible/ansible.cfg`), `ansible-config init`/`validate`/`dump`, per-section settings tables (`defaults`, `privilege_escalation`, `ssh_connection`, `inventory`, `galaxy`, `persistent_connection`) with `ANSIBLE_*` env equivalents, and the Ansible Vault deep dive (whole-file vs `encrypt_string`, password sources, `--vault-id LABEL@SOURCE`, multiple vaults, `vault_id_match`, rekey/view/edit, vaulted vars in playbooks & inventory).
- `references/version-features.md`: 37 source-verified `feature → minimum ansible-core version` rows (2.15→2.21), mirroring the git/fzf/fd/ripgrep/k3s skills.
- Inline `(ansible-core X.Y+)` version annotations sourced from maintainer-declared `version_added:` metadata in the ansible-core source (authoritative, not inferred); bedrock features (≤ ~2.10 / no `version_added`) left unannotated ("unlisted = long-standing"). Playbook keywords left unannotated (no version metadata in source).
- Scope boundary: ansible-core engine + CLI + authoring; collection modules are deferred to `ansible-doc -l` rather than enumerated.
