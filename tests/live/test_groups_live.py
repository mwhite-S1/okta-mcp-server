#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for group tools.

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

def test_groups_read(token):
    section("GROUPS — read-only")

    resp = call("GET", "/api/v1/groups?limit=5", token=token)
    if not report("GET /api/v1/groups?limit=5", resp):
        return

    groups = resp.json() if isinstance(resp.json(), list) else _items(resp.json())

    if groups:
        first_id = groups[0]["id"]

        resp = call("GET", f"/api/v1/groups/{first_id}", token=token)
        report("GET /api/v1/groups/{group_id}", resp)

        resp = call("GET", f"/api/v1/groups/{first_id}/users?limit=3", token=token)
        report("GET /api/v1/groups/{group_id}/users?limit=3", resp)

        resp = call("GET", f"/api/v1/groups/{first_id}/apps", token=token)
        report("GET /api/v1/groups/{group_id}/apps", resp)
    else:
        report_skip("GET /api/v1/groups/{group_id}", "no groups in tenant")
        report_skip("GET /api/v1/groups/{group_id}/users", "no groups in tenant")
        report_skip("GET /api/v1/groups/{group_id}/apps", "no groups in tenant")


def test_group_owners_read(token):
    """Read-only: list owners for an existing group."""
    section("GROUP OWNERS — read-only")

    resp = call("GET", "/api/v1/groups?limit=5", token=token)
    if not report("GET /api/v1/groups?limit=5 (for owner tests)", resp):
        return

    groups = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not groups:
        report_skip("group owners", "no groups in tenant")
        return

    group_id = groups[0]["id"]
    resp = call("GET", f"/api/v1/groups/{group_id}/owners", token=token)
    # 403 is expected if caller doesn't have group admin rights
    report(f"GET /api/v1/groups/{{groupId}}/owners (id: {group_id})", resp, (200, 403, 404))


def test_group_crud(token):
    section("GROUPS — CRUD (self-cleaning)")

    ts = int(time.time())
    body = {
        "profile": {
            "name": f"mcp-live-group-{ts}",
            "description": "MCP live test",
        }
    }

    resp = call("POST", "/api/v1/groups", body=body, token=token)
    if not report("POST /api/v1/groups (create)", resp, (200, 201)):
        return

    created = resp.json()
    group_id = created["id"]

    # Fetch a user for membership testing
    user_resp = call("GET", "/api/v1/users?limit=1", token=token)
    user_id = ""
    if user_resp.status_code == 200:
        users = user_resp.json() if isinstance(user_resp.json(), list) else _items(user_resp.json())
        if users:
            user_id = users[0]["id"]

    try:
        resp = call("GET", f"/api/v1/groups/{group_id}", token=token)
        report("GET /api/v1/groups/{group_id} (fetch created)", resp)

        resp = call(
            "POST",
            f"/api/v1/groups/{group_id}",
            body={"profile": {"name": f"mcp-live-group-{ts}-upd", "description": "MCP live test updated"}},
            token=token,
        )
        report("POST /api/v1/groups/{group_id} (update)", resp, (200, 204))

        if user_id:
            resp = call("PUT", f"/api/v1/groups/{group_id}/users/{user_id}", token=token)
            report("PUT /api/v1/groups/{group_id}/users/{user_id} (add member)", resp, (200, 204))

            resp = call("GET", f"/api/v1/groups/{group_id}/users", token=token)
            report("GET /api/v1/groups/{group_id}/users (after add)", resp, (200, 204))

            resp = call("DELETE", f"/api/v1/groups/{group_id}/users/{user_id}", token=token)
            report("DELETE /api/v1/groups/{group_id}/users/{user_id} (remove member)", resp, (200, 204))
        else:
            report_skip("Group membership operations", "no users available in tenant")

    finally:
        resp = call("DELETE", f"/api/v1/groups/{group_id}", token=token)
        report("DELETE /api/v1/groups/{group_id} (cleanup)", resp, (200, 204))
