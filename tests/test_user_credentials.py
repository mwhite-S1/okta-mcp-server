# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for user credential tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.users.user_credentials import (
    change_password,
    change_recovery_question,
    expire_password,
    expire_password_with_temp_password,
    forgot_password,
    reset_password,
)


USER_ID = "00u1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.users.user_credentials.get_okta_client"


def _make_token(url="https://example.okta.com/reset"):
    t = MagicMock()
    t.to_dict.return_value = {"resetPasswordUrl": url}
    return t


def _make_user():
    u = MagicMock()
    u.to_dict.return_value = {"id": USER_ID, "status": "PASSWORD_EXPIRED"}
    return u


def _make_creds():
    c = MagicMock()
    c.to_dict.return_value = {"password": {}, "recovery_question": {}}
    return c


# ---------------------------------------------------------------------------
# reset_password
# ---------------------------------------------------------------------------

class TestResetPassword:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_send_email_true(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.reset_password.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await reset_password(ctx=ctx_elicit_accept_true, user_id=USER_ID, send_email=True)

        client.reset_password.assert_called_once_with(USER_ID, sendEmail=True)
        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_send_email_false_returns_url(self, mock_get_client, ctx_elicit_accept_true):
        token = _make_token()
        client = AsyncMock()
        client.reset_password.return_value = (token, None, None)
        mock_get_client.return_value = client

        result = await reset_password(ctx=ctx_elicit_accept_true, user_id=USER_ID, send_email=False)

        assert "resetPasswordUrl" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.reset_password.return_value = (None, None, Exception("API error"))
        mock_get_client.return_value = client

        result = await reset_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.reset_password.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await reset_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# expire_password
# ---------------------------------------------------------------------------

class TestExpirePassword:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        user = _make_user()
        client = AsyncMock()
        client.expire_password.return_value = (user, None, None)
        mock_get_client.return_value = client

        result = await expire_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert result["status"] == "PASSWORD_EXPIRED"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.expire_password.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await expire_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.expire_password.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await expire_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# expire_password_with_temp_password
# ---------------------------------------------------------------------------

class TestExpirePasswordWithTempPassword:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        temp = MagicMock()
        temp.to_dict.return_value = {"tempPassword": "Temp1234!"}
        client = AsyncMock()
        client.expire_password_and_get_temporary_password.return_value = (temp, None, None)
        mock_get_client.return_value = client

        result = await expire_password_with_temp_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "tempPassword" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.expire_password_and_get_temporary_password.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await expire_password_with_temp_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.expire_password_and_get_temporary_password.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await expire_password_with_temp_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# change_password
# ---------------------------------------------------------------------------

class TestChangePassword:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        creds = _make_creds()
        client = AsyncMock()
        client.change_password.return_value = (creds, None, None)
        mock_get_client.return_value = client

        result = await change_password(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            old_password="OldPass1!",
            new_password="NewPass1!",
        )

        assert "password" in result
        expected_body = {
            "oldPassword": {"value": "OldPass1!"},
            "newPassword": {"value": "NewPass1!"},
        }
        client.change_password.assert_called_once_with(USER_ID, expected_body)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.change_password.return_value = (None, None, Exception("invalid"))
        mock_get_client.return_value = client

        result = await change_password(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            old_password="OldPass1!",
            new_password="NewPass1!",
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.change_password.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await change_password(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            old_password="OldPass1!",
            new_password="NewPass1!",
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# forgot_password
# ---------------------------------------------------------------------------

class TestForgotPassword:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success_no_email(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.forgot_password.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await forgot_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success_with_recovery_url(self, mock_get_client, ctx_elicit_accept_true):
        recovery = MagicMock()
        recovery.to_dict.return_value = {"resetPasswordUrl": "https://example.okta.com/reset"}
        client = AsyncMock()
        client.forgot_password.return_value = (recovery, None, None)
        mock_get_client.return_value = client

        result = await forgot_password(ctx=ctx_elicit_accept_true, user_id=USER_ID, send_email=False)

        assert "resetPasswordUrl" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.forgot_password.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await forgot_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.forgot_password.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await forgot_password(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# change_recovery_question
# ---------------------------------------------------------------------------

class TestChangeRecoveryQuestion:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        creds = _make_creds()
        client = AsyncMock()
        client.change_recovery_question.return_value = (creds, None, None)
        mock_get_client.return_value = client

        result = await change_recovery_question(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            password="MyPass1!",
            recovery_question="What is your pet's name?",
            recovery_answer="Fluffy",
        )

        assert "password" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.change_recovery_question.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await change_recovery_question(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            password="MyPass1!",
            recovery_question="Q",
            recovery_answer="A",
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.change_recovery_question.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await change_recovery_question(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            password="MyPass1!",
            recovery_question="Q",
            recovery_answer="A",
        )
        assert "error" in result
