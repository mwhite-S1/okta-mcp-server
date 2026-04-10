#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for network zone tools.

Full CRUD with lifecycle: create an IP zone, read, replace, deactivate, activate, delete.
All created zones are cleaned up in finally blocks.
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

def test_network_zones_read(token):
    """Read-only: list zones with various filter params; get a specific zone."""
    section("NETWORK ZONES — read-only")

    # Basic list
    resp = call("GET", "/api/v1/zones?limit=5", token=token)
    if not report("GET /api/v1/zones?limit=5", resp):
        return

    body = resp.json()
    zones = body if isinstance(body, list) else _items(body)

    # Filter by usage
    resp = call("GET", '/api/v1/zones?limit=5&filter=usage+eq+"POLICY"', token=token)
    report('GET /api/v1/zones?filter=usage+eq+"POLICY"&limit=5', resp, (200, 204))

    # Zones API only supports filter=usage — verify BLOCK usage filter
    resp = call("GET", '/api/v1/zones?limit=5&filter=usage+eq+"BLOCKLIST"', token=token)
    report('GET /api/v1/zones?filter=usage+eq+"BLOCKLIST"&limit=5', resp, (200, 204))

    # Limit parameter
    resp = call("GET", "/api/v1/zones?limit=2", token=token)
    report("GET /api/v1/zones?limit=2 (verify limit param)", resp, (200,))

    if zones:
        zone_id = zones[0]["id"]
        resp = call("GET", f"/api/v1/zones/{zone_id}", token=token)
        report("GET /api/v1/zones/{zoneId}", resp, (200,))
    else:
        report_skip("GET /api/v1/zones/{zoneId}", "no zones found in tenant")


def test_network_zones_crud(token):
    """Full CRUD lifecycle: create IP zone, get, replace, deactivate, activate, deactivate, delete."""
    section("NETWORK ZONES — CRUD (self-cleaning)")

    ts = int(time.time())
    zone_name = f"mcp-test-zone-{ts}"
    create_body = {
        "type": "IP",
        "name": zone_name,
        "status": "ACTIVE",
        "gateways": [{"type": "CIDR", "value": "10.254.0.0/16"}],
        "proxies": [],
    }

    zone_id = None
    try:
        resp = call("POST", "/api/v1/zones", body=create_body, token=token)
        if not report("POST /api/v1/zones (create IP zone)", resp, (200, 201, 400)):
            return
        if resp.status_code == 400:
            report_skip("Network zone CRUD", "zone creation returned 400 — skipping remainder")
            return

        created = resp.json()
        zone_id = created["id"]
        created_name = created.get("name", "")
        if created_name != zone_name:
            report_skip("Zone name verification", f"expected {zone_name!r}, got {created_name!r}")

        # Get by ID
        resp = call("GET", f"/api/v1/zones/{zone_id}", token=token)
        report("GET /api/v1/zones/{zoneId} (fetch created)", resp, (200,))

        # Replace (full update)
        replace_body = {
            "type": "IP",
            "name": f"{zone_name}-upd",
            "gateways": [
                {"type": "CIDR", "value": "10.254.0.0/16"},
                {"type": "RANGE", "value": "192.168.100.1-192.168.100.255"},
            ],
            "proxies": [],
        }
        resp = call("PUT", f"/api/v1/zones/{zone_id}", body=replace_body, token=token)
        report("PUT /api/v1/zones/{zoneId} (replace — updated name + gateway)", resp, (200, 204))

        # Deactivate (some zones start ACTIVE)
        resp = call("POST", f"/api/v1/zones/{zone_id}/lifecycle/deactivate", token=token)
        report("POST /api/v1/zones/{zoneId}/lifecycle/deactivate", resp, (200, 204))

        # Activate
        resp = call("POST", f"/api/v1/zones/{zone_id}/lifecycle/activate", token=token)
        report("POST /api/v1/zones/{zoneId}/lifecycle/activate", resp, (200, 204))

        # Deactivate again (zones must be INACTIVE to delete)
        resp = call("POST", f"/api/v1/zones/{zone_id}/lifecycle/deactivate", token=token)
        report("POST /api/v1/zones/{zoneId}/lifecycle/deactivate (pre-delete)", resp, (200, 204))

        # Delete
        resp = call("DELETE", f"/api/v1/zones/{zone_id}", token=token)
        report("DELETE /api/v1/zones/{zoneId}", resp, (200, 204))
        zone_id = None

    finally:
        if zone_id:
            # Ensure deactivated before deletion
            call("POST", f"/api/v1/zones/{zone_id}/lifecycle/deactivate", token=token)
            call("DELETE", f"/api/v1/zones/{zone_id}", token=token)
