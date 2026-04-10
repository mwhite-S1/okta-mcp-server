#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for enduser (/my/) governance endpoints.

These use a client_credentials token so endpoints may return limited data.
Accept 200, 204, 401, 403 as valid responses throughout.

Run with:
    pytest tests/live/test_governance_enduser_live.py -v -s
"""

from __future__ import annotations

import os
import sys
import time
from urllib.parse import urlencode

# Load .env
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# Ensure live test dir is on sys.path so we can import helpers.
_live_dir = os.path.dirname(__file__)
if _live_dir not in sys.path:
    sys.path.insert(0, _live_dir)

from test_governance_live import (  # noqa: E402
    call,
    _items,
    report,
    report_skip,
    section,
    cleanup_label,
    BASE_URL,
)

# Statuses that are always acceptable for /my/ endpoints backed by client_credentials
_MY_OK = (200, 204, 401, 403)


# ---------------------------------------------------------------------------
# Enduser My Settings
# ---------------------------------------------------------------------------

def test_enduser_my_settings(token: str) -> None:
    """GET /governance/api/v1/my/settings and delegate users list."""
    section("ENDUSER — My Settings")

    # Main settings
    resp = call("GET", "/governance/api/v1/my/settings", token=token)
    report("GET /governance/api/v1/my/settings", resp, _MY_OK)

    if resp.status_code == 200:
        body = resp.json()
        print(f"      settings keys: {list(body.keys())[:8]}")

    # Delegate users (limited list)
    params = urlencode({"limit": 5})
    resp = call("GET", f"/governance/api/v1/my/settings/delegate/users?{params}", token=token)
    report("GET /governance/api/v1/my/settings/delegate/users (limit=5)", resp, _MY_OK)

    if resp.status_code == 200:
        items = _items(resp.json())
        print(f"      Delegate users returned: {len(items)}")


# ---------------------------------------------------------------------------
# Enduser Catalog
# ---------------------------------------------------------------------------

def test_enduser_catalog(token: str) -> None:
    """GET /governance/api/v2/my/catalogs/default/entries and drill into a single entry."""
    section("ENDUSER — My Catalog")

    params = urlencode({"filter": "not(parent pr)", "limit": 5})
    resp = call("GET", f"/governance/api/v2/my/catalogs/default/entries?{params}", token=token)
    report("GET /governance/api/v2/my/catalogs/default/entries (limit=5)", resp, _MY_OK)

    if resp.status_code not in (200, 204):
        print(f"      Catalog not accessible ({resp.status_code}); skipping entry drill-down")
        return

    entries = _items(resp.json()) if resp.status_code == 200 else []
    print(f"      Catalog entries returned: {len(entries)}")

    if not entries:
        report_skip("GET /governance/api/v2/my/catalogs/default/entries/{id}", "no entries available")
        report_skip("GET /governance/api/v2/my/catalogs/default/entries/{id}/request-fields", "no entries available")
        return

    entry = entries[0]
    entry_id = entry.get("id", entry.get("entryId", ""))
    entry_name = entry.get("name", "")
    print(f"      Using entry_id={entry_id}  name={entry_name!r}")

    if not entry_id:
        report_skip("GET /governance/api/v2/my/catalogs/default/entries/{id}", "could not extract entry ID")
        report_skip("GET /governance/api/v2/my/catalogs/default/entries/{id}/request-fields", "could not extract entry ID")
        return

    # GET single entry
    resp = call("GET", f"/governance/api/v2/my/catalogs/default/entries/{entry_id}", token=token)
    report(f"GET /governance/api/v2/my/catalogs/default/entries/{entry_id}", resp, _MY_OK)

    # GET entry request-fields
    resp = call("GET", f"/governance/api/v2/my/catalogs/default/entries/{entry_id}/request-fields", token=token)
    report(
        f"GET /governance/api/v2/my/catalogs/default/entries/{entry_id}/request-fields",
        resp,
        _MY_OK,
    )
    if resp.status_code == 200:
        fields = _items(resp.json())
        print(f"      Request fields returned: {len(fields)}")


# ---------------------------------------------------------------------------
# Enduser Security Access Reviews (SARs)
# ---------------------------------------------------------------------------

def test_enduser_sar(token: str) -> None:
    """GET /governance/api/v2/my/security-access-reviews and related sub-resources."""
    section("ENDUSER — My Security Access Reviews")

    # List SARs
    resp = call("GET", "/governance/api/v2/my/security-access-reviews", token=token)
    report("GET /governance/api/v2/my/security-access-reviews (list)", resp, _MY_OK)

    # Stats endpoint
    resp_stats = call("GET", "/governance/api/v2/my/security-access-reviews/stats", token=token)
    report("GET /governance/api/v2/my/security-access-reviews/stats", resp_stats, _MY_OK)

    if resp_stats.status_code == 200:
        body = resp_stats.json()
        print(f"      SAR stats keys: {list(body.keys())[:8]}")

    if resp.status_code not in (200, 204):
        print(f"      SAR list not accessible ({resp.status_code}); skipping SAR drill-down")
        return

    sars = _items(resp.json()) if resp.status_code == 200 else []
    print(f"      SARs returned: {len(sars)}")

    if not sars:
        report_skip("GET /governance/api/v2/my/security-access-reviews/{id}", "no SARs available")
        report_skip("GET /governance/api/v2/my/security-access-reviews/{id}/actions", "no SARs available")
        report_skip("GET /governance/api/v2/my/security-access-reviews/{id}/history", "no SARs available")
        report_skip("GET /governance/api/v2/my/security-access-reviews/{id}/principal", "no SARs available")
        return

    sar = sars[0]
    sar_id = sar.get("id", sar.get("reviewId", ""))
    print(f"      Using sar_id={sar_id}")

    if not sar_id:
        report_skip("GET /governance/api/v2/my/security-access-reviews/{id}", "could not extract SAR ID")
        report_skip("GET /governance/api/v2/my/security-access-reviews/{id}/actions", "could not extract SAR ID")
        report_skip("GET /governance/api/v2/my/security-access-reviews/{id}/history", "could not extract SAR ID")
        report_skip("GET /governance/api/v2/my/security-access-reviews/{id}/principal", "could not extract SAR ID")
        return

    # GET single SAR
    resp = call("GET", f"/governance/api/v2/my/security-access-reviews/{sar_id}", token=token)
    report(f"GET /governance/api/v2/my/security-access-reviews/{sar_id}", resp, _MY_OK)

    # GET SAR actions
    resp = call("GET", f"/governance/api/v2/my/security-access-reviews/{sar_id}/actions", token=token)
    report(f"GET /governance/api/v2/my/security-access-reviews/{sar_id}/actions", resp, _MY_OK)
    if resp.status_code == 200:
        actions = _items(resp.json())
        print(f"      SAR actions returned: {len(actions)}")

    # GET SAR history
    resp = call("GET", f"/governance/api/v2/my/security-access-reviews/{sar_id}/history", token=token)
    report(f"GET /governance/api/v2/my/security-access-reviews/{sar_id}/history", resp, _MY_OK)
    if resp.status_code == 200:
        history = _items(resp.json())
        print(f"      SAR history entries returned: {len(history)}")

    # GET SAR principal
    resp = call("GET", f"/governance/api/v2/my/security-access-reviews/{sar_id}/principal", token=token)
    report(f"GET /governance/api/v2/my/security-access-reviews/{sar_id}/principal", resp, _MY_OK)
    if resp.status_code == 200:
        principal = resp.json()
        print(f"      SAR principal id: {principal.get('id', principal.get('principalId', 'n/a'))}")
