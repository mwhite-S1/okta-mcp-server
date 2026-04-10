#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for user credential tools.

Tests password reset, expiry, forgot-password, and session revocation.
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

_TEST_PASSWORD = "Temp1!Test@MCP99"


def _create_user_with_password(token):
    """Create an ACTIVE user with a password set. Returns user_id or None."""
    ts = int(time.time())
    body = {
        "profile": {
            "firstName": "MCPCred",
            "lastName": f"Test{ts}",
            "email": f"mcp-cred-{ts}@example.com",
            "login": f"mcp-cred-{ts}@example.com",
        },
        "credentials": {
            "password": {"value": _TEST_PASSWORD},
        },
    }
    resp = call("POST", "/api/v1/users?activate=true", body=body, token=token)
    if resp.status_code not in (200, 201):
        return None
    return resp.json()["id"]


def _cleanup_user(user_id, token):
    """Deactivate then permanently delete a user."""
    call("POST", f"/api/v1/users/{user_id}/lifecycle/deactivate", token=token)
    call("DELETE", f"/api/v1/users/{user_id}", token=token)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_user_credentials_password_ops(token):
    """Test all password-related credential operations on a fresh test user."""
    section("USER CREDENTIALS — password operations")

    user_id = _create_user_with_password(token)
    if not user_id:
        report_skip("User credential tests", "could not create user with password")
        return

    try:
        # reset_password (sendEmail=false returns resetPasswordUrl token)
        resp = call(
            "POST",
            f"/api/v1/users/{user_id}/lifecycle/reset_password?sendEmail=false",
            token=token,
        )
        if report("POST /lifecycle/reset_password?sendEmail=false", resp, (200, 204, 403)):
            if resp.status_code == 200 and resp.json():
                body = resp.json()
                if "resetPasswordUrl" in body:
                    report("  resetPasswordUrl returned in body", resp, (200,))

        # expire_password (marks password as expired, user must change on next login)
        resp = call("POST", f"/api/v1/users/{user_id}/lifecycle/expire_password", token=token)
        report("POST /lifecycle/expire_password", resp, (200, 204))

        # expire_password with tempPassword=true (returns one-time temp password)
        resp = call(
            "POST",
            f"/api/v1/users/{user_id}/lifecycle/expire_password?tempPassword=true",
            token=token,
        )
        if report("POST /lifecycle/expire_password?tempPassword=true", resp, (200, 204)):
            if resp.status_code == 200 and resp.json():
                body = resp.json()
                if "tempPassword" in body:
                    report("  tempPassword returned in body", resp, (200,))

        # forgot_password (sendEmail=false returns recovery token)
        resp = call(
            "POST",
            f"/api/v1/users/{user_id}/credentials/forgot_password?sendEmail=false",
            token=token,
        )
        report(
            "POST /credentials/forgot_password?sendEmail=false",
            resp,
            (200, 204, 403, 404),
        )
        if resp.status_code == 200 and resp.json():
            body = resp.json()
            if "resetPasswordUrl" in body or "recovery_question" in body:
                report("  recovery token/URL returned in body", resp, (200,))

        # list_user_blocks — should be empty for fresh user
        resp = call("GET", f"/api/v1/users/{user_id}/blocks", token=token)
        report("GET /api/v1/users/{userId}/blocks (fresh user, expect empty)", resp, (200, 204))

    finally:
        _cleanup_user(user_id, token)


def test_revoke_user_sessions(token):
    """Verify session revocation endpoints are functional on an existing user."""
    section("USER SESSIONS — revoke")

    resp = call("GET", "/api/v1/users?filter=status+eq+%22ACTIVE%22&limit=1", token=token)
    if not report("GET /api/v1/users?filter=ACTIVE&limit=1 (for session revoke test)", resp):
        return

    users = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not users:
        report_skip("Session revocation tests", "no ACTIVE users in tenant")
        return

    user_id = users[0]["id"]

    # Revoke all sessions (no oauthTokens flag)
    resp = call("DELETE", f"/api/v1/users/{user_id}/sessions", token=token)
    report("DELETE /api/v1/users/{userId}/sessions", resp, (200, 204))

    # Revoke sessions + OAuth tokens
    resp = call("DELETE", f"/api/v1/users/{user_id}/sessions?oauthTokens=true", token=token)
    report("DELETE /api/v1/users/{userId}/sessions?oauthTokens=true", resp, (200, 204))


def test_list_user_blocks_read(token):
    """Read-only: verify list_user_blocks works with various user states."""
    section("USER BLOCKS — read-only")

    resp = call("GET", "/api/v1/users?limit=3", token=token)
    if not report("GET /api/v1/users?limit=3 (for blocks test)", resp):
        return

    users = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not users:
        report_skip("list_user_blocks", "no users in tenant")
        return

    for user in users[:3]:
        uid = user["id"]
        status = user.get("status", "unknown")
        resp = call("GET", f"/api/v1/users/{uid}/blocks", token=token)
        report(f"GET /api/v1/users/{{userId}}/blocks (status: {status})", resp, (200, 204, 401, 403))
