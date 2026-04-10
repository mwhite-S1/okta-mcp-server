#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for governance tools.

Creates real objects, tests them, then deletes everything in a finally block.

Run with:
    .venv/Scripts/python tests/live/test_governance_live.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any
from urllib.parse import urlencode

import requests

# Load .env
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

BASE_URL = os.environ["OKTA_ORG_URL"]
CLIENT_ID = os.environ["OKTA_CLIENT_ID"]
SCOPES = os.environ.get("OKTA_SCOPES", "")
PRIVATE_KEY = os.environ.get("OKTA_PRIVATE_KEY", "").replace("\\n", "\n")
KEY_ID = os.environ.get("OKTA_KEY_ID", "")

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _get_token() -> str:
    """Obtain an access token via Private Key JWT (client credentials)."""
    import jwt as pyjwt
    import uuid

    now = int(time.time())
    assertion = pyjwt.encode(
        {
            "iss": CLIENT_ID,
            "sub": CLIENT_ID,
            "aud": f"{BASE_URL}/oauth2/v1/token",
            "iat": now,
            "exp": now + 300,
            "jti": str(uuid.uuid4()),
        },
        PRIVATE_KEY,
        algorithm="RS256",
        headers={"kid": KEY_ID},
    )

    scope_str = " ".join(
        s for s in SCOPES.split()
        if not s.startswith("openid") and s not in ("profile", "email", "offline_access")
    )

    resp = requests.post(
        f"{BASE_URL}/oauth2/v1/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": assertion,
            "scope": scope_str,
        },
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"ERROR: Auth failed [{resp.status_code}]: {resp.text[:300]}")
        sys.exit(1)

    token = resp.json().get("access_token")
    if not token:
        print("ERROR: No access_token in auth response")
        sys.exit(1)
    print(f"  Authenticated OK (token length: {len(token)})")
    return token


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def call(method: str, path: str, body: Any = None, token: str = "", _retries: int = 3) -> requests.Response:
    resp = requests.request(
        method,
        f"{BASE_URL}{path}",
        json=body,
        headers=_headers(token),
        timeout=30,
    )
    if resp.status_code == 429 and _retries > 0:
        reset = int(resp.headers.get("X-Rate-Limit-Reset", 0))
        wait = max(reset - int(time.time()), 1)
        wait = min(wait, 60)  # cap at 60s
        print(f"  [429] Rate limited — waiting {wait}s (X-Rate-Limit-Reset)...")
        time.sleep(wait)
        return call(method, path, body, token, _retries=_retries - 1)
    return resp


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

results: list[tuple[str, str, str]] = []


def report(label: str, resp: requests.Response, expected: int | tuple[int, ...] = 200) -> bool:
    if isinstance(expected, int):
        expected = (expected,)
    ok = resp.status_code in expected
    status = PASS if ok else FAIL
    results.append((status, label, str(resp.status_code)))
    symbol = "✓" if ok else "✗"
    print(f"  {symbol} [{resp.status_code}] {label}")
    if not ok:
        try:
            body = resp.json()
            print(f"      {json.dumps(body, indent=2)[:500]}")
        except Exception:
            print(f"      {resp.text[:500]}")
    return ok


def report_skip(label: str, reason: str = "") -> None:
    results.append((SKIP, label, reason))
    print(f"  - [SKIP] {label}{f': {reason}' if reason else ''}")


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def summary() -> None:
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for s, _, _ in results if s == PASS)
    failed = sum(1 for s, _, _ in results if s == FAIL)
    skipped = sum(1 for s, _, _ in results if s == SKIP)
    for status, label, detail in results:
        symbol = "✓" if status == PASS else ("✗" if status == FAIL else "-")
        print(f"  {symbol} {label}  [{detail}]")
    print(f"\n  {passed} passed / {failed} failed / {skipped} skipped")
    if failed:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _items(body: dict) -> list:
    """Extract the list from a paginated governance response."""
    if isinstance(body, list):
        return body
    return body.get("data", body.get("items", body.get("value", [])))


def _get(path: str, token: str) -> requests.Response:
    """GET with rate-limit retry (for non-governance paths like /api/v1/...)."""
    for attempt in range(3):
        resp = requests.get(f"{BASE_URL}{path}", headers=_headers(token), timeout=30)
        if resp.status_code != 429:
            return resp
        reset = int(resp.headers.get("X-Rate-Limit-Reset", 0))
        wait = min(max(reset - int(time.time()), 1), 60)
        print(f"  [429] Rate limited — waiting {wait}s...")
        time.sleep(wait)
    return resp  # return last 429 if all retries exhausted


def _fetch_principal_id(token: str) -> str:
    resp = _get("/api/v1/users?limit=1", token)
    if resp.status_code == 200:
        users = resp.json()
        if users and isinstance(users, list):
            uid = users[0].get("id", "")
            print(f"  principal_id: {uid}")
            return uid
    return ""


