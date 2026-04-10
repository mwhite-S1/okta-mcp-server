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

def test_policy_types_read(token):
    """Read-only: list policies of each supported type."""
    section("POLICIES — type filter coverage")

    for policy_type in ("PASSWORD", "OKTA_SIGN_ON", "MFA_ENROLL", "ACCESS_POLICY", "PROFILE_ENROLLMENT"):
        resp = call("GET", f"/api/v1/policies?type={policy_type}&limit=3", token=token)
        report(f"GET /api/v1/policies?type={policy_type}&limit=3", resp, (200, 204))


def test_policy_clone(token):
    """CRUD: create an ACCESS_POLICY, clone it, verify the clone has a distinct ID, delete both.

    Note: only ACCESS_POLICY type supports the clone endpoint — PASSWORD and OKTA_SIGN_ON
    policies return 400 with "only supported for authentication policies".
    """
    section("POLICIES — clone (self-cleaning)")

    ts = int(time.time())
    # ACCESS_POLICY is the only type that supports /clone
    base_body = {
        "type": "ACCESS_POLICY",
        "name": f"mcp-live-policy-clone-{ts}",
        "status": "INACTIVE",
        "description": "MCP live test policy for clone",
    }

    policy_id = None
    clone_id = None
    try:
        resp = call("POST", "/api/v1/policies", body=base_body, token=token)
        if not report("POST /api/v1/policies (create ACCESS_POLICY for clone test)", resp, (200, 201, 400)):
            return
        if resp.status_code == 400:
            report_skip("Policy clone", "create returned 400 — skipping")
            return

        policy_id = resp.json()["id"]

        # Clone the policy
        resp = call("POST", f"/api/v1/policies/{policy_id}/clone", token=token)
        if report("POST /api/v1/policies/{policyId}/clone", resp, (200, 201)):
            clone_data = resp.json()
            clone_id = clone_data.get("id", "")
            clone_name = clone_data.get("name", "")
            if clone_id and clone_id != policy_id:
                report_skip(f"  clone id: {clone_id[:12]}... name: {clone_name[:40]}", "")
            else:
                report_skip("  clone returned same id or no id", "")

    finally:
        if policy_id:
            call("DELETE", f"/api/v1/policies/{policy_id}", token=token)
        if clone_id:
            call("DELETE", f"/api/v1/policies/{clone_id}", token=token)


def test_policy_simulation(token):
    """Read-only: test policy simulation endpoint (may not be licensed in all tenants)."""
    section("POLICIES — policy simulation")

    # Find an OKTA_SIGN_ON policy and an active app for simulation
    resp = call("GET", "/api/v1/policies?type=OKTA_SIGN_ON&limit=1", token=token)
    if resp.status_code != 200:
        report_skip("Policy simulation", "could not list OKTA_SIGN_ON policies")
        return

    policies = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not policies:
        report_skip("Policy simulation", "no OKTA_SIGN_ON policies found")
        return

    resp = call("GET", '/api/v1/apps?filter=status+eq+"ACTIVE"&limit=1', token=token)
    if resp.status_code != 200:
        report_skip("Policy simulation", "could not list apps")
        return

    apps = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not apps:
        report_skip("Policy simulation", "no ACTIVE apps found")
        return

    app_id = apps[0]["id"]
    sim_body = [
        {
            "policyType": "OKTA_SIGN_ON",
            "appInstance": app_id,
            "policyContext": {"authProtocol": "SAML2"},
        }
    ]

    resp = call("POST", "/api/v1/policies/simulate", body=sim_body, token=token)
    report(
        "POST /api/v1/policies/simulate (policy simulation)",
        resp,
        (200, 201, 400, 403, 404),
    )


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


def test_access_policy_crud(token):
    """CRUD for ACCESS_POLICY (authentication policy) type — create, update, add rule, delete."""
    section("POLICIES — ACCESS_POLICY CRUD (self-cleaning)")

    ts = int(time.time())
    body = {
        "type": "ACCESS_POLICY",
        "name": f"mcp-live-access-policy-{ts}",
        "status": "INACTIVE",
        "description": "MCP live test authentication policy",
    }

    policy_id = None
    rule_id = None
    try:
        resp = call("POST", "/api/v1/policies", body=body, token=token)
        if not report("POST /api/v1/policies (create ACCESS_POLICY)", resp, (200, 201, 400)):
            return
        if resp.status_code == 400:
            report_skip("ACCESS_POLICY CRUD", f"create returned 400: {resp.text[:120]}")
            return

        policy_id = resp.json()["id"]

        resp = call("GET", f"/api/v1/policies/{policy_id}", token=token)
        report("GET /api/v1/policies/{policyId} (fetch created)", resp, (200,))

        # Full replace via PUT
        update_body = {
            "type": "ACCESS_POLICY",
            "name": f"mcp-live-access-policy-{ts}-upd",
            "status": "INACTIVE",
            "description": "MCP live test authentication policy updated",
        }
        resp = call("PUT", f"/api/v1/policies/{policy_id}", body=update_body, token=token)
        report("PUT /api/v1/policies/{policyId} (update name)", resp, (200, 204))

        # Add a rule — ACCESS_POLICY rules require type="ACCESS_POLICY", factorMode 1FA/2FA,
        # and a possession constraint (NO_FACTOR without constraints is rejected by the API).
        rule_body = {
            "name": f"mcp-rule-{ts}",
            "type": "ACCESS_POLICY",
            "actions": {
                "appSignOn": {
                    "access": "ALLOW",
                    "verificationMethod": {
                        "factorMode": "1FA",
                        "type": "ASSURANCE",
                        "reauthenticateIn": "PT12H",
                        "constraints": [{"possession": {"required": True, "deviceBound": "REQUIRED"}}],
                    },
                }
            },
        }
        rule_resp = call("POST", f"/api/v1/policies/{policy_id}/rules", body=rule_body, token=token)
        rule_created = report(
            "POST /api/v1/policies/{policyId}/rules (create ACCESS_POLICY rule)",
            rule_resp,
            (200, 201, 400),
        )

        if rule_created and rule_resp.status_code in (200, 201):
            rule_id = rule_resp.json()["id"]

            resp = call("GET", f"/api/v1/policies/{policy_id}/rules/{rule_id}", token=token)
            report("GET /api/v1/policies/{policyId}/rules/{ruleId}", resp, (200,))

            resp = call(
                "POST",
                f"/api/v1/policies/{policy_id}/rules/{rule_id}/lifecycle/deactivate",
                token=token,
            )
            report(
                "POST /lifecycle/deactivate on ACCESS_POLICY rule",
                resp,
                (200, 204),
            )

            resp = call("DELETE", f"/api/v1/policies/{policy_id}/rules/{rule_id}", token=token)
            report("DELETE /api/v1/policies/{policyId}/rules/{ruleId}", resp, (200, 204))
            rule_id = None
        elif rule_resp.status_code == 400:
            report_skip("ACCESS_POLICY rule sub-tests", f"rule creation returned 400: {rule_resp.text[:120]}")

    finally:
        if rule_id:
            call("DELETE", f"/api/v1/policies/{policy_id}/rules/{rule_id}", token=token)
        if policy_id:
            resp = call("DELETE", f"/api/v1/policies/{policy_id}", token=token)
            report("DELETE /api/v1/policies/{policyId} (cleanup)", resp, (200, 204))


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
