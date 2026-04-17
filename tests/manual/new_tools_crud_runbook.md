# New Tools CRUD Test Runbook

## Purpose

This runbook tests the four new tool domains added in the Tier 1/2 expansion:

- **Authenticators** — list, get, replace, lifecycle, methods, AAGUIDs
- **Application Credentials** — signing keys, CSRs, OAuth JWKs, client secrets
- **Agent Pools** — list pools and updates, get settings
- **User Role Targets** — list app/group targets, assign/unassign group targets

## How to Run

1. Rebuild and restart the MCP server so the new tools are loaded:
   ```
   docker compose -f docker-compose.yml build okta-mcp-server
   docker compose -f docker-compose.yml up -d
   ```
2. In a Claude conversation with the MCP server connected, paste:
   > "Please run the new tools CRUD test runbook at
   > `okta-mcp-server/tests/manual/new_tools_crud_runbook.md`.
   > Execute each tool call in order, report pass/fail for each check,
   > and perform cleanup when indicated."

Claude will execute the tool calls below in sequence, reporting results inline.

---

## Prerequisites

Before running, Claude should resolve these values and remember them for the
rest of the runbook:

| Variable            | How to resolve                                                        |
|---------------------|-----------------------------------------------------------------------|
| `$FIRST_APP_ID`     | Call `list_applications(limit=1)` → first item `id`                  |
| `$FIRST_GROUP_ID`   | Call `list_groups(limit=1)` → first item `id`                        |
| `$FIRST_USER_ID`    | Call `list_users(filter='status eq "ACTIVE"', limit=1)` → first `id` |
| `$PASSWORD_AUTH_ID` | Call `list_authenticators` → item where `key == "okta_password"` → `id` |

---

## 1. Authenticators

### 1.1 List Authenticators

**Tool:** `list_authenticators`  
**Parameters:** _(none)_  
**Checks:**
- Response is `{"items": [...], ...}`
- `items` is a non-empty list (every org has a password authenticator)
- Each item has `id`, `key`, `name`, `status`

Set `$PASSWORD_AUTH_ID` = the `id` of the item where `key == "okta_password"`.

---

### 1.2 Get Authenticator

**Tool:** `get_authenticator`  
**Parameters:** `authenticator_id=$PASSWORD_AUTH_ID`  
**Checks:**
- `result["id"] == $PASSWORD_AUTH_ID`
- `result["key"] == "okta_password"`
- No `error` key in result

---

### 1.3 List Authenticator Methods

**Tool:** `list_authenticator_methods`  
**Parameters:** `authenticator_id=$PASSWORD_AUTH_ID`  
**Checks:**
- `items` is a list
- Each item has a `type` field

Set `$PASSWORD_METHOD_TYPE` = `items[0]["type"]` (typically `"password"`).

---

### 1.4 Get Authenticator Method

**Tool:** `get_authenticator_method`  
**Parameters:** `authenticator_id=$PASSWORD_AUTH_ID`, `method_type="password"`  
**Checks:**
- `result["type"] == "password"`
- No `error` key

---

### 1.5 Replace Authenticator (no-op safe write)

**Tool:** `replace_authenticator`  
**Parameters:** `authenticator_id=$PASSWORD_AUTH_ID`, `authenticator_data={"name": "<current name from 1.2>"}`  
**Checks:**
- `result["id"] == $PASSWORD_AUTH_ID`
- `result["name"]` matches what was passed
- No `error` key

_This is a safe no-op write — it sends back the same name the authenticator already has._

---

### 1.6 Invalid ID Returns Error

**Tool:** `get_authenticator`  
**Parameters:** `authenticator_id="invalid-auth-000"`  
**Checks:**
- Result contains `"error"` key

---

### 1.7 WebAuthn AAGUIDs (conditional)

**Tool:** `list_custom_aaguids`  
**Parameters:** `authenticator_id=<id of item where key=="webauthn">` from the 1.1 list  
_Skip this test if no WebAuthn authenticator exists in the org._  
**Checks:**
- `items` is a list (may be empty)
- No `error` key

---

## 2. Application Credentials

### 2.1 List Application Signing Keys

**Tool:** `list_application_keys`  
**Parameters:** `app_id=$FIRST_APP_ID`  
**Checks:**
- `items` is a list
- Each item has `kid`

Set `$FIRST_KID` = `items[0]["kid"]` (skip section 2.2 if list is empty).

---

### 2.2 Get Application Signing Key

**Tool:** `get_application_key`  
**Parameters:** `app_id=$FIRST_APP_ID`, `key_id=$FIRST_KID`  
**Checks:**
- `result["kid"] == $FIRST_KID`
- No `error`

