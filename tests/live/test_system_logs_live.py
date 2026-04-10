#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for system log tools.

Read-only: system logs cannot be created or deleted via the API.
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

def test_system_logs_query_params(token):
    """Cover all key query parameters for get_logs."""
    section("SYSTEM LOGS — query parameter coverage")

    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    one_hour_ago = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # since= parameter (ISO 8601 timestamp)
    resp = call("GET", f"/api/v1/logs?since={one_hour_ago}&limit=5", token=token)
    report(f"GET /api/v1/logs?since={{1h_ago}}&limit=5 (since= param)", resp, (200, 204))

    # until= parameter
    resp = call("GET", f"/api/v1/logs?until={now_str}&limit=5", token=token)
    report(f"GET /api/v1/logs?until={{now}}&limit=5 (until= param)", resp, (200, 204))

    # since= + until= combined
    resp = call("GET", f"/api/v1/logs?since={one_hour_ago}&until={now_str}&limit=3", token=token)
    report("GET /api/v1/logs?since=..&until=..&limit=3 (since+until combined)", resp, (200, 204))

    # filter= expression
    resp = call("GET", '/api/v1/logs?filter=eventType+eq+"user.session.start"&limit=5', token=token)
    report('GET /api/v1/logs?filter=eventType+eq+"user.session.start"&limit=5 (filter=)', resp, (200, 204))

    # q= text search
    resp = call("GET", "/api/v1/logs?q=login&limit=5", token=token)
    report("GET /api/v1/logs?q=login&limit=5 (q= text search)", resp, (200, 204))

    # sortOrder=ASCENDING
    resp = call("GET", f"/api/v1/logs?since={one_hour_ago}&sortOrder=ASCENDING&limit=5", token=token)
    report("GET /api/v1/logs?sortOrder=ASCENDING&limit=5", resp, (200, 204))

    # sortOrder=DESCENDING (default)
    resp = call("GET", f"/api/v1/logs?since={one_hour_ago}&sortOrder=DESCENDING&limit=3", token=token)
    report("GET /api/v1/logs?sortOrder=DESCENDING&limit=3", resp, (200, 204))


def test_system_logs(token):
    section("SYSTEM LOGS")

    resp = call("GET", "/api/v1/logs?limit=5", token=token)
    report("GET /api/v1/logs?limit=5", resp)

    resp = call("GET", '/api/v1/logs?limit=3&filter=eventType eq "user.session.start"', token=token)
    report('GET /api/v1/logs?limit=3&filter=eventType eq "user.session.start"', resp, (200, 204))

    resp = call("GET", "/api/v1/logs?limit=3&q=login", token=token)
    report("GET /api/v1/logs?limit=3&q=login", resp, (200, 204))
