# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for user session revocation tool."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from okta_mcp_server.tools.users.user_sessions import revoke_user_sessions


USER_ID = "00u1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.users.user_sessions.get_okta_client"


class TestRevokeUserSessions:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_confirmed_revokes_sessions(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_user_sessions.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await revoke_user_sessions(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        client.revoke_user_sessions.assert_called_once_with(USER_ID)
        assert "message" in result
        assert "revoked" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_confirmed_with_oauth_tokens(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_user_sessions.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await revoke_user_sessions(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            oauth_tokens=True,
            forget_devices=True,
        )

        client.revoke_user_sessions.assert_called_once_with(USER_ID, oauthTokens=True, forgetDevices=True)
        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_cancelled_by_user(self, mock_get_client, ctx_elicit_accept_false):
        client = AsyncMock()
        mock_get_client.return_value = client

        result = await revoke_user_sessions(ctx=ctx_elicit_accept_false, user_id=USER_ID)

        client.revoke_user_sessions.assert_not_called()
        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error_from_api(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_user_sessions.return_value = (None, None, Exception("API error"))
        mock_get_client.return_value = client

        result = await revoke_user_sessions(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_user_sessions.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await revoke_user_sessions(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_fallback_when_no_elicitation(self, ctx_no_elicitation):
        result = await revoke_user_sessions(ctx=ctx_no_elicitation, user_id=USER_ID)
        assert result.get("confirmation_required") is True
