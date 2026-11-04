# Ownership and deployment review — 2026-11-04

This focused source review supports the homepage diagram and FAQ. It is not a
penetration test or verification of a particular user's accounts or deployment.
The website draft starts from `4d3f94b`; CLI and deployment sources were inspected
locally without syncing or changing those repositories.

## Evidence and boundaries

| Area | Observed behavior | Source |
| --- | --- | --- |
| Ownership | New application repos are private in the chosen owner's account. A Factory backup is optional and private. Shared deployment workflows are copied to the owner's private repository. | CLI `wizard/steps/finalize.py`, `factory_git.py`, `sync_commands.py` |
| Secret storage | Bootstrap encrypts configuration and the CI SSH key, rotates away from the template Vault password and checks the rotation. It stores the project Vault password through the local backend and sends it to GitHub Secrets via stdin. | CLI `wizard/steps/project.py`, `wizard/steps/finalize.py`, `wizard/vault_guard.py` |
| CI access | Deployment receives `VAULT_PASSWORD` and decrypts `ci_ssh_key` into an SSH agent. An authorized runner can use the secrets. Repository encryption is not isolation from CI. | Deployment `.github/actions/deploy/action.yml` |
| Server access | Deployment SSH credentials are administrative. Shared clusters are documented for mutually trusted projects of one owner, not customer isolation. | CLI skill, shared-cluster documentation |
| Network defaults | Kubernetes access uses an SSH tunnel; the cloud firewall defaults to an empty API-source allowlist. SSH uses `accept-new` host-key checking. | CLI `kube_access.py`; deployment `roles/hetzner-firewall/defaults/main.yml`, `ansible.cfg` |
| Agent access | The local agent can use whatever filesystem, command and credential access its environment permits. Agent instructions do not enforce isolation. | Local CLI credential and command execution paths; actual agent permissions need operator verification |
| Updates | Application templates and shared deployment updates are separate. Runtime action resolution supports a reviewed pin, but workflows also contain mutable `@main` references. | CLI `template_commands.py`, `sync_commands.py`; deployment workflows and `.github/actions/deploy/action.yml` |

Source revisions: CLI `76ad2e1c9c59dac131e59dbd92bed4a07da9f40e`;
deployment template `e233a554fd49e19c296fea1ad2695ec1925835e5`.
The inspected setup does not add a Deploy Your Startup collaborator or a separate
operator account. This does not establish absence of access granted separately,
nor remove the need to trust the upstream code you execute.

## Follow-up priorities

1. **Narrow bootstrap's default workflow permissions.** `FinalizeStep.run`
   sets `default_workflow_permissions=write` and
   `can_approve_pull_request_reviews=true`. Review which workflows need writes;
   default to read and grant writes explicitly at the job that needs them.
   The application deploy workflow already narrows its own token permissions,
   so this is a broad-default finding, not a demonstrated privilege escalation.
2. **Check production credential gates.** Full-stack bootstrap stores the Vault
   password as a repository secret. Verify branch protections, who can edit
   workflows and whether production environments/review gates are supported in
   the user's GitHub plan. A compromised authorized workflow can decrypt the
   Vault and use administrative SSH credentials. This is a trust boundary, not
   a claim that ordinary fork pull requests receive secrets.
3. **Trace every mutable runtime reference.** Confirm generated consumer pins
   and nested action resolution for the actual installed release before claiming
   all deployment code is immutable. Describe updates as user-controlled without
   promising that every upstream dependency is pinned.
4. **Verify recovery and first-contact trust separately.** `accept-new` accepts
   the first observed host key. Live firewall state, credential revocation,
   backups/restore, runtime secret permissions and application authorization were
   not tested here. They need a separately scoped operational review.

## Communication decision

Use one general FAQ with ownership, pricing, access and update questions. The
small homepage diagram describes the standard full-stack path and labels the
Cloudflare Pages exception. Explain CI decryption and administrative access;
avoid “only you can decrypt”, automatic isolation, or a blanket security claim.
No infrastructure, permissions or credentials were changed for this draft.

## Draft validation

- Website `mise run test`: 22 Python integration tests and five rendered-page
  scenarios passed; the latter build the real Astro site.
- Local browser E2E: all 13 scenarios passed, including FAQ and Factory overview navigation.
- Both macOS installer E2E scripts passed (isolated homes and cancelled cloud
  setup; no production provisioning).
- Hub `mise run test`: all 69 tests passed using `FACTORY_TEST_PYTHON` set to the
  existing CLI virtualenv. The initial system-Python run failed two cases because
  the CLI module was not installed in that interpreter.
- The first website test run exposed simultaneous builds writing the same output
  directory. The FAQ scenario now runs in the existing sequential page suite;
  the complete rerun passed.
- This repository exposes build/dev/test tasks, but no lint command. Whitespace
  checks passed. Browser CI is disabled by `run_e2e: false`; local E2E was run.
- No deployment, account permissions or credentials were changed.
