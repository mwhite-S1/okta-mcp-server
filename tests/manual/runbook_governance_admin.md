# Runbook: Governance — Admin (IAM Bundles, Delegates, Labels, Collections, Risk Rules, Settings, Request Types, Resource Owners)

Covers:
- `governance/iam_bundles.py` — 13 tools
- `governance/delegates.py` — 4 tools
- `governance/labels.py` — 8 tools
- `governance/collections.py` — 8 tools
- `governance/risk_rules.py` — 6 tools
- `governance/settings.py` — 8 tools
- `governance/request_types.py` — 7 tools
- `governance/resource_owners.py` — 4 tools
- `governance/operations.py` — 1 tool

**Total: 59 tools**

⏭️ All tests skip if Okta IGA is not enabled.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_ACTIVE_USER_ID` | `list_users(filter='status eq "ACTIVE"', limit=1)` → first `id` |
| `$FIRST_APP_ID` | `list_applications(limit=1)` → first `id` |
| `$FIRST_GROUP_ID` | `list_groups(limit=1)` → first `id` |

---

## Section 1 — IAM Governance Bundles

### T-1: list_iam_governance_bundles

**Call:** `list_iam_governance_bundles(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_IAM_BUNDLE_ID` = `items[0]["id"]` if non-empty

---

### T-2: get_iam_governance_bundle

⏭️ Skip if `$FIRST_IAM_BUNDLE_ID` not set.

**Call:** `get_iam_governance_bundle(bundle_id=$FIRST_IAM_BUNDLE_ID)`  
**Expect:** `result["id"] == $FIRST_IAM_BUNDLE_ID`; no `error`

---

### T-3: list_iam_bundle_entitlements

⏭️ Skip if `$FIRST_IAM_BUNDLE_ID` not set.

**Call:** `list_iam_bundle_entitlements(bundle_id=$FIRST_IAM_BUNDLE_ID)`  
**Expect:** `items` is a list; no `error`

---

### T-4: list_iam_bundle_entitlement_values

⏭️ Skip if `$FIRST_IAM_BUNDLE_ID` not set.

**Call:** `list_iam_bundle_entitlement_values(bundle_id=$FIRST_IAM_BUNDLE_ID)`  
**Expect:** `items` is a list; no `error`

---

### T-5: get_iam_governance_opt_in_status

**Call:** `get_iam_governance_opt_in_status()`  
**Expect:** no `error`; result indicates opted-in/out state

---

### T-6: 🔁 create_iam_governance_bundle → replace → delete

**CREATE:**
```
create_iam_governance_bundle(
  name="runbook-test-iam-bundle",
  description="Created by CRUD runbook"
)
```
**Expect:** `result["id"]` → `$NEW_IAM_BUNDLE_ID`

**REPLACE:** `replace_iam_governance_bundle(bundle_id=$NEW_IAM_BUNDLE_ID, name="runbook-test-iam-bundle-replaced")`  
**Expect:** no `error`

**DELETE:** `delete_iam_governance_bundle(bundle_id=$NEW_IAM_BUNDLE_ID)`  
**Expect:** no `error`

---

### T-7: get_user_role_governance_sources

**Call:** `get_user_role_governance_sources(user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** no `error`

---

### T-8: get_user_role_governance_grant

⏭️ Skip if user has no governance role grants.

**Call:** `get_user_role_governance_grant(user_id=$FIRST_ACTIVE_USER_ID, grant_id=<known_grant_id>)`  
**Expect:** no `error`

---

### T-9: get_user_role_governance_grant_resources

⏭️ Skip if user has no governance role grants.

**Call:** `get_user_role_governance_grant_resources(user_id=$FIRST_ACTIVE_USER_ID, grant_id=<known_grant_id>)`  
**Expect:** no `error`

---

## Section 2 — Governance Delegates

### T-10: get_governance_delegate_settings

**Call:** `get_governance_delegate_settings()`  
**Expect:** no `error`; result is a dict

---

### T-11: list_governance_delegates

**Call:** `list_governance_delegates(limit=5)`  
**Expect:** `items` is a list; no `error`

---

### T-12: get_principal_governance_settings

**Call:** `get_principal_governance_settings(principal_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** no `error`

---

### T-13: update_principal_governance_settings (no-op)

**Call:** `update_principal_governance_settings(principal_id=$FIRST_ACTIVE_USER_ID, settings=<current from T-12>)`  
**Expect:** no `error`

---

## Section 3 — Governance Labels

### T-14: list_governance_labels

**Call:** `list_governance_labels(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_LABEL_ID` = `items[0]["id"]` if non-empty

---

### T-15: get_governance_label

⏭️ Skip if `$FIRST_LABEL_ID` not set.

**Call:** `get_governance_label(label_id=$FIRST_LABEL_ID)`  
**Expect:** `result["id"] == $FIRST_LABEL_ID`; no `error`

---

### T-16: list_labeled_resources

⏭️ Skip if `$FIRST_LABEL_ID` not set.

**Call:** `list_labeled_resources(label_id=$FIRST_LABEL_ID, resource_type="APP")`  
**Expect:** `items` is a list; no `error`

---

### T-17: 🔁 create_governance_label → update → assign → unassign → delete

**CREATE:**
```
create_governance_label(
  name="runbook-test-label",
  description="Created by CRUD runbook"
)
```
**Expect:** `result["id"]` → `$NEW_LABEL_ID`

**UPDATE:** `update_governance_label(label_id=$NEW_LABEL_ID, name="runbook-test-label-updated")`  
**Expect:** no `error`

**ASSIGN:** `assign_governance_labels(resource_type="APP", resource_id=$FIRST_APP_ID, label_ids=[$NEW_LABEL_ID])`  
**Expect:** no `error`

**VERIFY:** `list_labeled_resources(label_id=$NEW_LABEL_ID, resource_type="APP")` → app appears

**UNASSIGN:** `unassign_governance_labels(resource_type="APP", resource_id=$FIRST_APP_ID, label_ids=[$NEW_LABEL_ID])`  
**Expect:** no `error`

**DELETE:** `delete_governance_label(label_id=$NEW_LABEL_ID)`  
**Expect:** no `error`

---

## Section 4 — Governance Collections

### T-18: list_collections

**Call:** `list_collections(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_COLLECTION_ID` = `items[0]["id"]` if non-empty

---

### T-19: get_collection

⏭️ Skip if `$FIRST_COLLECTION_ID` not set.

**Call:** `get_collection(collection_id=$FIRST_COLLECTION_ID)`  
**Expect:** `result["id"] == $FIRST_COLLECTION_ID`; no `error`

---

### T-20: list_collection_resources

⏭️ Skip if `$FIRST_COLLECTION_ID` not set.

**Call:** `list_collection_resources(collection_id=$FIRST_COLLECTION_ID)`  
**Expect:** `items` is a list; no `error`

---

### T-21: 🔁 create_collection → add resource → list → remove → update → delete

**CREATE:**
```
create_collection(
  name="runbook-test-collection",
  description="Created by CRUD runbook"
)
```
**Expect:** `result["id"]` → `$NEW_COLLECTION_ID`

**ADD RESOURCES:**
```
add_collection_resources(
  collection_id=$NEW_COLLECTION_ID,
  resources=[{"type": "APP", "id": $FIRST_APP_ID}]
)
```
**Expect:** no `error`

**LIST:** `list_collection_resources(collection_id=$NEW_COLLECTION_ID)` → app appears

**REMOVE:** `remove_collection_resource(collection_id=$NEW_COLLECTION_ID, resource_type="APP", resource_id=$FIRST_APP_ID)`  
**Expect:** no `error`

**UPDATE:** `update_collection(collection_id=$NEW_COLLECTION_ID, name="runbook-test-collection-updated")`  
**Expect:** no `error`

**DELETE:** `delete_collection(collection_id=$NEW_COLLECTION_ID)`  
**Expect:** no `error`

---

## Section 5 — Risk Rules

### T-22: list_risk_rules

**Call:** `list_risk_rules(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_RISK_RULE_ID` = `items[0]["id"]` if non-empty

---

### T-23: get_risk_rule

⏭️ Skip if `$FIRST_RISK_RULE_ID` not set.

**Call:** `get_risk_rule(rule_id=$FIRST_RISK_RULE_ID)`  
**Expect:** `result["id"] == $FIRST_RISK_RULE_ID`; no `error`

---

### T-24: assess_risk_rules

**Call:** `assess_risk_rules(user_id=$FIRST_ACTIVE_USER_ID, ip_address="1.2.3.4")`  
**Expect:** no `error`; result contains risk assessment

---

### T-25: 🔁 create_risk_rule → update → delete

**CREATE:**
```
create_risk_rule(
  name="runbook-test-risk-rule",
  conditions={"network": {"connection": "ANYWHERE"}}
)
```
**Expect:** `result["id"]` → `$NEW_RISK_RULE_ID`

**UPDATE:** `update_risk_rule(rule_id=$NEW_RISK_RULE_ID, name="runbook-test-risk-rule-updated")`  
**Expect:** no `error`

**DELETE:** `delete_risk_rule(rule_id=$NEW_RISK_RULE_ID)`  
**Expect:** no `error`

---

## Section 6 — Governance Settings

### T-26: list_governance_integrations

**Call:** `list_governance_integrations()`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_INTEGRATION_ID` = `items[0]["id"]` if non-empty

---

### T-27: 🔁 create_governance_integration → delete

⏭️ Skip if integration requirements not known for this org.

**CREATE:**
```
create_governance_integration(
  name="runbook-test-integration",
  type="<integration_type>"
)
```
**DELETE:** `delete_governance_integration(integration_id=$NEW_INTEGRATION_ID)`  
**Expect:** no `error`

---

### T-28: get_certification_settings / update_certification_settings (no-op)

**Call:** `get_certification_settings()`  
**Expect:** no `error`

**No-op update:** `update_certification_settings(<same values>)`  
**Expect:** no `error`

---

### T-29: get_resource_entitlement_settings / update_resource_entitlement_settings (no-op)

**Call:** `get_resource_entitlement_settings(resource_type="APP", resource_id=$FIRST_APP_ID)`  
**Expect:** no `error`

**No-op update:** `update_resource_entitlement_settings(resource_type="APP", resource_id=$FIRST_APP_ID, settings=<same>)`  
**Expect:** no `error`

---

### T-30: update_org_governance_settings (no-op)

**Call:** `update_org_governance_settings(settings=<read current first>)`  
⚠️ Read current settings before calling — send back the same values.  
**Expect:** no `error`

---

## Section 7 — Request Types

### T-31: list_governance_teams

**Call:** `list_governance_teams(limit=5)`  
**Expect:** `items` is a list; no `error`

---

### T-32: list_request_types

**Call:** `list_request_types(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_REQUEST_TYPE_ID` = `items[0]["id"]` if non-empty

---

### T-33: get_request_type

⏭️ Skip if `$FIRST_REQUEST_TYPE_ID` not set.

**Call:** `get_request_type(request_type_id=$FIRST_REQUEST_TYPE_ID)`  
**Expect:** `result["id"] == $FIRST_REQUEST_TYPE_ID`; no `error`

---

### T-34: 🔁 create_request_type → publish → unpublish → delete

**CREATE:**
```
create_request_type(
  name="runbook-test-request-type",
  description="Created by CRUD runbook",
  catalog_entry_id=$FIRST_CATALOG_ENTRY_ID
)
```
**Expect:** `result["id"]` → `$NEW_REQUEST_TYPE_ID`

**PUBLISH:** `publish_request_type(request_type_id=$NEW_REQUEST_TYPE_ID)`  
**Expect:** no `error`

**UNPUBLISH:** `unpublish_request_type(request_type_id=$NEW_REQUEST_TYPE_ID)`  
**Expect:** no `error`

**DELETE:** `delete_request_type(request_type_id=$NEW_REQUEST_TYPE_ID)`  
**Expect:** no `error`

---

## Section 8 — Resource Owners

### T-35: list_resource_owners

**Call:** `list_resource_owners(resource_type="APP", resource_id=$FIRST_APP_ID)`  
**Expect:** `items` is a list; no `error`

---

### T-36: list_resource_owners_catalog

**Call:** `list_resource_owners_catalog(limit=5)`  
**Expect:** `items` is a list; no `error`

---

### T-37: 🔁 create_resource_owner → update → verify

**CREATE:**
```
create_resource_owner(
  resource_type="APP",
  resource_id=$FIRST_APP_ID,
  user_id=$FIRST_ACTIVE_USER_ID
)
```
⏭️ Skip if user is already an owner.  
**Expect:** no `error`

**UPDATE:** `update_resource_owners(resource_type="APP", resource_id=$FIRST_APP_ID, owners=[...])`  
**Expect:** no `error`

---

## Section 9 — Governance Operations

### T-38: get_governance_operation

⏭️ Skip if no governance operation IDs are known.

**Call:** `get_governance_operation(operation_id=<known_op_id>)`  
**Expect:** no `error`; result has `id`, `status`

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| IAM Bundles | T-1 – T-9 | Full CRUD + opt-in status + user role grants |
| Delegates | T-10 – T-13 | Read + no-op update |
| Labels | T-14 – T-17 | Full CRUD + assign/unassign to app |
| Collections | T-18 – T-21 | Full CRUD + add/remove resource |
| Risk Rules | T-22 – T-25 | Full CRUD + risk assessment |
| Settings | T-26 – T-30 | Read + no-op updates |
| Request Types | T-31 – T-34 | Full lifecycle: create/publish/unpublish/delete |
| Resource Owners | T-35 – T-37 | List + create + update |
| Operations | T-38 | Read only |
