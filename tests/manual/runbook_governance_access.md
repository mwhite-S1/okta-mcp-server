# Runbook: Governance — Access Requests

Covers `governance/access_requests.py` — 23 tools total.

⏭️ All tests skip if Okta Governance (IGA) is not enabled in the org.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_CATALOG_ENTRY_ID` | `list_access_catalog_entries(limit=1)` → first `id` |
| `$FIRST_ACTIVE_USER_ID` | `list_users(filter='status eq "ACTIVE"', limit=1)` → first `id` |
| `$FIRST_APP_ID` | `list_applications(limit=1)` → first `id` |

---

## Section 1 — Access Catalog

### T-1: list_access_catalog_entries

**Call:** `list_access_catalog_entries(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_CATALOG_ENTRY_ID` = `items[0]["id"]` if non-empty  
⏭️ If empty: skip T-2 and T-3.

---

### T-2: get_access_catalog_entry

**Call:** `get_access_catalog_entry(catalog_entry_id=$FIRST_CATALOG_ENTRY_ID)`  
**Expect:** `result["id"] == $FIRST_CATALOG_ENTRY_ID`; no `error`

---

### T-3: get_catalog_entry_request_fields

**Call:** `get_catalog_entry_request_fields(catalog_entry_id=$FIRST_CATALOG_ENTRY_ID)`  
**Expect:** no `error`; result describes request form fields

---

### T-4: list_user_catalog_entries

**Call:** `list_user_catalog_entries(user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** `items` is a list; no `error`

---

## Section 2 — Access Requests

### T-5: list_access_requests

**Call:** `list_access_requests(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_REQUEST_ID` = `items[0]["id"]` if non-empty

---

### T-6: get_access_request

⏭️ Skip if `$FIRST_REQUEST_ID` not set.

**Call:** `get_access_request(request_id=$FIRST_REQUEST_ID)`  
**Expect:** `result["id"] == $FIRST_REQUEST_ID`; no `error`

---

### T-7: 🔁 create_access_request → add_request_message → cancel

⏭️ Skip if `$FIRST_CATALOG_ENTRY_ID` not set.

**CREATE:**
```
create_access_request(
  catalog_entry_id=$FIRST_CATALOG_ENTRY_ID,
  requestee_id=$FIRST_ACTIVE_USER_ID,
  justification="Runbook CRUD test"
)
```
**Expect:** `result["id"]` → `$NEW_REQUEST_ID`; no `error`

**MESSAGE:**
```
add_request_message(
  request_id=$NEW_REQUEST_ID,
  message="Added by runbook test"
)
```
**Expect:** no `error`

**CANCEL (cleanup):**
```
cancel_access_request(request_id=$NEW_REQUEST_ID)
```
**Expect:** no `error`

---

## Section 3 — Request Conditions

### T-8: list_request_conditions

**Call:** `list_request_conditions()`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_CONDITION_ID` = `items[0]["id"]` if non-empty

---

### T-9: get_request_condition

⏭️ Skip if `$FIRST_CONDITION_ID` not set.

**Call:** `get_request_condition(condition_id=$FIRST_CONDITION_ID)`  
**Expect:** `result["id"] == $FIRST_CONDITION_ID`; no `error`

---

### T-10: 🔁 create_request_condition → update → activate → deactivate → delete

**CREATE:**
```
create_request_condition(
  name="runbook-test-condition",
  type="GROUP_MEMBERSHIP",
  group_id=$FIRST_GROUP_ID
)
```
**Expect:** `result["id"]` → `$NEW_CONDITION_ID`

**UPDATE:** `update_request_condition(condition_id=$NEW_CONDITION_ID, name="runbook-test-condition-updated")`  
**Expect:** no `error`

**ACTIVATE:** `activate_request_condition(condition_id=$NEW_CONDITION_ID)`  
**Expect:** no `error`

**DEACTIVATE:** `deactivate_request_condition(condition_id=$NEW_CONDITION_ID)`  
**Expect:** no `error`

**DELETE (cleanup):** `delete_request_condition(condition_id=$NEW_CONDITION_ID)`  
**Expect:** no `error`

---

## Section 4 — Request Sequences

### T-11: list_request_sequences

**Call:** `list_request_sequences()`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_SEQUENCE_ID` = `items[0]["id"]` if non-empty

---

### T-12: get_request_sequence

⏭️ Skip if `$FIRST_SEQUENCE_ID` not set.

**Call:** `get_request_sequence(sequence_id=$FIRST_SEQUENCE_ID)`  
**Expect:** `result["id"] == $FIRST_SEQUENCE_ID`; no `error`

---

### T-13: delete_request_sequence

⏭️ Skip — deleting existing sequences may disrupt active workflows. Document expected behavior:
- Deletes the approval sequence; in-flight requests using it may fail
- Only delete test sequences created specifically for runbook purposes

---

## Section 5 — Request Settings

### T-14: list_request_settings

**Call:** `list_request_settings()`  
**Expect:** no `error`; result is a dict with settings fields

---

### T-15: update_request_settings (no-op)

**Call:** `update_request_settings(<current settings from T-14>)`  
**Expect:** no `error`

---

### T-16: get_resource_request_settings

**Call:** `get_resource_request_settings(resource_type="APP", resource_id=$FIRST_APP_ID)`  
**Expect:** no `error`

---

### T-17: update_resource_request_settings (no-op)

**Call:** `update_resource_request_settings(resource_type="APP", resource_id=$FIRST_APP_ID, settings=<current from T-16>)`  
**Expect:** no `error`

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| Access Catalog | T-1 – T-4 | Read-only |
| Access Requests | T-5 – T-7 | Create/message/cancel cycle |
| Conditions | T-8 – T-10 | Full CRUD + lifecycle |
| Sequences | T-11 – T-13 | Read-only; delete is risky |
| Settings | T-14 – T-17 | Read + no-op updates |
