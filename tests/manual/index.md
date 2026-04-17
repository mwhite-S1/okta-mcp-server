# Okta MCP Server — CRUD Test Runbook Index

Each runbook covers one object domain. Claude executes them by calling the live MCP tools in sequence, verifying outputs, and cleaning up any created resources.

## How to run a runbook

In a Claude conversation with the MCP server connected:

> "Please run the runbook at `okta-mcp-server/tests/manual/runbook_<domain>.md`.
> Execute every test in order, report **PASS / SKIP / FAIL** per test,
> and print a summary scorecard at the end."

## Notation

| Symbol | Meaning |
|--------|---------|
| `$VAR` | Value resolved earlier in the runbook and reused |
| **→ set `$VAR`** | Store this field for use in later tests |
| ⚠️ | Destructive — creates real state, always has a cleanup step |
| 🔁 | Reversible cycle: create → verify → undo |
| ⏭️ | Skip condition — test is skipped when prerequisite is absent |

## Runbooks

| File | Domain | Tools |
|------|--------|-------|
| [runbook_users.md](runbook_users.md) | Users, lifecycle, credentials, factors, OAuth tokens, role targets, sessions | 46 |
| [runbook_groups.md](runbook_groups.md) | Groups, group rules, group owners | 20 |
| [runbook_applications.md](runbook_applications.md) | Applications core, app users, app groups, tokens, features, grants, push | 41 |
| [runbook_application_credentials.md](runbook_application_credentials.md) | Signing keys, CSRs, OAuth JWKs, client secrets, provisioning connections | 27 |
| [runbook_policies.md](runbook_policies.md) | Policies, rules, simulations, mappings | 21 |
| [runbook_network_zones.md](runbook_network_zones.md) | Network zones | 7 |
| [runbook_trusted_origins.md](runbook_trusted_origins.md) | Trusted origins | 7 |
| [runbook_authenticators.md](runbook_authenticators.md) | Authenticators, methods, WebAuthn AAGUIDs | 18 |
| [runbook_devices.md](runbook_devices.md) | Devices, device users | 8 |
| [runbook_agent_pools.md](runbook_agent_pools.md) | Agent pools, update jobs | 14 |
| [runbook_schema_and_mappings.md](runbook_schema_and_mappings.md) | User/group/app schema, profile mappings | 9 |
| [runbook_system_logs.md](runbook_system_logs.md) | System logs | 1 |
| [runbook_governance_access.md](runbook_governance_access.md) | Access catalog, access requests, conditions, sequences, settings | 23 |
| [runbook_governance_entitlements.md](runbook_governance_entitlements.md) | Entitlements, bundles, grants, principal access | 23 |
| [runbook_governance_certifications.md](runbook_governance_certifications.md) | Certification campaigns, reviews, security access reviews | 17 |
| [runbook_governance_admin.md](runbook_governance_admin.md) | IAM bundles, delegates, labels, collections, risk rules, settings, request types, resource owners | 59 |
| [runbook_governance_enduser.md](runbook_governance_enduser.md) | End-user catalog, my access requests, my security reviews | 25 |

**Total: 362 tools**

---

`new_tools_crud_runbook.md` — legacy file covering only the Tier 1/2 domains. Superseded by the per-domain runbooks above.
