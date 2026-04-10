# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for device tools."""

from __future__ import annotations

import pytest

from okta_mcp_server.tools.devices.devices import (
    list_devices,
    get_device,
    list_device_users,
)


class TestListDevices:
    @pytest.mark.asyncio
    async def test_bare_call_no_params(self, real_ctx):
        """list_devices() with no params must work — catches bare-call SDK bugs."""
        result = await list_devices(ctx=real_ctx)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx):
        result = await list_devices(ctx=real_ctx, limit=20)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert "total_fetched" in result

    @pytest.mark.asyncio
    async def test_search_param(self, real_ctx):
        """search= SCIM expression must be accepted without raising."""
        result = await list_devices(ctx=real_ctx, search='status eq "ACTIVE"', limit=10)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_limit_param(self, real_ctx):
        """limit= must be accepted without raising."""
        result = await list_devices(ctx=real_ctx, limit=5)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert len(result["items"]) <= 5

    @pytest.mark.asyncio
    async def test_expand_user_summary(self, real_ctx):
        """expand=userSummary must be accepted without raising."""
        result = await list_devices(ctx=real_ctx, expand="userSummary", limit=5)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_total_fetched_matches_items(self, real_ctx):
        result = await list_devices(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert result["total_fetched"] == len(result["items"])

    @pytest.mark.asyncio
    async def test_pagination_metadata_present(self, real_ctx):
        """has_more must be a bool and next_cursor must be None or a string."""
        result = await list_devices(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert isinstance(result.get("has_more"), bool)
        assert result.get("next_cursor") is None or isinstance(result.get("next_cursor"), str)
        assert isinstance(result.get("total_fetched"), int)

    @pytest.mark.asyncio
    async def test_cursor_fetches_next_page(self, real_ctx):
        """If has_more is True, the cursor must retrieve a different page."""
        first_page = await list_devices(ctx=real_ctx, limit=5)
        assert "error" not in first_page, first_page.get("error")
        if not first_page.get("has_more"):
            pytest.skip("Only one page of devices — pagination not testable")

        cursor = first_page["next_cursor"]
        second_page = await list_devices(ctx=real_ctx, limit=5, after=cursor)
        assert "error" not in second_page, second_page.get("error")
        assert isinstance(second_page["items"], list)

        first_ids = {d["id"] for d in first_page["items"]}
        second_ids = {d["id"] for d in second_page["items"]}
        assert not first_ids & second_ids, "Second page shares items with first page"


class TestGetDevice:
    @pytest.mark.asyncio
    async def test_get_invalid_id_does_not_raise(self, real_ctx):
        """Invalid device ID must return an error dict, not raise."""
        result = await get_device(ctx=real_ctx, device_id="invalid-device-000")
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_returns_device_if_exists(self, real_ctx):
        """If devices exist, get the first one and verify shape."""
        devices_result = await list_devices(ctx=real_ctx, limit=1)
        assert "error" not in devices_result, devices_result.get("error")
        if not devices_result["items"]:
            pytest.skip("No devices in org")

        device_id = devices_result["items"][0]["id"]
        result = await get_device(ctx=real_ctx, device_id=device_id)
        assert result is not None
        assert "error" not in result, result.get("error")
        assert result.get("id") == device_id


class TestListDeviceUsers:
    @pytest.mark.asyncio
    async def test_list_users_for_first_device(self, real_ctx):
        """list_device_users must return a list (empty is valid)."""
        devices_result = await list_devices(ctx=real_ctx, limit=1)
        assert "error" not in devices_result, devices_result.get("error")
        if not devices_result["items"]:
            pytest.skip("No devices in org")

        device_id = devices_result["items"][0]["id"]
        result = await list_device_users(ctx=real_ctx, device_id=device_id)
        assert isinstance(result, list)
        assert not any(
            isinstance(item, dict) and "error" in item for item in result
        ), f"Error in device users: {result}"
