# Runbook: Network Zones

Covers `network_zones.py` — 7 tools total.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_ZONE_ID` | `list_network_zones()` → first item `id` |
| `$TEST_ZONE_ID` | Created in T-3; deleted in T-7 |

---

## Section 1 — Network Zones

### T-1: list_network_zones

**Call:** `list_network_zones()`  
**Expect:** `items` is a list; each item has `id`, `name`, `type`, `status`  
→ set `$FIRST_ZONE_ID` = `items[0]["id"]`

---

### T-2: get_network_zone

**Call:** `get_network_zone(zone_id=$FIRST_ZONE_ID)`  
**Expect:** `result["id"] == $FIRST_ZONE_ID`; no `error`

---

### T-3: 🔁 create_network_zone → get → activate/deactivate → replace → delete

**CREATE:**
```
create_network_zone(
  name="runbook-test-zone",
  type="IP",
  gateways=[{"type": "CIDR", "value": "10.99.0.0/16"}]
)
```
**Expect:** `result["id"]` → `$TEST_ZONE_ID`; `result["name"] == "runbook-test-zone"`

---

### T-4: get newly created zone

**Call:** `get_network_zone(zone_id=$TEST_ZONE_ID)`  
**Expect:** `result["id"] == $TEST_ZONE_ID`; no `error`

---

### T-5: activate_network_zone + deactivate_network_zone 🔁

**ACTIVATE:** `activate_network_zone(zone_id=$TEST_ZONE_ID)`  
**Expect:** no `error`; `result["status"] == "ACTIVE"` or confirm via get

**DEACTIVATE:** `deactivate_network_zone(zone_id=$TEST_ZONE_ID)`  
**Expect:** no `error`; `result["status"] == "INACTIVE"` or confirm via get

---

### T-6: replace_network_zone

**Call:**
```
replace_network_zone(
  zone_id=$TEST_ZONE_ID,
  name="runbook-test-zone-replaced",
  type="IP",
  gateways=[{"type": "CIDR", "value": "10.99.1.0/24"}]
)
```
**Expect:** no `error`; `result["name"] == "runbook-test-zone-replaced"`

---

### T-7: delete_network_zone ⚠️

**Call:** `delete_network_zone(zone_id=$TEST_ZONE_ID)`  
**Expect:** no `error`  
**VERIFY:** `get_network_zone(zone_id=$TEST_ZONE_ID)` → `"error"` in result

---

### T-8: invalid zone returns error _(bonus)_

**Call:** `get_network_zone(zone_id="invalid-zone-000")`  
**Expect:** `"error"` in result

---

## Summary

| Tests | Notes |
|-------|-------|
| T-1 – T-8 | Full CRUD + activate/deactivate lifecycle on a test IP zone |
