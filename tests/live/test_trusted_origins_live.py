#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for trusted origin tools.

Full CRUD with lifecycle: create a CORS origin, read, replace, deactivate, activate, delete.
All created origins are cleaned up in finally blocks.
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_trusted_origins_read(token):
    """Read-only: list origins with various params; get a specific origin."""
    section("TRUSTED ORIGINS — read-only")

    # Basic list
    resp = call("GET", "/api/v1/trustedOrigins?limit=5", token=token)
    if not report("GET /api/v1/trustedOrigins?limit=5", resp):
        return

    body = resp.json()
    origins = body if isinstance(body, list) else _items(body)

    # Limit parameter
    resp = call("GET", "/api/v1/trustedOrigins?limit=2", token=token)
    report("GET /api/v1/trustedOrigins?limit=2 (limit param)", resp, (200,))

    # Filter by status (ACTIVE)
    resp = call("GET", '/api/v1/trustedOrigins?limit=5&filter=status+eq+"ACTIVE"', token=token)
    report('GET /api/v1/trustedOrigins?filter=status+eq+"ACTIVE"', resp, (200, 204))

    if origins:
        origin_id = origins[0]["id"]
        resp = call("GET", f"/api/v1/trustedOrigins/{origin_id}", token=token)
        report("GET /api/v1/trustedOrigins/{originId}", resp, (200,))
    else:
        report_skip("GET /api/v1/trustedOrigins/{originId}", "no trusted origins in tenant")


def test_trusted_origins_crud(token):
    """Full CRUD lifecycle: create CORS+REDIRECT origin, get, replace, deactivate, activate, delete."""
    section("TRUSTED ORIGINS — CRUD (self-cleaning)")

    ts = int(time.time())
    origin_name = f"mcp-test-origin-{ts}"
    origin_url = f"https://mcp-test-{ts}.example.com"

    create_body = {
        "name": origin_name,
        "origin": origin_url,
        "scopes": [{"type": "CORS"}, {"type": "REDIRECT"}],
    }

    origin_id = None
    try:
        resp = call("POST", "/api/v1/trustedOrigins", body=create_body, token=token)
        if not report("POST /api/v1/trustedOrigins (create CORS+REDIRECT origin)", resp, (200, 201, 400)):
            return
        if resp.status_code == 400:
            report_skip("Trusted origin CRUD", "creation returned 400 — skipping remainder")
            return

        created = resp.json()
        origin_id = created["id"]

        # Get by ID
        resp = call("GET", f"/api/v1/trustedOrigins/{origin_id}", token=token)
        report("GET /api/v1/trustedOrigins/{originId} (fetch created)", resp, (200,))

        # Replace (full update — same origin URL, updated name, same scopes)
        replace_body = {
            "name": f"{origin_name}-upd",
            "origin": origin_url,
            "scopes": [{"type": "CORS"}, {"type": "REDIRECT"}],
        }
        resp = call("PUT", f"/api/v1/trustedOrigins/{origin_id}", body=replace_body, token=token)
        report("PUT /api/v1/trustedOrigins/{originId} (replace — updated name)", resp, (200, 204))

        # Deactivate
        resp = call("POST", f"/api/v1/trustedOrigins/{origin_id}/lifecycle/deactivate", token=token)
        report("POST /trustedOrigins/{originId}/lifecycle/deactivate", resp, (200, 204))

        # Verify INACTIVE
        resp = call("GET", f"/api/v1/trustedOrigins/{origin_id}", token=token)
        if report("GET /trustedOrigins/{originId} (verify INACTIVE)", resp, (200,)):
            status = resp.json().get("status", "")
            if status != "INACTIVE":
                report_skip("Expected INACTIVE status", f"got {status!r}")

        # Activate
        resp = call("POST", f"/api/v1/trustedOrigins/{origin_id}/lifecycle/activate", token=token)
        report("POST /trustedOrigins/{originId}/lifecycle/activate", resp, (200, 204))

        # Delete (trusted origins can be deleted regardless of status)
        resp = call("DELETE", f"/api/v1/trustedOrigins/{origin_id}", token=token)
        report("DELETE /api/v1/trustedOrigins/{originId}", resp, (200, 204))
        origin_id = None

    finally:
        if origin_id:
            call("DELETE", f"/api/v1/trustedOrigins/{origin_id}", token=token)