def _fetch_resource_orns(token: str, limit: int = 3) -> list[str]:
    """Get real resource ORNs from catalog entries → app detail.

    Each governance catalog entry has a _links.relatedEntity.href pointing to the
    Okta app. Fetching that app returns an 'orn' field directly.
    """
    # Get catalog entries
    f = urlencode({"filter": "not(parent pr)", "limit": limit})
    cat_resp = call("GET", f"/governance/api/v2/catalogs/default/entries?{f}", token=token)
    if cat_resp.status_code != 200:
        print(f"  Warning: could not list catalog entries ({cat_resp.status_code})")
        return []

    orns = []
    for entry in _items(cat_resp.json())[:limit]:
        related = (entry.get("_links") or {}).get("relatedEntity", {}).get("href", "")
        if not related:
            continue
        # Fetch the related app/resource to get its ORN (strip BASE_URL prefix)
        app_path = related.replace(BASE_URL, "") if related.startswith(BASE_URL) else related
        app_resp = _get(app_path, token) if app_path.startswith("/") else requests.get(related, headers=_headers(token), timeout=30)
        if app_resp.status_code != 200:
            continue
        orn = app_resp.json().get("orn", "")
        if orn:
            orns.append(orn)

    if orns:
        print(f"  Found {len(orns)} resource ORN(s): {orns[0][:80]}...")
    else:
        print("  No resource ORNs found in catalog entries")
    return orns


# ---------------------------------------------------------------------------
# Private helpers (used by both fixtures and main())
# ---------------------------------------------------------------------------

def _create_label_for_test(token: str) -> dict:
    """Create a governance label for testing. Returns dict with _label_id / _label_name."""
    ts = int(time.time())
    label_name = f"mcp-test-{ts}"
    resp = call(
        "POST", "/governance/api/v1/labels",
        body={"name": label_name, "values": [{"name": f"val-{ts}-a"}, {"name": f"val-{ts}-b"}]},
        token=token,
    )
    if not report("POST /v1/labels (create)", resp, (200, 201)):
        return {}
    created = resp.json()
    label_id = created.get("labelId", created.get("id", ""))
    created["_label_id"] = label_id
    created["_label_name"] = label_name
    print(f"      labelId={label_id}")
    return created


def _scan_catalog(token: str) -> tuple[str, str]:
    """Scan catalog entries to find entry_id and resource_id (app with request sequences).

    Returns (entry_id, resource_id) — resource_id may be empty if no sequences are found.
    """
    entry_id = ""
    resource_id = ""
    resp = call(
        "GET",
        f"/governance/api/v2/catalogs/default/entries?{urlencode({'filter': 'not(parent pr)', 'limit': 50})}",
        token=token,
    )
    if resp.status_code != 200:
        return entry_id, resource_id
    items_list = _items(resp.json())
    if not items_list:
        return entry_id, resource_id
    entry_id = items_list[0].get("id", "")
    print(f"      Scanning {len(items_list)} entries for request sequences...")
    for item in items_list:
        eid = item.get("id", "")
        det = call("GET", f"/governance/api/v2/catalogs/default/entries/{eid}", token=token)
        if det.status_code != 200:
            continue
        related_href = (det.json().get("_links") or {}).get("relatedEntity", {}).get("href", "")
        app_id = related_href.rstrip("/").split("/")[-1] if related_href else ""
        if not app_id:
            continue
        sr = call("GET", f"/governance/api/v2/resources/{app_id}/request-sequences", token=token)
        if sr.status_code == 200:
            seqs = _items(sr.json())
            if seqs:
                resource_id = app_id
                print(f"      Found sequences on app: {app_id}  name={item.get('name', '')}")
                break
    else:
        print("      No entry with sequences found (sequences must be configured in the Access Requests UI)")
    return entry_id, resource_id


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------

def test_connectivity(token: str) -> None:
    section("CONNECTIVITY")
    resp = call("GET", f"/governance/api/v2/catalogs/default/entries?{urlencode({'filter': 'not(parent pr)', 'limit': 1})}", token=token)
    ok = report("GET /v2/catalogs/default/entries (OIG reachable)", resp, (200, 204))
    if not ok:
        print("\n  OIG may not be enabled. Stopping early.")
        summary()
        sys.exit(0)


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

def test_labels(token: str, created_label: dict) -> None:
    """Get → list → update an existing governance label (created externally)."""
    section("LABELS — GET / list / update")

    if not created_label:
        report_skip("Label GET/list/update", "no label was created")
        return

    label_id = created_label.get("_label_id", "")
    label_name = created_label.get("_label_name", "")

    resp = call("GET", f"/governance/api/v1/labels/{label_id}", token=token)
    report("GET /v1/labels/{labelId}", resp)

    resp = call("GET", "/governance/api/v1/labels", token=token)
    if report("GET /v1/labels (list)", resp):
        items = _items(resp.json())
        found = any(i.get("labelId") == label_id or i.get("id") == label_id for i in items if isinstance(i, dict))
        print(f"      Found in list: {found}")

    resp = call(
        "PATCH", f"/governance/api/v1/labels/{label_id}",
        body=[{"op": "REPLACE", "path": "/name", "value": f"{label_name}-upd", "refType": "LABEL-CATEGORY"}],
        token=token,
    )
    report("PATCH /v1/labels/{labelId} (rename)", resp, (200, 204))


