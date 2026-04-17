# Runbook: Governance — End User (My Tools)

Covers `governance/enduser.py` — 25 tools total.

These tools operate in **caller context** — they act on behalf of the authenticated
user (the service account or delegated token holder), not an arbitrary user ID.
Results depend on what that caller has access to in IGA.

⏭️ All tests skip if Okta IGA is not enabled or the caller has no catalog entries / reviews.

---

## Prerequisites

The caller must be an active Okta user with IGA access.
No external variable setup needed — all tools use the caller's own context.

---

## Section 1 — My Catalog

### T-1: list_my_catalog_entries

**Call:** `list_my_catalog_entries(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$MY_CATALOG_ENTRY_ID` = `items[0]["id"]` if non-empty  
⏭️ If empty: skip T-2 through T-7.

---

### T-2: get_my_catalog_entry

**Call:** `get_my_catalog_entry(catalog_entry_id=$MY_CATALOG_ENTRY_ID)`  
**Expect:** `result["id"] == $MY_CATALOG_ENTRY_ID`; no `error`

---

### T-3: get_my_catalog_entry_request_fields

**Call:** `get_my_catalog_entry_request_fields(catalog_entry_id=$MY_CATALOG_ENTRY_ID)`  
**Expect:** no `error`; result describes request form fields

---

### T-4: list_my_catalog_entry_users

**Call:** `list_my_catalog_entry_users(catalog_entry_id=$MY_CATALOG_ENTRY_ID, limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$REQUESTEE_USER_ID` = `items[0]["id"]` if non-empty

---

### T-5: get_my_catalog_entry_user_request_fields

⏭️ Skip if `$REQUESTEE_USER_ID` not set.

**Call:** `get_my_catalog_entry_user_request_fields(catalog_entry_id=$MY_CATALOG_ENTRY_ID, user_id=$REQUESTEE_USER_ID)`  
**Expect:** no `error`

---

## Section 2 — My Access Requests

### T-6: 🔁 create_my_access_request → get → cancel

⏭️ Skip if `$MY_CATALOG_ENTRY_ID` not set.

**CREATE:**
```
create_my_access_request(
  catalog_entry_id=$MY_CATALOG_ENTRY_ID,
  requestee_id=$REQUESTEE_USER_ID,
  justification="Runbook CRUD test"
)
```
**Expect:** `result["id"]` → `$MY_NEW_REQUEST_ID`; no `error`

**GET:** `get_my_access_request(request_id=$MY_NEW_REQUEST_ID)`  
**Expect:** `result["id"] == $MY_NEW_REQUEST_ID`

**CANCEL (cleanup):** _(use `cancel_access_request` from the admin tools, or if self-service cancel is available)_  
⏭️ Cancel may not be available from end-user context depending on workflow stage.

---

## Section 3 — My Governance Settings & Connections

### T-7: get_my_governance_settings

**Call:** `get_my_governance_settings()`  
**Expect:** no `error`; result is a dict

---

### T-8: update_my_governance_settings (no-op)

**Call:** `update_my_governance_settings(<current settings from T-7>)`  
**Expect:** no `error`

---

### T-9: get_my_agent_managed_connections

**Call:** `get_my_agent_managed_connections()`  
**Expect:** no `error`; `items` is a list (may be empty)

---

### T-10: list_my_delegate_users

**Call:** `list_my_delegate_users(limit=5)`  
**Expect:** `items` is a list; no `error`

---

## Section 4 — My Security Access Reviews

### T-11: list_my_security_access_reviews

**Call:** `list_my_security_access_reviews(limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$MY_SAR_ID` = `items[0]["id"]` if non-empty  
⏭️ If empty: skip T-12 through T-21.

---

### T-12: get_my_security_access_review

**Call:** `get_my_security_access_review(review_id=$MY_SAR_ID)`  
**Expect:** `result["id"] == $MY_SAR_ID`; no `error`

---

### T-13: get_my_security_access_review_stats

**Call:** `get_my_security_access_review_stats(review_id=$MY_SAR_ID)`  
**Expect:** no `error`; result has counts/totals

---

### T-14: list_my_security_access_review_accesses

**Call:** `list_my_security_access_review_accesses(review_id=$MY_SAR_ID, limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$MY_SAR_ACCESS_ID` = `items[0]["id"]` if non-empty

---

### T-15: list_my_security_access_review_sub_accesses

⏭️ Skip if `$MY_SAR_ACCESS_ID` not set.

**Call:** `list_my_security_access_review_sub_accesses(review_id=$MY_SAR_ID, access_id=$MY_SAR_ACCESS_ID, limit=5)`  
**Expect:** `items` is a list; no `error`

---

### T-16: get_my_security_access_review_access_anomalies

⏭️ Skip if `$MY_SAR_ACCESS_ID` not set.

**Call:** `get_my_security_access_review_access_anomalies(review_id=$MY_SAR_ID, access_id=$MY_SAR_ACCESS_ID)`  
**Expect:** no `error`

---

### T-17: list_my_security_access_review_actions

**Call:** `list_my_security_access_review_actions(review_id=$MY_SAR_ID, limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$MY_SAR_ACTION_ID` = `items[0]["id"]` if non-empty

---

### T-18: submit_my_security_access_review_access_action

⏭️ Skip unless caller is assigned as reviewer and `$MY_SAR_ACCESS_ID` is set.

**Call:** `submit_my_security_access_review_access_action(review_id=$MY_SAR_ID, access_id=$MY_SAR_ACCESS_ID, decision="APPROVE")`  
**Expect:** no `error`

---

### T-19: submit_my_security_access_review_action

⏭️ Skip unless `$MY_SAR_ACTION_ID` is set and caller is reviewer.

**Call:** `submit_my_security_access_review_action(review_id=$MY_SAR_ID, action_id=$MY_SAR_ACTION_ID, decision="APPROVE")`  
**Expect:** no `error`

---

### T-20: add_my_security_access_review_comment

⏭️ Skip if `$MY_SAR_ID` not set.

**Call:** `add_my_security_access_review_comment(review_id=$MY_SAR_ID, comment="Runbook test comment")`  
**Expect:** no `error`

---

### T-21: get_my_security_access_review_history

**Call:** `get_my_security_access_review_history(review_id=$MY_SAR_ID)`  
**Expect:** no `error`; result has history entries

---

### T-22: get_my_security_access_review_principal

**Call:** `get_my_security_access_review_principal(review_id=$MY_SAR_ID)`  
**Expect:** no `error`; result identifies the principal being reviewed

---

### T-23: create_my_security_access_review_access_summary

⏭️ Skip if `$MY_SAR_ACCESS_ID` not set.

**Call:** `create_my_security_access_review_access_summary(review_id=$MY_SAR_ID, access_id=$MY_SAR_ACCESS_ID)`  
**Expect:** no `error`

---

### T-24: create_my_security_access_review_summary

**Call:** `create_my_security_access_review_summary(review_id=$MY_SAR_ID)`  
**Expect:** no `error`

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| My Catalog | T-1 – T-5 | Caller-context read; create/cancel access request |
| My Access Requests | T-6 | Create + cancel cycle |
| My Governance Settings | T-7 – T-10 | Read + no-op update; delegate list |
| My Security Reviews | T-11 – T-24 | Full review workflow; actions require reviewer role |
