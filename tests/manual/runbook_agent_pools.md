# Runbook: Agent Pools

Covers `agent_pools.py` — 14 tools total.

⏭️ All pool-specific tests skip if the org has no AD/LDAP agents configured.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_POOL_ID` | `list_agent_pools()` → first item `id` |
| `$FIRST_UPDATE_ID` | `list_agent_pool_updates(pool_id=$FIRST_POOL_ID)` → first item `id` |

---

## Section 1 — Agent Pools

### T-1: list_agent_pools

**Call:** `list_agent_pools()`  
**Expect:** `items` is a list; no `error`; each item (if any) has `id`, `type`  
→ set `$FIRST_POOL_ID` = `items[0]["id"]` if non-empty  
⏭️ If empty: skip T-2 through T-13.

---

### T-2: list_agent_pools with type filter

**Call:** `list_agent_pools(pool_type="AD")`  
**Expect:** `items` is a list; no `error`

---

### T-3: get_agent_pool_update_settings

**Call:** `get_agent_pool_update_settings(pool_id=$FIRST_POOL_ID)`  
**Expect:** no `error`; result is a dict with schedule/settings fields

---

### T-4: update_agent_pool_update_settings (no-op: same values)

**Call:** `update_agent_pool_update_settings(pool_id=$FIRST_POOL_ID, setting=<current value from T-3>)`  
**Expect:** no `error`

---

## Section 2 — Agent Pool Updates

### T-5: list_agent_pool_updates

**Call:** `list_agent_pool_updates(pool_id=$FIRST_POOL_ID)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_UPDATE_ID` = `items[0]["id"]` if non-empty

---

### T-6: list_agent_pool_updates with scheduled filter

**Call:** `list_agent_pool_updates(pool_id=$FIRST_POOL_ID, scheduled=True)`  
**Expect:** `items` is a list; no `error`

---

### T-7: get_agent_pool_update

⏭️ Skip if `$FIRST_UPDATE_ID` not set.

**Call:** `get_agent_pool_update(pool_id=$FIRST_POOL_ID, update_id=$FIRST_UPDATE_ID)`  
**Expect:** `result["id"] == $FIRST_UPDATE_ID`; no `error`

---

### T-8: 🔁 create_agent_pool_update → update → activate → pause → resume → stop → delete

⚠️ Agent pool updates schedule real agent software upgrades. Only run in a non-production environment.

**CREATE:**
```
create_agent_pool_update(
  pool_id=$FIRST_POOL_ID,
  agent_type="AD",
  schedule_type="MANUAL"
)
```
**Expect:** `result["id"]` → `$NEW_UPDATE_ID`; no `error`

---

### T-9: update_agent_pool_update

**Call:** `update_agent_pool_update(pool_id=$FIRST_POOL_ID, update_id=$NEW_UPDATE_ID, schedule_type="MANUAL")`  
**Expect:** no `error`

---

### T-10: activate_agent_pool_update

**Call:** `activate_agent_pool_update(pool_id=$FIRST_POOL_ID, update_id=$NEW_UPDATE_ID)`  
**Expect:** no `error`

---

### T-11: pause_agent_pool_update

**Call:** `pause_agent_pool_update(pool_id=$FIRST_POOL_ID, update_id=$NEW_UPDATE_ID)`  
**Expect:** no `error`

---

### T-12: resume_agent_pool_update

**Call:** `resume_agent_pool_update(pool_id=$FIRST_POOL_ID, update_id=$NEW_UPDATE_ID)`  
**Expect:** no `error`

---

### T-13: stop_agent_pool_update

**Call:** `stop_agent_pool_update(pool_id=$FIRST_POOL_ID, update_id=$NEW_UPDATE_ID)`  
**Expect:** no `error`

---

### T-14: delete_agent_pool_update ⚠️

**Call:** `delete_agent_pool_update(pool_id=$FIRST_POOL_ID, update_id=$NEW_UPDATE_ID)`  
**Expect:** no `error`

---

### T-15: invalid pool returns error

**Call:** `list_agent_pool_updates(pool_id="invalid-pool-000")`  
**Expect:** `"error"` in result

---

## Section 3 — Retry

### T-16: retry_agent_pool_update

⏭️ Only applies to updates in a `FAILED` state. Skip if no failed updates exist.

**Call:** `retry_agent_pool_update(pool_id=$FIRST_POOL_ID, update_id=<failed_update_id>)`  
**Expect:** no `error`

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| Pools | T-1 – T-4 | Read-only; pool type filter |
| Updates | T-5 – T-15 | Full lifecycle; ⚠️ production env only in MANUAL mode |
| Retry | T-16 | Requires a failed update to exist |
