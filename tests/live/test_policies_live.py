#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for policy tools.

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

def test_policies_read(token):
    section("POLICIES — read-only")

    resp = call("GET", "/api/v1/policies?type=PASSWORD&limit=5", token=token)
    if not report("GET /api/v1/policies?type=PASSWORD&limit=5", resp):
        return

    policies = resp.json() if isinstance(resp.json(), list) else _items(resp.json())

    if policies:
        policy_id = policies[0]["id"]

        resp = call("GET", f"/api/v1/policies/{policy_id}", token=token)
        report("GET /api/v1/policies/{policy_id}", resp)

        resp = call("GET", f"/api/v1/policies/{policy_id}/rules", token=token)
        if report("GET /api/v1/policies/{policy_id}/rules", resp):
            rules = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
            if rules:
                rule_id = rules[0]["id"]
                resp = call("GET", f"/api/v1/policies/{policy_id}/rules/{rule_id}", token=token)
                report("GET /api/v1/policies/{policy_id}/rules/{rule_id}", resp)
            else:
                report_skip("GET /api/v1/policies/{policy_id}/rules/{rule_id}", "policy has no rules")
    else:
        report_skip("GET /api/v1/policies/{policy_id}", "no PASSWORD policies in tenant")
        report_skip("GET /api/v1/policies/{policy_id}/rules", "no PASSWORD policies in tenant")
        report_skip("GET /api/v1/policies/{policy_id}/rules/{rule_id}", "no PASSWORD policies in tenant")


def test_policy_mappings_read(token):
    section("POLICY MAPPINGS — read-only")

    resp = call("GET", "/api/v1/policies?type=OKTA_SIGN_ON&limit=5", token=token)
    if not report("GET /api/v1/policies?type=OKTA_SIGN_ON&limit=5", resp):
        return

    policies = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not policies:
        report_skip("Policy mappings", "no OKTA_SIGN_ON policies in tenant")
        return

    policy_id = policies[0]["id"]

    resp = call("GET", f"/api/v1/policies/{policy_id}/mappings", token=token)
    report(f"GET /api/v1/policies/{{policyId}}/mappings (id: {policy_id})", resp, (200, 404))

    if resp.status_code == 200:
        body = resp.json()
        mappings = body if isinstance(body, list) else _items(body)
        if mappings:
            mapping_id = mappings[0].get("id", "")
            if mapping_id:
                resp = call("GET", f"/api/v1/policies/{policy_id}/mappings/{mapping_id}", token=token)
                report("GET /api/v1/policies/{policyId}/mappings/{mappingId}", resp, (200,))
        else:
            report_skip("GET /api/v1/policies/{policyId}/mappings/{mappingId}", "no mappings found")

    # Deprecated: list apps mapped to policy
    resp = call("GET", f"/api/v1/policies/{policy_id}/app", token=token)
    report(f"GET /api/v1/policies/{{policyId}}/app (deprecated)", resp, (200, 404))


def test_policy_crud(token):
    section("POLICIES — CRUD (self-cleaning)")

    ts = int(time.time())
    body = {
        "type": "PASSWORD",
        "name": f"mcp-live-policy-{ts}",
        "status": "INACTIVE",
        "description": "MCP live test policy",
        "settings": {
            "password": {
                "age": {
                    "maxAgeDays": 90,
                    "expireWarnDays": 14,
                    "minAgeMinutes": 0,
                    "historyCount": 4,
                },
                "complexity": {
                    "minLength": 8,
                    "minLowerCase": 1,
                    "minUpperCase": 1,
                    "minNumber": 1,
                    "minSymbol": 0,
                },
            }
        },
    }

    resp = call("POST", "/api/v1/policies", body=body, token=token)
    if not report("POST /api/v1/policies (create)", resp, (200, 201, 400)):
        return
    if resp.status_code == 400:
        report_skip("Policy CRUD", "policy creation returned 400 — skipping remainder")
        return

    created = resp.json()
    policy_id = created["id"]

    try:
        resp = call("GET", f"/api/v1/policies/{policy_id}", token=token)
        report("GET /api/v1/policies/{policy_id} (fetch created)", resp)

        # Full replace via PUT
        update_body = {
            "type": "PASSWORD",
            "name": f"mcp-live-policy-{ts}-upd",
            "status": "INACTIVE",
            "description": "MCP live test policy updated",
            "settings": body["settings"],
        }
        resp = call("PUT", f"/api/v1/policies/{policy_id}", body=update_body, token=token)
        report("PUT /api/v1/policies/{policy_id} (update name)", resp, (200, 204))

        # Rule CRUD
        rule_body = {
            "type": "PASSWORD",
            "name": f"mcp-rule-{ts}",
            "conditions": {
                "people": {"users": {"exclude": []}},
            },
            "actions": {
                "passwordChange": {"access": "ALLOW"},
                "selfServicePasswordReset": {"access": "ALLOW"},
                "selfServiceUnlock": {"access": "DENY"},
            },
        }
        rule_resp = call("POST", f"/api/v1/policies/{policy_id}/rules", body=rule_body, token=token)
        rule_created = report("POST /api/v1/policies/{policy_id}/rules (create rule)", rule_resp, (200, 201, 400))

        if rule_created and rule_resp.status_code in (200, 201):
            rule_id = rule_resp.json()["id"]

            resp = call("GET", f"/api/v1/policies/{policy_id}/rules/{rule_id}", token=token)
            report("GET /api/v1/policies/{policy_id}/rules/{rule_id}", resp)

            resp = call(
                "POST",
                f"/api/v1/policies/{policy_id}/rules/{rule_id}/lifecycle/deactivate",
                token=token,
            )
            report(
                "POST /api/v1/policies/{policy_id}/rules/{rule_id}/lifecycle/deactivate",
                resp,
                (200, 204),
            )

            resp = call("DELETE", f"/api/v1/policies/{policy_id}/rules/{rule_id}", token=token)
            report("DELETE /api/v1/policies/{policy_id}/rules/{rule_id} (cleanup rule)", resp, (200, 204))
        else:
            report_skip("Policy rule detail/deactivate/delete", "rule creation was skipped or returned 400")

    finally:
        resp = call("DELETE", f"/api/v1/policies/{policy_id}", token=token)
        report("DELETE /api/v1/policies/{policy_id} (cleanup)", resp, (200, 204))