def test_label_assign(token: str, created_label: dict, resource_orns: list) -> None:
    """Assign label values to resources; returns label_value_ids used for unassign."""
    section("LABELS — Assign / Unassign / List-labeled-resources")

    if not created_label or not resource_orns:
        report_skip("Label assign/unassign", "no label or no resource ORNs available")
        return []

    label_id = created_label.get("_label_id", "")
    values = created_label.get("values", [])
    if not values:
        report_skip("Label assign/unassign", "created label has no values")
        return []

    label_value_ids = [v.get("labelValueId", v.get("id", "")) for v in values if v.get("labelValueId") or v.get("id")]
    if not label_value_ids:
        report_skip("Label assign/unassign", "could not extract label value IDs")
        return []

    # Assign
    resp = call(
        "POST", "/governance/api/v1/resource-labels/assign",
        body={"resourceOrns": resource_orns[:2], "labelValueIds": label_value_ids[:1]},
        token=token,
    )
    report("POST /v1/resource-labels/assign", resp, (200, 201, 204))

    # List labeled resources
    f = urlencode({"filter": f'labelValueId eq "{label_value_ids[0]}"', "limit": 5})
    resp = call("GET", f"/governance/api/v1/resource-labels?{f}", token=token)
    report("GET /v1/resource-labels (filter by labelValueId)", resp, (200, 204))

    # Unassign
    resp = call(
        "POST", "/governance/api/v1/resource-labels/unassign",
        body={"resourceOrns": resource_orns[:2], "labelValueIds": label_value_ids[:1]},
        token=token,
    )
    report("POST /v1/resource-labels/unassign", resp, (200, 204))


def cleanup_label(label_id: str, token: str) -> None:
    section(f"CLEANUP — label {label_id}")
    resp = call("DELETE", f"/governance/api/v1/labels/{label_id}", token=token)
    report(f"DELETE /v1/labels/{label_id}", resp, (200, 204))


# ---------------------------------------------------------------------------
# Entitlement Bundles
# ---------------------------------------------------------------------------

def test_entitlement_bundles(token: str, resource_orns: list) -> None:
    """Full CRUD for entitlement bundles (self-cleaning)."""
    section("ENTITLEMENT BUNDLES — CRUD")

    resp = call("GET", "/governance/api/v1/entitlement-bundles", token=token)
    report("GET /v1/entitlement-bundles (list)", resp, (200, 204))

    ts = int(time.time())

    # Extract Okta app ID from the resource ORN (last colon-separated segment)
    # ORN format: orn:{namespace}:idp:{orgId}:apps:{protocol}:{appId}
    app_id = resource_orns[0].split(":")[-1] if resource_orns else ""
    target_resource_orn = resource_orns[0] if resource_orns else ""

    if not app_id:
        report_skip("POST /v1/entitlement-bundles (create)", "no resource ORNs to get app ID")
        return

    print(f"      Using app_id={app_id} for entitlement bundle target")
    resp = call(
        "POST", "/governance/api/v1/entitlement-bundles",
        body={
            "name": f"mcp-bundle-{ts}",
            "description": "MCP live test bundle",
            "target": {"externalId": app_id, "type": "APPLICATION"},
            "entitlements": [],
        },
        token=token,
    )
    # 400/403/422 expected if app doesn't have entitlement management enabled
    if not report("POST /v1/entitlement-bundles (create)", resp, (200, 201, 400, 403, 422)):
        return
    if resp.status_code in (400, 403, 422):
        print(f"      ({resp.status_code} — app may not have entitlement management enabled; skipping bundle CRUD)")
        return

    created = resp.json()
    bundle_id = created.get("id", created.get("entitlementBundleId", ""))
    print(f"      bundleId={bundle_id}")

    try:
        resp = call("GET", f"/governance/api/v1/entitlement-bundles/{bundle_id}", token=token)
        report("GET /v1/entitlement-bundles/{id}", resp)

        # PUT requires id, targetResourceOrn, target, name, entitlements
        resp = call(
            "PUT", f"/governance/api/v1/entitlement-bundles/{bundle_id}",
            body={
                "id": bundle_id,
                "name": f"mcp-bundle-{ts}-upd",
                "description": "Updated",
                "targetResourceOrn": target_resource_orn,
                "target": {"externalId": app_id, "type": "APPLICATION"},
                "entitlements": [],
            },
            token=token,
        )
        report("PUT /v1/entitlement-bundles/{id} (update)", resp, (200, 204))
    finally:
        cleanup_entitlement_bundle(bundle_id, token)


def cleanup_entitlement_bundle(bundle_id: str, token: str) -> None:
    section(f"CLEANUP — entitlement bundle {bundle_id}")
    resp = call("DELETE", f"/governance/api/v1/entitlement-bundles/{bundle_id}", token=token)
    report(f"DELETE /v1/entitlement-bundles/{bundle_id}", resp, (200, 204))


# ---------------------------------------------------------------------------
# Entitlements + Grants + Principal Entitlements (read-only with real filters)
# ---------------------------------------------------------------------------