---

### 2.3 Generate Signing Key (CREATE + CLEANUP)

**Tool:** `generate_application_key`  
**Parameters:** `app_id=$FIRST_APP_ID`, `validity_years=1`  
**Checks:**
- `result["kid"]` is present → set `$NEW_KID`
- No `error`

**Verify:**  
**Tool:** `get_application_key`  
**Parameters:** `app_id=$FIRST_APP_ID`, `key_id=$NEW_KID`  
**Checks:** `result["kid"] == $NEW_KID`

_Note: SSO signing keys cannot be deleted via API — they expire naturally. No cleanup needed._

---

### 2.4 List Application CSRs

**Tool:** `list_application_csrs`  
**Parameters:** `app_id=$FIRST_APP_ID`  
**Checks:**
- `items` is a list
- No `error`

---

### 2.5 Generate and Revoke CSR (CREATE → READ → DELETE)

**Tool:** `generate_application_csr`  
**Parameters:**
```json
{
  "app_id": "$FIRST_APP_ID",
  "subject": {
    "countryName": "US",
    "stateOrProvinceName": "California",
    "localityName": "San Francisco",
    "organizationName": "Runbook Test Org",
    "organizationalUnitName": "Engineering",
    "commonName": "runbook-test.example.com"
  }
}
```
**Checks:**
- `result["id"]` is present → set `$NEW_CSR_ID`
- `result["csrValue"]` or `result["kty"]` is present
- No `error`

**Verify:**  
**Tool:** `get_application_csr`  
**Parameters:** `app_id=$FIRST_APP_ID`, `csr_id=$NEW_CSR_ID`  
**Checks:** `result["id"] == $NEW_CSR_ID`

**Cleanup:**  
**Tool:** `revoke_application_csr`  
**Parameters:** `app_id=$FIRST_APP_ID`, `csr_id=$NEW_CSR_ID`  
**Checks:** No `error` key in result

---

### 2.6 List OAuth JWKs

**Tool:** `list_application_jwks`  
**Parameters:** `app_id=$FIRST_APP_ID`  
**Checks:**
- `items` is a list
- No `error`

---

### 2.7 List OAuth Client Secrets

**Tool:** `list_oauth2_client_secrets`  
**Parameters:** `app_id=$FIRST_APP_ID`  
**Checks:**
- `items` is a list
- No `error`
- No item has `"client_secret"` key (secret value must not be in list response)

---

### 2.8 Create and Delete Client Secret (CREATE → READ → DELETE)

**Tool:** `create_oauth2_client_secret`  
**Parameters:** `app_id=$FIRST_APP_ID`  
_Skip if result contains `error` — app may not support client secrets (e.g., SAML-only)._  
**Checks:**
- `result["id"]` is present → set `$NEW_SECRET_ID`
- `result["client_secret"]` or `result["secretHash"]` is present (value only returned at creation)

**Verify:**  
**Tool:** `get_oauth2_client_secret`  
**Parameters:** `app_id=$FIRST_APP_ID`, `secret_id=$NEW_SECRET_ID`  
**Checks:**
- `result["id"] == $NEW_SECRET_ID`
- `"client_secret"` NOT in result (value not re-retrievable after creation)

**Cleanup:**  
**Tool:** `delete_oauth2_client_secret`  
**Parameters:** `app_id=$FIRST_APP_ID`, `secret_id=$NEW_SECRET_ID`  
**Checks:** No `error`

---

### 2.9 Invalid App ID Returns Error

**Tool:** `list_application_keys`  
**Parameters:** `app_id="invalid-app-000"`  
**Checks:** `"error"` in result

---

## 3. Agent Pools

_If the org has no AD/LDAP agents configured, all pool-specific tests (3.2–3.4)
will return empty lists or errors — skip them gracefully._

### 3.1 List Agent Pools

**Tool:** `list_agent_pools`  
**Parameters:** _(none)_  
**Checks:**
- `items` is a list
- No `error`
- Each item (if any) has `id` and `type`

If `items` is empty: skip 3.2–3.4.  
Otherwise set `$FIRST_POOL_ID` = `items[0]["id"]`.

---

### 3.2 List Agent Pool Updates

**Tool:** `list_agent_pool_updates`  
**Parameters:** `pool_id=$FIRST_POOL_ID`  
**Checks:**
- `items` is a list
- No `error`

Set `$FIRST_UPDATE_ID` = `items[0]["id"]` if list is non-empty.

---

### 3.3 Get Agent Pool Update Settings

**Tool:** `get_agent_pool_update_settings`  
**Parameters:** `pool_id=$FIRST_POOL_ID`  
**Checks:**
- No `error`
- Result is a dict

