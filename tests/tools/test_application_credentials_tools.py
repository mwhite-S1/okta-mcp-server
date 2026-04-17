# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for application credential tools.

Tests cover: SSO signing keys, CSRs, OAuth JWKs, and OAuth client secrets.
Write operations use real create/delete cycles with guaranteed cleanup.
Elicitation is disabled in the test context — destructive tools fall through
to the auto-confirm fallback path and return confirmation_required dicts
rather than executing — so cleanup uses _execute directly.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from okta_mcp_server.tools.applications.application_credentials import (
    clone_application_key,
    generate_application_csr,
    generate_application_key,
    get_application_csr,
    get_application_key,
    get_application_jwk,
    get_oauth2_client_secret,
    list_application_csrs,
    list_application_jwks,
    list_application_keys,
    list_oauth2_client_secrets,
    create_oauth2_client_secret,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _direct_delete(real_ctx, path: str) -> None:
    """Delete a resource directly via _execute, bypassing elicitation."""
    from okta_mcp_server.tools.applications.application_credentials import _execute
    from okta_mcp_server.utils.client import get_okta_client
    manager = real_ctx.request_context.lifespan_context.okta_auth_manager
    client = await get_okta_client(manager)
    await _execute(client, "DELETE", path)


# ---------------------------------------------------------------------------
# SSO Signing Keys
# ---------------------------------------------------------------------------

class TestListApplicationKeys:
    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx, first_app_id):
        result = await list_application_keys(ctx=real_ctx, app_id=first_app_id)
        assert isinstance(result, dict), f"Expected dict: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_key_shape(self, real_ctx, first_app_id):
        """Each key must have a kid field."""
        result = await list_application_keys(ctx=real_ctx, app_id=first_app_id)
        assert "error" not in result, result.get("error")
        for key in result["items"]:
            assert isinstance(key, dict)
            assert key.get("kid"), f"Key missing kid: {key}"

    @pytest.mark.asyncio
    async def test_invalid_app_id_returns_error(self, real_ctx):
        result = await list_application_keys(ctx=real_ctx, app_id="invalid-app-000")
        assert "error" in result


class TestGetApplicationKey:
    @pytest.mark.asyncio
    async def test_get_first_key(self, real_ctx, first_app_id):
        keys = await list_application_keys(ctx=real_ctx, app_id=first_app_id)
        assert "error" not in keys
        if not keys["items"]:
            pytest.skip("App has no signing keys")
        kid = keys["items"][0]["kid"]
        result = await get_application_key(ctx=real_ctx, app_id=first_app_id, key_id=kid)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert result.get("kid") == kid


class TestGenerateApplicationKey:
    @pytest.mark.asyncio
    async def test_generate_key_creates_and_is_retrievable(self, real_ctx, first_app_id):
        """Generate a new key, verify it's retrievable, then clean up."""
        result = await generate_application_key(ctx=real_ctx, app_id=first_app_id, validity_years=1)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        kid = result.get("kid")
        assert kid, f"No kid in generated key: {result}"

        try:
            fetched = await get_application_key(ctx=real_ctx, app_id=first_app_id, key_id=kid)
            assert "error" not in fetched, fetched.get("error")
            assert fetched.get("kid") == kid
        finally:
            # SSO signing keys cannot be deleted via the API — they expire.
            # No cleanup needed.
            pass


# ---------------------------------------------------------------------------
# CSRs
# ---------------------------------------------------------------------------

class TestListApplicationCSRs:
    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx, first_app_id):
        result = await list_application_csrs(ctx=real_ctx, app_id=first_app_id)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_invalid_app_id_returns_error(self, real_ctx):
        result = await list_application_csrs(ctx=real_ctx, app_id="invalid-000")
        assert "error" in result