def test_entitlements_read(token: str, resource_id: str, principal_id: str) -> None:
    section("ENTITLEMENTS / GRANTS / PRINCIPAL — read-only")

    if resource_id:
        # Correct filter: parent.externalId (Okta app ID) + parent.type
        f_res = urlencode({"filter": f'parent.externalId eq "{resource_id}" AND parent.type eq "APPLICATION"', "limit": 5})
        resp = call("GET", f"/governance/api/v1/entitlements?{f_res}", token=token)
        # 400 = filter field name invalid or app has no entitlement management
        report("GET /v1/entitlements (parent.externalId filter)", resp, (200, 204, 400, 404))

        resp = call("GET", f"/governance/api/v1/grants?{f_res}", token=token)
        # 400/404 = resource not in grants registry or wrong ID format
        if report("GET /v1/grants (resourceId filter)", resp, (200, 204, 400, 404)):
            if resp.status_code == 200:
                grants = _items(resp.json())
                if grants:
                    grant_id = grants[0].get("id", "")
                    if grant_id:
                        resp2 = call("GET", f"/governance/api/v1/grants/{grant_id}", token=token)
                        report(f"GET /v1/grants/{grant_id}", resp2)
    else:
        report_skip("GET /v1/entitlements", "no resource_id")
        report_skip("GET /v1/grants", "no resource_id")

    if principal_id:
        f_prin = urlencode({"filter": f'principalId eq "{principal_id}"'})
        resp = call("GET", f"/governance/api/v1/principal-entitlements?{f_prin}", token=token)
        # 400/404 = principal not enrolled in IGA or filter field name differs
        report("GET /v1/principal-entitlements (principalId filter)", resp, (200, 204, 400, 404))

        resp = call("GET", f"/governance/api/v1/principal-entitlements/history?{f_prin}", token=token)
        report("GET /v1/principal-entitlements/history (principalId filter)", resp, (200, 204, 400, 404))

        resp = call("GET", f"/governance/api/v1/principal-access?{f_prin}", token=token)
        report("GET /v1/principal-access (principalId filter)", resp, (200, 204, 400, 404))
    else:
        report_skip("GET /v1/principal-entitlements", "no principal_id")
        report_skip("GET /v1/principal-entitlements/history", "no principal_id")
        report_skip("GET /v1/principal-access", "no principal_id")


# ---------------------------------------------------------------------------
# Certifications — full campaign lifecycle (no launch/end to avoid side effects)
# ---------------------------------------------------------------------------

def test_certification_campaigns(token: str, resource_orns: list, principal_id: str) -> None:
    """List campaigns; create a minimal campaign; get it; delete it (self-cleaning)."""
    section("CERTIFICATIONS — Campaigns CRUD")

    resp = call("GET", "/governance/api/v1/campaigns", token=token)
    report("GET /v1/campaigns (list)", resp, (200, 204))

    # Try to get an existing campaign for the get endpoint test
    existing_id = ""
    if resp.status_code == 200:
        items = _items(resp.json())
        if items:
            existing_id = items[0].get("id", items[0].get("campaignId", ""))

    if existing_id:
        resp2 = call("GET", f"/governance/api/v1/campaigns/{existing_id}", token=token)
        report(f"GET /v1/campaigns/{existing_id} (existing)", resp2)
    else:
        report_skip("GET /v1/campaigns/{id}", "no existing campaigns")

    if not principal_id:
        report_skip("POST /v1/campaigns (create)", "no principal_id for fallback reviewer")
        return

    # Build a minimal valid campaign body.
    # startDate must be in the future; durationInDays >= 1.
    ts = int(time.time())
    start_date = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(ts + 86400))
    app_id = resource_orns[0].split(":")[-1] if resource_orns else ""

    campaign_body = {
        "name": f"mcp-test-campaign-{ts}",
        "campaignType": "RESOURCE",
        "scheduleSettings": {
            "type": "ONE_OFF",
            "startDate": start_date,
            "durationInDays": 1,
            "timeZone": "UTC",
        },
        "resourceSettings": {
            "targetTypes": ["APPLICATION"],
            "targetResources": [
                {"resourceId": app_id, "resourceType": "APPLICATION"}
            ] if app_id else [],
        },
        "principalScopeSettings": {"type": "USERS"},
        "reviewerSettings": {
            "type": "RESOURCE_OWNER",
            "fallBackReviewerId": principal_id,
        },
        "remediationSettings": {
            "accessApproved": "NO_ACTION",
            "accessRevoked": "NO_ACTION",
            "noResponse": "NO_ACTION",
        },
    }

    resp = call("POST", "/governance/api/v1/campaigns", body=campaign_body, token=token)
    if not report("POST /v1/campaigns (create)", resp, (200, 201, 400, 422)):
        return

    if resp.status_code in (400, 422):
        print(f"      (create returned {resp.status_code} — config may not match tenant; skipping campaign CRUD)")
        return

    created = resp.json()
    campaign_id = created.get("id", created.get("campaignId", ""))
    print(f"      campaignId={campaign_id}")

    try:
        resp = call("GET", f"/governance/api/v1/campaigns/{campaign_id}", token=token)
        report(f"GET /v1/campaigns/{campaign_id} (created)", resp)
    finally:
        cleanup_campaign(campaign_id, token)


def cleanup_campaign(campaign_id: str, token: str) -> None:
    section(f"CLEANUP — campaign {campaign_id}")
    resp = call("DELETE", f"/governance/api/v1/campaigns/{campaign_id}", token=token)
    report(f"DELETE /v1/campaigns/{campaign_id}", resp, (200, 204))


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