---

### 3.4 Get Agent Pool Update (conditional)

_Skip if `$FIRST_UPDATE_ID` is not set (no updates exist)._

**Tool:** `get_agent_pool_update`  
**Parameters:** `pool_id=$FIRST_POOL_ID`, `update_id=$FIRST_UPDATE_ID`  
**Checks:**
- `result["id"] == $FIRST_UPDATE_ID`
- No `error`

---

### 3.5 Pool Type Filter

**Tool:** `list_agent_pools`  
**Parameters:** `pool_type="AD"`  
**Checks:**
- `items` is a list
- No `error`

---

### 3.6 Invalid Pool ID Returns Error

**Tool:** `list_agent_pool_updates`  
**Parameters:** `pool_id="invalid-pool-000"`  
**Checks:** `"error"` in result

---

## 4. User Role Targets

_These tests require a user with at least one admin role assignment.
If no such user exists, skip the role-specific sub-tests._

### 4.1 Find a User with a Role Assignment

**Tool:** `list_users`  
**Parameters:** `filter='status eq "ACTIVE"'`, `limit=10`  

For each user returned, call:

**Tool:** (internal — use Okta SDK or `get_user_role_targets`)  
The simplest approach: call `list_user_group_role_targets` with candidate user IDs
until one succeeds without a 403/404.

Alternatively, if the org's admin structure is known, use that user's ID directly.

Set `$ROLE_USER_ID` and `$ROLE_ASSIGNMENT_ID`.  
_Skip 4.2–4.7 if no user with a role assignment is found._

---

### 4.2 List User App Role Targets

**Tool:** `list_user_app_role_targets`  
**Parameters:** `user_id=$ROLE_USER_ID`, `role_assignment_id=$ROLE_ASSIGNMENT_ID`  
**Checks:**
- `items` is a list
- No `error`
- Each item (if any) has `id` or `name`

---

### 4.3 List User Group Role Targets

**Tool:** `list_user_group_role_targets`  
**Parameters:** `user_id=$ROLE_USER_ID`, `role_assignment_id=$ROLE_ASSIGNMENT_ID`  
**Checks:**
- `items` is a list
- No `error`
- Each item (if any) has `id`

---

### 4.4 Get User Role Targets (combined view)

**Tool:** `get_user_role_targets`  
**Parameters:** `user_id=$ROLE_USER_ID`, `role_id=$ROLE_ASSIGNMENT_ID`  
**Checks:**
- Response is a dict
- No `error`

---

### 4.5 Assign and Unassign Group Target (CREATE → VERIFY → DELETE)

_Skip if `$FIRST_GROUP_ID` is already in the targets list from 4.3._

**Tool:** `assign_group_target_to_user_role`  
**Parameters:**
```json
{
  "user_id": "$ROLE_USER_ID",
  "role_assignment_id": "$ROLE_ASSIGNMENT_ID",
  "group_id": "$FIRST_GROUP_ID"
}
```
**Checks:**
- No `error`

**Verify:**  
**Tool:** `list_user_group_role_targets`  
**Parameters:** `user_id=$ROLE_USER_ID`, `role_assignment_id=$ROLE_ASSIGNMENT_ID`  
**Checks:** `$FIRST_GROUP_ID` appears in `items[*]["id"]`

**Cleanup:**  
**Tool:** `unassign_group_target_from_user_role`  
**Parameters:** `user_id=$ROLE_USER_ID`, `role_assignment_id=$ROLE_ASSIGNMENT_ID`, `group_id=$FIRST_GROUP_ID`  
**Checks:** No `error`

**Verify cleanup:**  
**Tool:** `list_user_group_role_targets`  
**Parameters:** `user_id=$ROLE_USER_ID`, `role_assignment_id=$ROLE_ASSIGNMENT_ID`  
**Checks:** `$FIRST_GROUP_ID` no longer appears in `items[*]["id"]`

---

### 4.6 Invalid User Returns Error

**Tool:** `list_user_app_role_targets`  
**Parameters:** `user_id="invalid-user-000"`, `role_assignment_id="role-000"`  
**Checks:** `"error"` in result

---

## 5. Summary Scorecard

After running all tests, report a table:

| Domain                   | Tests Run | Passed | Skipped | Failed |
|--------------------------|-----------|--------|---------|--------|
| Authenticators           |           |        |         |        |
| Application Credentials  |           |        |         |        |
| Agent Pools              |           |        |         |        |
| User Role Targets        |           |        |         |        |
| **Total**                |           |        |         |        |

List any failures with the tool name, parameters used, and actual vs. expected result.
