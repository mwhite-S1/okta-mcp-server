# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for network zone tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.network_zones.network_zones import (
    activate_network_zone,
    create_network_zone,
    deactivate_network_zone,
    delete_network_zone,
    get_network_zone,
    list_network_zones,
    replace_network_zone,
)


ZONE_ID = "nzo1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.network_zones.network_zones.get_okta_client"

ZONE_BODY = {
    "type": "IP",
    "name": "Test Zone",
    "gateways": [{"type": "CIDR", "value": "1.2.3.4/24"}],
}


def _make_zone(zone_id=ZONE_ID, name="Test Zone"):
    z = MagicMock()
    z.id = zone_id
    z.to_dict.return_value = {"id": zone_id, "name": name, "type": "IP", "status": "ACTIVE"}
    return z


# ---------------------------------------------------------------------------
# list_network_zones
# ---------------------------------------------------------------------------

class TestListNetworkZones:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_zones(self, mock_get_client, ctx_elicit_accept_true):
        zone = _make_zone()
        client = AsyncMock()
        client.list_network_zones.return_value = ([zone], None, None)
        mock_get_client.return_value = client

        result = await list_network_zones(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 1
        assert result["items"][0]["id"] == ZONE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_network_zones.return_value = ([], None, None)
        mock_get_client.return_value = client

        result = await list_network_zones(ctx=ctx_elicit_accept_true)
        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_network_zones.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await list_network_zones(ctx=ctx_elicit_accept_true)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_network_zones.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await list_network_zones(ctx=ctx_elicit_accept_true)
        assert "error" in result


# ---------------------------------------------------------------------------
# create_network_zone
# ---------------------------------------------------------------------------

class TestCreateNetworkZone:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        zone = _make_zone()
        client = AsyncMock()
        client.create_network_zone.return_value = (zone, None, None)
        mock_get_client.return_value = client

        result = await create_network_zone(ctx=ctx_elicit_accept_true, zone=ZONE_BODY)

        client.create_network_zone.assert_called_once_with(ZONE_BODY)
        assert result["id"] == ZONE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_network_zone.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await create_network_zone(ctx=ctx_elicit_accept_true, zone=ZONE_BODY)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_network_zone.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await create_network_zone(ctx=ctx_elicit_accept_true, zone=ZONE_BODY)
        assert "error" in result


# ---------------------------------------------------------------------------
# get_network_zone
# ---------------------------------------------------------------------------

class TestGetNetworkZone:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        zone = _make_zone()
        client = AsyncMock()
        client.get_network_zone.return_value = (zone, None, None)
        mock_get_client.return_value = client

        result = await get_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)

        assert result["id"] == ZONE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_network_zone.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await get_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_network_zone.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await get_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# replace_network_zone
# ---------------------------------------------------------------------------

class TestReplaceNetworkZone:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        zone = _make_zone()
        client = AsyncMock()
        client.replace_network_zone.return_value = (zone, None, None)
        mock_get_client.return_value = client

        result = await replace_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID, zone=ZONE_BODY)

        client.replace_network_zone.assert_called_once_with(ZONE_ID, ZONE_BODY)
        assert result["id"] == ZONE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.replace_network_zone.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await replace_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID, zone=ZONE_BODY)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.replace_network_zone.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await replace_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID, zone=ZONE_BODY)
        assert "error" in result


# ---------------------------------------------------------------------------
# delete_network_zone (with elicitation)
# ---------------------------------------------------------------------------

class TestDeleteNetworkZone:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_confirmed_deletes(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_network_zone.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await delete_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)

        client.delete_network_zone.assert_called_once_with(ZONE_ID)
        assert "deleted" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_cancelled(self, mock_get_client, ctx_elicit_accept_false):
        client = AsyncMock()
        mock_get_client.return_value = client

        result = await delete_network_zone(ctx=ctx_elicit_accept_false, zone_id=ZONE_ID)

        client.delete_network_zone.assert_not_called()
        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_network_zone.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await delete_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_fallback_when_no_elicitation(self, ctx_no_elicitation):
        result = await delete_network_zone(ctx=ctx_no_elicitation, zone_id=ZONE_ID)
        assert result.get("confirmation_required") is True


# ---------------------------------------------------------------------------
# activate_network_zone
# ---------------------------------------------------------------------------

class TestActivateNetworkZone:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        zone = _make_zone()
        client = AsyncMock()
        client.activate_network_zone.return_value = (zone, None, None)
        mock_get_client.return_value = client

        result = await activate_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)

        assert result["id"] == ZONE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_network_zone.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await activate_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_network_zone.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await activate_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# deactivate_network_zone
# ---------------------------------------------------------------------------

class TestDeactivateNetworkZone:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        zone = _make_zone()
        client = AsyncMock()
        client.deactivate_network_zone.return_value = (zone, None, None)
        mock_get_client.return_value = client

        result = await deactivate_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)

        assert result["id"] == ZONE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.deactivate_network_zone.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await deactivate_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.deactivate_network_zone.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await deactivate_network_zone(ctx=ctx_elicit_accept_true, zone_id=ZONE_ID)
        assert "error" in result
