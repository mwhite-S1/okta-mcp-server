# Runbook: Schema and Profile Mappings

Covers `schema.py` and `profile_mappings.py` — 9 tools total.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_APP_ID` | `list_applications(limit=1)` → first `id` |
| `$FIRST_MAPPING_ID` | `list_profile_mappings(limit=1)` → first item `id` |

---

## Section 1 — Schema

### T-1: get_user_schema

**Call:** `get_user_schema()`  
**Expect:** result has `id`, `definitions` (with `base` and `custom`); no `error`

---

### T-2: get_group_schema

**Call:** `get_group_schema()`  
**Expect:** result has schema structure; no `error`

---

### T-3: get_application_user_schema

**Call:** `get_application_user_schema(app_id=$FIRST_APP_ID)`  
**Expect:** result has schema structure; no `error`

---

### T-4: update_user_profile (safe no-op)

Read the current user schema definition first, then send back an existing custom property unchanged.

**Call:** `update_user_profile(schema_update={"definitions": {"custom": {"properties": {}}}})`  
**Expect:** no `error`; schema returned

⚠️ Actually adding or removing schema properties affects all users — only run in dev orgs.

---

### T-5: update_group_schema (safe no-op)

**Call:** `update_group_schema(schema_update={"definitions": {"custom": {"properties": {}}}})`  
**Expect:** no `error`

---

### T-6: update_application_user_profile (safe no-op)

**Call:** `update_application_user_profile(app_id=$FIRST_APP_ID, schema_update={"definitions": {"custom": {"properties": {}}}})`  
**Expect:** no `error`

---

## Section 2 — Profile Mappings

### T-7: list_profile_mappings

**Call:** `list_profile_mappings(limit=5)`  
**Expect:** `items` is a list; each item has `id`, `source`, `target`; no `error`  
→ set `$FIRST_MAPPING_ID` = `items[0]["id"]` if non-empty

---

### T-8: get_profile_mapping

⏭️ Skip if `$FIRST_MAPPING_ID` not set.

**Call:** `get_profile_mapping(mapping_id=$FIRST_MAPPING_ID)`  
**Expect:** `result["id"] == $FIRST_MAPPING_ID`; has `source`, `target`, `properties`; no `error`

---

### T-9: update_profile_mapping (no-op)

Read the current mapping, then send back the same `properties` dict unchanged.

**Call:** `update_profile_mapping(mapping_id=$FIRST_MAPPING_ID, properties=<current properties from T-8>)`  
**Expect:** no `error`

⚠️ Changing property expressions affects how user profiles sync — only change in dev orgs.

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| Schema | T-1 – T-6 | Read-only safe; update ops are no-ops or dev-only |
| Profile Mappings | T-7 – T-9 | Read-only safe; update is a no-op |
