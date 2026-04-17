# Runbook: Governance — Entitlements

Covers `governance/entitlements.py` — 23 tools total.

⏭️ All tests skip if Okta IGA is not enabled or no entitlements are configured.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_APP_ID` | `list_applications(limit=1)` → first `id` |
| `$FIRST_ACTIVE_USER_ID` | `list_users(filter='status eq "ACTIVE"', limit=1)` → first `id` |
| `$FIRST_ENTITLEMENT_ID` | `list_entitlements(app_id=$FIRST_APP_ID)` → first `id` |
| `$FIRST_BUNDLE_ID` | `list_entitlement_bundles()` → first `id` |

---

## Section 1 — Entitlements

### T-1: list_entitlements

**Call:** `list_entitlements(app_id=$FIRST_APP_ID, limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_ENTITLEMENT_ID` = `items[0]["id"]` if non-empty

---

### T-2: get_entitlement

⏭️ Skip if `$FIRST_ENTITLEMENT_ID` not set.

**Call:** `get_entitlement(entitlement_id=$FIRST_ENTITLEMENT_ID)`  
**Expect:** `result["id"] == $FIRST_ENTITLEMENT_ID`; no `error`

---

### T-3: list_entitlement_values

⏭️ Skip if `$FIRST_ENTITLEMENT_ID` not set.

**Call:** `list_entitlement_values(entitlement_id=$FIRST_ENTITLEMENT_ID)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_ENTITLEMENT_VALUE_ID` = `items[0]["id"]` if non-empty

---

### T-4: get_entitlement_value

⏭️ Skip if `$FIRST_ENTITLEMENT_VALUE_ID` not set.

**Call:** `get_entitlement_value(entitlement_id=$FIRST_ENTITLEMENT_ID, value_id=$FIRST_ENTITLEMENT_VALUE_ID)`  
**Expect:** `result["id"] == $FIRST_ENTITLEMENT_VALUE_ID`; no `error`

---

### T-5: 🔁 create_entitlement → update → patch → delete

⏭️ Skip if IGA entitlement management is read-only in this org.

**CREATE:**
```
create_entitlement(
  app_id=$FIRST_APP_ID,
  name="runbook-test-entitlement",
  description="Created by CRUD runbook"
)
```
**Expect:** `result["id"]` → `$NEW_ENTITLEMENT_ID`

**UPDATE:** `update_entitlement(entitlement_id=$NEW_ENTITLEMENT_ID, name="runbook-test-entitlement-updated")`  
**Expect:** no `error`

**PATCH:** `patch_entitlement(entitlement_id=$NEW_ENTITLEMENT_ID, description="Patched by runbook")`  
**Expect:** no `error`

**DELETE (cleanup):** `delete_entitlement(entitlement_id=$NEW_ENTITLEMENT_ID)`  
**Expect:** no `error`

---

## Section 2 — Entitlement Bundles

### T-6: list_entitlement_bundles

**Call:** `list_entitlement_bundles(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_BUNDLE_ID` = `items[0]["id"]` if non-empty

---

### T-7: get_entitlement_bundle

⏭️ Skip if `$FIRST_BUNDLE_ID` not set.

**Call:** `get_entitlement_bundle(bundle_id=$FIRST_BUNDLE_ID)`  
**Expect:** `result["id"] == $FIRST_BUNDLE_ID`; no `error`

---

### T-8: 🔁 create_entitlement_bundle → update → delete

**CREATE:**
```
create_entitlement_bundle(
  name="runbook-test-bundle",
  description="Created by CRUD runbook"
)
```
**Expect:** `result["id"]` → `$NEW_BUNDLE_ID`

**UPDATE:** `update_entitlement_bundle(bundle_id=$NEW_BUNDLE_ID, name="runbook-test-bundle-updated")`  
**Expect:** no `error`

**DELETE (cleanup):** `delete_entitlement_bundle(bundle_id=$NEW_BUNDLE_ID)`  
**Expect:** no `error`

---

## Section 3 — Grants

### T-9: list_grants

**Call:** `list_grants(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_GRANT_ID` = `items[0]["id"]` if non-empty

---

### T-10: get_grant

⏭️ Skip if `$FIRST_GRANT_ID` not set.

**Call:** `get_grant(grant_id=$FIRST_GRANT_ID)`  
**Expect:** `result["id"] == $FIRST_GRANT_ID`; no `error`

---

### T-11: 🔁 create_grant → update → patch

⏭️ Skip if entitlement values list is empty.

**CREATE:**
```
create_grant(
  entitlement_value_id=$FIRST_ENTITLEMENT_VALUE_ID,
  principal_id=$FIRST_ACTIVE_USER_ID,
  principal_type="USER"
)
```
**Expect:** `result["id"]` → `$NEW_GRANT_ID`

**UPDATE:** `update_grant(grant_id=$NEW_GRANT_ID, ...)`  
**PATCH:** `patch_grant(grant_id=$NEW_GRANT_ID, ...)`  
**Expect:** no `error` on both

---

## Section 4 — Principal Access

### T-12: list_principal_entitlements

**Call:** `list_principal_entitlements(principal_id=$FIRST_ACTIVE_USER_ID, principal_type="USER")`  
**Expect:** `items` is a list; no `error`

---

### T-13: get_principal_entitlement_history

**Call:** `get_principal_entitlement_history(principal_id=$FIRST_ACTIVE_USER_ID, principal_type="USER")`  
**Expect:** no `error`; result describes history

---

### T-14: get_principal_entitlements_change

**Call:** `get_principal_entitlements_change(principal_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** no `error`

---

### T-15: get_principal_access

**Call:** `get_principal_access(principal_id=$FIRST_ACTIVE_USER_ID, principal_type="USER")`  
**Expect:** no `error`

---

### T-16: revoke_principal_access

⚠️ Revokes all entitlement grants for the user. Run only on a test user.

**Call:** `revoke_principal_access(principal_id=<test_user_id>)`  
⏭️ Skip unless running against a dedicated test user.  
**Expect:** no `error`

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| Entitlements | T-1 – T-5 | Full CRUD; create requires app with entitlements |
| Bundles | T-6 – T-8 | Full CRUD |
| Grants | T-9 – T-11 | Full cycle; requires entitlement values |
| Principal Access | T-12 – T-16 | Read-only; revoke is destructive |
