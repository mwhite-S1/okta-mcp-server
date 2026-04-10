#!/usr/bin/env python3
# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Live integration tests for user OAuth token tools.

Read-only: lists and fetches refresh tokens. Revocation is deliberately skipped
to avoid invalidating real user sessions in the test tenant.
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

def test_user_oauth_tokens_read(token):
    """Read-only: discover user→client relationships and list/get refresh tokens."""
    section("USER OAUTH TOKENS — read-only")

    # Get first active user
    resp = call("GET", "/api/v1/users?filter=status+eq+%22ACTIVE%22&limit=1", token=token)
    if not report("GET /api/v1/users?filter=ACTIVE&limit=1 (for OAuth token test)", resp):
        return

    users = resp.json() if isinstance(resp.json(), list) else _items(resp.json())
    if not users:
        report_skip("User OAuth token tests", "no ACTIVE users in tenant")
        return

    user_id = users[0]["id"]

    # List clients the user has granted tokens to (not a tool, but needed to find client IDs)
    resp = call("GET", f"/api/v1/users/{user_id}/clients", token=token)
    report(
        "GET /api/v1/users/{userId}/clients (discover token-granting clients)",
        resp,
        (200, 204, 404),
    )

    clients = []
    if resp.status_code == 200:
        body = resp.json()
        clients = body if isinstance(body, list) else _items(body)

    if not clients:
        report_skip("List/get refresh tokens", "user has no OAuth token-granting clients")
        return

    # Test tokens for up to 3 clients
    for client in clients[:3]:
        client_id = client.get("client_id") or client.get("clientId") or client.get("id", "")
        if not client_id:
            continue

        # list_refresh_tokens_for_user_and_client
        resp = call(
            "GET",
            f"/api/v1/users/{user_id}/clients/{client_id}/tokens?limit=5",
            token=token,
        )
        if not report(
            f"GET /api/v1/users/{{userId}}/clients/{{clientId}}/tokens (client: {client_id[:8]}...)",
            resp,
            (200, 204, 404),
        ):
            continue

        tokens_body = resp.json()
        user_tokens = tokens_body if isinstance(tokens_body, list) else _items(tokens_body)

        if user_tokens:
            tok_id = user_tokens[0].get("id", "")
            if tok_id:
                # get_refresh_token_for_user_and_client
                resp = call(
                    "GET",
                    f"/api/v1/users/{user_id}/clients/{client_id}/tokens/{tok_id}",
                    token=token,
                )
                report(
                    "GET /api/v1/users/{userId}/clients/{clientId}/tokens/{tokenId}",
                    resp,
                    (200, 404),
                )

                # Test expand=issuer parameter
                resp = call(
                    "GET",
                    f"/api/v1/users/{user_id}/clients/{client_id}/tokens/{tok_id}?expand=scope",
                    token=token,
                )
                report(
                    "GET /tokens/{tokenId}?expand=scope (expand parameter)",
                    resp,
                    (200, 400, 404),
                )
        else:
            report_skip(
                "GET /tokens/{tokenId}",
                f"no tokens for client {client_id[:8]}...",
            )

        # list with limit= parameter
        resp = call(
            "GET",
            f"/api/v1/users/{user_id}/clients/{client_id}/tokens?limit=2",
            token=token,
        )
        report(
            "GET /tokens?limit=2 (limit parameter)",
            resp,
            (200, 204, 404),
        )
