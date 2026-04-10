# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for all group tools: list, get, create, update, delete, list_users, list_apps, add/remove user."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.groups.groups import (
    add_user_to_group,
    create_group,
    get_group,
    list_group_apps,
    list_group_users,
    list_groups,
    remove_user_from_group,
    update_group,
)


GROUP_ID = "00g1234567890ABCDEF"
USER_ID = "00u1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.groups.groups.get_okta_client"


def _make_group(group_id=GROUP_ID, name="Test Group"):
    profile = MagicMock()
    profile.name = name
    group = MagicMock()
    group.id = group_id
    group.profile = profile
    return group


def _make_paginated_response(has_next=False):
    response = MagicMock()
    response.has_next.return_value = has_next
    return response


def _make_app():
    app = MagicMock()
    app.as_dict.return_value = {"id": "0oa123", "label": "Test App", "status": "ACTIVE"}
    return app


# ---------------------------------------------------------------------------
# list_groups
# ---------------------------------------------------------------------------

class TestListGroups:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_groups(self, mock_get_client, ctx_elicit_accept_true):
        group = _make_group()
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_groups.return_value = ([group], response, None)
        mock_get_client.return_value = client

        result = await list_groups(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 1
        assert result["has_more"] is False
        assert result["items"] == [group]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_groups.return_value = ([], response, None)
        mock_get_client.return_value = client

        result = await list_groups(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_groups.return_value = (None, None, "API Error")
        mock_get_client.return_value = client

        result = await list_groups(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_groups(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_limit_clamped_below_minimum(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_groups.return_value = ([], response, None)
        mock_get_client.return_value = client

        await list_groups(ctx=ctx_elicit_accept_true, limit=5)
        call_params = client.list_groups.call_args.kwargs
        assert call_params.get("limit") == 20

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_limit_clamped_above_maximum(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_groups.return_value = ([], response, None)
        mock_get_client.return_value = client

        await list_groups(ctx=ctx_elicit_accept_true, limit=500)
        call_params = client.list_groups.call_args.kwargs
        assert call_params.get("limit") == 100

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_search_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_groups.return_value = ([], response, None)
        mock_get_client.return_value = client

        await list_groups(ctx=ctx_elicit_accept_true, search='profile.name sw "Eng"')
        call_params = client.list_groups.call_args.kwargs
        assert "search" in call_params

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_has_more_when_response_has_next(self, mock_get_client, ctx_elicit_accept_true):
        group = _make_group()
        response = _make_paginated_response(has_next=True)
        client = AsyncMock()
        client.list_groups.return_value = ([group], response, None)
        mock_get_client.return_value = client

        result = await list_groups(ctx=ctx_elicit_accept_true)

        assert result["has_more"] is True


# ---------------------------------------------------------------------------
# get_group
# ---------------------------------------------------------------------------

class TestGetGroup:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_group(self, mock_get_client, ctx_elicit_accept_true):
        group = _make_group()
        client = AsyncMock()
        client.get_group.return_value = (group, None, None)
        mock_get_client.return_value = client

        result = await get_group(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert result == [group]
        client.get_group.assert_awaited_once_with(GROUP_ID)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await get_group(group_id="bad/id", ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_group.return_value = (None, None, "Group not found")
        mock_get_client.return_value = client

        result = await get_group(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Not found")

        result = await get_group(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert "Exception" in result[0]


# ---------------------------------------------------------------------------
# create_group
# ---------------------------------------------------------------------------

class TestCreateGroup:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_group(self, mock_get_client, ctx_elicit_accept_true):
        group = _make_group()
        client = AsyncMock()
        client.create_group.return_value = (group, None, None)
        mock_get_client.return_value = client

        profile = {"name": "Test Group", "description": "A test group"}
        result = await create_group(profile=profile, ctx=ctx_elicit_accept_true)

        assert result == [group]
        client.create_group.assert_awaited_once_with({"profile": profile})

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_group.return_value = (None, None, "Group name already exists")
        mock_get_client.return_value = client

        result = await create_group(profile={"name": "Dup"}, ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_group(profile={}, ctx=ctx_elicit_accept_true)

        assert "Exception" in result[0]


# ---------------------------------------------------------------------------
# update_group
# ---------------------------------------------------------------------------

class TestUpdateGroup:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_group(self, mock_get_client, ctx_elicit_accept_true):
        group = _make_group()
        client = AsyncMock()
        client.update_group.return_value = (group, None, None)
        mock_get_client.return_value = client

        profile = {"name": "Updated Group"}
        result = await update_group(group_id=GROUP_ID, profile=profile, ctx=ctx_elicit_accept_true)

        assert result == [group]
        client.update_group.assert_awaited_once_with(GROUP_ID, {"profile": profile})

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await update_group(group_id="../bad", profile={}, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_group.return_value = (None, None, "Group not found")
        mock_get_client.return_value = client

        result = await update_group(group_id=GROUP_ID, profile={}, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await update_group(group_id=GROUP_ID, profile={}, ctx=ctx_elicit_accept_true)

        assert "Exception" in result[0]


# ---------------------------------------------------------------------------
# list_group_users
# ---------------------------------------------------------------------------

class TestListGroupUsers:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_users(self, mock_get_client, ctx_elicit_accept_true):
        user = MagicMock()
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_group_users.return_value = ([user], response, None)
        mock_get_client.return_value = client

        result = await list_group_users(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 1
        assert result["has_more"] is False

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_group_users.return_value = ([], response, None)
        mock_get_client.return_value = client

        result = await list_group_users(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_group_users.return_value = (None, None, "API Error")
        mock_get_client.return_value = client

        result = await list_group_users(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_group_users(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await list_group_users(group_id="bad/id", ctx=ctx_elicit_accept_true)

        assert "error" in result


# ---------------------------------------------------------------------------
# list_group_apps
# ---------------------------------------------------------------------------

class TestListGroupApps:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_apps(self, mock_get_client, ctx_elicit_accept_true):
        app = _make_app()
        client = AsyncMock()
        client.list_assigned_applications_for_group.return_value = ([app], None, None)
        mock_get_client.return_value = client

        result = await list_group_apps(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert len(result) == 1
        assert result[0] == {"id": "0oa123", "label": "Test App", "status": "ACTIVE"}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_assigned_applications_for_group.return_value = ([], None, None)
        mock_get_client.return_value = client

        result = await list_group_apps(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert result == []

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_assigned_applications_for_group.return_value = (None, None, "API Error")
        mock_get_client.return_value = client

        result = await list_group_apps(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_group_apps(group_id=GROUP_ID, ctx=ctx_elicit_accept_true)

        assert "Exception" in result[0]

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await list_group_apps(group_id="bad/id", ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]


# ---------------------------------------------------------------------------
# add_user_to_group
# ---------------------------------------------------------------------------

class TestAddUserToGroup:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_adds_user(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.add_user_to_group.return_value = (None, None)
        mock_get_client.return_value = client

        result = await add_user_to_group(group_id=GROUP_ID, user_id=USER_ID, ctx=ctx_elicit_accept_true)

        assert USER_ID in result[0]
        assert GROUP_ID in result[0]
        client.add_user_to_group.assert_awaited_once_with(GROUP_ID, USER_ID)

    @pytest.mark.asyncio
    async def test_invalid_group_id_rejected(self, ctx_elicit_accept_true):
        result = await add_user_to_group(group_id="bad/id", user_id=USER_ID, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    async def test_invalid_user_id_rejected(self, ctx_elicit_accept_true):
        result = await add_user_to_group(group_id=GROUP_ID, user_id="bad/id", ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.add_user_to_group.return_value = (None, "User already in group")
        mock_get_client.return_value = client

        result = await add_user_to_group(group_id=GROUP_ID, user_id=USER_ID, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await add_user_to_group(group_id=GROUP_ID, user_id=USER_ID, ctx=ctx_elicit_accept_true)

        assert "Exception" in result[0]


# ---------------------------------------------------------------------------
# remove_user_from_group
# ---------------------------------------------------------------------------

class TestRemoveUserFromGroup:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_removes_user(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.remove_user_from_group.return_value = (None, None)
        mock_get_client.return_value = client

        result = await remove_user_from_group(group_id=GROUP_ID, user_id=USER_ID, ctx=ctx_elicit_accept_true)

        assert USER_ID in result[0]
        assert GROUP_ID in result[0]
        client.remove_user_from_group.assert_awaited_once_with(GROUP_ID, USER_ID)

    @pytest.mark.asyncio
    async def test_invalid_group_id_rejected(self, ctx_elicit_accept_true):
        result = await remove_user_from_group(group_id="bad/id", user_id=USER_ID, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.remove_user_from_group.return_value = (None, "User not in group")
        mock_get_client.return_value = client

        result = await remove_user_from_group(group_id=GROUP_ID, user_id=USER_ID, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await remove_user_from_group(group_id=GROUP_ID, user_id=USER_ID, ctx=ctx_elicit_accept_true)

        assert "Exception" in result[0]


# ---------------------------------------------------------------------------
# Group lifecycle: create → get → update → add_user → remove_user
# ---------------------------------------------------------------------------

class TestGroupLifecycle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_create_get_update_add_remove(self, mock_get_client, ctx_elicit_accept_true):
        created_group = _make_group(group_id="00gnew123", name="New Group")
        updated_group = _make_group(group_id="00gnew123", name="Updated Group")
        user = MagicMock()

        client = AsyncMock()
        client.create_group.return_value = (created_group, None, None)
        client.get_group.return_value = (created_group, None, None)
        client.update_group.return_value = (updated_group, None, None)
        client.add_user_to_group.return_value = (None, None)
        client.remove_user_from_group.return_value = (None, None)
        mock_get_client.return_value = client

        # Step 1: create
        create_result = await create_group(
            profile={"name": "New Group", "description": "test"},
            ctx=ctx_elicit_accept_true,
        )
        assert create_result == [created_group]

        # Step 2: get
        get_result = await get_group(group_id="00gnew123", ctx=ctx_elicit_accept_true)
        assert get_result == [created_group]

        # Step 3: update
        update_result = await update_group(
            group_id="00gnew123",
            profile={"name": "Updated Group"},
            ctx=ctx_elicit_accept_true,
        )
        assert update_result == [updated_group]

        # Step 4: add user
        add_result = await add_user_to_group(
            group_id="00gnew123", user_id=USER_ID, ctx=ctx_elicit_accept_true
        )
        assert USER_ID in add_result[0]

        # Step 5: remove user
        remove_result = await remove_user_from_group(
            group_id="00gnew123", user_id=USER_ID, ctx=ctx_elicit_accept_true
        )
        assert USER_ID in remove_result[0]
