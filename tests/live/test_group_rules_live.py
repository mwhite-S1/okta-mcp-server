#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for group rules tools.

Creates real objects, tests them, then deletes everything in a finally block.
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

def test_group_rules_query_params(token):
    """Cover key query parameters for list_group_rules."""
    section("GROUP RULES — query parameter coverage")

    # Basic list with limit
    resp = call("GET", "/api/v1/groups/rules?limit=2", token=token)
    report("GET /api/v1/groups/rules?limit=2 (limit param)", resp, (200, 204))

    # search= text
    resp = call("GET", "/api/v1/groups/rules?search=mcp&limit=5", token=token)
    report("GET /api/v1/groups/rules?search=mcp&limit=5 (search= param)", resp, (200, 204))

    # expand= groupIdToGroupNameMap
    resp = call("GET", "/api/v1/groups/rules?expand=groupIdToGroupNameMap&limit=3", token=token)
    report("GET /api/v1/groups/rules?expand=groupIdToGroupNameMap&limit=3 (expand= param)", resp, (200, 204))


def test_group_rules_read(token):
    """Read-only tests: list existing group rules."""
    section("GROUP RULES — read-only")

    resp = call("GET", "/api/v1/groups/rules?limit=5", token=token)
    if not report("GET /api/v1/groups/rules?limit=5", resp):
        return

    body = resp.json()
    rules = body if isinstance(body, list) else _items(body)

    if rules:
        rule_id = rules[0]["id"]
        resp = call("GET", f"/api/v1/groups/rules/{rule_id}", token=token)
        report("GET /api/v1/groups/rules/{rule_id}", resp)

        # Test search
        resp = call("GET", "/api/v1/groups/rules?search=rule", token=token)
        report("GET /api/v1/groups/rules?search=rule", resp, (200,))
    else:
        report_skip("GET /api/v1/groups/rules/{rule_id}", "no group rules in tenant")


def test_group_rules_crud(token):
    """Full CRUD cycle: create, read, deactivate, replace, activate, deactivate, delete."""
    section("GROUP RULES — CRUD (self-cleaning)")

    # We need a target group to assign users to.
    # Create a temporary group first.
    ts = int(time.time())
    group_name = f"mcp-live-rule-target-{ts}"
    group_resp = call(
        "POST",
        "/api/v1/groups",
        body={"profile": {"name": group_name, "description": "temp group for rule test"}},
        token=token,
    )
    if not report("POST /api/v1/groups (temp group for rule)", group_resp, (200, 201)):
        return

    target_group_id = group_resp.json()["id"]

    # Create the group rule (INACTIVE by default)
    rule_name = f"mcp-live-group-rule-{ts}"
    create_body = {
        "type": "group_rule",
        "name": rule_name,
        "conditions": {
            "expression": {
                "type": "urn:okta:expression:1.0",
                "value": 'user.department eq "MCP-Live-Test"',
            }
        },
        "actions": {
            "assignUserToGroups": {
                "groupIds": [target_group_id],
            }
        },
    }

    resp = call("POST", "/api/v1/groups/rules", body=create_body, token=token)
    if not report("POST /api/v1/groups/rules (create)", resp, (200, 201)):
        call("DELETE", f"/api/v1/groups/{target_group_id}", token=token)
        return

    rule_id = resp.json()["id"]

    try:
        # GET the created rule
        resp = call("GET", f"/api/v1/groups/rules/{rule_id}", token=token)
        report("GET /api/v1/groups/rules/{rule_id} (fetch created)", resp)

        # Activate the rule
        resp = call("POST", f"/api/v1/groups/rules/{rule_id}/lifecycle/activate", token=token)
        report("POST /api/v1/groups/rules/{rule_id}/lifecycle/activate", resp, (200, 204))

        # GET again to confirm ACTIVE status
        resp = call("GET", f"/api/v1/groups/rules/{rule_id}", token=token)
        report("GET /api/v1/groups/rules/{rule_id} (after activate)", resp)

        # Deactivate before replace (required by API)
        resp = call("POST", f"/api/v1/groups/rules/{rule_id}/lifecycle/deactivate", token=token)
        report("POST /api/v1/groups/rules/{rule_id}/lifecycle/deactivate", resp, (200, 204))

        # Replace (update name/conditions; actions cannot change)
        replace_body = {
            "type": "group_rule",
            "name": f"{rule_name}-upd",
            "conditions": {
                "expression": {
                    "type": "urn:okta:expression:1.0",
                    "value": 'user.department eq "MCP-Live-Test-Updated"',
                }
            },
            "actions": {
                "assignUserToGroups": {
                    "groupIds": [target_group_id],
                }
            },
        }
        resp = call("PUT", f"/api/v1/groups/rules/{rule_id}", body=replace_body, token=token)
        report("PUT /api/v1/groups/rules/{rule_id} (replace)", resp, (200, 204))

        # Activate again after replace
        resp = call("POST", f"/api/v1/groups/rules/{rule_id}/lifecycle/activate", token=token)
        report("POST /api/v1/groups/rules/{rule_id}/lifecycle/activate (2nd)", resp, (200, 204))

        # Deactivate before delete (required by API)
        resp = call("POST", f"/api/v1/groups/rules/{rule_id}/lifecycle/deactivate", token=token)
        report("POST /api/v1/groups/rules/{rule_id}/lifecycle/deactivate (pre-delete)", resp, (200, 204))

    finally:
        # Delete the rule (must be INACTIVE)
        resp = call("DELETE", f"/api/v1/groups/rules/{rule_id}", token=token)
        report("DELETE /api/v1/groups/rules/{rule_id} (cleanup)", resp, (200, 202, 204))

        # Delete the temp group
        resp = call("DELETE", f"/api/v1/groups/{target_group_id}", token=token)
        report("DELETE /api/v1/groups/{target_group_id} (cleanup)", resp, (200, 204))
