# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for application tools."""

from __future__ import annotations

import pytest

from okta_mcp_server.tools.applications.applications import (
    get_application,
    list_applications,
)


class TestListApplications:
    @pytest.mark.asyncio
    async def test_bare_call_no_params(self, real_ctx):
        """list_applications() with no params must work — catches bare-call SDK bugs."""
        result = await list_applications(ctx=real_ctx)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx):
        result = await list_applications(ctx=real_ctx, limit=20)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)
        assert len(result["items"]) > 0

    @pytest.mark.asyncio
    async def test_app_shape(self, real_ctx):
        result = await list_applications(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        for app in result["items"]:
            assert "id" in app, f"Missing 'id' in app: {app}"
            assert "label" in app or "name" in app
            assert "status" in app

    @pytest.mark.asyncio
    async def test_limit_param_accepted(self, real_ctx):
        """limit= must not raise a type error (clamped to 20 minimum)."""
        result = await list_applications(ctx=real_ctx, limit=5)
        assert isinstance(result, dict), result
        assert "error" not in result, result.get("error")
        assert len(result["items"]) <= 20  # clamped from 5 to minimum of 20

    @pytest.mark.asyncio
    async def test_filter_by_active_status(self, real_ctx):
        result = await list_applications(ctx=real_ctx, filter='status eq "ACTIVE"', limit=10)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        for app in result["items"]:
            assert app.get("status") == "ACTIVE"

    @pytest.mark.asyncio
    async def test_query_param(self, real_ctx):
        result = await list_applications(ctx=real_ctx, q="Okta", limit=5)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_total_fetched_matches_items(self, real_ctx):
        result = await list_applications(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert result["total_fetched"] == len(result["items"])

    @pytest.mark.asyncio
    async def test_pagination_metadata_present(self, real_ctx):
        """has_more must be a bool and next_cursor must be None or a string."""
        result = await list_applications(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert isinstance(result.get("has_more"), bool)
        assert result.get("next_cursor") is None or isinstance(result.get("next_cursor"), str)

    @pytest.mark.asyncio
    async def test_cursor_fetches_next_page(self, real_ctx):
        """If has_more is True, the next_cursor must retrieve a different page."""
        first_page = await list_applications(ctx=real_ctx, limit=20)
        assert "error" not in first_page, first_page.get("error")
        if not first_page.get("has_more"):
            pytest.skip("Only one page of applications available — pagination not testable")

        cursor = first_page["next_cursor"]
        second_page = await list_applications(ctx=real_ctx, limit=20, after=cursor)
        assert "error" not in second_page, second_page.get("error")
        assert isinstance(second_page["items"], list)

        first_ids = {app["id"] for app in first_page["items"]}
        second_ids = {app["id"] for app in second_page["items"]}
        assert not first_ids & second_ids, "Second page shares items with first page"


class TestGetApplication:
    @pytest.mark.asyncio
    async def test_get_returns_app(self, real_ctx, first_app_id):
        result = await get_application(ctx=real_ctx, app_id=first_app_id)
        assert result is not None
        # get_application returns a list with one item
        app = result[0] if isinstance(result, list) else result
        assert "id" in app
        assert app.get("id") == first_app_id

    @pytest.mark.asyncio
    async def test_get_invalid_id(self, real_ctx):
        result = await get_application(ctx=real_ctx, app_id="invalid-app-000")
        # Should return an error string or dict, not raise
        assert result is not None
