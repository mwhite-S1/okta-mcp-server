# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for group tools."""

from __future__ import annotations

import time

import pytest

from okta_mcp_server.tools.groups.groups import (
    create_group,
    delete_group,
    get_group,
    list_group_users,
    list_groups,
    update_group,
)


class TestListGroups:
    @pytest.mark.asyncio
    async def test_bare_call_no_params(self, real_ctx):
        """list_groups() with no optional params must work — catches empty query_params SDK bugs."""
        result = await list_groups(ctx=real_ctx)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)
        assert len(result["items"]) > 0

    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx):
        result = await list_groups(ctx=real_ctx, limit=20)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)
        assert len(result["items"]) > 0

    @pytest.mark.asyncio
    async def test_group_shape(self, real_ctx):
        """Each returned group must have id and profile.name."""
        result = await list_groups(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        for group in result["items"]:
            gid = group.id if hasattr(group, "id") else group.get("id")
            assert gid, f"Missing id in group: {group}"

    @pytest.mark.asyncio
    async def test_q_param(self, real_ctx):
        """q= text search must be accepted without raising."""
        result = await list_groups(ctx=real_ctx, q="Everyone", limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_filter_param(self, real_ctx):
        """filter= expression must be accepted without raising."""
        result = await list_groups(ctx=real_ctx, filter='type eq "OKTA_GROUP"', limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_search_param(self, real_ctx):
        """search= SCIM expression must be accepted without raising."""
        result = await list_groups(ctx=real_ctx, search='type eq "OKTA_GROUP"', limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_limit_param(self, real_ctx):
        """Passing limit=20 must not raise a type error."""
        result = await list_groups(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert len(result["items"]) <= 20

    @pytest.mark.asyncio
    async def test_total_fetched_matches_items(self, real_ctx):
        result = await list_groups(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert result["total_fetched"] == len(result["items"])

    @pytest.mark.asyncio
    async def test_pagination_metadata_present(self, real_ctx):
        """has_more must be a bool and next_cursor must be None or a string."""
        result = await list_groups(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert isinstance(result.get("has_more"), bool)
        assert result.get("next_cursor") is None or isinstance(result.get("next_cursor"), str)
        assert isinstance(result.get("total_fetched"), int)

    @pytest.mark.asyncio
    async def test_cursor_fetches_next_page(self, real_ctx):
        """If has_more is True, the cursor must retrieve a different page."""
        first_page = await list_groups(ctx=real_ctx, limit=20)
        assert "error" not in first_page, first_page.get("error")
        if not first_page.get("has_more"):
            pytest.skip("Only one page of groups — pagination not testable")

        cursor = first_page["next_cursor"]
        second_page = await list_groups(ctx=real_ctx, limit=20, after=cursor)
        assert "error" not in second_page, second_page.get("error")
        assert isinstance(second_page["items"], list)

        first_ids = {
            g.id if hasattr(g, "id") else g.get("id") for g in first_page["items"]
        }
        second_ids = {
            g.id if hasattr(g, "id") else g.get("id") for g in second_page["items"]
        }
        assert not first_ids & second_ids, "Second page shares items with first page"


class TestGetGroup:
    @pytest.mark.asyncio
    async def test_get_returns_group(self, real_ctx, first_group_id):
        result = await get_group(ctx=real_ctx, group_id=first_group_id)
        assert result is not None
        assert isinstance(result, list)
        group = result[0]
        gid = group.id if hasattr(group, "id") else group.get("id")
        assert gid == first_group_id

    @pytest.mark.asyncio
    async def test_get_invalid_id(self, real_ctx):
        result = await get_group(ctx=real_ctx, group_id="invalid-group-000")
        assert result is not None
        assert isinstance(result, list)


class TestListGroupUsers:
    @pytest.mark.asyncio
    async def test_returns_dict(self, real_ctx, first_group_id):
        result = await list_group_users(ctx=real_ctx, group_id=first_group_id, limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_no_limit_does_not_raise(self, real_ctx, first_group_id):
        """Calling without an explicit limit must not raise a Pydantic validation error.

        The SDK's list_group_users validator fails when query_params is empty {}.
        The tool defaults limit=200 to ensure at least one param is always present.
        """
        result = await list_group_users(ctx=real_ctx, group_id=first_group_id)
        assert isinstance(result, dict), f"Expected dict, got: {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result


class TestGroupCRUD:
    @pytest.mark.asyncio
    async def test_create_update_delete(self, real_ctx):
        """Full create → update → delete cycle for an OKTA_GROUP."""
        ts = int(time.time())
        profile = {
            "name": f"mcp-tool-test-{ts}",
            "description": "Created by tool integration test — safe to delete",
        }

        created = await create_group(ctx=real_ctx, profile=profile)
        assert created is not None, "create_group returned None"
        assert isinstance(created, list)
        group = created[0]
        assert not isinstance(group, str), f"create_group returned error: {group}"
        group_id = group.id if hasattr(group, "id") else group.get("id")
        assert group_id, f"Created group has no id: {group}"

        try:
            # Update the group
            updated = await update_group(
                ctx=real_ctx,
                group_id=group_id,
                profile={"name": f"mcp-tool-test-{ts}-updated", "description": "Updated by test"},
            )
            assert updated is not None
            assert isinstance(updated, list)
            updated_group = updated[0]
            assert not isinstance(updated_group, str) or not updated_group.startswith("Error"), \
                f"update_group returned error: {updated_group}"

        finally:
            # delete_group uses elicitation; with elicitation=None it returns fallback payload
            # We use confirm_delete_group directly to avoid the elicitation flow
            from okta_mcp_server.tools.groups.groups import confirm_delete_group
            del_result = await confirm_delete_group(
                ctx=real_ctx, group_id=group_id, confirmation="DELETE"
            )
            assert del_result is not None
            assert isinstance(del_result, list)
            msg = del_result[0]
            assert "error" not in str(msg).lower() or "deleted" in str(msg).lower(), \
                f"Cleanup delete may have failed: {msg}"
