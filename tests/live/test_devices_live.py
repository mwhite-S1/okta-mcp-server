#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for device tools.

Read-only: device enrollment is managed externally and cannot be synthesised in tests.
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

def test_devices_read(token):
    section("DEVICES — read-only")

    resp = call("GET", "/api/v1/devices?limit=5", token=token)
    if not report("GET /api/v1/devices?limit=5", resp):
        return

    devices = resp.json() if isinstance(resp.json(), list) else _items(resp.json())

    if devices:
        device_id = devices[0]["id"]

        resp = call("GET", f"/api/v1/devices/{device_id}", token=token)
        report("GET /api/v1/devices/{device_id}", resp)

        resp = call("GET", f"/api/v1/devices/{device_id}/users", token=token)
        report("GET /api/v1/devices/{device_id}/users", resp)
    else:
        report_skip("Device detail/users", "no devices enrolled in tenant")
