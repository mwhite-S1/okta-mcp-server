# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for profile mapping tools: list, get, update."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.profile_mappings.profile_mappings import (
    get_profile_mapping,
    list_profile_mappings,
    update_profile_mapping,
)


MAPPING_ID = "prm1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.profile_mappings.profile_mappings.get_okta_client"


def _make_mapping(mapping_id=MAPPING_ID):
    mapping = MagicMock()
    mapping.id = mapping_id
    mapping.to_dict.return_value = {
        "id": mapping_id,
        "source": {"id": "src123", "type": "user"},
        "target": {"id": "tgt456", "type": "appuser"},
        "properties": {},
    }
    return mapping


# ---------------------------------------------------------------------------
# list_profile_mappings
# ---------------------------------------------------------------------------

class TestListProfileMappings:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_mappings(self, mock_get_client, ctx_elicit_accept_true):
        mapping = _make_mapping()
        client = AsyncMock()
        client.list_profile_mappings.return_value = ([mapping], None, None)
        mock_get_client.return_value = client

        result = await list_profile_mappings(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 1
        assert result["items"][0]["id"] == MAPPING_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_profile_mappings.return_value = ([], None, None)
        mock_get_client.return_value = client

        result = await list_profile_mappings(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 0
        assert result["items"] == []

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_source_id_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_profile_mappings.return_value = ([], None, None)
        mock_get_client.return_value = client

        await list_profile_mappings(ctx=ctx_elicit_accept_true, source_id="src123")

        client.list_profile_mappings.assert_awaited_once_with(sourceId="src123")

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_target_id_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_profile_mappings.return_value = ([], None, None)
        mock_get_client.return_value = client

        await list_profile_mappings(ctx=ctx_elicit_accept_true, target_id="tgt456")

        client.list_profile_mappings.assert_awaited_once_with(targetId="tgt456")

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_profile_mappings.return_value = (None, None, "Insufficient permissions")
        mock_get_client.return_value = client

        result = await list_profile_mappings(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_profile_mappings(ctx=ctx_elicit_accept_true)

        assert "error" in result


# ---------------------------------------------------------------------------
# get_profile_mapping
# ---------------------------------------------------------------------------

class TestGetProfileMapping:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_mapping(self, mock_get_client, ctx_elicit_accept_true):
        mapping = _make_mapping()
        client = AsyncMock()
        client.get_profile_mapping.return_value = (mapping, None, None)
        mock_get_client.return_value = client

        result = await get_profile_mapping(ctx=ctx_elicit_accept_true, mapping_id=MAPPING_ID)

        assert result["id"] == MAPPING_ID
        client.get_profile_mapping.assert_awaited_once_with(MAPPING_ID)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await get_profile_mapping(ctx=ctx_elicit_accept_true, mapping_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_profile_mapping.return_value = (None, None, "Mapping not found")
        mock_get_client.return_value = client

        result = await get_profile_mapping(ctx=ctx_elicit_accept_true, mapping_id=MAPPING_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Timeout")

        result = await get_profile_mapping(ctx=ctx_elicit_accept_true, mapping_id=MAPPING_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# update_profile_mapping
# ---------------------------------------------------------------------------

class TestUpdateProfileMapping:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_mapping(self, mock_get_client, ctx_elicit_accept_true):
        mapping = _make_mapping()
        client = AsyncMock()
        client.update_profile_mapping.return_value = (mapping, None, None)
        mock_get_client.return_value = client

        props = {"firstName": {"expression": "user.firstName", "pushStatus": "PUSH"}}
        result = await update_profile_mapping(ctx=ctx_elicit_accept_true, mapping_id=MAPPING_ID, properties=props)

        assert result["id"] == MAPPING_ID
        client.update_profile_mapping.assert_awaited_once_with(MAPPING_ID, {"properties": props})

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await update_profile_mapping(ctx=ctx_elicit_accept_true, mapping_id="../bad", properties={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_profile_mapping.return_value = (None, None, "Invalid expression")
        mock_get_client.return_value = client

        result = await update_profile_mapping(ctx=ctx_elicit_accept_true, mapping_id=MAPPING_ID, properties={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await update_profile_mapping(ctx=ctx_elicit_accept_true, mapping_id=MAPPING_ID, properties={})

        assert "error" in result
