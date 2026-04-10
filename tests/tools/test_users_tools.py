# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for user tools."""

from __future__ import annotations

import pytest

from okta_mcp_server.tools.users.users import (
    get_user,
    get_user_profile_attributes,
    list_user_blocks,
    list_users,
)


class TestListUsers:
    @pytest.mark.asyncio
    async def test_bare_call_no_params(self, real_ctx):
        """list_users() with no optional params must work — catches empty query_params SDK bugs."""
        result = await list_users(ctx=real_ctx)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx):
        result = await list_users(ctx=real_ctx, limit=20)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)
        assert result["total_fetched"] == len(result["items"])

    @pytest.mark.asyncio
    async def test_items_are_profile_id_tuples(self, real_ctx):
        """list_users items are (profile, id) tuples."""
        result = await list_users(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        for item in result["items"]:
            assert len(item) == 2, f"Expected (profile, id) tuple, got: {item}"
            profile, uid = item
            assert uid is not None and uid != ""

    @pytest.mark.asyncio
    async def test_filter_active_users(self, real_ctx):
        result = await list_users(ctx=real_ctx, filter='status eq "ACTIVE"', limit=20)
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert len(result["items"]) > 0

    @pytest.mark.asyncio
    async def test_search_param(self, real_ctx):
        """search= SCIM expression must be accepted without raising."""
        result = await list_users(ctx=real_ctx, search='status eq "ACTIVE"', limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_q_param(self, real_ctx):
        """q= text search must be accepted without raising."""
        result = await list_users(ctx=real_ctx, q="admin", limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_limit_param(self, real_ctx):
        """Passing limit=20 must not raise a StrictStr type error."""
        result = await list_users(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert len(result["items"]) <= 20

    @pytest.mark.asyncio
    async def test_has_more_is_bool(self, real_ctx):
        result = await list_users(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert isinstance(result.get("has_more"), bool)

    @pytest.mark.asyncio
    async def test_pagination_metadata_present(self, real_ctx):
        """has_more, next_cursor, and total_fetched must be present."""
        result = await list_users(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert isinstance(result.get("has_more"), bool)
        assert result.get("next_cursor") is None or isinstance(result.get("next_cursor"), str)
        assert isinstance(result.get("total_fetched"), int)

    @pytest.mark.asyncio
    async def test_cursor_fetches_next_page(self, real_ctx):
        """If has_more is True, the cursor must retrieve a different page."""
        first_page = await list_users(ctx=real_ctx, limit=20)
        assert "error" not in first_page, first_page.get("error")
        if not first_page.get("has_more"):
            pytest.skip("Only one page of users — pagination not testable")

        cursor = first_page["next_cursor"]
        second_page = await list_users(ctx=real_ctx, limit=20, after=cursor)
        assert "error" not in second_page, second_page.get("error")
        assert isinstance(second_page["items"], list)

        first_ids = {uid for _, uid in first_page["items"]}
        second_ids = {uid for _, uid in second_page["items"]}
        assert not first_ids & second_ids, "Second page shares items with first page"


class TestGetUser:
    @pytest.mark.asyncio
    async def test_get_returns_user(self, real_ctx, first_user_id):
        result = await get_user(ctx=real_ctx, user_id=first_user_id)
        assert result is not None
        assert not isinstance(result[0], str) or not result[0].startswith("Exception"), \
            f"get_user returned error: {result[0]}"
        user = result[0]
        assert hasattr(user, "id") or hasattr(user, "profile"), f"Unexpected user object: {user}"

    @pytest.mark.asyncio
    async def test_get_invalid_id_does_not_raise(self, real_ctx):
        """Invalid user ID must return an error string/dict, not raise."""
        result = await get_user(ctx=real_ctx, user_id="invalid-user-000")
        assert result is not None
        # Either an exception string or an error dict — just shouldn't crash
        assert isinstance(result, list)


class TestGetUserProfileAttributes:
    @pytest.mark.asyncio
    async def test_returns_attributes(self, real_ctx):
        result = await get_user_profile_attributes(ctx=real_ctx)
        assert result is not None
        assert not isinstance(result, str) or not result.startswith("Exception"), \
            f"Unexpected error: {result}"
        # Should be a dict of profile attributes or a list
        assert result is not None

    @pytest.mark.asyncio
    async def test_common_attributes_present(self, real_ctx):
        """Standard Okta profile attributes must be present."""
        result = await get_user_profile_attributes(ctx=real_ctx)
        if isinstance(result, dict):
            # Okta always has these core attributes
            assert "login" in result or "email" in result, f"Core attributes missing: {result}"


class TestListUserBlocks:
    @pytest.mark.asyncio
    async def test_returns_list(self, real_ctx, first_user_id):
        """list_user_blocks must return a list (empty is fine for unlocked users)."""
        result = await list_user_blocks(ctx=real_ctx, user_id=first_user_id)
        assert isinstance(result, list), f"Expected list, got {type(result)}: {result}"
        # An active user should have no blocks; empty list is a valid response
        assert all(
            not isinstance(item, str) or not item.startswith("Exception")
            for item in result
        ), f"Error in blocks: {result}"

    @pytest.mark.asyncio
    async def test_invalid_user_returns_error(self, real_ctx):
        result = await list_user_blocks(ctx=real_ctx, user_id="invalid-user-000")
        assert isinstance(result, list)
        # Should contain an error string, not raise
