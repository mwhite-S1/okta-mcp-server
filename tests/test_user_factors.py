# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for user factor tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.users.user_factors import (
    activate_factor,
    enroll_factor,
    get_factor,
    get_factor_transaction_status,
    list_factors,
    list_supported_factors,
    list_supported_security_questions,
    resend_enroll_factor,
    unenroll_factor,
    verify_factor,
)


USER_ID = "00u1234567890ABCDEF"
FACTOR_ID = "mfa1234567890ABCDEF"
TRANSACTION_ID = "v2mst.GldkAPI1ReaKi7bRR0001"
PATCH_CLIENT = "okta_mcp_server.tools.users.user_factors.get_okta_client"

FACTOR_BODY = {"factorType": "token:software:totp", "provider": "GOOGLE"}


def _make_factor(factor_id=FACTOR_ID, factor_type="token:software:totp"):
    f = MagicMock()
    f.id = factor_id
    f.to_dict.return_value = {"id": factor_id, "factorType": factor_type, "status": "ACTIVE"}
    return f


def _make_question(question_id="favorite_art_piece"):
    q = MagicMock()
    q.to_dict.return_value = {"question": question_id, "questionText": "What is your favorite art piece?"}
    return q


# ---------------------------------------------------------------------------
# list_factors
# ---------------------------------------------------------------------------

