════════════════════════════════════════
POLICIES
════════════════════════════════════════

**`list_policies` requires the `type` parameter — it is mandatory, there is no default.**

Policy types: `OKTA_SIGN_ON`, `PASSWORD`, `MFA_ENROLL`, `IDP_DISCOVERY`, `ACCESS_POLICY`, `PROFILE_ENROLLMENT`, `POST_AUTH_SESSION`, `ENTITY_RISK`

| Goal | Tool | Parameters |
|------|------|------------|
| List sign-on policies | `list_policies` | `type="OKTA_SIGN_ON"` |
| List password policies | `list_policies` | `type="PASSWORD"` |
| Active policies only | `list_policies` | `type="PASSWORD", status="ACTIVE"` |
| Search by name | `list_policies` | `type="MFA_ENROLL", q="Default"` |
| Get policy detail | `get_policy` | `policy_id` |
| List rules in a policy | `list_policy_rules` | `policy_id` |
| Get a specific rule | `get_policy_rule` | `policy_id, rule_id` |

## Policy Lifecycle

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Create policy | `create_policy` | `type, name, status="ACTIVE", ...` |
| Update policy | `update_policy` | `policy_id, policy_data={...}` |
| Delete policy | `delete_policy` | `policy_id` |
| Activate policy | `activate_policy` | `policy_id` |
| Deactivate policy | `deactivate_policy` | `policy_id` |
| Clone policy | `clone_policy` | `policy_id` |

## Policy Rules (Write)

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Create rule | `create_policy_rule` | `policy_id, rule_data={...}` |
| Update rule | `update_policy_rule` | `policy_id, rule_id, rule_data={...}` |
| Delete rule | `delete_policy_rule` | `policy_id, rule_id` |
| Activate rule | `activate_policy_rule` | `policy_id, rule_id` |
| Deactivate rule | `deactivate_policy_rule` | `policy_id, rule_id` |

## Policy ↔ Resource Mappings

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List mappings for a policy | `list_policy_mappings` | `policy_id` |
| Get a mapping | `get_policy_mapping` | `policy_id, mapping_id` |
| Map resource to policy | `map_resource_to_policy` | `policy_id, resource_id, resource_type` |
| Remove mapping | `delete_policy_resource_mapping` | `policy_id, mapping_id` |
| List apps using a policy | `list_policy_apps` | `policy_id` |

## Policy Simulation

Test which policy would apply to a given sign-on context without triggering a real auth.

> **⚠ `create_policy_simulation` is currently broken** — see `skill://detail/policies/simulation` for details.

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Simulate policy evaluation | `create_policy_simulation` | `app_instance_id, user_id, policy_context={...}` ⚠ broken |

## Risk Rules

> **⚠ Risk rule tools require governance scopes** (`okta.governance.riskRule.manage`, `okta.governance.riskRule.read`). Without them, `list_risk_rules` returns 403.
>
> **`conflict_criteria` structure** — each criteria item requires `operation` (CONTAINS_ONE or CONTAINS_ALL), not `criteria-operation`. Value IDs must belong to the specified entitlement. See `skill://detail/governance/risk-rules` for the full structure.

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List rules | `list_risk_rules` | (no params) |
| Get rule | `get_risk_rule` | `rule_id` |
| Create SOD rule | `create_risk_rule` | `name`, `resources=[{"resourceOrn":"orn:..."}]`, `conflict_criteria={...}` (see detail resource) |
| Update rule | `update_risk_rule` | `rule_id`, `name`, `description`, `notes` |
| Delete rule | `delete_risk_rule` | `rule_id` |
| Assess principal | `assess_risk_rules` | `principal_orn`, `resource_orns=[...]` (**required** — must be entitlement/bundle/collection ORNs) |
