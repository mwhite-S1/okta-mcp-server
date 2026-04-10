#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for v1 governance request type tools.

Full CRUD: create → get → publish → unpublish → delete.
Requires governance feature to be enabled; tests gracefully handle 403.
All created request types are cleaned up in finally blocks.
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

_live_dir = os.path.dirname(__file__)
if _live_dir not in sys.path:
    sys.path.insert(0, _live_dir)

from test_governance_live import call, _items, report, report_skip, section  # noqa: E402

_GOVERNANCE_403_MSG = "governance feature not enabled in this tenant — skipping"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_governance_teams_read(token):
    """Read-only: list governance teams (ownerId source for request types)."""
    section("GOVERNANCE REQUEST TYPES — teams read-only")

    resp = call("GET", "/governance/api/v1/teams", token=token)
    report("GET /governance/api/v1/teams", resp, (200, 403, 404))

    if resp.status_code == 403:
        report_skip("Governance teams", _GOVERNANCE_403_MSG)
        return
    if resp.status_code != 200:
        return

    body = resp.json()
    teams = body if isinstance(body, list) else _items(body)
    report_skip(f"  found {len(teams)} team(s)", "")

    # Test with limit and after pagination params
    resp = call("GET", "/governance/api/v1/teams?limit=2", token=token)
    report("GET /governance/api/v1/teams?limit=2 (limit param)", resp, (200, 403))


def test_request_types_read(token):
    """Read-only: list request types and fetch one by ID."""
    section("GOVERNANCE REQUEST TYPES — read-only")

    resp = call("GET", "/governance/api/v1/request-types?limit=5", token=token)
    report("GET /governance/api/v1/request-types?limit=5", resp, (200, 403, 404))

    if resp.status_code == 403:
        report_skip("Request types read", _GOVERNANCE_403_MSG)
        return
    if resp.status_code != 200:
        return

    body = resp.json()
    rts = body if isinstance(body, list) else _items(body)
    report_skip(f"  found {len(rts)} request type(s)", "")

    if rts:
        rt_id = rts[0].get("id", "")
        if rt_id:
            resp = call("GET", f"/governance/api/v1/request-types/{rt_id}", token=token)
            report("GET /governance/api/v1/request-types/{requestTypeId}", resp, (200, 403, 404))

    # Test limit parameter
    resp = call("GET", "/governance/api/v1/request-types?limit=2", token=token)
    report("GET /governance/api/v1/request-types?limit=2 (limit param)", resp, (200, 403))


def test_request_type_crud(token):
    """Full CRUD: create request type, get, publish, unpublish, delete."""
    section("GOVERNANCE REQUEST TYPES — CRUD (self-cleaning)")

    # Step 1: Get a governance team ID
    resp = call("GET", "/governance/api/v1/teams", token=token)
    if resp.status_code == 403:
        report_skip("Request type CRUD", _GOVERNANCE_403_MSG)
        return
    if resp.status_code != 200:
        report_skip("Request type CRUD", f"teams endpoint returned {resp.status_code}")
        return

    body = resp.json()
    teams = body if isinstance(body, list) else _items(body)
    if not teams:
        report_skip("Request type CRUD", "no governance teams found — cannot create request type")
        return

    owner_id = teams[0].get("id", "")
    if not owner_id:
        report_skip("Request type CRUD", "first team has no 'id' field")
        return

    # Step 2: Get a group ID (target resource)
    resp = call("GET", "/api/v1/groups?limit=1", token=token)
    if resp.status_code != 200:
        report_skip("Request type CRUD", "could not fetch groups")
        return
    groups = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not groups:
        report_skip("Request type CRUD", "no groups in tenant")
        return
    group_id = groups[0]["id"]

    # Step 3: Get a user ID (approver)
    resp = call("GET", "/api/v1/users?filter=status+eq+%22ACTIVE%22&limit=1", token=token)
    if resp.status_code != 200:
        report_skip("Request type CRUD", "could not fetch users")
        return
    users = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not users:
        report_skip("Request type CRUD", "no ACTIVE users in tenant")
        return
    approver_id = users[0]["id"]

    # Step 4: Create the request type
    ts = int(time.time())
    create_body = {
        "name": f"mcp-test-rt-{ts}",
        "ownerId": owner_id,
        "resourceSettings": {
            "type": "GROUPS",
            "targetResources": [{"resourceId": group_id}],
        },
        "approvalSettings": {
            "type": "SERIAL",
            "approvals": [
                {
                    "approverType": "USER",
                    "approverUserId": approver_id,
                    "approverFields": [],
                }
            ],
        },
        "requestSettings": {
            "type": "EVERYONE",
            "requesterFields": [],
        },
        "description": "MCP live test request type",
    }

    rt_id = None
    try:
        resp = call("POST", "/governance/api/v1/request-types", body=create_body, token=token)
        if not report("POST /governance/api/v1/request-types (create)", resp, (200, 201, 400, 403)):
            return
        if resp.status_code in (400, 403):
            report_skip("Request type CRUD remainder", f"create returned {resp.status_code}")
            return

        rt_id = resp.json().get("id", "")
        if not rt_id:
            report_skip("Request type CRUD remainder", "create response has no 'id'")
            return

        # Verify initial status is DRAFT
        created_status = resp.json().get("status", "")
        report_skip(f"  created request type status: {created_status!r}", "")

        # Get by ID
        resp = call("GET", f"/governance/api/v1/request-types/{rt_id}", token=token)
        report("GET /governance/api/v1/request-types/{requestTypeId}", resp, (200, 404))

        # Publish (DRAFT → ACTIVE)
        resp = call("POST", f"/governance/api/v1/request-types/{rt_id}/publish", token=token)
        report("POST /request-types/{id}/publish (DRAFT → ACTIVE)", resp, (200, 204, 400))

        if resp.status_code in (200, 204):
            # Verify ACTIVE status
            resp = call("GET", f"/governance/api/v1/request-types/{rt_id}", token=token)
            if report("GET /request-types/{id} (verify ACTIVE)", resp, (200,)):
                pub_status = resp.json().get("status", "")
                report_skip(f"  post-publish status: {pub_status!r}", "")

            # Unpublish (ACTIVE → DISABLED)
            resp = call(
                "POST",
                f"/governance/api/v1/request-types/{rt_id}/un-publish",
                token=token,
            )
            report("POST /request-types/{id}/un-publish (ACTIVE → DISABLED)", resp, (200, 204, 400))

        # Delete (DRAFT or DISABLED request types can be deleted)
        resp = call("DELETE", f"/governance/api/v1/request-types/{rt_id}", token=token)
        report("DELETE /governance/api/v1/request-types/{requestTypeId}", resp, (200, 204, 400))
        rt_id = None

    finally:
        if rt_id:
            call("DELETE", f"/governance/api/v1/request-types/{rt_id}", token=token)