class TestListFactors:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_factors(self, mock_get_client, ctx_elicit_accept_true):
        factor = _make_factor()
        client = AsyncMock()
        client.list_factors.return_value = ([factor], None, None)
        mock_get_client.return_value = client

        result = await list_factors(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert result["total_fetched"] == 1
        assert result["items"][0]["id"] == FACTOR_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_factors.return_value = ([], None, None)
        mock_get_client.return_value = client

        result = await list_factors(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_factors.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await list_factors(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_factors.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await list_factors(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# list_supported_factors
# ---------------------------------------------------------------------------

class TestListSupportedFactors:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_supported(self, mock_get_client, ctx_elicit_accept_true):
        factor = _make_factor()
        client = AsyncMock()
        client.list_supported_factors.return_value = ([factor], None, None)
        mock_get_client.return_value = client

        result = await list_supported_factors(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert result["total_fetched"] == 1

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_supported_factors.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await list_supported_factors(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_supported_factors.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await list_supported_factors(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# list_supported_security_questions
# ---------------------------------------------------------------------------

class TestListSupportedSecurityQuestions:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_questions(self, mock_get_client, ctx_elicit_accept_true):
        question = _make_question()
        client = AsyncMock()
        client.list_supported_security_questions.return_value = ([question], None, None)
        mock_get_client.return_value = client

        result = await list_supported_security_questions(ctx=ctx_elicit_accept_true, user_id=USER_ID)

        assert result["total_fetched"] == 1
        assert "question" in result["items"][0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_supported_security_questions.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await list_supported_security_questions(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_supported_security_questions.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await list_supported_security_questions(ctx=ctx_elicit_accept_true, user_id=USER_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# get_factor
# ---------------------------------------------------------------------------

class TestGetFactor:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        factor = _make_factor()
        client = AsyncMock()
        client.get_factor.return_value = (factor, None, None)
        mock_get_client.return_value = client

        result = await get_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor_id=FACTOR_ID)

        client.get_factor.assert_called_once_with(USER_ID, FACTOR_ID)
        assert result["id"] == FACTOR_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_factor.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await get_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor_id=FACTOR_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_factor.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await get_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor_id=FACTOR_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# enroll_factor
# ---------------------------------------------------------------------------

class TestEnrollFactor:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        factor = _make_factor()
        client = AsyncMock()
        client.enroll_factor.return_value = (factor, None, None)
        mock_get_client.return_value = client

        result = await enroll_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor=FACTOR_BODY)

        client.enroll_factor.assert_called_once_with(USER_ID, FACTOR_BODY)
        assert result["id"] == FACTOR_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_with_activate_flag(self, mock_get_client, ctx_elicit_accept_true):
        factor = _make_factor()
        client = AsyncMock()
        client.enroll_factor.return_value = (factor, None, None)
        mock_get_client.return_value = client

        await enroll_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor=FACTOR_BODY, activate=True)

        client.enroll_factor.assert_called_once_with(USER_ID, FACTOR_BODY, activate=True)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.enroll_factor.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await enroll_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor=FACTOR_BODY)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.enroll_factor.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await enroll_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor=FACTOR_BODY)
        assert "error" in result


# ---------------------------------------------------------------------------
# activate_factor
# ---------------------------------------------------------------------------

class TestActivateFactor:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        factor = _make_factor()
        client = AsyncMock()
        client.activate_factor.return_value = (factor, None, None)
        mock_get_client.return_value = client

        result = await activate_factor(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            factor_id=FACTOR_ID,
            activation={"passCode": "123456"},
        )

        client.activate_factor.assert_called_once_with(USER_ID, FACTOR_ID, {"passCode": "123456"})
        assert result["id"] == FACTOR_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_factor.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await activate_factor(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            factor_id=FACTOR_ID,
            activation={"passCode": "000000"},
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_factor.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await activate_factor(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            factor_id=FACTOR_ID,
            activation={},
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# unenroll_factor (elicitation required)
# ---------------------------------------------------------------------------

class TestUnenrollFactor:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_confirmed_unenrolls(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unenroll_factor.return_value = (None, None, None)
        mock_get_client.return_value = client

        result = await unenroll_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor_id=FACTOR_ID)

        client.unenroll_factor.assert_called_once_with(USER_ID, FACTOR_ID)
        assert "unenrolled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_cancelled(self, mock_get_client, ctx_elicit_accept_false):
        client = AsyncMock()
        mock_get_client.return_value = client

        result = await unenroll_factor(ctx=ctx_elicit_accept_false, user_id=USER_ID, factor_id=FACTOR_ID)

        client.unenroll_factor.assert_not_called()
        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unenroll_factor.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await unenroll_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor_id=FACTOR_ID)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_fallback_when_no_elicitation(self, ctx_no_elicitation):
        result = await unenroll_factor(ctx=ctx_no_elicitation, user_id=USER_ID, factor_id=FACTOR_ID)
        assert result.get("confirmation_required") is True


# ---------------------------------------------------------------------------
# verify_factor
# ---------------------------------------------------------------------------

class TestVerifyFactor:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success_with_passcode(self, mock_get_client, ctx_elicit_accept_true):
        res = MagicMock()
        res.to_dict.return_value = {"factorResult": "SUCCESS"}
        client = AsyncMock()
        client.verify_factor.return_value = (res, None, None)
        mock_get_client.return_value = client

        result = await verify_factor(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            factor_id=FACTOR_ID,
            verification={"passCode": "123456"},
        )

        client.verify_factor.assert_called_once_with(USER_ID, FACTOR_ID, {"passCode": "123456"})
        assert result["factorResult"] == "SUCCESS"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_no_verification_payload(self, mock_get_client, ctx_elicit_accept_true):
        res = MagicMock()
        res.to_dict.return_value = {"factorResult": "WAITING"}
        client = AsyncMock()
        client.verify_factor.return_value = (res, None, None)
        mock_get_client.return_value = client

        result = await verify_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor_id=FACTOR_ID)

        client.verify_factor.assert_called_once_with(USER_ID, FACTOR_ID, {})

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.verify_factor.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await verify_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor_id=FACTOR_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.verify_factor.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await verify_factor(ctx=ctx_elicit_accept_true, user_id=USER_ID, factor_id=FACTOR_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# resend_enroll_factor
# ---------------------------------------------------------------------------

class TestResendEnrollFactor:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        factor = _make_factor()
        client = AsyncMock()
        client.resend_enroll_factor.return_value = (factor, None, None)
        mock_get_client.return_value = client

        result = await resend_enroll_factor(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            factor_id=FACTOR_ID,
            factor=FACTOR_BODY,
        )

        client.resend_enroll_factor.assert_called_once_with(USER_ID, FACTOR_ID, FACTOR_BODY)
        assert result["id"] == FACTOR_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.resend_enroll_factor.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await resend_enroll_factor(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            factor_id=FACTOR_ID,
            factor=FACTOR_BODY,
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.resend_enroll_factor.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await resend_enroll_factor(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            factor_id=FACTOR_ID,
            factor=FACTOR_BODY,
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# get_factor_transaction_status
# ---------------------------------------------------------------------------

class TestGetFactorTransactionStatus:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        res = MagicMock()
        res.to_dict.return_value = {"factorResult": "WAITING"}
        client = AsyncMock()
        client.get_factor_transaction_status.return_value = (res, None, None)
        mock_get_client.return_value = client

        result = await get_factor_transaction_status(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            factor_id=FACTOR_ID,
            transaction_id=TRANSACTION_ID,
        )

        client.get_factor_transaction_status.assert_called_once_with(USER_ID, FACTOR_ID, TRANSACTION_ID)
        assert result["factorResult"] == "WAITING"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_factor_transaction_status.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await get_factor_transaction_status(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            factor_id=FACTOR_ID,
            transaction_id=TRANSACTION_ID,
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_factor_transaction_status.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await get_factor_transaction_status(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            factor_id=FACTOR_ID,
            transaction_id=TRANSACTION_ID,
        )
        assert "error" in result
