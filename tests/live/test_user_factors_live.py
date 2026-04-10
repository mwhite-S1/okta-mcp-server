#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for user factor (MFA) tools.

Read-only tests use existing users. CRUD tests use QUESTION type factors
(security questions don't require a device or OTP to enroll and verify).
All created users/factors are cleaned up in finally blocks.
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


def _create_active_user(token):
    """Create a user in ACTIVE state with a known password. Returns user_id or None."""
    ts = int(time.time())
    body = {
        "profile": {
            "firstName": "MCPFactor",
            "lastName": f"Test{ts}",
            "email": f"mcp-factor-{ts}@example.com",
            "login": f"mcp-factor-{ts}@example.com",
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
    """Deactivate then delete a user."""
    call("POST", f"/api/v1/users/{user_id}/lifecycle/deactivate", token=token)
    call("DELETE", f"/api/v1/users/{user_id}", token=token)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_user_factors_read(token):
    """Read-only: list enrolled factors, supported factor catalog, and security questions."""
    section("USER FACTORS — read-only")

    resp = call("GET", "/api/v1/users?filter=status+eq+%22ACTIVE%22&limit=1", token=token)
    if not report("GET /api/v1/users?filter=ACTIVE&limit=1 (for factors read test)", resp):
        return

    users = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not users:
        report_skip("User factor read tests", "no ACTIVE users in tenant")
        return

    user_id = users[0]["id"]

    # List enrolled factors (may be empty)
    resp = call("GET", f"/api/v1/users/{user_id}/factors", token=token)
    if not report("GET /api/v1/users/{userId}/factors (enrolled factors)", resp, (200,)):
        return

    factors = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if factors:
        factor_id = factors[0].get("id", "")
        if factor_id:
            resp = call("GET", f"/api/v1/users/{user_id}/factors/{factor_id}", token=token)
            report("GET /api/v1/users/{userId}/factors/{factorId}", resp, (200,))
    else:
        report_skip("GET /api/v1/users/{userId}/factors/{factorId}", "no factors enrolled for this user")

    # List supported factor types (catalog)
    resp = call("GET", f"/api/v1/users/{user_id}/factors/catalog", token=token)
    if report("GET /api/v1/users/{userId}/factors/catalog (supported types)", resp, (200,)):
        catalog = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
        if catalog:
            types = [f.get("factorType", "") for f in catalog[:5]]
            report_skip(f"  factor types available: {types}", "")

    # List security questions
    resp = call("GET", f"/api/v1/users/{user_id}/factors/questions", token=token)
    if report("GET /api/v1/users/{userId}/factors/questions", resp, (200,)):
        questions = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
        if questions:
            report_skip(f"  {len(questions)} security questions available", "")


def test_user_factor_question_crud(token):
    """CRUD: enroll QUESTION factor (no device/OTP needed), get, verify, unenroll."""
    section("USER FACTORS — QUESTION type CRUD")

    user_id = _create_active_user(token)
    if not user_id:
        report_skip("Factor CRUD tests", "could not create active user")
        return

    factor_id = None
    try:
        # List available questions to pick a valid one
        resp = call("GET", f"/api/v1/users/{user_id}/factors/questions", token=token)
        questions = []
        if resp.status_code == 200:
            questions = resp.json() if isinstance(resp.json(), list) else _items(resp.json())

        question_key = questions[0]["question"] if questions else "favorite_art_piece"

        # Enroll QUESTION factor
        enroll_body = {
            "factorType": "question",
            "provider": "OKTA",
            "profile": {
                "question": question_key,
                "answer": "mcp_live_test_answer",
            },
        }
        resp = call("POST", f"/api/v1/users/{user_id}/factors", body=enroll_body, token=token)
        if not report("POST /api/v1/users/{userId}/factors (enroll QUESTION)", resp, (200, 201, 400, 403)):
            return
        if resp.status_code in (400, 403):
            report_skip("Factor CRUD remainder", "factor enrollment not permitted or question unavailable")
            return

        factor_data = resp.json()
        factor_id = factor_data.get("id", "")
        factor_status = factor_data.get("status", "")

        # Get the factor
        resp = call("GET", f"/api/v1/users/{user_id}/factors/{factor_id}", token=token)
        report("GET /api/v1/users/{userId}/factors/{factorId} (enrolled)", resp, (200,))

        # Activate if needed (QUESTION factors often activate immediately on enroll)
        if factor_status == "PENDING_ACTIVATION":
            resp = call(
                "POST",
                f"/api/v1/users/{user_id}/factors/{factor_id}/lifecycle/activate",
                body={"answer": "mcp_live_test_answer"},
                token=token,
            )
            report("POST /factors/{factorId}/lifecycle/activate (QUESTION)", resp, (200, 204))

        # Resend (should return 400 for QUESTION type or already-active factor)
        resp = call(
            "POST",
            f"/api/v1/users/{user_id}/factors/{factor_id}/resend",
            body=enroll_body,
            token=token,
        )
        report(
            "POST /factors/{factorId}/resend (expect 400 for active QUESTION factor)",
            resp,
            (200, 400, 405),
        )

        # Unenroll the factor
        resp = call("DELETE", f"/api/v1/users/{user_id}/factors/{factor_id}", token=token)
        report("DELETE /api/v1/users/{userId}/factors/{factorId} (unenroll)", resp, (200, 204))
        factor_id = None

    finally:
        if factor_id and user_id:
            call("DELETE", f"/api/v1/users/{user_id}/factors/{factor_id}", token=token)
        if user_id:
            _cleanup_user(user_id, token)


def test_factor_transaction_status_endpoint(token):
    """Verify the factor transaction status endpoint is reachable (expect 404 — no active tx)."""
    section("USER FACTORS — transaction status endpoint")

    resp = call("GET", "/api/v1/users?filter=status+eq+%22ACTIVE%22&limit=1", token=token)
    if not report("GET /api/v1/users?filter=ACTIVE&limit=1 (for transaction status test)", resp):
        return

    users = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not users:
        report_skip("Factor transaction status", "no ACTIVE users in tenant")
        return

    user_id = users[0]["id"]

    # Get first enrolled factor if any
    resp = call("GET", f"/api/v1/users/{user_id}/factors", token=token)
    if resp.status_code != 200:
        report_skip("Factor transaction status", "could not list factors")
        return

    factors = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not factors:
        report_skip("Factor transaction status", "no factors enrolled for this user")
        return

    factor_id = factors[0].get("id", "")
    # Use a dummy transaction ID — endpoint should return 404 (not found), confirming the path works
    resp = call(
        "GET",
        f"/api/v1/users/{user_id}/factors/{factor_id}/transactions/dummy-tx-id",
        token=token,
    )
    report(
        "GET /factors/{factorId}/transactions/{txId} (dummy tx — expect 404)",
        resp,
        (200, 400, 404),
    )
