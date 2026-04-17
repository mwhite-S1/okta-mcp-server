# Runbook: System Logs

Covers `system_logs.py` — 1 tool.

---

## Section 1 — System Logs

### T-1: get_logs (basic)

**Call:** `get_logs(limit=5)`  
**Expect:** `items` is a list; each item has `eventType`, `published`, `actor`; no `error`

---

### T-2: get_logs with filter

**Call:** `get_logs(filter='eventType eq "user.session.start"', limit=3)`  
**Expect:** `items` is a list; no `error`; all items (if any) have `eventType == "user.session.start"`

---

### T-3: get_logs with date range

**Call:** `get_logs(since="2026-01-01T00:00:00.000Z", until="2026-12-31T23:59:59.000Z", limit=3)`  
**Expect:** `items` is a list; no `error`

---

### T-4: get_logs with q (keyword search)

**Call:** `get_logs(q="user", limit=3)`  
**Expect:** `items` is a list; no `error`

---

## Summary

| Tests | Notes |
|-------|-------|
| T-1 – T-4 | All read-only; tests filter, date range, and keyword params |
