# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for user lifecycle tools: activate, reactivate, reset_factors, suspend, unlock, unsuspend."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.users.user_lifecycle import (
    activate_user,
    reactivate_user,
    reset_factors,
    suspend_user,
    unlock_user,
    unsuspend_user,
)


USER_ID = "00u1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.users.user_lifecycle.get_okta_client"


# ---------------------------------------------------------------------------
# activate_user
# ---------------------------------------------------------------------------

class TestActivateUser:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_activates_user_with_email(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_user.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await activate_user(ctx=ctx_elicit_accept_true, user_id=USER_ID, send_email=True)

        assert "message" in result
        assert "activated" in result["message"]
        client.activate_user.assert_awaited_once_with(USER_ID, send_email=True)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_activates_user_returns_token(self, mock_get_client, ctx_elicit_accept_true):
        token = MagicMock()
        token.to_dict.return_value = {"activationToken": "abc123", "activationUrl": "https://example.okta.com/..."}
        client = AsyncMock()
        client.activate_user.return_value = (token, None, None)
        mock_get_client.return_value = client

        result = await activate_user(ctx=ctx_elicit_accept_true, user_id=USER_ID, send_email=False)

        assert result["activationToken"] == "abc123"

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await activate_user(ctx=ctx_elicit_accept_true, user_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_user.return_value = (None, None, "User already active")
        mock_get_client.return_value = client

        result = await activate_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await activate_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# reactivate_user
# ---------------------------------------------------------------------------

class TestReactivateUser:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_reactivates_user(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.reactivate_user.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await reactivate_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "message" in result
        assert "reactivated" in result["message"]
        client.reactivate_user.assert_awaited_once_with(USER_ID, send_email=True)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_reactivates_user_returns_token(self, mock_get_client, ctx_elicit_accept_true):
        token = MagicMock()
        token.to_dict.return_value = {"activationToken": "xyz789", "activationUrl": "https://example.okta.com/..."}
        client = AsyncMock()
        client.reactivate_user.return_value = (token, None, None)
        mock_get_client.return_value = client

        result = await reactivate_user(ctx=ctx_elicit_accept_true, user_id=USER_ID, send_email=False)

        assert result["activationToken"] == "xyz789"

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await reactivate_user(ctx=ctx_elicit_accept_true, user_id="../bad")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.reactivate_user.return_value = (None, None, "User not in PROVISIONED state")
        mock_get_client.return_value = client

        result = await reactivate_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Network error")

        result = await reactivate_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# reset_factors
# ---------------------------------------------------------------------------

class TestResetFactors:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_resets_factors(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.reset_factors.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await reset_factors(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "message" in result
        assert "reset" in result["message"]
        client.reset_factors.assert_awaited_once_with(USER_ID)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await reset_factors(ctx=ctx_elicit_accept_true, user_id="bad?id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.reset_factors.return_value = (None, None, "User not found")
        mock_get_client.return_value = client

        result = await reset_factors(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Timeout")

        result = await reset_factors(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# suspend_user
# ---------------------------------------------------------------------------

class TestSuspendUser:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_suspends_user(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.suspend_user.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await suspend_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "message" in result
        assert "suspended" in result["message"]
        client.suspend_user.assert_awaited_once_with(USER_ID)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await suspend_user(ctx=ctx_elicit_accept_true, user_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.suspend_user.return_value = (None, None, "Cannot suspend user in STAGED state")
        mock_get_client.return_value = client

        result = await suspend_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await suspend_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# unlock_user
# ---------------------------------------------------------------------------

class TestUnlockUser:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_unlocks_user(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unlock_user.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await unlock_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "message" in result
        assert "unlocked" in result["message"]
        client.unlock_user.assert_awaited_once_with(USER_ID)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await unlock_user(ctx=ctx_elicit_accept_true, user_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unlock_user.return_value = (None, None, "User is not locked out")
        mock_get_client.return_value = client

        result = await unlock_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await unlock_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# unsuspend_user
# ---------------------------------------------------------------------------

class TestUnsuspendUser:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_unsuspends_user(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unsuspend_user.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await unsuspend_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "message" in result
        assert "unsuspended" in result["message"]
        client.unsuspend_user.assert_awaited_once_with(USER_ID)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await unsuspend_user(ctx=ctx_elicit_accept_true, user_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unsuspend_user.return_value = (None, None, "User is not suspended")
        mock_get_client.return_value = client

        result = await unsuspend_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Network timeout")

        result = await unsuspend_user(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "error" in result
