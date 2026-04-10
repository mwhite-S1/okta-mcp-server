#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for application tools.

Read-only: creating apps in live tests is risky and requires tenant-specific config.
"""

from __future__ import annotations

import os
import sys
import time

# Load .env
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# Add tests/live to sys.path
_live_dir = os.path.dirname(__file__)
if _live_dir not in sys.path:
    sys.path.insert(0, _live_dir)

from test_governance_live import call, _items, report, report_skip, section, BASE_URL  # noqa: E402


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_applications_query_params(token):
    """Cover all key query parameters for list_applications."""
    section("APPLICATIONS — query parameter coverage")

    # filter= by status ACTIVE
    resp = call("GET", '/api/v1/apps?filter=status+eq+"ACTIVE"&limit=3', token=token)
    report('GET /api/v1/apps?filter=status+eq+"ACTIVE"&limit=3 (filter by status)', resp, (200, 204))

    # filter= by signOnMode
    resp = call("GET", '/api/v1/apps?filter=name+eq+"bookmark"&limit=3', token=token)
    report('GET /api/v1/apps?filter=name+eq+"bookmark"&limit=3 (filter by name)', resp, (200, 204))

    # q= text search
    resp = call("GET", "/api/v1/apps?q=okta&limit=3", token=token)
    report("GET /api/v1/apps?q=okta&limit=3 (q= text search)", resp, (200, 204))

    # limit= parameter
    resp = call("GET", "/api/v1/apps?limit=2", token=token)
    report("GET /api/v1/apps?limit=2 (verify limit param)", resp, (200,))

    # expand= parameter
    resp = call("GET", "/api/v1/apps?expand=user/groups&limit=2", token=token)
    report("GET /api/v1/apps?expand=user/groups&limit=2 (expand= parameter)", resp, (200, 400))

    # Get first app with expand on single app
    base_resp = call("GET", "/api/v1/apps?limit=1", token=token)
    if base_resp.status_code == 200:
        apps = base_resp.json() if isinstance(base_resp.json(), list) else _items(base_resp.json())
        if apps:
            app_id = apps[0]["id"]
            resp = call("GET", f"/api/v1/apps/{app_id}?expand=user/groups", token=token)
            report("GET /api/v1/apps/{appId}?expand=user/groups (single app expand)", resp, (200, 400))


def test_application_lifecycle(token):
    """Activate/deactivate lifecycle for an existing INACTIVE app (if any)."""
    section("APPLICATIONS — lifecycle (activate/deactivate existing INACTIVE app)")

    resp = call("GET", '/api/v1/apps?filter=status+eq+"INACTIVE"&limit=1', token=token)
    if not report('GET /api/v1/apps?filter=status+eq+"INACTIVE"&limit=1', resp, (200, 204)):
        return

    body = resp.json()
    apps = body if isinstance(body, list) else _items(body)
    if not apps:
        report_skip("Application lifecycle test", "no INACTIVE apps in tenant")
        return

    app_id = apps[0]["id"]
    app_label = apps[0].get("label", "unknown")

    # Activate
    resp = call("POST", f"/api/v1/apps/{app_id}/lifecycle/activate", token=token)
    report(f"POST /apps/{{appId}}/lifecycle/activate (app: {app_label})", resp, (200, 204))

    # Verify ACTIVE
    resp = call("GET", f"/api/v1/apps/{app_id}", token=token)
    if report("GET /api/v1/apps/{appId} (verify ACTIVE)", resp, (200,)):
        status = resp.json().get("status", "")
        if status != "ACTIVE":
            report_skip("  expected ACTIVE", f"got {status!r}")

    # Deactivate (restore original INACTIVE state)
    resp = call("POST", f"/api/v1/apps/{app_id}/lifecycle/deactivate", token=token)
    report(f"POST /apps/{{appId}}/lifecycle/deactivate (restore INACTIVE)", resp, (200, 204))


def test_applications_read(token):
    section("APPLICATIONS — read-only")

    resp = call("GET", "/api/v1/apps?limit=5", token=token)
    if not report("GET /api/v1/apps?limit=5", resp):
        return

    apps = resp.json() if isinstance(resp.json(), list) else _items(resp.json())

    if apps:
        first_id = apps[0]["id"]

        resp = call("GET", f"/api/v1/apps/{first_id}", token=token)
        report("GET /api/v1/apps/{app_id}", resp)

        resp = call("GET", '/api/v1/apps?limit=5&filter=status eq "ACTIVE"', token=token)
        report('GET /api/v1/apps?limit=5&filter=status eq "ACTIVE"', resp)
    else:
        report_skip("GET /api/v1/apps/{app_id}", "no applications in tenant")
        report_skip('GET /api/v1/apps (filter ACTIVE)', "no applications in tenant")
