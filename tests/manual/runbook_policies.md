# Runbook: Policies

Covers `policies.py` — 21 tools total.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_APP_ID` | `list_applications(limit=1)` → first `id` |
| `$FIRST_GROUP_ID` | `list_groups(limit=1)` → first `id` |
| `$ACCESS_POLICY_ID` | `list_policies(type="ACCESS_POLICY", limit=1)` → first `id` |
| `$TEST_POLICY_ID` | Created in T-5; deleted in T-11 |
| `$TEST_RULE_ID` | Created in T-14; deleted in T-18 |

---

## Section 1 — Policy CRUD

### T-1: list_policies

**Call:** `list_policies(limit=5)`  
**Expect:** `items` is a list; each item has `id`, `name`, `type`, `status`

---

### T-2: list_policies with type filter

**Call:** `list_policies(type="ACCESS_POLICY", limit=5)`  
**Expect:** all items have `type == "ACCESS_POLICY"`  
→ set `$ACCESS_POLICY_ID` = `items[0]["id"]`

---

### T-3: get_policy

**Call:** `get_policy(policy_id=$ACCESS_POLICY_ID)`  
**Expect:** `result["id"] == $ACCESS_POLICY_ID`; no `error`

---

### T-4: list_policy_apps

**Call:** `list_policy_apps(policy_id=$ACCESS_POLICY_ID)`  
**Expect:** `items` is a list; no `error`

---

### T-5: list_policy_mappings

**Call:** `list_policy_mappings(policy_id=$ACCESS_POLICY_ID)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_MAPPING_ID` = `items[0]["id"]` if non-empty

---

### T-6: get_policy_mapping

⏭️ Skip if `$FIRST_MAPPING_ID` not set.

**Call:** `get_policy_mapping(policy_id=$ACCESS_POLICY_ID, mapping_id=$FIRST_MAPPING_ID)`  
**Expect:** `result["id"] == $FIRST_MAPPING_ID`; no `error`

---

### T-7: 🔁 create_policy → activate → deactivate → delete

**CREATE:**
```
create_policy(
  type="PASSWORD",
  name="runbook-test-policy",
  description="Created by CRUD runbook",
  status="INACTIVE"
)
```
**Expect:** `result["id"]` → `$TEST_POLICY_ID`; `result["name"] == "runbook-test-policy"`

---

### T-8: update_policy

**Call:** `update_policy(policy_id=$TEST_POLICY_ID, name="runbook-test-policy-updated", type="PASSWORD")`  
**Expect:** no `error`; `result["name"] == "runbook-test-policy-updated"`

---

### T-9: activate_policy

**Call:** `activate_policy(policy_id=$TEST_POLICY_ID)`  
**Expect:** no `error`  
**VERIFY:** `get_policy(policy_id=$TEST_POLICY_ID)` → `status == "ACTIVE"`

---

### T-10: deactivate_policy

**Call:** `deactivate_policy(policy_id=$TEST_POLICY_ID)`  
**Expect:** no `error`  
**VERIFY:** `get_policy(policy_id=$TEST_POLICY_ID)` → `status == "INACTIVE"`

---

### T-11: delete_policy ⚠️

**Call:** `delete_policy(policy_id=$TEST_POLICY_ID)`  
**Expect:** no `error`

---

### T-12: clone_policy

**Call:** `clone_policy(policy_id=$ACCESS_POLICY_ID)`  
**Expect:** `result["id"]` → `$CLONED_POLICY_ID` (differs from `$ACCESS_POLICY_ID`)

**CLEANUP:** deactivate and delete `$CLONED_POLICY_ID`

---

## Section 2 — Policy Rules

### T-13: list_policy_rules

**Call:** `list_policy_rules(policy_id=$ACCESS_POLICY_ID)`  
**Expect:** `items` is a list; each item has `id`, `name`, `type`, `status`  
→ set `$FIRST_RULE_ID` = `items[0]["id"]` if non-empty

---

### T-14: get_policy_rule

⏭️ Skip if `$FIRST_RULE_ID` not set.

**Call:** `get_policy_rule(policy_id=$ACCESS_POLICY_ID, rule_id=$FIRST_RULE_ID)`  
**Expect:** `result["id"] == $FIRST_RULE_ID`; no `error`

---

### T-15: 🔁 create_policy_rule → activate → deactivate → delete

First create a fresh PASSWORD policy to own the test rule:

```
create_policy(type="PASSWORD", name="runbook-rule-test-policy", status="ACTIVE")
```
→ `$RULE_POLICY_ID`

**CREATE:**
```
create_policy_rule(
  policy_id=$RULE_POLICY_ID,
  name="runbook-test-rule",
  type="PASSWORD"
)
```
**Expect:** `result["id"]` → `$TEST_RULE_ID`

---

### T-16: update_policy_rule

**Call:** `update_policy_rule(policy_id=$RULE_POLICY_ID, rule_id=$TEST_RULE_ID, name="runbook-test-rule-updated", type="PASSWORD")`  
**Expect:** no `error`

---

### T-17: activate_policy_rule + deactivate_policy_rule 🔁

**ACTIVATE:** `activate_policy_rule(policy_id=$RULE_POLICY_ID, rule_id=$TEST_RULE_ID)`  
**DEACTIVATE:** `deactivate_policy_rule(policy_id=$RULE_POLICY_ID, rule_id=$TEST_RULE_ID)`  
**Expect:** no `error` on both

---

### T-18: delete_policy_rule ⚠️

**Call:** `delete_policy_rule(policy_id=$RULE_POLICY_ID, rule_id=$TEST_RULE_ID)`  
**Expect:** no `error`

**CLEANUP:** delete `$RULE_POLICY_ID` as well

---

## Section 3 — Policy Simulation & Mapping

### T-19: create_policy_simulation

**Call:**
```
create_policy_simulation(
  app_id=$FIRST_APP_ID,
  user_id=$FIRST_ACTIVE_USER_ID,
  policy_context={"policyType": ["ACCESS_POLICY"]}
)
```
**Expect:** no `error`; result contains policy evaluation output

---

### T-20: 🔁 map_resource_to_policy → get → delete

**MAP:** `map_resource_to_policy(policy_id=$ACCESS_POLICY_ID, resource_id=$FIRST_APP_ID)`  
⏭️ Skip if app is already mapped to this policy.  
**Expect:** no `error`; `result["id"]` → `$NEW_MAPPING_ID`

**GET:** `get_policy_mapping(policy_id=$ACCESS_POLICY_ID, mapping_id=$NEW_MAPPING_ID)`  
**Expect:** `result["id"] == $NEW_MAPPING_ID`

**DELETE (cleanup):** `delete_policy_resource_mapping(policy_id=$ACCESS_POLICY_ID, mapping_id=$NEW_MAPPING_ID)`  
**Expect:** no `error`

---

### T-21: invalid policy returns error

**Call:** `get_policy(policy_id="invalid-policy-000")`  
**Expect:** `"error"` in result

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| Policy CRUD | T-1 – T-12 | Full lifecycle + clone |
| Policy Rules | T-13 – T-18 | Nested CRUD + lifecycle |
| Simulation & Mapping | T-19 – T-21 | Sim requires app+user; mapping is reversible |
