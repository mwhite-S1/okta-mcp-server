#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for IAM governance bundles and user role governance.

Tests the /api/v1/iam/governance/ endpoints.

Run with:
    pytest tests/live/test_governance_iam_live.py -v -s
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


# ---------------------------------------------------------------------------
# IAM Opt-In Status
# ---------------------------------------------------------------------------

def test_iam_opt_in_status(token: str) -> None:
    """GET /api/v1/iam/governance/optIn — report the opt-in status without mutating it."""
    section("IAM GOVERNANCE — Opt-In Status (read-only)")

    resp = call("GET", "/api/v1/iam/governance/optIn", token=token)
    # 403 if IAM governance feature is not enabled on the tenant
    report("GET /api/v1/iam/governance/optIn", resp, (200, 403, 404))

    if resp.status_code == 200:
        body = resp.json()
        opted_in = body.get("optedIn", body.get("enabled", body.get("status", "unknown")))
        print(f"      optIn status: {opted_in}")
    elif resp.status_code == 403:
        print("      (403 — IAM governance feature may not be enabled on this tenant)")
    elif resp.status_code == 404:
        print("      (404 — endpoint not found; feature may be unavailable)")


# ---------------------------------------------------------------------------
# IAM Governance Bundles — full CRUD (self-cleaning)
# ---------------------------------------------------------------------------

def test_iam_governance_bundles(token: str) -> None:
    """Full CRUD for /api/v1/iam/governance/bundles (self-cleaning)."""
    section("IAM GOVERNANCE BUNDLES — CRUD")

    # LIST
    resp = call("GET", "/api/v1/iam/governance/bundles", token=token)
    report("GET /api/v1/iam/governance/bundles (list)", resp, (200, 204, 403, 404))

    if resp.status_code == 403:
        print("      (403 — IAM governance bundles feature not enabled; skipping CRUD)")
        return
    if resp.status_code == 404:
        print("      (404 — endpoint not found; skipping CRUD)")
        return

    ts = int(time.time())
    bundle_name = f"mcp-live-bundle-{ts}"

    # CREATE
    create_resp = call(
        "POST", "/api/v1/iam/governance/bundles",
        body={"name": bundle_name},
        token=token,
    )
    # 400 = validation error, 403 = feature disabled
    if not report("POST /api/v1/iam/governance/bundles (create)", create_resp, (200, 201, 400, 403)):
        return

    if create_resp.status_code in (400, 403):
        print(f"      ({create_resp.status_code} — bundle creation not available; skipping sub-tests)")
        return

    created = create_resp.json()
    bundle_id = created.get("id", created.get("bundleId", ""))
    print(f"      bundleId={bundle_id}  name={bundle_name}")

    if not bundle_id:
        print("      Could not extract bundle ID from response; skipping sub-tests")
        return

    try:
        # GET single bundle
        resp = call("GET", f"/api/v1/iam/governance/bundles/{bundle_id}", token=token)
        report(f"GET /api/v1/iam/governance/bundles/{bundle_id}", resp, (200, 404))

        # LIST entitlements associated with the bundle
        resp = call("GET", f"/api/v1/iam/governance/bundles/{bundle_id}/entitlements", token=token)
        report(f"GET /api/v1/iam/governance/bundles/{bundle_id}/entitlements", resp, (200, 204, 404))
        if resp.status_code == 200:
            items = _items(resp.json())
            print(f"      Entitlements in bundle: {len(items)}")

        # PUT — rename the bundle
        put_resp = call(
            "PUT", f"/api/v1/iam/governance/bundles/{bundle_id}",
            body={"name": f"{bundle_name}-upd"},
            token=token,
        )
        report(f"PUT /api/v1/iam/governance/bundles/{bundle_id} (rename)", put_resp, (200, 204, 400))

    finally:
        # Always attempt DELETE regardless of sub-test outcomes
        del_resp = call("DELETE", f"/api/v1/iam/governance/bundles/{bundle_id}", token=token)
        report(f"DELETE /api/v1/iam/governance/bundles/{bundle_id} (cleanup)", del_resp, (200, 204, 404))
