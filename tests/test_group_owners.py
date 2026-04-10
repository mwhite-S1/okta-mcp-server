# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for group owner tools: list, assign, delete."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.groups.group_owners import (
    assign_group_owner,
    delete_group_owner,
    list_group_owners,
)


GROUP_ID = "00g1234567890ABCDEF"
OWNER_ID = "00u1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.groups.group_owners.get_okta_client"


def _make_owner(owner_id=OWNER_ID, display_name="Test Owner", owner_type="USER"):
    owner = MagicMock()
    owner.id = owner_id
    owner.display_name = display_name
    owner.type = owner_type
    owner.to_dict.return_value = {"id": owner_id, "displayName": display_name, "type": owner_type}
    return owner


# ---------------------------------------------------------------------------
# list_group_owners
# ---------------------------------------------------------------------------

class TestListGroupOwners:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_owners(self, mock_get_client, ctx_elicit_accept_true):
        owner = _make_owner()
        client = AsyncMock()
        client.list_group_owners.return_value = ([owner], None, None)
        mock_get_client.return_value = client

        result = await list_group_owners(ctx=ctx_elicit_accept_true, group_id=GROUP_ID)

        assert result["total_fetched"] == 1
        assert result["items"][0]["id"] == OWNER_ID
        client.list_group_owners.assert_awaited_once_with(GROUP_ID)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_group_owners.return_value = ([], None, None)
        mock_get_client.return_value = client

        result = await list_group_owners(ctx=ctx_elicit_accept_true, group_id=GROUP_ID)

        assert result["total_fetched"] == 0
        assert result["items"] == []

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_search_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_group_owners.return_value = ([], None, None)
        mock_get_client.return_value = client

        await list_group_owners(ctx=ctx_elicit_accept_true, group_id=GROUP_ID, search="Alice")

        client.list_group_owners.assert_awaited_once_with(GROUP_ID, search="Alice")

    @pytest.mark.asyncio
    async def test_invalid_group_id_rejected(self, ctx_elicit_accept_true):
        result = await list_group_owners(ctx=ctx_elicit_accept_true, group_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_group_owners.return_value = (None, None, "Group not found")
        mock_get_client.return_value = client

        result = await list_group_owners(ctx=ctx_elicit_accept_true, group_id=GROUP_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_group_owners(ctx=ctx_elicit_accept_true, group_id=GROUP_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# assign_group_owner
# ---------------------------------------------------------------------------

class TestAssignGroupOwner:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_assigns_owner(self, mock_get_client, ctx_elicit_accept_true):
        owner = _make_owner()
        client = AsyncMock()
        client.assign_group_owner.return_value = (owner, None, None)
        mock_get_client.return_value = client

        owner_data = {"id": OWNER_ID, "type": "USER"}
        result = await assign_group_owner(ctx=ctx_elicit_accept_true, group_id=GROUP_ID, owner=owner_data)

        assert result["id"] == OWNER_ID
        client.assign_group_owner.assert_awaited_once_with(GROUP_ID, owner_data)

    @pytest.mark.asyncio
    async def test_invalid_group_id_rejected(self, ctx_elicit_accept_true):
        result = await assign_group_owner(ctx=ctx_elicit_accept_true, group_id="bad/id", owner={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.assign_group_owner.return_value = (None, None, "User not found")
        mock_get_client.return_value = client

        result = await assign_group_owner(ctx=ctx_elicit_accept_true, group_id=GROUP_ID, owner={"id": OWNER_ID, "type": "USER"})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection timeout")

        result = await assign_group_owner(ctx=ctx_elicit_accept_true, group_id=GROUP_ID, owner={})

        assert "error" in result


# ---------------------------------------------------------------------------
# delete_group_owner (with elicitation)
# ---------------------------------------------------------------------------

class TestDeleteGroupOwner:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_deletes_owner_when_confirmed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_group_owner.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await delete_group_owner(ctx=ctx_elicit_accept_true, group_id=GROUP_ID, owner_id=OWNER_ID)

        assert "message" in result
        assert "removed" in result["message"]
        client.delete_group_owner.assert_awaited_once_with(GROUP_ID, OWNER_ID)

    @pytest.mark.asyncio
    async def test_cancelled_when_not_confirmed(self, ctx_elicit_accept_false):
        result = await delete_group_owner(ctx=ctx_elicit_accept_false, group_id=GROUP_ID, owner_id=OWNER_ID)

        assert "cancelled" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_invalid_group_id_rejected(self, ctx_elicit_accept_true):
        result = await delete_group_owner(ctx=ctx_elicit_accept_true, group_id="bad/id", owner_id=OWNER_ID)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_owner_id_rejected(self, ctx_elicit_accept_true):
        result = await delete_group_owner(ctx=ctx_elicit_accept_true, group_id=GROUP_ID, owner_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_group_owner.return_value = (None, None, "Owner not found")
        mock_get_client.return_value = client

        result = await delete_group_owner(ctx=ctx_elicit_accept_true, group_id=GROUP_ID, owner_id=OWNER_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_group_owner.side_effect = Exception("Connection error")
        mock_get_client.return_value = client

        result = await delete_group_owner(ctx=ctx_elicit_accept_true, group_id=GROUP_ID, owner_id=OWNER_ID)

        assert "error" in result
