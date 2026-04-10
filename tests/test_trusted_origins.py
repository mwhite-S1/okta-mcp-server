# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for trusted origin tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.trusted_origins.trusted_origins import (
    activate_trusted_origin,
    create_trusted_origin,
    deactivate_trusted_origin,
    delete_trusted_origin,
    get_trusted_origin,
    list_trusted_origins,
    replace_trusted_origin,
)


ORIGIN_ID = "tos1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.trusted_origins.trusted_origins.get_okta_client"

SCOPES = [{"type": "CORS"}, {"type": "REDIRECT"}]
ORIGIN_URL = "https://example.com"


def _make_origin(origin_id=ORIGIN_ID, name="Example", origin_url=ORIGIN_URL):
    o = MagicMock()
    o.id = origin_id
    o.to_dict.return_value = {
        "id": origin_id,
        "name": name,
        "origin": origin_url,
        "status": "ACTIVE",
        "scopes": SCOPES,
    }
    return o


# ---------------------------------------------------------------------------
# list_trusted_origins
# ---------------------------------------------------------------------------

class TestListTrustedOrigins:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_origins(self, mock_get_client, ctx_elicit_accept_true):
        origin = _make_origin()
        client = AsyncMock()
        client.list_origins.return_value = ([origin], None, None)
        mock_get_client.return_value = client

        result = await list_trusted_origins(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 1
        assert result["items"][0]["id"] == ORIGIN_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_origins.return_value = ([], None, None)
        mock_get_client.return_value = client

        result = await list_trusted_origins(ctx=ctx_elicit_accept_true)
        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_origins.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await list_trusted_origins(ctx=ctx_elicit_accept_true)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_origins.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await list_trusted_origins(ctx=ctx_elicit_accept_true)
        assert "error" in result


# ---------------------------------------------------------------------------
# create_trusted_origin
# ---------------------------------------------------------------------------

class TestCreateTrustedOrigin:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        origin = _make_origin()
        client = AsyncMock()
        client.create_origin.return_value = (origin, None, None)
        mock_get_client.return_value = client

        result = await create_trusted_origin(
            ctx=ctx_elicit_accept_true,
            name="Example",
            origin=ORIGIN_URL,
            scopes=SCOPES,
        )

        expected_body = {"name": "Example", "origin": ORIGIN_URL, "scopes": SCOPES}
        client.create_origin.assert_called_once_with(expected_body)
        assert result["id"] == ORIGIN_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_origin.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await create_trusted_origin(
            ctx=ctx_elicit_accept_true,
            name="Example",
            origin=ORIGIN_URL,
            scopes=SCOPES,
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_origin.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await create_trusted_origin(
            ctx=ctx_elicit_accept_true,
            name="Example",
            origin=ORIGIN_URL,
            scopes=SCOPES,
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# get_trusted_origin
# ---------------------------------------------------------------------------

class TestGetTrustedOrigin:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        origin = _make_origin()
        client = AsyncMock()
        client.get_origin.return_value = (origin, None, None)
        mock_get_client.return_value = client

        result = await get_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)

        assert result["id"] == ORIGIN_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_origin.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await get_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_origin.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await get_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# replace_trusted_origin
# ---------------------------------------------------------------------------

class TestReplaceTrustedOrigin:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        origin = _make_origin()
        client = AsyncMock()
        client.replace_origin.return_value = (origin, None, None)
        mock_get_client.return_value = client

        result = await replace_trusted_origin(
            ctx=ctx_elicit_accept_true,
            origin_id=ORIGIN_ID,
            name="Updated",
            origin=ORIGIN_URL,
            scopes=SCOPES,
        )

        assert result["id"] == ORIGIN_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.replace_origin.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await replace_trusted_origin(
            ctx=ctx_elicit_accept_true,
            origin_id=ORIGIN_ID,
            name="Updated",
            origin=ORIGIN_URL,
            scopes=SCOPES,
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.replace_origin.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await replace_trusted_origin(
            ctx=ctx_elicit_accept_true,
            origin_id=ORIGIN_ID,
            name="Updated",
            origin=ORIGIN_URL,
            scopes=SCOPES,
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# delete_trusted_origin (with elicitation)
# ---------------------------------------------------------------------------

class TestDeleteTrustedOrigin:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_confirmed_deletes(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_origin.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await delete_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)

        client.delete_origin.assert_called_once_with(ORIGIN_ID)
        assert "deleted" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_cancelled(self, mock_get_client, ctx_elicit_accept_false):
        client = AsyncMock()
        mock_get_client.return_value = client

        result = await delete_trusted_origin(ctx=ctx_elicit_accept_false, origin_id=ORIGIN_ID)

        client.delete_origin.assert_not_called()
        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_origin.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await delete_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_fallback_when_no_elicitation(self, ctx_no_elicitation):
        result = await delete_trusted_origin(ctx=ctx_no_elicitation, origin_id=ORIGIN_ID)
        assert result.get("confirmation_required") is True


# ---------------------------------------------------------------------------
# activate_trusted_origin
# ---------------------------------------------------------------------------

class TestActivateTrustedOrigin:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        origin = _make_origin()
        client = AsyncMock()
        client.activate_origin.return_value = (origin, None, None)
        mock_get_client.return_value = client

        result = await activate_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)

        assert result["id"] == ORIGIN_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_origin.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await activate_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_origin.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await activate_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# deactivate_trusted_origin
# ---------------------------------------------------------------------------

class TestDeactivateTrustedOrigin:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        origin = _make_origin()
        client = AsyncMock()
        client.deactivate_origin.return_value = (origin, None, None)
        mock_get_client.return_value = client

        result = await deactivate_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)

        assert result["id"] == ORIGIN_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.deactivate_origin.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await deactivate_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.deactivate_origin.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await deactivate_trusted_origin(ctx=ctx_elicit_accept_true, origin_id=ORIGIN_ID)
        assert "error" in result
