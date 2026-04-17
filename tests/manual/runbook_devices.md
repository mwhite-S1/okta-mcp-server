# Runbook: Devices

Covers `devices.py` — 8 tools total.

⚠️ Device operations directly affect enrolled managed devices.
Run against a sandbox/test device wherever possible.

---

## Prerequisites

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_DEVICE_ID` | `list_devices(limit=1)` → first item `id` |

⏭️ All tests skip if org has no enrolled devices.

---

## Section 1 — Devices

### T-1: list_devices

**Call:** `list_devices(limit=5)`  
**Expect:** `items` is a list; each item has `id`, `status`, `profile`  
→ set `$FIRST_DEVICE_ID` = `items[0]["id"]`  
⏭️ Skip all remaining tests if list is empty.

---

### T-2: get_device

**Call:** `get_device(device_id=$FIRST_DEVICE_ID)`  
**Expect:** `result["id"] == $FIRST_DEVICE_ID`; no `error`

---

### T-3: list_device_users

**Call:** `list_device_users(device_id=$FIRST_DEVICE_ID)`  
**Expect:** `items` is a list; no `error`

---

### T-4: deactivate_device + activate_device 🔁

⚠️ Deactivating a device affects the device user's access.  
⏭️ Skip unless `$FIRST_DEVICE_ID` is a known test device.

**DEACTIVATE:** `deactivate_device(device_id=$FIRST_DEVICE_ID)`  
**Expect:** no `error`

**ACTIVATE:** `activate_device(device_id=$FIRST_DEVICE_ID)`  
**Expect:** no `error`

---

### T-5: suspend_device + unsuspend_device 🔁

⚠️ Suspending a device blocks the user from using it.

**SUSPEND:** `suspend_device(device_id=$FIRST_DEVICE_ID)`  
**Expect:** no `error`

**UNSUSPEND:** `unsuspend_device(device_id=$FIRST_DEVICE_ID)`  
**Expect:** no `error`

---

### T-6: delete_device ⚠️

⚠️ Permanently removes the device enrollment. Only run on a test device.

**Call:** `delete_device(device_id=$FIRST_DEVICE_ID)`  
⏭️ Skip unless explicitly running against a disposable test device.  
**Expect:** no `error`

---

### T-7: invalid device returns error

**Call:** `get_device(device_id="invalid-device-000")`  
**Expect:** `"error"` in result

---

## Summary

| Tests | Notes |
|-------|-------|
| T-1 – T-7 | Read-only safe; lifecycle ops require test device |
