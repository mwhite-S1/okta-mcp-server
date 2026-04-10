# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Fixtures for tool integration tests.

These tests call the real MCP tool functions with a live Okta client — no SDK
mocking.  They catch the class of bugs that unit tests miss: SDK type
mismatches, response-deserialization failures, wrong method names, etc.

Requirements:
  - .env with OKTA_ORG_URL, OKTA_CLIENT_ID, OKTA_PRIVATE_KEY, OKTA_KEY_ID
    (same credentials used by tests/live/).
  - Run with: pytest tests/tools/ -v -s
"""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Load .env before importing anything that reads os.environ
# ---------------------------------------------------------------------------
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# ---------------------------------------------------------------------------
# Replace the system keyring with an in-memory backend BEFORE any imports
# that touch keyring.  The Windows credential store fails in sandbox/CI
# environments with (1783, 'CredWrite', 'The stub received bad data').
# ---------------------------------------------------------------------------
import keyring  # noqa: E402
from keyring.backend import KeyringBackend  # noqa: E402


class _MemoryKeyring(KeyringBackend):
    """Thread-safe in-memory keyring; avoids Windows credential store."""
    priority = 100  # override any system backend

    def __init__(self):
        self._store: dict = {}

    def get_password(self, service, username):
        return self._store.get((service, username))

    def set_password(self, service, username, password):
        self._store[(service, username)] = password

    def delete_password(self, service, username):
        self._store.pop((service, username), None)


keyring.set_keyring(_MemoryKeyring())

from okta_mcp_server.utils.auth.auth_manager import OktaAuthManager  # noqa: E402


# ---------------------------------------------------------------------------
# Context construction
# ---------------------------------------------------------------------------

@dataclass
class _LifespanContext:
    okta_auth_manager: Any


def _build_ctx(manager: OktaAuthManager) -> MagicMock:
    """Build a minimal MCP Context backed by a real OktaAuthManager.

    Elicitation is reported as unsupported so that tools with confirmation
    prompts fall through to their auto-confirm fallback path.
    """
    capabilities = MagicMock()
    capabilities.elicitation = None  # not supported → auto-confirm fallback

    client_params = MagicMock()
    client_params.capabilities = capabilities

    session = MagicMock()
    session.client_params = client_params

    request_context = MagicMock()
    request_context.session = session
    request_context.lifespan_context = _LifespanContext(okta_auth_manager=manager)

    ctx = MagicMock()
    ctx.request_context = request_context
    ctx.elicit = AsyncMock(return_value=None)

    return ctx


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def auth_manager():
    """Authenticate once for the entire test session."""
    manager = OktaAuthManager()
    asyncio.run(manager.authenticate())
    return manager


@pytest.fixture(scope="session")
def real_ctx(auth_manager):
    """MCP context wired to a real authenticated Okta client."""
    return _build_ctx(auth_manager)


@pytest.fixture(scope="session")
def first_access_policy_id(real_ctx):
    """ID of the first ACCESS_POLICY in the org (used by rule/mapping tests)."""
    from okta_mcp_server.tools.policies.policies import list_policies
    result = asyncio.run(list_policies(ctx=real_ctx, type="ACCESS_POLICY"))
    policies = result.get("items", [])
    if not policies:
        pytest.skip("No ACCESS_POLICY policies found in org")
    return policies[0]["id"]


@pytest.fixture(scope="session")
def first_app_id(real_ctx):
    """ID of the first application in the org."""
    from okta_mcp_server.tools.applications.applications import list_applications
    result = asyncio.run(list_applications(ctx=real_ctx))
    apps = result.get("items", []) if isinstance(result, dict) else []
    if not apps:
        pytest.skip("No applications found in org")
    return apps[0]["id"]


@pytest.fixture(scope="session")
def first_user_id(real_ctx):
    """ID of the first ACTIVE user in the org."""
    from okta_mcp_server.tools.users.users import list_users
    result = asyncio.run(list_users(ctx=real_ctx, filter='status eq "ACTIVE"', limit=1))
    # list_users returns {"items": [(profile, id), ...], ...}
    items = result.get("items", []) if isinstance(result, dict) else []
    if not items:
        pytest.skip("No ACTIVE users found in org")
    _profile, uid = items[0]
    return uid


@pytest.fixture(scope="session")
def first_group_id(real_ctx):
    """ID of the first group in the org."""
    from okta_mcp_server.tools.groups.groups import list_groups
    result = asyncio.run(list_groups(ctx=real_ctx, limit=1))
    items = result.get("items", []) if isinstance(result, dict) else []
    if not items:
        pytest.skip("No groups found in org")
    group = items[0]
    return group.id if hasattr(group, "id") else group.get("id")


@pytest.fixture(scope="session")
def first_network_zone_id(real_ctx):
    """ID of the first network zone in the org."""
    from okta_mcp_server.tools.network_zones.network_zones import list_network_zones
    result = asyncio.run(list_network_zones(ctx=real_ctx))
    items = result.get("items", []) if isinstance(result, dict) else []
    if not items:
        pytest.skip("No network zones found in org")
    zone = items[0]
    return zone.get("id") if isinstance(zone, dict) else zone.id
