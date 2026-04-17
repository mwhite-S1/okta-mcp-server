# Runbook: Authenticators

Covers `authenticators.py` — 18 tools total.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_AUTH_ID` | `list_authenticators()` → first item `id` |
| `$PASSWORD_AUTH_ID` | `list_authenticators()` → item where `key == "okta_password"` → `id` |
| `$WEBAUTHN_AUTH_ID` | `list_authenticators()` → item where `key == "webauthn"` → `id` (may not exist) |

---

## Section 1 — Authenticators (Core)

### T-1: list_authenticators

**Call:** `list_authenticators()`  
**Expect:** `items` is a non-empty list (every org has password); each item has `id`, `key`, `name`, `status`  
→ set `$FIRST_AUTH_ID`, `$PASSWORD_AUTH_ID`, `$WEBAUTHN_AUTH_ID` (if present)

---

### T-2: get_authenticator

**Call:** `get_authenticator(authenticator_id=$PASSWORD_AUTH_ID)`  
**Expect:** `result["id"] == $PASSWORD_AUTH_ID`; `result["key"] == "okta_password"`; no `error`

---

### T-3: replace_authenticator (no-op safe write)

**Call:** `replace_authenticator(authenticator_id=$PASSWORD_AUTH_ID, authenticator_data={"name": "<current name from T-2>"})`  
**Expect:** `result["id"] == $PASSWORD_AUTH_ID`; no `error`

---

### T-4: activate_authenticator + deactivate_authenticator 🔁

⚠️ Deactivating an in-use authenticator blocks users. Use a non-primary test authenticator.  
⏭️ Skip unless org has a non-critical inactive authenticator to cycle.

**DEACTIVATE:** `deactivate_authenticator(authenticator_id=$FIRST_AUTH_ID)`  
**Expect:** no `error`

**ACTIVATE:** `activate_authenticator(authenticator_id=$FIRST_AUTH_ID)`  
**Expect:** no `error`

---

### T-5: invalid id returns error

**Call:** `get_authenticator(authenticator_id="invalid-auth-000")`  
**Expect:** `"error"` in result

---

## Section 2 — Authenticator Methods

### T-6: list_authenticator_methods

**Call:** `list_authenticator_methods(authenticator_id=$PASSWORD_AUTH_ID)`  
**Expect:** `items` is a list; each item has `type`; no `error`  
→ set `$FIRST_METHOD_TYPE` = `items[0]["type"]` (typically `"password"`)

---

### T-7: get_authenticator_method

**Call:** `get_authenticator_method(authenticator_id=$PASSWORD_AUTH_ID, method_type="password")`  
**Expect:** `result["type"] == "password"`; no `error`

---

### T-8: invalid method type returns error

**Call:** `get_authenticator_method(authenticator_id=$PASSWORD_AUTH_ID, method_type="nonexistent_method_type")`  
**Expect:** `"error"` in result

---

### T-9: replace_authenticator_method (no-op)

**Call:** `replace_authenticator_method(authenticator_id=$PASSWORD_AUTH_ID, method_type="password", method_data={"type": "password"})`  
**Expect:** no `error`

---

### T-10: activate_authenticator_method + deactivate_authenticator_method 🔁

⏭️ Skip unless org has a non-critical method that can be safely cycled.

**DEACTIVATE:** `deactivate_authenticator_method(authenticator_id=$FIRST_AUTH_ID, method_type=$FIRST_METHOD_TYPE)`  
**ACTIVATE:** `activate_authenticator_method(authenticator_id=$FIRST_AUTH_ID, method_type=$FIRST_METHOD_TYPE)`  
**Expect:** no `error` on both

---

## Section 3 — WebAuthn AAGUIDs

⏭️ All tests in this section skip if `$WEBAUTHN_AUTH_ID` is not set.

### T-11: list_custom_aaguids

**Call:** `list_custom_aaguids(authenticator_id=$WEBAUTHN_AUTH_ID)`  
**Expect:** `items` is a list (may be empty); no `error`  
→ set `$FIRST_AAGUID` = `items[0]["aaguid"]` if non-empty

---

### T-12: 🔁 create_custom_aaguid → get → replace → update → delete

**CREATE:**
```
create_custom_aaguid(
  authenticator_id=$WEBAUTHN_AUTH_ID,
  aaguid="00000000-0000-0000-0000-000000000001",
  name="Runbook Test Key"
)
```
**Expect:** no `error`; result has `aaguid` field

---

### T-13: get_custom_aaguid

**Call:** `get_custom_aaguid(authenticator_id=$WEBAUTHN_AUTH_ID, aaguid="00000000-0000-0000-0000-000000000001")`  
**Expect:** `result["aaguid"] == "00000000-0000-0000-0000-000000000001"`; no `error`

---

### T-14: replace_custom_aaguid

**Call:** `replace_custom_aaguid(authenticator_id=$WEBAUTHN_AUTH_ID, aaguid="00000000-0000-0000-0000-000000000001", name="Runbook Test Key Updated")`  
**Expect:** no `error`; `result["name"] == "Runbook Test Key Updated"`

---

### T-15: update_custom_aaguid (partial)

**Call:** `update_custom_aaguid(authenticator_id=$WEBAUTHN_AUTH_ID, aaguid="00000000-0000-0000-0000-000000000001", name="Runbook Test Key Patched")`  
**Expect:** no `error`

---

### T-16: delete_custom_aaguid ⚠️

**Call:** `delete_custom_aaguid(authenticator_id=$WEBAUTHN_AUTH_ID, aaguid="00000000-0000-0000-0000-000000000001")`  
**Expect:** no `error`

---

## Section 4 — RP ID Domain Verification

### T-17: verify_rp_id_domain

**Call:** `verify_rp_id_domain(authenticator_id=$WEBAUTHN_AUTH_ID, rp_id="example.com")`  
⏭️ Skip if `$WEBAUTHN_AUTH_ID` not set.  
**Expect:** no `error`; result indicates whether the RP ID domain is verifiable

---

### T-18: invalid authenticator returns error

**Call:** `list_authenticator_methods(authenticator_id="invalid-000")`  
**Expect:** `"error"` in result

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| Authenticators (core) | T-1 – T-5 | Replace (no-op), activate/deactivate cautiously |
| Methods | T-6 – T-10 | Get/replace password method; cycle non-critical |
| AAGUIDs | T-11 – T-16 | Full CRUD; WebAuthn authenticator required |
| RP ID | T-17 – T-18 | Domain verification |