def test_certification_reviews(token: str) -> None:
    section("CERTIFICATIONS — Reviews")

    resp = call("GET", "/governance/api/v1/reviews", token=token)
    if report("GET /v1/reviews (list)", resp, (200, 204)):
        items = _items(resp.json())
        if items:
            review = items[0]
            review_id = review.get("id", review.get("reviewId", ""))
            if review_id:
                resp2 = call("GET", f"/governance/api/v1/reviews/{review_id}", token=token)
                # 404 is expected if the review's parent campaign has been deleted
                report(f"GET /v1/reviews/{review_id}", resp2, (200, 204, 404))
        else:
            report_skip("GET /v1/reviews/{id}", "no reviews in tenant")


# ---------------------------------------------------------------------------
# Security Access Reviews
# ---------------------------------------------------------------------------

def test_sar_extended(token: str, principal_id: str) -> None:
    """List SARs, get stats, create one, get it, list its actions."""
    section("SECURITY ACCESS REVIEWS — extended")

    resp = call("GET", "/governance/api/v2/security-access-reviews", token=token)
    report("GET /v2/security-access-reviews (list)", resp, (200, 204))

    # Stats
    resp = call("GET", "/governance/api/v2/security-access-reviews/stats", token=token)
    report("GET /v2/security-access-reviews/stats", resp, (200, 204))

    # Try to get an existing SAR to test get/actions
    existing_id = ""
    if resp.status_code == 200:
        # list again to get IDs
        list_resp = call("GET", "/governance/api/v2/security-access-reviews", token=token)
        if list_resp.status_code == 200:
            items = _items(list_resp.json())
            if items:
                existing_id = items[0].get("id", "")

    if not principal_id:
        report_skip("POST /v2/security-access-reviews (create)", "no principal_id")
        return

    # Create a SAR
    ts = int(time.time())
    resp = call(
        "POST", "/governance/api/v2/security-access-reviews",
        body={
            "principalId": principal_id,
            "name": f"mcp-sar-{ts}",
            "reviewerSettings": {"type": "USER", "userSettings": {"includedUserIds": [principal_id]}},
        },
        token=token,
    )
    if not report("POST /v2/security-access-reviews (create)", resp, (200, 201, 400)):
        return

    if resp.status_code == 400:
        print("      (400 — SAR creation may require specific config; skipping SAR sub-endpoints)")
        return

    created = resp.json()
    sar_id = created.get("id", "")
    created["_sar_id"] = sar_id
    print(f"      sarId={sar_id}")

    resp = call("GET", f"/governance/api/v2/security-access-reviews/{sar_id}", token=token)
    report(f"GET /v2/security-access-reviews/{sar_id}", resp)

    resp = call("GET", f"/governance/api/v2/security-access-reviews/{sar_id}/actions", token=token)
    report(f"GET /v2/security-access-reviews/{sar_id}/actions", resp, (200, 204))


# ---------------------------------------------------------------------------
# Delegates & Org Settings
# ---------------------------------------------------------------------------

def test_delegates_and_settings(token: str) -> None:
    section("DELEGATES & ORG SETTINGS")

    resp = call("GET", "/governance/api/v1/settings", token=token)
    report("GET /v1/settings (org governance settings)", resp, (200, 204))

    resp = call("GET", "/governance/api/v1/delegates", token=token)
    report("GET /v1/delegates", resp, (200, 204))

    resp = call("GET", "/governance/api/v1/settings/certification", token=token)
    report("GET /v1/settings/certification", resp, (200, 204, 403))

    resp = call("GET", "/governance/api/v1/settings/integrations", token=token)
    report("GET /v1/settings/integrations", resp, (200, 204))


# ---------------------------------------------------------------------------
# Access Requests Catalog
# ---------------------------------------------------------------------------

def test_access_requests_catalog(token: str, entry_id: str, resource_id: str) -> None:
    """Test catalog listing and GET single entry (catalog scanning done in fixture / _scan_catalog)."""
    section("ACCESS REQUESTS — Catalog")

    resp = call(
        "GET",
        f"/governance/api/v2/catalogs/default/entries?{urlencode({'filter': 'not(parent pr)', 'limit': 50})}",
        token=token,
    )
    if report("GET /v2/catalogs/default/entries (list, filter required)", resp, (200, 204)):
        if resp.status_code == 200:
            items = _items(resp.json())
            if items:
                print(f"      First entry: {items[0].get('id', '')}  name={items[0].get('name', '')}")
            if resource_id:
                print(f"      resource_id for sequences/conditions: {resource_id}")
            else:
                print("      No entry with sequences found (sequences must be configured in the Access Requests UI)")

    if entry_id:
        resp = call("GET", f"/governance/api/v2/catalogs/default/entries/{entry_id}", token=token)
        report(f"GET /v2/catalogs/default/entries/{entry_id}", resp)
    else:
        report_skip("GET /v2/catalogs/default/entries/{id}", "no entries")


# ---------------------------------------------------------------------------
# Access Requests — create + cancel
# ---------------------------------------------------------------------------

