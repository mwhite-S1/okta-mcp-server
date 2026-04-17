# Runbook: Groups

Covers `groups.py`, `group_rules.py`, `group_owners.py` — 20 tools total.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_ACTIVE_USER_ID` | `list_users(filter='status eq "ACTIVE"', limit=1)` → first `id` |
| `$TEST_GROUP_ID` | Created in T-4; deleted in T-9 |
| `$TEST_RULE_ID` | Created in T-14; deleted in T-18 |

---

## Section 1 — Groups (Core)

### T-1: list_groups

**Call:** `list_groups(limit=5)`  
**Expect:** `{"items": [...]}` — each item has `id`, `profile.name`, `type`  
→ set `$FIRST_GROUP_ID` = `items[0]["id"]`

---

### T-2: get_group

**Call:** `get_group(group_id=$FIRST_GROUP_ID)`  
**Expect:** `result["id"] == $FIRST_GROUP_ID`; no `error`

---

### T-3: list_group_users

**Call:** `list_group_users(group_id=$FIRST_GROUP_ID, limit=5)`  
**Expect:** `items` is a list; no `error`

---

### T-4: list_group_apps

**Call:** `list_group_apps(group_id=$FIRST_GROUP_ID, limit=5)`  
**Expect:** `items` is a list; no `error`

---

### T-5: 🔁 create_group → update → add user → remove user → delete

**CREATE:** `create_group(name="runbook-test-group", description="Created by CRUD runbook")`  
**Expect:** `result["id"]` set → `$TEST_GROUP_ID`; `result["profile"]["name"] == "runbook-test-group"`

---

### T-6: update_group

**Call:** `update_group(group_id=$TEST_GROUP_ID, name="runbook-test-group-updated", description="Updated by runbook")`  
**Expect:** no `error`; `result["profile"]["name"] == "runbook-test-group-updated"`

---

### T-7: add_user_to_group

**Call:** `add_user_to_group(group_id=$TEST_GROUP_ID, user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** no `error`

**VERIFY:** `list_group_users(group_id=$TEST_GROUP_ID)` → user appears

---

### T-8: remove_user_from_group

**Call:** `remove_user_from_group(group_id=$TEST_GROUP_ID, user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** no `error`

---

### T-9: delete_group ⚠️

**Call:** `delete_group(group_id=$TEST_GROUP_ID)`  
**Expect:** no `error`  
**VERIFY:** `get_group(group_id=$TEST_GROUP_ID)` → `"error"` in result

---

### T-10: invalid group returns error

**Call:** `get_group(group_id="invalid-group-000")`  
**Expect:** `"error"` in result

---

## Section 2 — Group Rules

### T-11: list_group_rules

**Call:** `list_group_rules(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_RULE_ID` = `items[0]["id"]` if non-empty

---

### T-12: get_group_rule

⏭️ Skip if `$FIRST_RULE_ID` not set.

**Call:** `get_group_rule(rule_id=$FIRST_RULE_ID)`  
**Expect:** `result["id"] == $FIRST_RULE_ID`; has `name`, `conditions`, `actions`

---

### T-13: 🔁 create_group_rule → activate → deactivate → delete

First create a fresh target group for the rule:  
`create_group(name="runbook-rule-target")` → set `$RULE_TARGET_GROUP_ID`

**CREATE:**
```
create_group_rule(
  name="runbook-test-rule",
  group_ids=[$RULE_TARGET_GROUP_ID],
  expression_type="urn:okta:expression:1.0",
  expression_value='user.department == "Runbook"'
)
```
**Expect:** `result["id"]` → `$TEST_RULE_ID`; `result["status"] == "INACTIVE"`

---

### T-14: activate_group_rule

**Call:** `activate_group_rule(rule_id=$TEST_RULE_ID)`  
**Expect:** no `error`  
**VERIFY:** `get_group_rule(rule_id=$TEST_RULE_ID)` → `status == "ACTIVE"`

---

### T-15: deactivate_group_rule

**Call:** `deactivate_group_rule(rule_id=$TEST_RULE_ID)`  
**Expect:** no `error`  
**VERIFY:** `get_group_rule(rule_id=$TEST_RULE_ID)` → `status == "INACTIVE"`

---

### T-16: replace_group_rule

**Call:** `replace_group_rule(rule_id=$TEST_RULE_ID, name="runbook-test-rule-renamed", group_ids=[$RULE_TARGET_GROUP_ID], expression_type="urn:okta:expression:1.0", expression_value='user.department == "Runbook"')`  
**Expect:** no `error`; `result["name"] == "runbook-test-rule-renamed"`

---

### T-17: delete_group_rule ⚠️

**Call:** `delete_group_rule(rule_id=$TEST_RULE_ID)`  
**Expect:** no `error`

**CLEANUP:** `delete_group(group_id=$RULE_TARGET_GROUP_ID)`  
**Expect:** no `error`

---

## Section 3 — Group Owners

### T-18: list_group_owners

**Call:** `list_group_owners(group_id=$FIRST_GROUP_ID)`  
**Expect:** `items` is a list (may be empty); no `error`

---

### T-19: 🔁 assign_group_owner → verify → delete_group_owner

**ASSIGN:** `assign_group_owner(group_id=$FIRST_GROUP_ID, user_id=$FIRST_ACTIVE_USER_ID, type="USER")`  
**Expect:** no `error`; `result["id"]` set → `$NEW_OWNER_ID`

⏭️ Skip if the user is already an owner.

**VERIFY:** `list_group_owners(group_id=$FIRST_GROUP_ID)` → `$FIRST_ACTIVE_USER_ID` appears

**CLEANUP:** `delete_group_owner(group_id=$FIRST_GROUP_ID, user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** no `error`

---

### T-20: invalid owner returns error

**Call:** `delete_group_owner(group_id="invalid-group-000", user_id="invalid-user-000")`  
**Expect:** `"error"` in result

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| Groups (core) | T-1 – T-10 | Full CRUD + add/remove user |
| Group Rules | T-11 – T-17 | Create/activate/deactivate/rename/delete cycle |
| Group Owners | T-18 – T-20 | Assign/verify/remove cycle |
