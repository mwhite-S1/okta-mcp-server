# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for directory agent pool tools.

Tests cover: list agent pools and read update settings/jobs.
All tests are read-only — creating/modifying update jobs on real AD/LDAP agents
is destructive and environment-specific, so write operations are not tested here.

If the org has no agent pools (no AD/LDAP configured), all pool-specific tests
are automatically skipped via the first_agent_pool_id fixture.
"""

from __future__ import annotations

import pytest

from okta_mcp_server.tools.agent_pools.agent_pools import (
    get_agent_pool_update,
    get_agent_pool_update_settings,
    list_agent_pool_updates,
    list_agent_pools,
)


# ---------------------------------------------------------------------------
# list_agent_pools
# ---------------------------------------------------------------------------

class TestListAgentPools:
    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx):
        result = await list_agent_pools(ctx=real_ctx)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_pool_type_filter(self, real_ctx):
        """pool_type= filter must be accepted without error."""
        result = await list_agent_pools(ctx=real_ctx, pool_type="AD")
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_agent_pool_shape(self, real_ctx):
        """Each pool must have an id and type field."""
        result = await list_agent_pools(ctx=real_ctx)
        assert "error" not in result, result.get("error")
        for pool in result["items"]:
            assert isinstance(pool, dict), f"Expected dict pool, got: {type(pool)}"
            assert pool.get("id"), f"Pool missing id: {pool}"
            assert pool.get("type"), f"Pool missing type: {pool}"


# ---------------------------------------------------------------------------
# list_agent_pool_updates
# ---------------------------------------------------------------------------

class TestListAgentPoolUpdates:
    @pytest.mark.asyncio
    async def test_list_updates_returns_response(self, real_ctx, first_agent_pool_id):
        result = await list_agent_pool_updates(ctx=real_ctx, pool_id=first_agent_pool_id)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_scheduled_filter(self, real_ctx, first_agent_pool_id):
        """scheduled=True filter must be accepted without error."""
        result = await list_agent_pool_updates(
            ctx=real_ctx, pool_id=first_agent_pool_id, scheduled=True
        )
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_invalid_pool_id_returns_error(self, real_ctx):
        result = await list_agent_pool_updates(ctx=real_ctx, pool_id="invalid-pool-000")
        assert isinstance(result, dict)
        assert "error" in result


# ---------------------------------------------------------------------------
# get_agent_pool_update_settings
# ---------------------------------------------------------------------------

class TestGetAgentPoolUpdateSettings:
    @pytest.mark.asyncio
    async def test_get_settings_returns_response(self, real_ctx, first_agent_pool_id):
        result = await get_agent_pool_update_settings(ctx=real_ctx, pool_id=first_agent_pool_id)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_invalid_pool_id_returns_error(self, real_ctx):
        result = await get_agent_pool_update_settings(ctx=real_ctx, pool_id="invalid-pool-000")
        assert isinstance(result, dict)
        assert "error" in result


# ---------------------------------------------------------------------------
# get_agent_pool_update (read-only: only runs if updates exist)
# ---------------------------------------------------------------------------

class TestGetAgentPoolUpdate:
    @pytest.mark.asyncio
    async def test_get_first_update_if_exists(self, real_ctx, first_agent_pool_id):
        updates = await list_agent_pool_updates(ctx=real_ctx, pool_id=first_agent_pool_id)
        assert "error" not in updates
        if not updates["items"]:
            pytest.skip("No agent pool updates found — nothing to get")
        update_id = updates["items"][0].get("id")
        if not update_id:
            pytest.skip("First update has no id")

        result = await get_agent_pool_update(
            ctx=real_ctx, pool_id=first_agent_pool_id, update_id=update_id
        )
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert result.get("id") == update_id

    @pytest.mark.asyncio
    async def test_invalid_update_id_returns_error(self, real_ctx, first_agent_pool_id):
        result = await get_agent_pool_update(
            ctx=real_ctx, pool_id=first_agent_pool_id, update_id="invalid-update-000"
        )
        assert isinstance(result, dict)
        assert "error" in result