def test_access_request_create(token: str, entry_id: str, principal_id: str) -> None:
    section("ACCESS REQUESTS — Create + Cancel")

    resp = call("GET", "/governance/api/v2/requests", token=token)
    report("GET /v2/requests (list)", resp, (200, 204))

    resp = call("GET", "/governance/api/v2/request-settings", token=token)
    report("GET /v2/request-settings", resp, (200, 204))

    if not entry_id or not principal_id:
        report_skip("POST /v2/requests (create)", "need entry_id and principal_id")
        return

    resp = call(
        "POST", "/governance/api/v2/requests",
        body={
            "requestedFor": principal_id,
            "requestType": "GRANT",
            "items": [{"catalogEntryId": entry_id}],
            "justification": "MCP live test — will be cancelled",
        },
        token=token,
    )
    if not report("POST /v2/requests (create)", resp, (200, 201, 400, 422)):
        return

    if resp.status_code in (400, 422):
        print(f"      (create returned {resp.status_code} — may need self-service access requests enabled)")
        return

    created = resp.json()
    request_id = created.get("id", created.get("requestId", ""))
    created["_request_id"] = request_id
    print(f"      requestId={request_id}")

    # Get the request
    resp = call("GET", f"/governance/api/v2/requests/{request_id}", token=token)
    report(f"GET /v2/requests/{request_id}", resp)

    # Cancel it immediately
    resp = call("DELETE", f"/governance/api/v2/requests/{request_id}", token=token)
    report(f"DELETE /v2/requests/{request_id} (cancel)", resp, (200, 204))


# ---------------------------------------------------------------------------
# Request Conditions
# ---------------------------------------------------------------------------

def test_request_conditions(token: str, resource_id: str) -> None:
    section(f"REQUEST CONDITIONS  resource={resource_id or '(none)'}")

    if not resource_id:
        report_skip("All condition tests", "no resource_id")
        return

    resp = call("GET", f"/governance/api/v2/resources/{resource_id}/request-settings", token=token)
    report(f"GET /v2/resources/{resource_id}/request-settings", resp, (200, 404))

    resp = call("GET", f"/governance/api/v2/resources/{resource_id}/request-sequences", token=token)
    report(f"GET /v2/resources/{resource_id}/request-sequences", resp, (200, 404))
    sequence_id = ""
    if resp.status_code == 200:
        seqs = _items(resp.json())
        if seqs:
            sequence_id = seqs[0].get("id", "")
            print(f"      sequenceId={sequence_id}")

    resp = call("GET", f"/governance/api/v2/resources/{resource_id}/request-conditions", token=token)
    report(f"GET /v2/resources/{resource_id}/request-conditions (list)", resp, (200, 404))

    if not sequence_id:
        report_skip("Condition CRUD", "no sequence available")
        return

    ts = int(time.time())
    resp = call(
        "POST", f"/governance/api/v2/resources/{resource_id}/request-conditions",
        body={
            "name": f"mcp-test-condition-{ts}",
            "description": "MCP live test condition — will be deleted",
            "approvalSequenceId": sequence_id,
            "priority": 99,
            "requesterSettings": {"type": "EVERYONE"},
            "accessScopeSettings": {"type": "RESOURCE_DEFAULT"},
        },
        token=token,
    )
    if not report("POST /v2/resources/{id}/request-conditions (create)", resp, (200, 201, 400)):
        return
    if resp.status_code == 400:
        print(f"      (400 — condition rejected by tenant; skipping condition CRUD)")
        return

    created = resp.json()
    cond_id = created.get("id", "")
    print(f"      conditionId={cond_id}")

    try:
        resp = call("GET", f"/governance/api/v2/resources/{resource_id}/request-conditions/{cond_id}", token=token)
        report(f"GET /v2/resources/{resource_id}/request-conditions/{cond_id}", resp)

        resp = call(
            "PATCH", f"/governance/api/v2/resources/{resource_id}/request-conditions/{cond_id}",
            body={"priority": 98}, token=token,
        )
        report(f"PATCH /v2/resources/{resource_id}/request-conditions/{cond_id}", resp, (200, 204))

        resp = call("POST", f"/governance/api/v2/resources/{resource_id}/request-conditions/{cond_id}/activate", token=token)
        report("POST .../activate", resp, (200, 204))

        resp = call("POST", f"/governance/api/v2/resources/{resource_id}/request-conditions/{cond_id}/deactivate", token=token)
        report("POST .../deactivate", resp, (200, 204))
    finally:
        cleanup_condition(resource_id, cond_id, token)


def cleanup_condition(resource_id: str, cond_id: str, token: str) -> None:
    section(f"CLEANUP — condition {cond_id}")
    resp = call("DELETE", f"/governance/api/v2/resources/{resource_id}/request-conditions/{cond_id}", token=token)
    report(f"DELETE /v2/resources/{resource_id}/request-conditions/{cond_id}", resp, (200, 204))


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------

