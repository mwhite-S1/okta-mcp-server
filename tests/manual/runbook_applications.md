# Runbook: Applications

Covers `applications.py`, `application_users.py`, `application_groups.py`,
`application_tokens.py`, `application_features.py`, `application_grants.py`,
`application_push.py` — 41 tools total.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_APP_ID` | `list_applications(limit=1)` → first `id` |
| `$FIRST_ACTIVE_USER_ID` | `list_users(filter='status eq "ACTIVE"', limit=1)` → first `id` |
| `$FIRST_GROUP_ID` | `list_groups(limit=1)` → first `id` |
| `$TEST_APP_ID` | Created in T-5; deleted in T-9 |

---

## Section 1 — Applications (Core)

### T-1: list_applications

**Call:** `list_applications(limit=5)`  
**Expect:** `{"items": [...]}` — each item has `id`, `name`, `status`, `signOnMode`

---

### T-2: get_application

**Call:** `get_application(app_id=$FIRST_APP_ID)`  
**Expect:** `result["id"] == $FIRST_APP_ID`; no `error`

---

### T-3: deactivate_application + activate_application 🔁

⚠️ Deactivating affects real users. Run only on a test/sandbox app.  
⏭️ Skip unless `$FIRST_APP_ID` is a known test app.

**DEACTIVATE:** `deactivate_application(app_id=$FIRST_APP_ID)`  
**Expect:** no `error`

**VERIFY:** `get_application(app_id=$FIRST_APP_ID)` → `status == "INACTIVE"`

**ACTIVATE:** `activate_application(app_id=$FIRST_APP_ID)`  
**Expect:** no `error`

**VERIFY:** `get_application(app_id=$FIRST_APP_ID)` → `status == "ACTIVE"`

---

### T-4: update_application

**Call:** `update_application(app_id=$FIRST_APP_ID, label="<current_label>")` _(no-op: same label)_  
**Expect:** no `error`; `result["id"] == $FIRST_APP_ID`

---

### T-5: 🔁 create_application → delete

**CREATE:**
```
create_application(
  name="bookmark",
  label="runbook-test-app",
  sign_on_mode="BOOKMARK",
  settings={"app": {"requestIntegration": False, "url": "https://example.com"}}
)
```
**Expect:** `result["id"]` → `$TEST_APP_ID`; `result["status"] == "ACTIVE"`

---

### T-6: delete_application ⚠️

First deactivate (required before delete):  
**Call:** `deactivate_application(app_id=$TEST_APP_ID)`

**DELETE:** `delete_application(app_id=$TEST_APP_ID)`  
**Expect:** no `error`  
**VERIFY:** `get_application(app_id=$TEST_APP_ID)` → `"error"` in result

---

### T-7: invalid app returns error

**Call:** `get_application(app_id="invalid-app-000")`  
**Expect:** `"error"` in result

---

## Section 2 — Application Users

### T-8: list_application_users

**Call:** `list_application_users(app_id=$FIRST_APP_ID, limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_APP_USER_ID` = `items[0]["id"]` if non-empty

---

### T-9: get_application_user

⏭️ Skip if `$FIRST_APP_USER_ID` not set.

**Call:** `get_application_user(app_id=$FIRST_APP_ID, user_id=$FIRST_APP_USER_ID)`  
**Expect:** `result["id"] == $FIRST_APP_USER_ID`; no `error`

---

### T-10: 🔁 assign_user_to_application → update → unassign

⏭️ Skip if `$FIRST_ACTIVE_USER_ID` is already assigned to `$FIRST_APP_ID`.

**ASSIGN:** `assign_user_to_application(app_id=$FIRST_APP_ID, user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** no `error`

**UPDATE:** `update_application_user(app_id=$FIRST_APP_ID, user_id=$FIRST_ACTIVE_USER_ID, profile={})`  
**Expect:** no `error`

**UNASSIGN:** `unassign_user_from_application(app_id=$FIRST_APP_ID, user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** no `error`

---

## Section 3 — Application Groups

### T-11: list_application_group_assignments

**Call:** `list_application_group_assignments(app_id=$FIRST_APP_ID, limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_APP_GROUP_ID` = `items[0]["id"]` if non-empty

---

### T-12: get_application_group_assignment

⏭️ Skip if `$FIRST_APP_GROUP_ID` not set.

**Call:** `get_application_group_assignment(app_id=$FIRST_APP_ID, group_id=$FIRST_APP_GROUP_ID)`  
**Expect:** `result["id"] == $FIRST_APP_GROUP_ID`; no `error`

---

### T-13: 🔁 assign_group_to_application → update → unassign

⏭️ Skip if `$FIRST_GROUP_ID` is already assigned to `$FIRST_APP_ID`.

**ASSIGN:** `assign_group_to_application(app_id=$FIRST_APP_ID, group_id=$FIRST_GROUP_ID)`  
**Expect:** no `error`

**UPDATE:** `update_application_group_assignment(app_id=$FIRST_APP_ID, group_id=$FIRST_GROUP_ID, priority=1)`  
**Expect:** no `error`

**UNASSIGN:** `unassign_group_from_application(app_id=$FIRST_APP_ID, group_id=$FIRST_GROUP_ID)`  
**Expect:** no `error`

---

## Section 4 — Application Tokens

### T-14: list_application_tokens

**Call:** `list_application_tokens(app_id=$FIRST_APP_ID, limit=5)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_TOKEN_ID` = `items[0]["id"]` if non-empty

---

### T-15: get_application_token

⏭️ Skip if `$FIRST_TOKEN_ID` not set.

**Call:** `get_application_token(app_id=$FIRST_APP_ID, token_id=$FIRST_TOKEN_ID)`  
**Expect:** `result["id"] == $FIRST_TOKEN_ID`; no `error`

---

### T-16: revoke_application_token ⚠️

⏭️ Skip unless `$FIRST_TOKEN_ID` is a test/disposable token.

**Call:** `revoke_application_token(app_id=$FIRST_APP_ID, token_id=$FIRST_TOKEN_ID)`  
**Expect:** no `error`

---

## Section 5 — Application Features

### T-17: list_application_features

**Call:** `list_application_features(app_id=$FIRST_APP_ID)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_FEATURE_NAME` = `items[0]["name"]` if non-empty

---

### T-18: get_application_feature

⏭️ Skip if `$FIRST_FEATURE_NAME` not set.

**Call:** `get_application_feature(app_id=$FIRST_APP_ID, feature_name=$FIRST_FEATURE_NAME)`  
**Expect:** `result["name"] == $FIRST_FEATURE_NAME`; no `error`

---

### T-19: preview_saml_metadata

⏭️ Skip if `$FIRST_APP_ID` is not a SAML app.

**Call:** `preview_saml_metadata(app_id=$FIRST_APP_ID)`  
**Expect:** result contains XML metadata string or dict with metadata; no `error`

---

### T-20: assign_application_policy

⏭️ Requires knowledge of a policy ID. Skip if not available.

**Call:** `assign_application_policy(app_id=$FIRST_APP_ID, policy_id=<an_access_policy_id>)`  
**Expect:** no `error`

---

## Section 6 — Application Grants (OAuth Scope Consents)

### T-21: list_scope_consent_grants

**Call:** `list_scope_consent_grants(app_id=$FIRST_APP_ID)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_GRANT_ID` = `items[0]["id"]` if non-empty

---

### T-22: get_scope_consent_grant

⏭️ Skip if `$FIRST_GRANT_ID` not set.

**Call:** `get_scope_consent_grant(app_id=$FIRST_APP_ID, grant_id=$FIRST_GRANT_ID)`  
**Expect:** `result["id"] == $FIRST_GRANT_ID`; no `error`

---

### T-23: 🔁 grant_consent_to_scope → revoke

**GRANT:**
```
grant_consent_to_scope(
  app_id=$FIRST_APP_ID,
  scope_id="okta.users.read",
  issuer="<org_url>"
)
```
⏭️ Skip if scope already granted.  
**Expect:** `result["id"]` → `$NEW_GRANT_ID`

**REVOKE:** `revoke_scope_consent_grant(app_id=$FIRST_APP_ID, grant_id=$NEW_GRANT_ID)`  
**Expect:** no `error`

---

## Section 7 — Group Push Mappings

### T-24: list_group_push_mappings

**Call:** `list_group_push_mappings(app_id=$FIRST_APP_ID)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_MAPPING_ID` = `items[0]["mappingId"]` if non-empty

---

### T-25: get_group_push_mapping

⏭️ Skip if `$FIRST_MAPPING_ID` not set.

**Call:** `get_group_push_mapping(app_id=$FIRST_APP_ID, mapping_id=$FIRST_MAPPING_ID)`  
**Expect:** `result["mappingId"] == $FIRST_MAPPING_ID`; no `error`

---

### T-26: 🔁 create_group_push_mapping → update → delete

⏭️ Skip unless the app supports group push (e.g., SCIM provisioning apps).

**CREATE:**
```
create_group_push_mapping(
  app_id=$FIRST_APP_ID,
  group_id=$FIRST_GROUP_ID,
  push_status="PUSH"
)
```
**Expect:** `result["mappingId"]` → `$NEW_MAPPING_ID`

**UPDATE:** `update_group_push_mapping(app_id=$FIRST_APP_ID, mapping_id=$NEW_MAPPING_ID, push_status="PUSH")`  
**Expect:** no `error`

**DELETE:** `delete_group_push_mapping(app_id=$FIRST_APP_ID, mapping_id=$NEW_MAPPING_ID)`  
**Expect:** no `error`

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| Applications (core) | T-1 – T-7 | CRUD + lifecycle; use test app for deactivate |
| App Users | T-8 – T-10 | Assign/update/unassign cycle |
| App Groups | T-11 – T-13 | Assign/update/unassign cycle |
| Tokens | T-14 – T-16 | Read-only preferred; revoke only disposable tokens |
| Features | T-17 – T-20 | Read-only; policy assign requires known policy ID |
| Grants | T-21 – T-23 | Grant/revoke scope consent cycle |
| Push Mappings | T-24 – T-26 | SCIM apps only; full CRUD cycle |
