# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for user OAuth token tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.users.user_oauth import (
    get_refresh_token_for_user_and_client,
    list_refresh_tokens_for_user_and_client,
    revoke_token_for_user_and_client,
    revoke_tokens_for_user_and_client,
)


USER_ID = "00u1234567890ABCDEF"
CLIENT_ID = "0oa1234567890ABCDEF"
TOKEN_ID = "sHHSth05thF7v0x2K2p5"
PATCH_CLIENT = "okta_mcp_server.tools.users.user_oauth.get_okta_client"


def _make_token():
    t = MagicMock()
    t.to_dict.return_value = {"id": TOKEN_ID, "clientId": CLIENT_ID}
    return t


# ---------------------------------------------------------------------------
# list_refresh_tokens_for_user_and_client
# ---------------------------------------------------------------------------

class TestListRefreshTokensForUserAndClient:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_tokens(self, mock_get_client, ctx_elicit_accept_true):
        token = _make_token()
        client = AsyncMock()
        client.list_refresh_tokens_for_user_and_client.return_value = ([token], None, None)
        mock_get_client.return_value = client

        result = await list_refresh_tokens_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
        )

        assert result["total_fetched"] == 1
        assert result["items"][0]["id"] == TOKEN_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_refresh_tokens_for_user_and_client.return_value = ([], None, None)
        mock_get_client.return_value = client

        result = await list_refresh_tokens_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
        )
        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_refresh_tokens_for_user_and_client.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await list_refresh_tokens_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_refresh_tokens_for_user_and_client.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await list_refresh_tokens_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# get_refresh_token_for_user_and_client
# ---------------------------------------------------------------------------

class TestGetRefreshTokenForUserAndClient:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        token = _make_token()
        client = AsyncMock()
        client.get_refresh_token_for_user_and_client.return_value = (token, None, None)
        mock_get_client.return_value = client

        result = await get_refresh_token_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
            token_id=TOKEN_ID,
        )

        assert result["id"] == TOKEN_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_refresh_token_for_user_and_client.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await get_refresh_token_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
            token_id=TOKEN_ID,
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_refresh_token_for_user_and_client.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await get_refresh_token_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
            token_id=TOKEN_ID,
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# revoke_tokens_for_user_and_client (all tokens — elicitation required)
# ---------------------------------------------------------------------------

class TestRevokeTokensForUserAndClient:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_confirmed_revokes_all(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_tokens_for_user_and_client.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await revoke_tokens_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
        )

        client.revoke_tokens_for_user_and_client.assert_called_once_with(USER_ID, CLIENT_ID)
        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_cancelled(self, mock_get_client, ctx_elicit_accept_false):
        client = AsyncMock()
        mock_get_client.return_value = client

        result = await revoke_tokens_for_user_and_client(
            ctx=ctx_elicit_accept_false,
            user_id=USER_ID,
            client_id=CLIENT_ID,
        )

        client.revoke_tokens_for_user_and_client.assert_not_called()
        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_tokens_for_user_and_client.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await revoke_tokens_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_fallback_when_no_elicitation(self, ctx_no_elicitation):
        result = await revoke_tokens_for_user_and_client(
            ctx=ctx_no_elicitation,
            user_id=USER_ID,
            client_id=CLIENT_ID,
        )
        assert result.get("confirmation_required") is True


# ---------------------------------------------------------------------------
# revoke_token_for_user_and_client (single token — no elicitation)
# ---------------------------------------------------------------------------

class TestRevokeTokenForUserAndClient:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_token_for_user_and_client.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await revoke_token_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
            token_id=TOKEN_ID,
        )

        client.revoke_token_for_user_and_client.assert_called_once_with(USER_ID, CLIENT_ID, TOKEN_ID)
        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_token_for_user_and_client.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await revoke_token_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
            token_id=TOKEN_ID,
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_token_for_user_and_client.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await revoke_token_for_user_and_client(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            client_id=CLIENT_ID,
            token_id=TOKEN_ID,
        )
        assert "error" in result
