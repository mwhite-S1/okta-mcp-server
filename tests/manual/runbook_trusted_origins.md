# Runbook: Trusted Origins

Covers `trusted_origins.py` — 7 tools total.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_ORIGIN_ID` | `list_trusted_origins()` → first item `id` |
| `$TEST_ORIGIN_ID` | Created in T-3; deleted in T-7 |

---

## Section 1 — Trusted Origins

### T-1: list_trusted_origins

**Call:** `list_trusted_origins()`  
**Expect:** `items` is a list; each item has `id`, `name`, `origin`, `status`  
→ set `$FIRST_ORIGIN_ID` = `items[0]["id"]` if non-empty

---

### T-2: get_trusted_origin

⏭️ Skip if `$FIRST_ORIGIN_ID` not set.

**Call:** `get_trusted_origin(trusted_origin_id=$FIRST_ORIGIN_ID)`  
**Expect:** `result["id"] == $FIRST_ORIGIN_ID`; no `error`

---

### T-3: 🔁 create_trusted_origin → activate/deactivate → replace → delete

**CREATE:**
```
create_trusted_origin(
  name="runbook-test-origin",
  origin="https://runbook-test.example.com",
  scopes=[{"type": "CORS"}, {"type": "REDIRECT"}]
)
```
**Expect:** `result["id"]` → `$TEST_ORIGIN_ID`; `result["name"] == "runbook-test-origin"`

---

### T-4: get newly created origin

**Call:** `get_trusted_origin(trusted_origin_id=$TEST_ORIGIN_ID)`  
**Expect:** `result["id"] == $TEST_ORIGIN_ID`; `result["origin"] == "https://runbook-test.example.com"`

---

### T-5: activate_trusted_origin + deactivate_trusted_origin 🔁

**ACTIVATE:** `activate_trusted_origin(trusted_origin_id=$TEST_ORIGIN_ID)`  
**Expect:** no `error`

**DEACTIVATE:** `deactivate_trusted_origin(trusted_origin_id=$TEST_ORIGIN_ID)`  
**Expect:** no `error`

---

### T-6: replace_trusted_origin

**Call:**
```
replace_trusted_origin(
  trusted_origin_id=$TEST_ORIGIN_ID,
  name="runbook-test-origin-replaced",
  origin="https://runbook-test.example.com",
  scopes=[{"type": "CORS"}]
)
```
**Expect:** no `error`; `result["name"] == "runbook-test-origin-replaced"`

---

### T-7: delete_trusted_origin ⚠️

**Call:** `delete_trusted_origin(trusted_origin_id=$TEST_ORIGIN_ID)`  
**Expect:** no `error`  
**VERIFY:** `get_trusted_origin(trusted_origin_id=$TEST_ORIGIN_ID)` → `"error"` in result

---

## Summary

| Tests | Notes |
|-------|-------|
| T-1 – T-7 | Full CRUD + activate/deactivate on a test origin |
