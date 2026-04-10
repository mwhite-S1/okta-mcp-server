#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for profile mapping tools.

Read-only: lists mappings and fetches one by ID.
"""

from __future__ import annotations

import os
import sys

# Load .env
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

_live_dir = os.path.dirname(__file__)
if _live_dir not in sys.path:
    sys.path.insert(0, _live_dir)

from test_governance_live import call, _items, report, report_skip, section, BASE_URL  # noqa: E402


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_profile_mappings_params(token):
    """Cover key query parameters for list_profile_mappings."""
    section("PROFILE MAPPINGS — query parameter coverage")

    # limit= parameter
    resp = call("GET", "/api/v1/mappings?limit=3", token=token)
    report("GET /api/v1/mappings?limit=3 (limit param)", resp, (200, 204))

    # Get first app for sourceId/targetId filter tests
    app_resp = call("GET", "/api/v1/apps?limit=1", token=token)
    app_id = ""
    if app_resp.status_code == 200:
        apps = app_resp.json() if isinstance(app_resp.json(), list) else _items(app_resp.json())
        if apps:
            app_id = apps[0]["id"]

    if app_id:
        # sourceId= filter (mappings where this app is the source; 404 = app has no mapping as source)
        resp = call("GET", f"/api/v1/mappings?sourceId={app_id}&limit=5", token=token)
        report("GET /api/v1/mappings?sourceId={appId}&limit=5 (sourceId= filter)", resp, (200, 204, 404))

        # targetId= filter (mappings where this app is the target; 404 = app has no mapping as target)
        resp = call("GET", f"/api/v1/mappings?targetId={app_id}&limit=5", token=token)
        report("GET /api/v1/mappings?targetId={appId}&limit=5 (targetId= filter)", resp, (200, 204, 404))
    else:
        report_skip("sourceId/targetId filter tests", "no apps found in tenant")


def test_profile_mapping_update(token):
    """Safe no-op update: POST a mapping with an empty properties dict (idempotent)."""
    section("PROFILE MAPPINGS — safe update")

    resp = call("GET", "/api/v1/mappings?limit=1", token=token)
    if not report("GET /api/v1/mappings?limit=1 (find mapping for update test)", resp):
        return

    body = resp.json()
    mappings = body if isinstance(body, list) else _items(body)
    if not mappings:
        report_skip("Profile mapping update", "no mappings in tenant")
        return

    mapping_id = mappings[0].get("id", "")
    if not mapping_id:
        report_skip("Profile mapping update", "mapping has no id")
        return

    # Empty properties dict — no actual change to mapping expressions
    resp = call(
        "POST",
        f"/api/v1/mappings/{mapping_id}",
        body={"properties": {}},
        token=token,
    )
    report(
        "POST /api/v1/mappings/{mappingId} (empty properties — no-op update)",
        resp,
        (200, 204),
    )


def test_profile_mappings_read(token):
    """Read-only: list profile mappings and fetch one."""
    section("PROFILE MAPPINGS — read-only")

    resp = call("GET", "/api/v1/mappings?limit=5", token=token)
    if not report("GET /api/v1/mappings?limit=5", resp):
        return

    body = resp.json()
    mappings = body if isinstance(body, list) else _items(body)

    if not mappings:
        report_skip("GET /api/v1/mappings/{mappingId}", "no profile mappings in tenant")
        return

    mapping_id = mappings[0].get("id", "")
    if not mapping_id:
        report_skip("GET /api/v1/mappings/{mappingId}", "mapping has no id field")
        return

    resp = call("GET", f"/api/v1/mappings/{mapping_id}", token=token)
    report("GET /api/v1/mappings/{mappingId}", resp, (200,))
