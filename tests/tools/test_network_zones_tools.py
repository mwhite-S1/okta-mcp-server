# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for network zone tools."""

from __future__ import annotations

import time

import pytest

from okta_mcp_server.tools.network_zones.network_zones import (
    activate_network_zone,
    create_network_zone,
    deactivate_network_zone,
    get_network_zone,
    list_network_zones,
    replace_network_zone,
)


class TestListNetworkZones:
    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx):
        result = await list_network_zones(ctx=real_ctx)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_zone_shape(self, real_ctx):
        """Each returned zone must have id, name, and type."""
        result = await list_network_zones(ctx=real_ctx)
        assert "error" not in result, result.get("error")
        for zone in result["items"]:
            zid = zone.get("id") if isinstance(zone, dict) else zone.id
            assert zid, f"Missing id in zone: {zone}"

    @pytest.mark.asyncio
    async def test_filter_param(self, real_ctx):
        """filter= expression must be accepted without raising."""
        result = await list_network_zones(ctx=real_ctx, filter='usage eq "POLICY"')
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_limit_param(self, real_ctx):
        """limit= must be accepted without raising."""
        result = await list_network_zones(ctx=real_ctx, limit=5)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert len(result["items"]) <= 5

    @pytest.mark.asyncio
    async def test_pagination_metadata_present(self, real_ctx):
        """has_more must be a bool and next_cursor must be None or a string."""
        result = await list_network_zones(ctx=real_ctx)
        assert "error" not in result, result.get("error")
        assert isinstance(result.get("has_more"), bool)
        assert result.get("next_cursor") is None or isinstance(result.get("next_cursor"), str)
        assert isinstance(result.get("total_fetched"), int)

    @pytest.mark.asyncio
    async def test_cursor_fetches_next_page(self, real_ctx):
        """If has_more is True, the cursor must retrieve a different page."""
        first_page = await list_network_zones(ctx=real_ctx, limit=2)
        assert "error" not in first_page, first_page.get("error")
        if not first_page.get("has_more"):
            pytest.skip("Only one page of network zones — pagination not testable")

        cursor = first_page["next_cursor"]
        second_page = await list_network_zones(ctx=real_ctx, limit=2, after=cursor)
        assert "error" not in second_page, second_page.get("error")
        assert isinstance(second_page["items"], list)

        first_ids = {z["id"] for z in first_page["items"]}
        second_ids = {z["id"] for z in second_page["items"]}
        assert not first_ids & second_ids, "Second page shares items with first page"


class TestGetNetworkZone:
    @pytest.mark.asyncio
    async def test_get_returns_zone(self, real_ctx, first_network_zone_id):
        result = await get_network_zone(ctx=real_ctx, zone_id=first_network_zone_id)
        assert result is not None
        assert "error" not in result, result.get("error")
        zid = result.get("id") if isinstance(result, dict) else result.id
        assert zid == first_network_zone_id

    @pytest.mark.asyncio
    async def test_get_invalid_id(self, real_ctx):
        result = await get_network_zone(ctx=real_ctx, zone_id="invalid-zone-000")
        assert result is not None
        assert "error" in result


class TestNetworkZoneCRUD:
    @pytest.mark.asyncio
    async def test_create_replace_lifecycle_delete(self, real_ctx):
        """Full create → replace → deactivate → activate → deactivate → delete cycle."""
        ts = int(time.time())
        zone_def = {
            "type": "IP",
            "name": f"mcp-tool-test-{ts}",
            "status": "ACTIVE",
            "gateways": [{"type": "CIDR", "value": "10.254.0.0/16"}],
            "proxies": [],
        }

        created = await create_network_zone(ctx=real_ctx, zone=zone_def)
        assert created is not None
        assert "error" not in created, f"create_network_zone failed: {created.get('error')}"
        zone_id = created.get("id")
        assert zone_id, f"Created zone has no id: {created}"

        try:
            # Replace (update)
            replace_def = {**zone_def, "name": f"mcp-tool-test-{ts}-updated"}
            replaced = await replace_network_zone(ctx=real_ctx, zone_id=zone_id, zone=replace_def)
            assert "error" not in replaced, f"replace_network_zone failed: {replaced.get('error')}"
            assert replaced.get("name") == f"mcp-tool-test-{ts}-updated"

            # Deactivate (required before delete)
            deactivated = await deactivate_network_zone(ctx=real_ctx, zone_id=zone_id)
            assert "error" not in deactivated, f"deactivate failed: {deactivated.get('error')}"

            # Activate
            activated = await activate_network_zone(ctx=real_ctx, zone_id=zone_id)
            assert "error" not in activated, f"activate failed: {activated.get('error')}"

            # Deactivate again so we can delete
            deactivated2 = await deactivate_network_zone(ctx=real_ctx, zone_id=zone_id)
            assert "error" not in deactivated2, f"second deactivate failed: {deactivated2.get('error')}"

        finally:
            # delete_network_zone uses elicitation; call the SDK directly for cleanup
            from okta_mcp_server.utils.client import get_okta_client
            manager = real_ctx.request_context.lifespan_context.okta_auth_manager
            client = await get_okta_client(manager)
            _, _, err = await client.delete_network_zone(zone_id)
            if err:
                pytest.fail(f"Cleanup delete of network zone {zone_id} failed: {err}")
