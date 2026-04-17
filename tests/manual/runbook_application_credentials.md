# Runbook: Application Credentials

Covers `application_credentials.py` and `application_connections.py` — 27 tools total.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_APP_ID` | `list_applications(limit=1)` → first `id` |

---

## Section 1 — SSO Signing Keys

### T-1: list_application_keys

**Call:** `list_application_keys(app_id=$FIRST_APP_ID)`  
**Expect:** `items` is a list; each item has `kid`; no `error`  
→ set `$FIRST_KID` = `items[0]["kid"]` if non-empty

---

### T-2: get_application_key

⏭️ Skip if `$FIRST_KID` not set.

**Call:** `get_application_key(app_id=$FIRST_APP_ID, key_id=$FIRST_KID)`  
**Expect:** `result["kid"] == $FIRST_KID`; no `error`

---

### T-3: generate_application_key

**Call:** `generate_application_key(app_id=$FIRST_APP_ID, validity_years=1)`  
**Expect:** `result["kid"]` set → `$NEW_KID`; no `error`

**VERIFY:** `get_application_key(app_id=$FIRST_APP_ID, key_id=$NEW_KID)` → `result["kid"] == $NEW_KID`

_Note: SSO signing keys cannot be deleted via API — they expire. No cleanup needed._

---

### T-4: clone_application_key

⏭️ Skip if org has only one application or `$FIRST_KID` not set.

**Call:** `clone_application_key(app_id=$FIRST_APP_ID, key_id=$FIRST_KID, target_app_id=<second_app_id>)`  
**Expect:** cloned key appears in target app's key list; no `error`

---

### T-5: invalid app returns error

**Call:** `list_application_keys(app_id="invalid-app-000")`  
**Expect:** `"error"` in result

---

## Section 2 — Certificate Signing Requests (CSRs)

### T-6: list_application_csrs

**Call:** `list_application_csrs(app_id=$FIRST_APP_ID)`  
**Expect:** `items` is a list; no `error`

---

### T-7: 🔁 generate_application_csr → get → revoke

**GENERATE:**
```
generate_application_csr(
  app_id=$FIRST_APP_ID,
  subject={
    "countryName": "US",
    "stateOrProvinceName": "California",
    "localityName": "San Francisco",
    "organizationName": "Runbook Test",
    "organizationalUnitName": "Engineering",
    "commonName": "runbook-csr.example.com"
  }
)
```
**Expect:** `result["id"]` → `$NEW_CSR_ID`; `result["csrValue"]` or `result["kty"]` present

**GET:** `get_application_csr(app_id=$FIRST_APP_ID, csr_id=$NEW_CSR_ID)`  
**Expect:** `result["id"] == $NEW_CSR_ID`; no `error`

**REVOKE (cleanup):** `revoke_application_csr(app_id=$FIRST_APP_ID, csr_id=$NEW_CSR_ID)`  
**Expect:** no `error`

**VERIFY:** `get_application_csr(app_id=$FIRST_APP_ID, csr_id=$NEW_CSR_ID)` → `"error"` in result

---

### T-8: publish_application_csr

⏭️ Requires a signed certificate PEM. Skip in automated context.  
Behavior: accepts the CSR id and a DER/PEM certificate body, activates the key.

---

## Section 3 — OAuth JWKs (Public Keys)

### T-9: list_application_jwks

**Call:** `list_application_jwks(app_id=$FIRST_APP_ID)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_JWK_KID` = `items[0]["kid"]` if non-empty

---

### T-10: get_application_jwk

⏭️ Skip if `$FIRST_JWK_KID` not set.

**Call:** `get_application_jwk(app_id=$FIRST_APP_ID, key_id=$FIRST_JWK_KID)`  
**Expect:** `result["kid"] == $FIRST_JWK_KID`; no `error`

---

### T-11: 🔁 add_application_jwk → activate → deactivate → delete

⏭️ Skip unless app is an OAuth/OIDC app that supports JWKs.

**ADD:**
```
add_application_jwk(
  app_id=$FIRST_APP_ID,
  jwk={
    "kty": "RSA",
    "use": "sig",
    "n": "<base64url-modulus>",
    "e": "AQAB",
    "kid": "runbook-test-jwk"
  }
)
```
**Expect:** `result["kid"]` → `$NEW_JWK_KID`; no `error`

**ACTIVATE:** `activate_application_jwk(app_id=$FIRST_APP_ID, key_id=$NEW_JWK_KID)`  
**Expect:** no `error`

**DEACTIVATE:** `deactivate_application_jwk(app_id=$FIRST_APP_ID, key_id=$NEW_JWK_KID)`  
**Expect:** no `error`

**DELETE (cleanup):** `delete_application_jwk(app_id=$FIRST_APP_ID, key_id=$NEW_JWK_KID)`  
**Expect:** no `error`

---

## Section 4 — OAuth Client Secrets

### T-12: list_oauth2_client_secrets

**Call:** `list_oauth2_client_secrets(app_id=$FIRST_APP_ID)`  
**Expect:** `items` is a list; no `error`  
- Each item must have `id` but NOT `client_secret` (value never returned in list)  
→ set `$FIRST_SECRET_ID` = `items[0]["id"]` if non-empty

---

### T-13: get_oauth2_client_secret

⏭️ Skip if `$FIRST_SECRET_ID` not set.

**Call:** `get_oauth2_client_secret(app_id=$FIRST_APP_ID, secret_id=$FIRST_SECRET_ID)`  
**Expect:** `result["id"] == $FIRST_SECRET_ID`; `"client_secret"` NOT in result; no `error`

---

### T-14: 🔁 create_oauth2_client_secret → get → activate → deactivate → delete

⏭️ Skip if app does not support client secrets (e.g., SAML-only apps); result will contain `error`.

**CREATE:** `create_oauth2_client_secret(app_id=$FIRST_APP_ID)`  
**Expect:** `result["id"]` → `$NEW_SECRET_ID`; `result["client_secret"]` or `result["secretHash"]` present (only at creation)

**GET:** `get_oauth2_client_secret(app_id=$FIRST_APP_ID, secret_id=$NEW_SECRET_ID)`  
**Expect:** `result["id"] == $NEW_SECRET_ID`; `"client_secret"` NOT in result

**ACTIVATE:** `activate_oauth2_client_secret(app_id=$FIRST_APP_ID, secret_id=$NEW_SECRET_ID)`  
**Expect:** no `error`

**DEACTIVATE:** `deactivate_oauth2_client_secret(app_id=$FIRST_APP_ID, secret_id=$NEW_SECRET_ID)`  
**Expect:** no `error`

**DELETE (cleanup):** `delete_oauth2_client_secret(app_id=$FIRST_APP_ID, secret_id=$NEW_SECRET_ID)`  
**Expect:** no `error`

---

## Section 5 — Provisioning Connections

### T-15: get_default_provisioning_connection

**Call:** `get_default_provisioning_connection(app_id=$FIRST_APP_ID)`  
**Expect:** no `error` (may return 404 if app has no provisioning — that is an `error`)  
⏭️ Skip subsequent provisioning tests if this returns an error.

---

### T-16: get_provisioning_connection_jwks

**Call:** `get_provisioning_connection_jwks(app_id=$FIRST_APP_ID)`  
**Expect:** result has JWKS structure or empty; no `error`

---

### T-17: verify_provisioning_connection

**Call:** `verify_provisioning_connection(app_id=$FIRST_APP_ID)`  
**Expect:** no `error`; result may indicate connection status

---

### T-18: deactivate_provisioning_connection + activate 🔁

⚠️ Deactivating stops user provisioning. Run only on a test/dev app.

**DEACTIVATE:** `deactivate_provisioning_connection(app_id=$FIRST_APP_ID)`  
**Expect:** no `error`

**ACTIVATE:** `activate_provisioning_connection(app_id=$FIRST_APP_ID)`  
**Expect:** no `error`

---

### T-19: update_default_provisioning_connection

⏭️ Requires provisioning credentials (token/key). Skip if not available.

**Call:** `update_default_provisioning_connection(app_id=$FIRST_APP_ID, authScheme="TOKEN", token="<provisioning_token>")`  
**Expect:** no `error`

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| SSO Keys | T-1 – T-5 | Generate always works; clone needs second app |
| CSRs | T-6 – T-8 | Full generate/get/revoke cycle |
| JWKs | T-9 – T-11 | Add/activate/deactivate/delete; OAuth apps only |
| Client Secrets | T-12 – T-14 | Full lifecycle; secret value only at creation |
| Provisioning | T-15 – T-19 | SCIM/provisioning apps only |