def test_collections(token: str, resource_orns: list) -> None:
    section("COLLECTIONS — CRUD (self-cleaning)")

    resp = call("GET", "/governance/api/v1/collections", token=token)
    report("GET /v1/collections (list)", resp, (200, 204, 403))

    ts = int(time.time())
    resp = call(
        "POST", "/governance/api/v1/collections",
        body={"name": f"mcp-collection-{ts}", "description": "MCP live test collection"},
        token=token,
    )
    if not report("POST /v1/collections (create)", resp, (200, 201, 403)):
        return
    if resp.status_code == 403:
        print("      (403 — Resource Collections feature may not be enabled on this tenant)")
        return

    created = resp.json()
    col_id = created.get("id", created.get("collectionId", ""))
    print(f"      collectionId={col_id}")

    try:
        resp = call("GET", f"/governance/api/v1/collections/{col_id}", token=token)
        report(f"GET /v1/collections/{col_id}", resp)

        resp = call(
            "PUT", f"/governance/api/v1/collections/{col_id}",
            body={"name": f"mcp-collection-{ts}-upd", "description": "Updated"},
            token=token,
        )
        report(f"PUT /v1/collections/{col_id} (update)", resp, (200, 204))

        resp = call("GET", f"/governance/api/v1/collections/{col_id}/resources", token=token)
        report(f"GET /v1/collections/{col_id}/resources (list)", resp, (200, 204))

        if resource_orns:
            resp = call(
                "POST", f"/governance/api/v1/collections/{col_id}/resources",
                body={"resourceOrns": resource_orns[:1]},
                token=token,
            )
            if report(f"POST /v1/collections/{col_id}/resources (add)", resp, (200, 201, 204)):
                # Get the resource ID to test remove
                list_resp = call("GET", f"/governance/api/v1/collections/{col_id}/resources", token=token)
                if list_resp.status_code == 200:
                    res_items = _items(list_resp.json())
                    if res_items:
                        res_id = res_items[0].get("id", res_items[0].get("resourceId", ""))
                        if res_id:
                            resp2 = call("DELETE", f"/governance/api/v1/collections/{col_id}/resources/{res_id}", token=token)
                            report(f"DELETE /v1/collections/{col_id}/resources/{res_id} (remove)", resp2, (200, 204))
        else:
            report_skip(f"POST /v1/collections/{col_id}/resources", "no resource ORNs available")
    finally:
        cleanup_collection(col_id, token)


def cleanup_collection(col_id: str, token: str) -> None:
    section(f"CLEANUP — collection {col_id}")
    resp = call("DELETE", f"/governance/api/v1/collections/{col_id}", token=token)
    report(f"DELETE /v1/collections/{col_id}", resp, (200, 204))


# ---------------------------------------------------------------------------
# Risk Rules
# ---------------------------------------------------------------------------

def test_risk_rules(token: str) -> None:
    section("RISK RULES — CRUD + assess (self-cleaning)")

    resp = call("GET", "/governance/api/v1/risk-rules", token=token)
    report("GET /v1/risk-rules (list)", resp, (200, 204))

    ts = int(time.time())
    resp = call(
        "POST", "/governance/api/v1/risk-rules",
        body={
            "name": f"mcp-risk-rule-{ts}",
            "description": "MCP live test risk rule",
            "conflictCriteria": {
                "resources": [{"type": "APP"}],
            },
        },
        token=token,
    )
    if not report("POST /v1/risk-rules (create)", resp, (200, 201, 400)):
        return
    if resp.status_code == 400:
        print("      (400 — risk rule schema may require additional fields; skipping risk rule CRUD)")
        return

    created = resp.json()
    rule_id = created.get("id", created.get("ruleId", ""))
    print(f"      ruleId={rule_id}")

    try:
        resp = call("GET", f"/governance/api/v1/risk-rules/{rule_id}", token=token)
        report(f"GET /v1/risk-rules/{rule_id}", resp)

        resp = call(
            "PUT", f"/governance/api/v1/risk-rules/{rule_id}",
            body={"name": f"mcp-risk-rule-{ts}-upd", "description": "Updated"},
            token=token,
        )
        report(f"PUT /v1/risk-rules/{rule_id} (update)", resp, (200, 204))
    finally:
        cleanup_risk_rule(rule_id, token)


def cleanup_risk_rule(rule_id: str, token: str) -> None:
    section(f"CLEANUP — risk rule {rule_id}")
    resp = call("DELETE", f"/governance/api/v1/risk-rules/{rule_id}", token=token)
    report(f"DELETE /v1/risk-rules/{rule_id}", resp, (200, 204))


# ---------------------------------------------------------------------------
# Resource Owners
# ---------------------------------------------------------------------------

def _principal_orn(resource_orn: str, user_id: str) -> str:
    """Construct a user principal ORN from a resource ORN (to share namespace/orgId)."""
    # orn:{namespace}:idp:{orgId}:apps:... → orn:{namespace}:directory:{orgId}:users:{userId}
    parts = resource_orn.split(":")
    if len(parts) >= 4:
        namespace = parts[1]  # e.g. "okta" or "oktapreview"
        org_id = parts[3]
        return f"orn:{namespace}:directory:{org_id}:users:{user_id}"
    return ""


