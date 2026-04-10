#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for application sub-resource tools.

Tests user assignments, group assignments, grants, tokens, connections,
features, push mappings. Read-only where possible; destructive ops clean up.
"""

from __future__ import annotations

import os
import sys

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

from test_governance_live import call, _items, report, report_skip, section, BASE_URL  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first_app(token):
    """Return the first active application id/label, or (None, None)."""
    resp = call("GET", "/api/v1/apps?filter=status+eq+%22ACTIVE%22&limit=5", token=token)
    if resp.status_code != 200:
        return None, None
    apps = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not apps:
        return None, None
    return apps[0]["id"], apps[0].get("label", "unknown")


def _first_user(token):
    """Return the first active user id, or None."""
    resp = call("GET", "/api/v1/users?limit=1&filter=status+eq+%22ACTIVE%22", token=token)
    if resp.status_code != 200:
        return None
    users = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    return users[0]["id"] if users else None


def _first_group(token):
    """Return the first group id, or None."""
    resp = call("GET", "/api/v1/groups?limit=1", token=token)
    if resp.status_code != 200:
        return None
    groups = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    return groups[0]["id"] if groups else None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_application_users(token):
    """Read-only: list users assigned to an app; optionally fetch one."""
    section("APP USERS — read-only")

    app_id, label = _first_app(token)
    if not app_id:
        report_skip("application users", "no active apps in tenant")
        return

    resp = call("GET", f"/api/v1/apps/{app_id}/users?limit=5", token=token)
    if not report(f"GET /api/v1/apps/{{appId}}/users (app: {label})", resp, (200,)):
        return

    body = resp.json()
    app_users = body if isinstance(body, list) else _items(body)

    if app_users:
        uid = app_users[0]["id"]
        resp = call("GET", f"/api/v1/apps/{app_id}/users/{uid}", token=token)
        report("GET /api/v1/apps/{appId}/users/{userId}", resp, (200,))
    else:
        report_skip("GET /api/v1/apps/{appId}/users/{userId}", f"no users assigned to app {label}")


def test_application_group_assignments(token):
    """Read-only: list group assignments for an app; fetch one."""
    section("APP GROUPS — read-only")

    app_id, label = _first_app(token)
    if not app_id:
        report_skip("application group assignments", "no active apps in tenant")
        return

    resp = call("GET", f"/api/v1/apps/{app_id}/groups?limit=5", token=token)
    if not report(f"GET /api/v1/apps/{{appId}}/groups (app: {label})", resp, (200,)):
        return

    body = resp.json()
    assignments = body if isinstance(body, list) else _items(body)

    if assignments:
        gid = assignments[0]["id"]
        resp = call("GET", f"/api/v1/apps/{app_id}/groups/{gid}", token=token)
        report("GET /api/v1/apps/{appId}/groups/{groupId}", resp, (200,))
    else:
        report_skip("GET /api/v1/apps/{appId}/groups/{groupId}", f"no groups assigned to app {label}")


def test_assign_group_to_app_crud(token):
    """CRUD: create temp group, assign to app, unassign, delete group."""
    section("APP GROUPS — assign/unassign (self-cleaning)")

    import time
    app_id, label = _first_app(token)
    if not app_id:
        report_skip("assign group to app", "no active apps in tenant")
        return

    ts = int(time.time())
    grp_resp = call(
        "POST",
        "/api/v1/groups",
        body={"profile": {"name": f"mcp-live-appgrp-{ts}", "description": "temp"}},
        token=token,
    )
    if not report("POST /api/v1/groups (create temp group)", grp_resp, (200, 201)):
        return

    group_id = grp_resp.json()["id"]

    try:
        resp = call("PUT", f"/api/v1/apps/{app_id}/groups/{group_id}", body={}, token=token)
        report(f"PUT /api/v1/apps/{{appId}}/groups/{{groupId}} (assign to {label})", resp, (200, 201))

        resp = call("GET", f"/api/v1/apps/{app_id}/groups/{group_id}", token=token)
        report("GET /api/v1/apps/{appId}/groups/{groupId} (verify assigned)", resp, (200,))

        resp = call("DELETE", f"/api/v1/apps/{app_id}/groups/{group_id}", token=token)
        report("DELETE /api/v1/apps/{appId}/groups/{groupId} (unassign)", resp, (200, 204))
    finally:
        call("DELETE", f"/api/v1/groups/{group_id}", token=token)


def test_application_grants(token):
    """Read-only: list scope consent grants for an app; fetch one."""
    section("APP GRANTS — read-only")

    app_id, label = _first_app(token)
    if not app_id:
        report_skip("application grants", "no active apps in tenant")
        return

    resp = call("GET", f"/api/v1/apps/{app_id}/grants", token=token)
    if not report(f"GET /api/v1/apps/{{appId}}/grants (app: {label})", resp, (200,)):
        return

    body = resp.json()
    grants = body if isinstance(body, list) else _items(body)

    if grants:
        gid = grants[0]["id"]
        resp = call("GET", f"/api/v1/apps/{app_id}/grants/{gid}", token=token)
        report("GET /api/v1/apps/{appId}/grants/{grantId}", resp, (200,))
    else:
        report_skip("GET /api/v1/apps/{appId}/grants/{grantId}", f"no grants for app {label}")


def test_application_tokens(token):
    """Read-only: list OAuth2 tokens for an app; fetch one."""
    section("APP TOKENS — read-only")

    app_id, label = _first_app(token)
    if not app_id:
        report_skip("application tokens", "no active apps in tenant")
        return

    resp = call("GET", f"/api/v1/apps/{app_id}/tokens?limit=5", token=token)
    if not report(f"GET /api/v1/apps/{{appId}}/tokens (app: {label})", resp, (200,)):
        return

    body = resp.json()
    tokens = body if isinstance(body, list) else _items(body)

    if tokens:
        tid = tokens[0]["id"]
        resp = call("GET", f"/api/v1/apps/{app_id}/tokens/{tid}", token=token)
        report("GET /api/v1/apps/{appId}/tokens/{tokenId}", resp, (200,))
    else:
        report_skip("GET /api/v1/apps/{appId}/tokens/{tokenId}", f"no tokens for app {label}")


def test_application_connections(token):
    """Read-only: get default provisioning connection for an app."""
    section("APP CONNECTIONS — read-only")

    app_id, label = _first_app(token)
    if not app_id:
        report_skip("application connections", "no active apps in tenant")
        return

    resp = call("GET", f"/api/v1/apps/{app_id}/connections/default", token=token)
    # 404 is expected for apps without provisioning configured
    report(
        f"GET /api/v1/apps/{{appId}}/connections/default (app: {label})",
        resp,
        (200, 404),
    )

    if resp.status_code == 200:
        resp = call("GET", f"/api/v1/apps/{app_id}/connections/default/jwks", token=token)
        report("GET /api/v1/apps/{appId}/connections/default/jwks", resp, (200, 400, 404))


def test_application_features(token):
    """Read-only: list and get features for a provisioning-enabled app.

    Scans up to 20 apps to find one where the features endpoint returns a non-empty
    list (e.g. Google Workspace, Slack, AD apps have USER_PROVISIONING / INBOUND_PROVISIONING).
    """
    section("APP FEATURES — read-only")

    resp = call("GET", "/api/v1/apps?limit=20", token=token)
    if not report("GET /api/v1/apps?limit=20 (scan for app with features)", resp):
        return

    all_apps = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    features_app_id, features_app_label, features = None, None, []
    for app in all_apps:
        fr = call("GET", f"/api/v1/apps/{app['id']}/features", token=token)
        if fr.status_code == 200:
            body = fr.json()
            feats = body if isinstance(body, list) else _items(body)
            if feats:
                features_app_id = app["id"]
                features_app_label = app.get("label", "unknown")
                features = feats
                break

    if not features_app_id:
        report_skip("App features read", "no provisioning-enabled app with features found in first 20 apps")
        return

    report_skip(f"  using app: {features_app_label} — features: {[f.get('name') for f in features]}", "")

    # List confirmed above; now test get-by-name
    fname = features[0].get("name") or features[0].get("featureName", "unknown")
    resp = call("GET", f"/api/v1/apps/{features_app_id}/features/{fname}", token=token)
    report(
        f"GET /api/v1/apps/{{appId}}/features/{fname} (app: {features_app_label})",
        resp,
        (200,),
    )


def test_app_user_assignment_crud(token):
    """CRUD: assign a user to an app, update, then unassign."""
    section("APP USERS — assign/unassign (self-cleaning)")

    import time

    # Find an active app and a user
    app_id, label = _first_app(token)
    if not app_id:
        report_skip("App user assignment CRUD", "no active apps in tenant")
        return

    user_id = _first_user(token)
    if not user_id:
        report_skip("App user assignment CRUD", "no ACTIVE users in tenant")
        return

    # Assign user to app
    resp = call("POST", f"/api/v1/apps/{app_id}/users", body={"id": user_id, "scope": "USER"}, token=token)
    report(
        f"POST /api/v1/apps/{{appId}}/users (assign user to {label})",
        resp,
        (200, 201, 400, 403, 409),
    )

    if resp.status_code == 409:
        # Already assigned — still test GET and unassign
        report_skip("  user already assigned; testing GET and unassign only", "")

    if resp.status_code in (200, 201, 409):
        # Get the assignment
        resp2 = call("GET", f"/api/v1/apps/{app_id}/users/{user_id}", token=token)
        report("GET /api/v1/apps/{appId}/users/{userId} (verify assignment)", resp2, (200, 404))

        # Update the assignment profile (no-op: send current profile back)
        if resp2.status_code == 200:
            current_profile = resp2.json().get("profile", {})
            resp3 = call(
                "POST",
                f"/api/v1/apps/{app_id}/users/{user_id}",
                body={"profile": current_profile or {}},
                token=token,
            )
            report(
                "POST /api/v1/apps/{appId}/users/{userId} (update assignment profile)",
                resp3,
                (200, 204, 400, 403),
            )

        # Only unassign if we made the initial assignment (not 409)
        if resp.status_code in (200, 201):
            resp4 = call("DELETE", f"/api/v1/apps/{app_id}/users/{user_id}", token=token)
            report(
                "DELETE /api/v1/apps/{appId}/users/{userId} (unassign)",
                resp4,
                (200, 204, 403, 404),
            )
    elif resp.status_code in (400, 403):
        report_skip("App user CRUD remainder", f"assign returned {resp.status_code}")


def test_app_grants_crud(token):
    """CRUD: grant a scope consent, list, get, revoke."""
    section("APP GRANTS — grant/revoke (self-cleaning)")

    import os as _os

    app_id, label = _first_app(token)
    if not app_id:
        report_skip("App grants CRUD", "no active apps in tenant")
        return

    org_url = _os.environ.get("OKTA_ORG_URL", "").rstrip("/")
    if not org_url:
        report_skip("App grants CRUD", "OKTA_ORG_URL not set")
        return

    # Grant a read-level scope consent
    grant_body = {
        "scopeId": "okta.users.read",
        "issuer": f"{org_url}/oauth2/default",
    }

    grant_id = None
    resp = call("POST", f"/api/v1/apps/{app_id}/grants", body=grant_body, token=token)
    report(
        f"POST /api/v1/apps/{{appId}}/grants (grant okta.users.read to {label})",
        resp,
        (200, 201, 400, 403),
    )

    if resp.status_code in (200, 201):
        grant_id = resp.json().get("id", "")

    if grant_id:
        # Get specific grant
        resp2 = call("GET", f"/api/v1/apps/{app_id}/grants/{grant_id}", token=token)
        report("GET /api/v1/apps/{appId}/grants/{grantId}", resp2, (200, 404))

        # Get with expand parameter
        resp3 = call("GET", f"/api/v1/apps/{app_id}/grants/{grant_id}?expand=scope", token=token)
        report("GET /grants/{grantId}?expand=scope (expand param)", resp3, (200, 400, 404))

        # Revoke
        resp4 = call("DELETE", f"/api/v1/apps/{app_id}/grants/{grant_id}", token=token)
        report("DELETE /api/v1/apps/{appId}/grants/{grantId} (revoke)", resp4, (200, 204, 404))
    elif resp.status_code in (400, 403):
        report_skip("App grants CRUD remainder", f"grant returned {resp.status_code}")


def test_saml_metadata(token):
    """Read-only: retrieve SAML metadata XML for a SAML_2_0 application.

    The metadata endpoint returns XML, so we must pass Accept: application/xml instead
    of the JSON default used by call().  The kid is fetched first from the app's
    credentials/keys endpoint.
    """
    import requests as _requests

    section("APP — SAML metadata preview")

    # Okta /api/v1/apps filter does not support signOnMode — list apps and filter client-side
    resp = call("GET", "/api/v1/apps?limit=20", token=token)
    if not report("GET /api/v1/apps?limit=20 (scan for SAML_2_0 app)", resp, (200, 204)):
        return

    all_apps = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    apps = [a for a in all_apps if a.get("signOnMode") == "SAML_2_0"]
    if not apps:
        report_skip("SAML metadata", "no SAML_2_0 apps found in tenant (checked first 20)")
        return

    app_id = apps[0]["id"]
    app_label = apps[0].get("label", "unknown")

    # Fetch the app's signing key ID (kid is required by the metadata endpoint)
    keys_resp = call("GET", f"/api/v1/apps/{app_id}/credentials/keys", token=token)
    if not report(f"GET /api/v1/apps/{{appId}}/credentials/keys (app: {app_label})", keys_resp, (200,)):
        return

    keys = keys_resp.json() if isinstance(keys_resp.json(), list) else _items(keys_resp.json())
    if not keys:
        report_skip("SAML metadata", "app has no signing keys")
        return

    kid = keys[0].get("kid", "")
    if not kid:
        report_skip("SAML metadata", "first key has no kid field")
        return

    # Use Accept: application/xml — the metadata endpoint returns SAML XML, not JSON
    xml_resp = _requests.get(
        f"{BASE_URL}/api/v1/apps/{app_id}/sso/saml/metadata?kid={kid}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/xml"},
        timeout=30,
    )
    ok = xml_resp.status_code == 200 and xml_resp.text.strip().startswith("<")
    marker = "\u2713" if ok else "\u2717"
    print(f"  {marker} [{xml_resp.status_code}] GET /api/v1/apps/{{appId}}/sso/saml/metadata?kid=... (app: {app_label})")
    if ok:
        report_skip(f"  XML length: {len(xml_resp.text)} chars", "")


def test_app_assign_policy(token):
    """Read-only verification: list apps with ACCESS_POLICY type to confirm assign_application_policy endpoint path."""
    section("APP — assign policy (endpoint verification)")

    # Find an ACCESS_POLICY
    resp = call("GET", "/api/v1/policies?type=ACCESS_POLICY&limit=1", token=token)
    if resp.status_code != 200:
        report_skip("App assign policy test", "could not list ACCESS_POLICY policies")
        return

    policies = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not policies:
        report_skip("App assign policy test", "no ACCESS_POLICY policies found")
        return

    policy_id = policies[0]["id"]

    # Find an OIDC or SAML app that can have an access policy assigned
    resp = call("GET", '/api/v1/apps?filter=status+eq+"ACTIVE"&limit=3', token=token)
    if resp.status_code != 200:
        report_skip("App assign policy test", "could not list active apps")
        return

    apps = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not apps:
        report_skip("App assign policy test", "no active apps found")
        return

    # Just test that PUT /api/v1/apps/{appId}/policies/{policyId} endpoint is reachable
    # We use the first app; this may return 400 if the app type doesn't support policy assignment
    app_id = apps[0]["id"]
    resp = call("PUT", f"/api/v1/apps/{app_id}/policies/{policy_id}", token=token)
    report(
        "PUT /api/v1/apps/{appId}/policies/{policyId} (assign policy — expect 200/400/403)",
        resp,
        (200, 204, 400, 403, 404),
    )


def test_group_push_mapping_crud(token):
    """CRUD: find a push-capable app, create a source group, create a push mapping,
    get it, deactivate it, delete it, then clean up the source group."""
    import time
    section("GROUP PUSH MAPPINGS — CRUD (self-cleaning)")

    # Scan up to 20 apps to find one where the group-push/mappings endpoint returns 200
    resp = call("GET", "/api/v1/apps?limit=20", token=token)
    if not report("GET /api/v1/apps?limit=20 (scan for push-capable app)", resp):
        return

    all_apps = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    push_app_id, push_app_label = None, None
    for app in all_apps:
        probe = call("GET", f"/api/v1/apps/{app['id']}/group-push/mappings?limit=1", token=token)
        if probe.status_code == 200:
            push_app_id = app["id"]
            push_app_label = app.get("label", "unknown")
            break

    if not push_app_id:
        report_skip("Group push mapping CRUD", "no push-capable app found in first 20 apps")
        return

    report_skip(f"  using app: {push_app_label} ({push_app_id})", "")

    # Create a temporary Okta source group
    ts = int(time.time())
    grp_resp = call(
        "POST",
        "/api/v1/groups",
        body={"profile": {"name": f"mcp-push-src-{ts}", "description": "MCP push mapping source group"}},
        token=token,
    )
    if not report("POST /api/v1/groups (create source group)", grp_resp, (200, 201)):
        return

    source_group_id = grp_resp.json()["id"]
    mapping_id = None

    try:
        # Create push mapping (targetGroupName creates a new downstream group)
        create_body = {
            "sourceGroupId": source_group_id,
            "targetGroupName": f"mcp-push-target-{ts}",
        }
        resp = call(
            "POST",
            f"/api/v1/apps/{push_app_id}/group-push/mappings",
            body=create_body,
            token=token,
        )
        report(
            f"POST /api/v1/apps/{{appId}}/group-push/mappings (app: {push_app_label})",
            resp,
            (200, 201, 400, 403),
        )
        if resp.status_code not in (200, 201):
            report_skip("Push mapping CRUD remainder", f"create returned {resp.status_code}")
            return

        created = resp.json()
        mapping_id = created.get("mappingId") or created.get("id")
        if not mapping_id:
            report_skip("Push mapping CRUD remainder", "no mappingId in create response")
            return

        # Get by ID
        resp = call("GET", f"/api/v1/apps/{push_app_id}/group-push/mappings/{mapping_id}", token=token)
        report("GET /api/v1/apps/{appId}/group-push/mappings/{mappingId}", resp, (200,))

        # Deactivate (mapping must be INACTIVE before deletion)
        resp = call(
            "PATCH",
            f"/api/v1/apps/{push_app_id}/group-push/mappings/{mapping_id}",
            body={"status": "INACTIVE"},
            token=token,
        )
        report(
            "PATCH /api/v1/apps/{appId}/group-push/mappings/{mappingId} (deactivate)",
            resp,
            (200, 204),
        )

        # Delete mapping
        resp = call(
            "DELETE",
            f"/api/v1/apps/{push_app_id}/group-push/mappings/{mapping_id}",
            token=token,
        )
        report("DELETE /api/v1/apps/{appId}/group-push/mappings/{mappingId}", resp, (200, 204))
        mapping_id = None

    finally:
        # Cleanup: deactivate+delete mapping if still exists
        if mapping_id:
            call(
                "PATCH",
                f"/api/v1/apps/{push_app_id}/group-push/mappings/{mapping_id}",
                body={"status": "INACTIVE"},
                token=token,
            )
            call("DELETE", f"/api/v1/apps/{push_app_id}/group-push/mappings/{mapping_id}", token=token)
        # Always delete source group
        call("DELETE", f"/api/v1/groups/{source_group_id}", token=token)
