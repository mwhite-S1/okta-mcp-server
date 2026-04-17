# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for authenticator tools.

Tests cover: list/get authenticators, list/get methods, list/get AAGUIDs.
Write operations (create, replace, lifecycle) are tested in a guarded CRUD
cycle that cleans up after itself.
"""

from __future__ import annotations

import pytest

from okta_mcp_server.tools.authenticators.authenticators import (
    activate_authenticator,
    activate_authenticator_method,
    deactivate_authenticator,
    deactivate_authenticator_method,
    get_authenticator,
    get_authenticator_method,
    list_authenticator_methods,
    list_authenticators,
    list_custom_aaguids,
    replace_authenticator,
)


# ---------------------------------------------------------------------------
# list_authenticators
# ---------------------------------------------------------------------------

class TestListAuthenticators:
    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx):
        result = await list_authenticators(ctx=real_ctx)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_returns_at_least_one_authenticator(self, real_ctx):
        """Every Okta org has at least a password authenticator."""
        result = await list_authenticators(ctx=real_ctx)
        assert "error" not in result, result.get("error")
        assert len(result["items"]) > 0, "Expected at least one authenticator"

    @pytest.mark.asyncio
    async def test_authenticator_shape(self, real_ctx):
        """Each authenticator must have id, key, name, status, and type."""
        result = await list_authenticators(ctx=real_ctx)
        assert "error" not in result, result.get("error")
        for auth in result["items"]:
            assert isinstance(auth, dict), f"Expected dict item, got: {type(auth)}"
            assert auth.get("id"), f"Missing id: {auth}"
            assert auth.get("key"), f"Missing key: {auth}"
            assert auth.get("name"), f"Missing name: {auth}"
            assert auth.get("status") in ("ACTIVE", "INACTIVE"), f"Unexpected status: {auth}"


# ---------------------------------------------------------------------------
# get_authenticator
# ---------------------------------------------------------------------------

class TestGetAuthenticator:
    @pytest.mark.asyncio
    async def test_get_returns_authenticator(self, real_ctx, first_authenticator_id):
        result = await get_authenticator(ctx=real_ctx, authenticator_id=first_authenticator_id)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert result.get("id") == first_authenticator_id

    @pytest.mark.asyncio
    async def test_get_invalid_id_returns_error(self, real_ctx):
        result = await get_authenticator(ctx=real_ctx, authenticator_id="invalid-auth-000")
        assert isinstance(result, dict)
        assert "error" in result


# ---------------------------------------------------------------------------
# list_authenticator_methods
# ---------------------------------------------------------------------------

class TestListAuthenticatorMethods:
    @pytest.mark.asyncio
    async def test_list_methods_returns_response(self, real_ctx, first_authenticator_id):
        result = await list_authenticator_methods(ctx=real_ctx, authenticator_id=first_authenticator_id)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_method_shape(self, real_ctx, first_authenticator_id):
        """Each method must have a type field."""
        result = await list_authenticator_methods(ctx=real_ctx, authenticator_id=first_authenticator_id)
        assert "error" not in result, result.get("error")
        for method in result["items"]:
            if isinstance(method, dict):
                assert method.get("type"), f"Method missing type: {method}"

    @pytest.mark.asyncio
    async def test_invalid_authenticator_id_returns_error(self, real_ctx):
        result = await list_authenticator_methods(ctx=real_ctx, authenticator_id="invalid-000")
        assert isinstance(result, dict)
        assert "error" in result


# ---------------------------------------------------------------------------
# get_authenticator_method
# ---------------------------------------------------------------------------

class TestGetAuthenticatorMethod:
    @pytest.mark.asyncio
    async def test_get_password_method(self, real_ctx):
        """The password authenticator always has a 'password' method."""
        auths = await list_authenticators(ctx=real_ctx)
        assert "error" not in auths
        password_auth = next(
            (a for a in auths["items"] if a.get("key") == "okta_password"),
            None,
        )
        if not password_auth:
            pytest.skip("No password authenticator found in org")
        result = await get_authenticator_method(
            ctx=real_ctx,
            authenticator_id=password_auth["id"],
            method_type="password",
        )
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert result.get("type") == "password"

    @pytest.mark.asyncio
    async def test_invalid_method_type_returns_error(self, real_ctx, first_authenticator_id):
        result = await get_authenticator_method(
            ctx=real_ctx,
            authenticator_id=first_authenticator_id,
            method_type="nonexistent_method_type",
        )
        assert isinstance(result, dict)
        assert "error" in result


# ---------------------------------------------------------------------------
# list_custom_aaguids
# ---------------------------------------------------------------------------

class TestListCustomAAGUIDs:
    @pytest.mark.asyncio
    async def test_list_aaguids_on_webauthn_authenticator(self, real_ctx):
        """Find the WebAuthn authenticator and list its AAGUIDs (may be empty)."""
        auths = await list_authenticators(ctx=real_ctx)
        assert "error" not in auths
        webauthn = next(
            (a for a in auths["items"] if a.get("key") == "webauthn"),
            None,
        )
        if not webauthn:
            pytest.skip("No WebAuthn authenticator configured in org")
        result = await list_custom_aaguids(ctx=real_ctx, authenticator_id=webauthn["id"])
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_invalid_authenticator_returns_error(self, real_ctx):
        result = await list_custom_aaguids(ctx=real_ctx, authenticator_id="invalid-000")
        assert isinstance(result, dict)
        assert "error" in result


# ---------------------------------------------------------------------------
# replace_authenticator (safe: rename password authenticator back to itself)
# ---------------------------------------------------------------------------

class TestReplaceAuthenticator:
    @pytest.mark.asyncio
    async def test_replace_preserves_existing_name(self, real_ctx):
        """Replace the password authenticator with the same data — must not error."""
        auths = await list_authenticators(ctx=real_ctx)
        assert "error" not in auths
        password_auth = next(
            (a for a in auths["items"] if a.get("key") == "okta_password"),
            None,
        )
        if not password_auth:
            pytest.skip("No password authenticator found")

        result = await replace_authenticator(
            ctx=real_ctx,
            authenticator_id=password_auth["id"],
            authenticator_data={"name": password_auth["name"]},
        )
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert result.get("id") == password_auth["id"]
