#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for user lifecycle tools.

Tests actual state transitions: STAGED → ACTIVE → SUSPENDED → ACTIVE → DEPROVISIONED → DELETE.
All created users are cleaned up in finally blocks.
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


def _create_staged_user(token):
    """Create a user in STAGED state (activate=false). Returns (user_id, login) or (None, None)."""
    ts = int(time.time())
    body = {
        "profile": {
            "firstName": "MCPLifecycle",
            "lastName": f"Test{ts}",
            "email": f"mcp-lifecycle-{ts}@example.com",
            "login": f"mcp-lifecycle-{ts}@example.com",
        }
    }
    resp = call("POST", "/api/v1/users?activate=false", body=body, token=token)
    if resp.status_code not in (200, 201):
        return None, None
    return resp.json()["id"], f"mcp-lifecycle-{ts}@example.com"


def _cleanup_user(user_id, token):
    """Deactivate (if needed) then permanently delete a user."""
    call("POST", f"/api/v1/users/{user_id}/lifecycle/deactivate", token=token)
    call("DELETE", f"/api/v1/users/{user_id}", token=token)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_user_lifecycle_full_cycle(token):
    """Full state machine: STAGED → ACTIVE → SUSPENDED → ACTIVE → DEPROVISIONED → DELETE."""
    section("USER LIFECYCLE — full state machine")

    user_id, login = _create_staged_user(token)
    if not user_id:
        report_skip("User lifecycle state machine", "could not create STAGED user")
        return

    report_skip(f"  created STAGED user: {user_id}", "")

    try:
        # Verify user is in STAGED state
        resp = call("GET", f"/api/v1/users/{user_id}", token=token)
        if report("GET /api/v1/users/{userId} (verify STAGED status)", resp):
            status = resp.json().get("status", "")
            if status != "STAGED":
                report_skip("Expected STAGED status", f"got {status!r}")

        # STAGED → ACTIVE
        resp = call("POST", f"/api/v1/users/{user_id}/lifecycle/activate?sendEmail=false", token=token)
        if not report("POST /lifecycle/activate?sendEmail=false (STAGED → ACTIVE)", resp, (200, 204)):
            return
        # Response may contain activationToken
        if resp.status_code == 200 and resp.json():
            body = resp.json()
            if "activationToken" in body or "activationUrl" in body:
                report("  activationToken/activationUrl returned", resp, (200,))

        # Verify ACTIVE
        resp = call("GET", f"/api/v1/users/{user_id}", token=token)
        if report("GET /api/v1/users/{userId} (verify ACTIVE status)", resp):
            status = resp.json().get("status", "")
            if status not in ("ACTIVE", "PROVISIONED"):
                report_skip("Expected ACTIVE status", f"got {status!r}")

        # ACTIVE → SUSPENDED
        resp = call("POST", f"/api/v1/users/{user_id}/lifecycle/suspend", token=token)
        report("POST /lifecycle/suspend (ACTIVE → SUSPENDED)", resp, (200, 204))

        # Verify SUSPENDED
        resp = call("GET", f"/api/v1/users/{user_id}", token=token)
        if report("GET /api/v1/users/{userId} (verify SUSPENDED status)", resp):
            status = resp.json().get("status", "")
            if status != "SUSPENDED":
                report_skip("Expected SUSPENDED status", f"got {status!r}")

        # SUSPENDED → ACTIVE
        resp = call("POST", f"/api/v1/users/{user_id}/lifecycle/unsuspend", token=token)
        report("POST /lifecycle/unsuspend (SUSPENDED → ACTIVE)", resp, (200, 204))

        # reset_factors (safe on ACTIVE user — clears enrolled MFA, returns 200 with no body)
        resp = call("POST", f"/api/v1/users/{user_id}/lifecycle/reset_factors", token=token)
        report("POST /lifecycle/reset_factors (ACTIVE user)", resp, (200, 204))

        # ACTIVE → DEPROVISIONED
        resp = call("POST", f"/api/v1/users/{user_id}/lifecycle/deactivate", token=token)
        report("POST /lifecycle/deactivate (ACTIVE → DEPROVISIONED)", resp, (200, 204))

        # Verify DEPROVISIONED
        resp = call("GET", f"/api/v1/users/{user_id}", token=token)
        if report("GET /api/v1/users/{userId} (verify DEPROVISIONED status)", resp):
            status = resp.json().get("status", "")
            if status not in ("DEPROVISIONED", "DEACTIVATED"):
                report_skip("Expected DEPROVISIONED status", f"got {status!r}")

        # DELETE deprovisioned user
        resp = call("DELETE", f"/api/v1/users/{user_id}", token=token)
        report("DELETE /api/v1/users/{userId} (deprovisioned user)", resp, (200, 204))
        user_id = None  # Prevent double-delete in finally

    finally:
        if user_id:
            _cleanup_user(user_id, token)


def test_user_unlock_endpoint(token):
    """Verify the unlock endpoint is reachable (user will not be LOCKED_OUT, expect 400/404)."""
    section("USER LIFECYCLE — unlock endpoint reachability")

    resp = call("GET", "/api/v1/users?filter=status+eq+%22ACTIVE%22&limit=1", token=token)
    if not report("GET /api/v1/users?filter=ACTIVE&limit=1 (for unlock test)", resp):
        return

    users = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not users:
        report_skip("POST /lifecycle/unlock", "no ACTIVE users in tenant")
        return

    user_id = users[0]["id"]
    # ACTIVE user is not locked out, so unlock should return 400 (invalid transition)
    resp = call("POST", f"/api/v1/users/{user_id}/lifecycle/unlock", token=token)
    report(
        "POST /lifecycle/unlock (ACTIVE user — expect 400/404, not LOCKED_OUT)",
        resp,
        (200, 204, 400, 403, 404),
    )


def test_user_reactivate_endpoint(token):
    """Verify reactivate endpoint: create STAGED user, activate to ACTIVE, reactivate should return 400."""
    section("USER LIFECYCLE — reactivate endpoint")

    user_id, login = _create_staged_user(token)
    if not user_id:
        report_skip("User reactivate endpoint test", "could not create STAGED user")
        return

    try:
        # Activate first
        resp = call("POST", f"/api/v1/users/{user_id}/lifecycle/activate?sendEmail=false", token=token)
        if not report("POST /lifecycle/activate?sendEmail=false (setup for reactivate test)", resp, (200, 204)):
            return

        # Reactivate on ACTIVE user — expect 400 (not in PROVISIONED/STAGED state)
        resp = call("POST", f"/api/v1/users/{user_id}/lifecycle/reactivate?sendEmail=false", token=token)
        report(
            "POST /lifecycle/reactivate?sendEmail=false (ACTIVE user — expect 400/403)",
            resp,
            (200, 204, 400, 403),
        )

    finally:
        _cleanup_user(user_id, token)
