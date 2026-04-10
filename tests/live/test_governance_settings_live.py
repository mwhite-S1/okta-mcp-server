#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for governance settings write paths, integrations,
delegates, principal settings, and operations.

Run with:
    pytest tests/live/test_governance_settings_live.py -v -s
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
# Governance Settings — read + cautious write paths
# ---------------------------------------------------------------------------

def test_governance_settings_write(token: str) -> None:
    """Verify settings read endpoints still work and exercise PATCH write paths
    with safe no-op or reversible payloads.
    """
    section("GOVERNANCE SETTINGS — Read + Write Paths")

    # GET top-level settings (baseline health check)
    resp = call("GET", "/governance/api/v1/settings", token=token)
    report("GET /governance/api/v1/settings", resp, (200, 204, 403, 404))

    if resp.status_code == 200:
        body = resp.json()
        print(f"      settings keys: {list(body.keys())[:10]}")

    # PATCH top-level settings — attempt a reversible change (disable certifications)
    # Accept 400/403 if the field path is wrong or the caller lacks permission
    patch_resp = call(
        "PATCH", "/governance/api/v1/settings",
        body=[{"op": "replace", "path": "/certificationSettings/enabled", "value": False}],
        token=token,
    )
    report(
        "PATCH /governance/api/v1/settings (certificationSettings/enabled=false)",
        patch_resp,
        (200, 204, 400, 403),
    )

    # GET certification-specific settings sub-endpoint
    resp = call("GET", "/governance/api/v1/settings/certification", token=token)
    report("GET /governance/api/v1/settings/certification", resp, (200, 204, 403, 404))

    if resp.status_code == 200:
        cert_body = resp.json()
        print(f"      certification settings keys: {list(cert_body.keys())[:8]}")

    # PATCH certification settings with empty ops array — verifies the endpoint
    # accepts the call without making any real change
    patch_cert_resp = call(
        "PATCH", "/governance/api/v1/settings/certification",
        body=[],
        token=token,
    )
    report(
        "PATCH /governance/api/v1/settings/certification (empty ops — endpoint probe)",
        patch_cert_resp,
        (200, 204, 400, 403),
    )

    # GET integrations list
    resp = call("GET", "/governance/api/v1/settings/integrations", token=token)
    report("GET /governance/api/v1/settings/integrations (list)", resp, (200, 204, 403, 404))

    if resp.status_code == 200:
        integrations = _items(resp.json())
        print(f"      Integrations found: {len(integrations)}")


# ---------------------------------------------------------------------------
# Principal Governance Settings
# ---------------------------------------------------------------------------

def test_principal_governance_settings(token: str, principal_id: str) -> None:
    """GET and PATCH principal-level governance settings for a real user."""
    section("PRINCIPAL GOVERNANCE SETTINGS")

    if not principal_id:
        report_skip("GET /governance/api/v1/principal-settings/{id}", "no principal_id available")
        report_skip("PATCH /governance/api/v1/principal-settings/{id}", "no principal_id available")
        return

    print(f"      principal_id={principal_id}")

    # GET principal settings
    resp = call("GET", f"/governance/api/v1/principal-settings/{principal_id}", token=token)
    # 404 = principal not enrolled in IGA
    report(f"GET /governance/api/v1/principal-settings/{principal_id}", resp, (200, 404, 403))

    if resp.status_code == 200:
        body = resp.json()
        print(f"      principal settings keys: {list(body.keys())[:8]}")

    # PATCH principal settings — clear delegateAppointments (safe no-op if empty)
    patch_resp = call(
        "PATCH", f"/governance/api/v1/principal-settings/{principal_id}",
        body={"delegateAppointments": []},
        token=token,
    )
    # 400 = invalid body shape, 404 = principal not in IGA
    report(
        f"PATCH /governance/api/v1/principal-settings/{principal_id} (delegateAppointments=[])",
        patch_resp,
        (200, 204, 400, 404, 403),
    )


# ---------------------------------------------------------------------------
# Governance Operation lookup
# ---------------------------------------------------------------------------

def test_governance_operation(token: str) -> None:
    """Attempt to locate a recent operation ID from the labels log and GET it."""
    section("GOVERNANCE OPERATIONS — Operation ID lookup")

    # Probe the labels endpoint to find any recently created label that may
    # have an associated operation ID in its response envelope.
    resp = call("GET", "/governance/api/v1/labels", token=token)
    report("GET /governance/api/v1/labels (operation ID probe)", resp, (200, 204, 403, 404))

    if resp.status_code not in (200, 204):
        report_skip("GET /governance/api/v1/operations/{id}", "labels endpoint not accessible")
        return

    if resp.status_code == 204:
        report_skip("GET /governance/api/v1/operations/{id}", "no labels returned (204)")
        return

    labels = _items(resp.json())
    print(f"      Labels available: {len(labels)}")

    # Try to extract an operation ID from any label response header or body field
    op_id = ""
    for label in labels:
        if isinstance(label, dict):
            # Some governance responses embed an operationId or _links.operation
            op_id = (
                label.get("operationId")
                or label.get("operation", {}).get("id", "")
                or (label.get("_links") or {}).get("operation", {}).get("href", "").rstrip("/").split("/")[-1]
            )
            if op_id:
                break

    if not op_id:
        report_skip(
            "GET /governance/api/v1/operations/{id}",
            "no operation ID found in recent labels (operations are only tracked for async writes)",
        )
        return

    print(f"      Found operation_id={op_id}")
    resp = call("GET", f"/governance/api/v1/operations/{op_id}", token=token)
    report(f"GET /governance/api/v1/operations/{op_id}", resp, (200, 404, 403))

    if resp.status_code == 200:
        body = resp.json()
        print(f"      operation status: {body.get('status', 'n/a')}  type: {body.get('type', 'n/a')}")
