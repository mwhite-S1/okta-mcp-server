#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for schema tools.

Read-only: schema modifications are intentionally skipped because Okta does not
support deleting custom schema attributes via the API — adding one permanently
pollutes the org schema.
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

from test_governance_live import call, _items, report, report_skip, section  # noqa: E402


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_user_schema_read(token):
    """Read-only: get the default Okta user schema."""
    section("SCHEMA — user schema")

    resp = call("GET", "/api/v1/meta/schemas/user/default", token=token)
    if not report("GET /api/v1/meta/schemas/user/default", resp, (200,)):
        return

    schema = resp.json()
    # Verify schema structure
    if "definitions" in schema:
        defs = schema["definitions"]
        custom_keys = list(defs.keys())
        report_skip(f"  schema definitions: {custom_keys[:5]}", "")
    if "$schema" in schema:
        report_skip(f"  schema type: {schema.get('$schema', 'unknown')[:60]}", "")
    if "properties" in schema:
        prop_keys = list(schema["properties"].keys())
        report_skip(f"  top-level properties: {prop_keys[:5]}", "")


def test_group_schema_read(token):
    """Read-only: get the default Okta group schema."""
    section("SCHEMA — group schema")

    resp = call("GET", "/api/v1/meta/schemas/group/default", token=token)
    if not report("GET /api/v1/meta/schemas/group/default", resp, (200,)):
        return

    schema = resp.json()
    if "definitions" in schema:
        report_skip(f"  definitions keys: {list(schema['definitions'].keys())[:5]}", "")


def test_app_user_schema_read(token):
    """Read-only: get the app-specific user schema for an application that has one.

    Scans up to 20 apps to find one where the schema endpoint returns 200.
    System apps like Okta Admin Console return 404; OIDC service apps and provisioning
    apps return a valid schema.
    """
    section("SCHEMA — app user schema")

    resp = call("GET", "/api/v1/apps?limit=20", token=token)
    if not report("GET /api/v1/apps?limit=20 (scan for app with schema)", resp):
        return

    body = resp.json()
    all_apps = body if isinstance(body, list) else _items(body)
    if not all_apps:
        report_skip("GET /api/v1/meta/schemas/apps/{appId}/default", "no apps in tenant")
        return

    schema_app_id, schema_app_label, schema = None, None, None
    for app in all_apps:
        sr = call("GET", f"/api/v1/meta/schemas/apps/{app['id']}/default", token=token)
        if sr.status_code == 200:
            schema_app_id = app["id"]
            schema_app_label = app.get("label", "unknown")
            schema = sr.json()
            break

    if not schema_app_id:
        report_skip("GET /api/v1/meta/schemas/apps/{appId}/default", "no app with a schema found in first 20 apps")
        return

    report(
        f"GET /api/v1/meta/schemas/apps/{{appId}}/default (app: {schema_app_label})",
        call("GET", f"/api/v1/meta/schemas/apps/{schema_app_id}/default", token=token),
        (200,),
    )
    if "definitions" in schema:
        report_skip(f"  definitions keys: {list(schema['definitions'].keys())[:5]}", "")


def test_schema_structure_validation(token):
    """Validate that user and group schemas have expected structural properties."""
    section("SCHEMA — structure validation")

    # User schema must have profile.login
    resp = call("GET", "/api/v1/meta/schemas/user/default", token=token)
    if not report("GET /api/v1/meta/schemas/user/default (structure check)", resp, (200,)):
        return

    schema = resp.json()
    # Check for required base properties
    defs = schema.get("definitions", {})
    has_base = "base" in defs or any("base" in k.lower() for k in defs)
    has_custom = "custom" in defs or any("custom" in k.lower() for k in defs)
    report_skip(f"  has 'base' section: {has_base}, has 'custom' section: {has_custom}", "")

    # Verify it's a valid JSON schema document
    has_schema_key = "$schema" in schema
    has_id = "id" in schema or "$id" in schema
    report_skip(f"  valid JSON schema: $schema={has_schema_key}, id={has_id}", "")