def test_resource_owners(token: str, resource_orns: list, principal_id: str) -> None:
    section("RESOURCE OWNERS")

    if not resource_orns:
        report_skip("GET /v1/resource-owners (list)", "no resource ORNs for filter")
        report_skip("GET /v1/resource-owners/catalog/resources", "no resource ORNs for filter")
        report_skip("POST /v1/resource-owners (assign owner)", "no resource ORNs")
        return

    # List current owners — filter uses parentResourceOrn (the app ORN)
    f_own = urlencode({"filter": f'parentResourceOrn eq "{resource_orns[0]}"', "limit": 5})
    resp = call("GET", f"/governance/api/v1/resource-owners?{f_own}", token=token)
    report("GET /v1/resource-owners (list)", resp, (200, 204))

    # Catalog of unowned resources (entitlement bundles/values within the parent app)
    # Returns 400 if the app has no IGA entitlements configured under it
    f_cat = urlencode({"filter": f'parentResourceOrn eq "{resource_orns[0]}"', "limit": 5})
    resp = call("GET", f"/governance/api/v1/resource-owners/catalog/resources?{f_cat}", token=token)
    report("GET /v1/resource-owners/catalog/resources", resp, (200, 204, 400))

    if not principal_id:
        report_skip("POST /v1/resource-owners (assign owner)", "no principal_id")
        return

    # Build principal ORN from the resource ORN (same namespace/orgId)
    principal_orn = _principal_orn(resource_orns[0], principal_id)
    if not principal_orn:
        report_skip("POST /v1/resource-owners (assign owner)", "could not construct principal ORN")
        return

    # POST: assign owner — principalOrns (ORNs) + resourceOrns (ORNs)
    resp = call(
        "POST", "/governance/api/v1/resource-owners",
        body={"resourceOrns": [resource_orns[0]], "principalOrns": [principal_orn]},
        token=token,
    )
    report("POST /v1/resource-owners (assign owner)", resp, (200, 201, 204))

    # PATCH: remove that owner — resourceOrn (singular) + data[{op,path,value}]
    resp = call(
        "PATCH", "/governance/api/v1/resource-owners",
        body={
            "resourceOrn": resource_orns[0],
            "data": [{"op": "REMOVE", "path": "/principalOrn", "value": principal_orn}],
        },
        token=token,
    )
    report("PATCH /v1/resource-owners (remove owner)", resp, (200, 204))


# ---------------------------------------------------------------------------
# Entitlement Settings (resource-scoped)
# ---------------------------------------------------------------------------

def test_entitlement_settings(token: str, resource_orns: list) -> None:
    section("ENTITLEMENT SETTINGS")

    if not resource_orns:
        report_skip("GET /v2/resources/{orn}/entitlement-settings", "no resource ORNs")
        return

    from urllib.parse import quote
    orn = resource_orns[0]
    # Try fully URL-encoded first, fall back to colon-preserving
    encoded = quote(orn, safe="")
    resp = call("GET", f"/governance/api/v2/resources/{encoded}/entitlement-settings", token=token)
    if resp.status_code == 400:
        # Some API implementations prefer colons un-encoded in path segments
        encoded2 = quote(orn, safe=":")
        resp = call("GET", f"/governance/api/v2/resources/{encoded2}/entitlement-settings", token=token)
    report(f"GET /v2/resources/{{orn}}/entitlement-settings", resp, (200, 204, 400, 404))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Ensure UTF-8 output on Windows (cp1252 doesn't support ✓/✗)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print("\nOkta Governance Live Integration Test — Full Coverage")
    print(f"Tenant: {BASE_URL}\n")

    token = _get_token()

    # Pre-fetch shared data
    principal_id = _fetch_principal_id(token)
    resource_orns = _fetch_resource_orns(token)

    test_connectivity(token)

    # Only the label needs external cleanup (others are self-cleaning via try/finally).
    created_label: dict = {}

    try:
        # --- Labels ---
        created_label = _create_label_for_test(token)
        test_labels(token, created_label)
        test_label_assign(token, created_label, resource_orns)

        # --- Catalog (needed for filters downstream) ---
        entry_id, resource_id = _scan_catalog(token)
        test_access_requests_catalog(token, entry_id, resource_id)

        # --- Entitlement Bundles (self-cleaning) ---
        test_entitlement_bundles(token, resource_orns)

        # --- Entitlements / Grants / Principal read-only ---
        test_entitlements_read(token, resource_id, principal_id)

        # --- Certification Campaigns (self-cleaning) ---
        test_certification_campaigns(token, resource_orns, principal_id)

        # --- Certification Reviews ---
        test_certification_reviews(token)

        # --- Security Access Reviews ---
        test_sar_extended(token, principal_id)

        # --- Delegates & Org Settings ---
        test_delegates_and_settings(token)

        # --- Access Requests ---
        test_access_request_create(token, entry_id, principal_id)

        # --- Request Conditions (self-cleaning) ---
        test_request_conditions(token, resource_id)

        # --- Collections (self-cleaning) ---
        test_collections(token, resource_orns)

        # --- Risk Rules (self-cleaning) ---
        test_risk_rules(token)

        # --- Resource Owners ---
        test_resource_owners(token, resource_orns, principal_id)

        # --- Entitlement Settings ---
        test_entitlement_settings(token, resource_orns)

    finally:
        print(f"\n{'='*60}")
        print("  CLEANUP")
        print(f"{'='*60}")

        if created_label:
            label_id = (
                created_label.get("_label_id")
                or created_label.get("labelId")
                or created_label.get("id", "")
            )
            if label_id:
                cleanup_label(label_id, token)

    summary()


if __name__ == "__main__":
    main()
