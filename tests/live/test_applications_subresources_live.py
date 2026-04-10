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
    """Read-only: list features for an app with provisioning."""
    section("APP FEATURES — read-only")

    app_id, label = _first_app(token)
    if not app_id:
        report_skip("application features", "no active apps in tenant")
        return

    resp = call("GET", f"/api/v1/apps/{app_id}/features", token=token)
    # 400 is expected for apps without provisioning enabled
    report(
        f"GET /api/v1/apps/{{appId}}/features (app: {label})",
        resp,
        (200, 400, 404),
    )

    if resp.status_code == 200:
        body = resp.json()
        features = body if isinstance(body, list) else _items(body)
        if features:
            fname = features[0].get("name") or features[0].get("featureName", "unknown")
            resp = call("GET", f"/api/v1/apps/{app_id}/features/{fname}", token=token)
            report("GET /api/v1/apps/{appId}/features/{featureName}", resp, (200,))
        else:
            report_skip("GET /api/v1/apps/{appId}/features/{featureName}", "no features returned")


def test_group_push_mappings(token):
    """Read-only: list group push mappings for an app."""
    section("GROUP PUSH MAPPINGS — read-only")

    app_id, label = _first_app(token)
    if not app_id:
        report_skip("group push mappings", "no active apps in tenant")
        return

    resp = call("GET", f"/api/v1/apps/{app_id}/group-push/mappings?limit=5", token=token)
    # 400/404 expected for apps without group push configured
    report(
        f"GET /api/v1/apps/{{appId}}/group-push/mappings (app: {label})",
        resp,
        (200, 400, 401, 403, 404),
    )

    if resp.status_code == 200:
        body = resp.json()
        mappings = body if isinstance(body, list) else _items(body)
        if mappings:
            mid = mappings[0].get("mappingId") or mappings[0].get("id", "unknown")
            resp = call("GET", f"/api/v1/apps/{app_id}/group-push/mappings/{mid}", token=token)
            report("GET /api/v1/apps/{appId}/group-push/mappings/{mappingId}", resp, (200,))
        else:
            report_skip("GET push mapping by ID", "no mappings for this app")