class TestApplicationCSRLifecycle:
    @pytest.mark.asyncio
    async def test_generate_and_get_csr(self, real_ctx, first_app_id):
        """Generate a CSR, verify it's retrievable, then revoke it (direct delete)."""
        ts = int(time.time())
        subject = {
            "countryName": "US",
            "stateOrProvinceName": "California",
            "localityName": "San Francisco",
            "organizationName": "Test Org",
            "organizationalUnitName": "Engineering",
            "commonName": f"mcp-test-{ts}.example.com",
        }
        created = await generate_application_csr(ctx=real_ctx, app_id=first_app_id, subject=subject)
        assert isinstance(created, dict)
        assert "error" not in created, f"generate_application_csr failed: {created.get('error')}"
        csr_id = created.get("id")
        assert csr_id, f"No id in created CSR: {created}"
        assert created.get("csrValue") or created.get("kty"), f"CSR missing expected fields: {created}"

        try:
            fetched = await get_application_csr(ctx=real_ctx, app_id=first_app_id, csr_id=csr_id)
            assert "error" not in fetched, fetched.get("error")
            assert fetched.get("id") == csr_id
        finally:
            # revoke_application_csr uses elicitation; bypass for cleanup
            await _direct_delete(real_ctx, f"/api/v1/apps/{first_app_id}/credentials/csrs/{csr_id}")


# ---------------------------------------------------------------------------
# OAuth JWKs
# ---------------------------------------------------------------------------

class TestListApplicationJWKs:
    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx, first_app_id):
        result = await list_application_jwks(ctx=real_ctx, app_id=first_app_id)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_invalid_app_returns_error(self, real_ctx):
        result = await list_application_jwks(ctx=real_ctx, app_id="invalid-000")
        assert "error" in result


class TestGetApplicationJWK:
    @pytest.mark.asyncio
    async def test_get_first_jwk_if_exists(self, real_ctx, first_app_id):
        jwks = await list_application_jwks(ctx=real_ctx, app_id=first_app_id)
        assert "error" not in jwks
        if not jwks["items"]:
            pytest.skip("App has no OAuth JWKs")
        kid = jwks["items"][0].get("kid")
        if not kid:
            pytest.skip("First JWK has no kid")
        result = await get_application_jwk(ctx=real_ctx, app_id=first_app_id, key_id=kid)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert result.get("kid") == kid


# ---------------------------------------------------------------------------
# OAuth Client Secrets
# ---------------------------------------------------------------------------

class TestListOAuth2ClientSecrets:
    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx, first_app_id):
        result = await list_oauth2_client_secrets(ctx=real_ctx, app_id=first_app_id)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_secret_shape(self, real_ctx, first_app_id):
        """Secrets must never expose the actual secret value in list responses."""
        result = await list_oauth2_client_secrets(ctx=real_ctx, app_id=first_app_id)
        assert "error" not in result
        for secret in result["items"]:
            if isinstance(secret, dict):
                # The actual client_secret value must not be present in list
                assert "client_secret" not in secret, (
                    f"Secret value leaked in list response: {secret}"
                )
                assert secret.get("id"), f"Secret missing id: {secret}"

    @pytest.mark.asyncio
    async def test_invalid_app_returns_error(self, real_ctx):
        result = await list_oauth2_client_secrets(ctx=real_ctx, app_id="invalid-000")
        assert "error" in result


class TestOAuth2ClientSecretLifecycle:
    @pytest.mark.asyncio
    async def test_create_secret_returns_value_once(self, real_ctx, first_app_id):
        """Create a secret, verify the value is returned, get metadata, then clean up."""
        created = await create_oauth2_client_secret(ctx=real_ctx, app_id=first_app_id)
        assert isinstance(created, dict)

        # Some apps don't support client secrets (e.g. SAML-only apps)
        if "error" in created:
            pytest.skip(f"App does not support client secrets: {created['error']}")

        secret_id = created.get("id")
        assert secret_id, f"No id in created secret: {created}"
        # The actual secret value is only present at creation
        assert created.get("client_secret") or created.get("secretHash"), (
            f"Expected secret value or hash at creation: {created}"
        )

        try:
            fetched = await get_oauth2_client_secret(
                ctx=real_ctx, app_id=first_app_id, secret_id=secret_id
            )
            assert "error" not in fetched, fetched.get("error")
            assert fetched.get("id") == secret_id
            # Value must NOT be present when fetching after creation
            assert "client_secret" not in fetched, "Secret value should not be re-retrievable"
        finally:
            # delete_oauth2_client_secret uses elicitation; bypass for cleanup
            await _direct_delete(
                real_ctx, f"/api/v1/apps/{first_app_id}/credentials/secrets/{secret_id}"
            )
