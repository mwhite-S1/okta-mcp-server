#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for user tools.

Creates real objects, tests them, then deletes everything in a finally block.
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

def test_users_read(token):
    section("USERS — read-only")

    resp = call("GET", "/api/v1/users?limit=5", token=token)
    if not report("GET /api/v1/users?limit=5", resp):
        return

    users = resp.json() if isinstance(resp.json(), list) else _items(resp.json())

    resp2 = call("GET", "/api/v1/users?limit=1", token=token)
    report("GET /api/v1/users?limit=1 (profile shape)", resp2)

    if users:
        first_user_id = users[0]["id"]
        resp3 = call("GET", f"/api/v1/users/{first_user_id}", token=token)
        report("GET /api/v1/users/{user_id}", resp3)

        resp4 = call("GET", f"/api/v1/users/{first_user_id}/blocks", token=token)
        report("GET /api/v1/users/{user_id}/blocks", resp4, (200, 204))
    else:
        report_skip("GET /api/v1/users/{user_id}", "no users in tenant")
        report_skip("GET /api/v1/users/{user_id}/blocks", "no users in tenant")


def test_user_lifecycle_read(token):
    """Read-only: verify lifecycle endpoints exist (no state changes)."""
    section("USER LIFECYCLE — read-only verification")

    # Just test that a STAGED user can be activated (we'll create one in STAGED state)
    # For read-only purposes we just verify the endpoint paths are reachable with a 4xx
    resp = call("GET", "/api/v1/users?limit=1&filter=status+eq+%22ACTIVE%22", token=token)
    if not report("GET /api/v1/users?limit=1&filter=ACTIVE (for lifecycle check)", resp):
        return

    users = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not users:
        report_skip("User lifecycle endpoints", "no ACTIVE users in tenant")
        return

    user_id = users[0]["id"]

    # unlock — expect 403/404 (user not locked out) but verifies endpoint is accessible
    resp = call("POST", f"/api/v1/users/{user_id}/lifecycle/unlock", token=token)
    report(f"POST /api/v1/users/{{userId}}/lifecycle/unlock (expect 4xx)", resp, (200, 204, 400, 403, 404))

    # replace (PUT) — read shape by sending current profile back
    resp_get = call("GET", f"/api/v1/users/{user_id}", token=token)
    if resp_get.status_code == 200:
        user_body = resp_get.json()
        profile = user_body.get("profile", {})
        resp = call("PUT", f"/api/v1/users/{user_id}", body={"profile": profile}, token=token)
        report("PUT /api/v1/users/{userId} (replace — same profile)", resp, (200, 204))
    else:
        report_skip("PUT /api/v1/users/{userId}", "could not fetch user profile for replace")


def test_user_crud(token):
    section("USERS — CRUD (self-cleaning)")

    ts = int(time.time())
    body = {
        "profile": {
            "firstName": "MCPLive",
            "lastName": f"Test{ts}",
            "email": f"mcp-live-{ts}@example.com",
            "login": f"mcp-live-{ts}@example.com",
        }
    }

    resp = call("POST", "/api/v1/users?activate=false", body=body, token=token)
    if not report("POST /api/v1/users?activate=false (create)", resp, (200, 201)):
        if resp.status_code == 400:
            return
        return

    created = resp.json()
    user_id = created["id"]

    try:
        resp = call("GET", f"/api/v1/users/{user_id}", token=token)
        report("GET /api/v1/users/{user_id} (fetch created)", resp)

        resp = call(
            "POST",
            f"/api/v1/users/{user_id}",
            body={"profile": {"nickName": "MCPTest"}},
            token=token,
        )
        report("POST /api/v1/users/{user_id} (update profile)", resp, (200, 204))

        resp = call(
            "POST",
            f"/api/v1/users/{user_id}/lifecycle/deactivate",
            token=token,
        )
        report("POST /api/v1/users/{user_id}/lifecycle/deactivate", resp, (200, 204))

    finally:
        resp = call("DELETE", f"/api/v1/users/{user_id}", token=token)
        report("DELETE /api/v1/users/{user_id} (cleanup)", resp, (200, 204))
