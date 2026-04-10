# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for governance elicitation flows: delete_governance_label, revoke_principal_access,
cancel_access_request, delete_request_condition."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.governance.access_requests import (
    cancel_access_request,
    delete_request_condition,
)
from okta_mcp_server.tools.governance.entitlements import revoke_principal_access
from okta_mcp_server.tools.governance.labels import delete_governance_label


LABEL_ID = "lbl0001testABCDEF"
PRINCIPAL_ID = "00u1234567890abcdef"
RESOURCE_ID = "res0001testABCDEF"
REQUEST_ID = "req0001testABCDEF"
CONDITION_ID = "cond001testABCDEF"

PATCH_LABELS = "okta_mcp_server.tools.governance.labels.get_okta_client"
PATCH_ENTITLEMENTS = "okta_mcp_server.tools.governance.entitlements.get_okta_client"
PATCH_ACCESS_REQUESTS = "okta_mcp_server.tools.governance.access_requests.get_okta_client"


def _make_executor(no_content=False, execute_error=None):
    executor = AsyncMock()
    executor.create_request.return_value = (MagicMock(), None)
    if execute_error:
        executor.execute.return_value = (MagicMock(), execute_error)
    elif no_content:
        executor.execute.return_value = (None, None)
    else:
        resp = MagicMock()
        resp.get_body.return_value = None
        executor.execute.return_value = (resp, None)
    return executor


def _make_client(no_content=True, execute_error=None):
    executor = _make_executor(no_content=no_content, execute_error=execute_error)
    client = MagicMock()
    client.get_request_executor.return_value = executor
    client.get_base_url.return_value = "https://test.okta.com"
    return client


# ---------------------------------------------------------------------------
# delete_governance_label — elicitation flows
# ---------------------------------------------------------------------------

class TestDeleteGovernanceLabelElicitation:
    @pytest.mark.asyncio
    @patch(PATCH_LABELS)
    async def test_accept_confirmed_deletes(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await delete_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID)

        assert "deleted successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_accept_not_confirmed_cancels(self, ctx_elicit_accept_false):
        result = await delete_governance_label(ctx=ctx_elicit_accept_false, label_id=LABEL_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_decline_cancels(self, ctx_elicit_decline):
        result = await delete_governance_label(ctx=ctx_elicit_decline, label_id=LABEL_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_cancels(self, ctx_elicit_cancel):
        result = await delete_governance_label(ctx=ctx_elicit_cancel, label_id=LABEL_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_LABELS)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Label still has assigned values")
        mock_get_client.return_value = client

        result = await delete_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_LABELS)
    async def test_exception_during_delete(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await delete_governance_label(ctx=ctx_elicit_accept_true, label_id=LABEL_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# delete_governance_label — fallback flows (returns fallback_payload)
# ---------------------------------------------------------------------------

class TestDeleteGovernanceLabelFallback:
    @pytest.mark.asyncio
    async def test_no_elicitation_returns_fallback_payload(self, ctx_no_elicitation):
        result = await delete_governance_label(ctx=ctx_no_elicitation, label_id=LABEL_ID)

        assert result["confirmation_required"] is True
        assert LABEL_ID in result["message"]
        assert result["label_id"] == LABEL_ID

    @pytest.mark.asyncio
    async def test_exception_returns_fallback_payload(self, ctx_elicit_exception):
        result = await delete_governance_label(ctx=ctx_elicit_exception, label_id=LABEL_ID)

        assert result["confirmation_required"] is True
        assert LABEL_ID in result["message"]

    @pytest.mark.asyncio
    async def test_mcp_error_method_not_found_returns_fallback(self, ctx_elicit_mcp_error_method_not_found):
        result = await delete_governance_label(ctx=ctx_elicit_mcp_error_method_not_found, label_id=LABEL_ID)

        assert result["confirmation_required"] is True
        assert LABEL_ID in result["message"]


# ---------------------------------------------------------------------------
# revoke_principal_access — elicitation flows
# ---------------------------------------------------------------------------

class TestRevokePrincipalAccessElicitation:
    @pytest.mark.asyncio
    @patch(PATCH_ENTITLEMENTS)
    async def test_accept_confirmed_revokes(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await revoke_principal_access(
            ctx=ctx_elicit_accept_true,
            resource_id=RESOURCE_ID,
            principal_id=PRINCIPAL_ID,
        )

        assert "revoked" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_accept_not_confirmed_cancels(self, ctx_elicit_accept_false):
        result = await revoke_principal_access(
            ctx=ctx_elicit_accept_false,
            resource_id=RESOURCE_ID,
            principal_id=PRINCIPAL_ID,
        )

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_decline_cancels(self, ctx_elicit_decline):
        result = await revoke_principal_access(
            ctx=ctx_elicit_decline,
            resource_id=RESOURCE_ID,
            principal_id=PRINCIPAL_ID,
        )

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_cancels(self, ctx_elicit_cancel):
        result = await revoke_principal_access(
            ctx=ctx_elicit_cancel,
            resource_id=RESOURCE_ID,
            principal_id=PRINCIPAL_ID,
        )

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_ENTITLEMENTS)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Principal access not found")
        mock_get_client.return_value = client

        result = await revoke_principal_access(
            ctx=ctx_elicit_accept_true,
            resource_id=RESOURCE_ID,
            principal_id=PRINCIPAL_ID,
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_ENTITLEMENTS)
    async def test_exception_during_revoke(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await revoke_principal_access(
            ctx=ctx_elicit_accept_true,
            resource_id=RESOURCE_ID,
            principal_id=PRINCIPAL_ID,
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# revoke_principal_access — fallback flows (returns fallback_payload)
# ---------------------------------------------------------------------------

class TestRevokePrincipalAccessFallback:
    @pytest.mark.asyncio
    async def test_no_elicitation_returns_fallback_payload(self, ctx_no_elicitation):
        result = await revoke_principal_access(
            ctx=ctx_no_elicitation,
            resource_id=RESOURCE_ID,
            principal_id=PRINCIPAL_ID,
        )

        assert result["confirmation_required"] is True
        assert PRINCIPAL_ID in result["message"]
        assert result["principal_id"] == PRINCIPAL_ID
        assert result["resource_id"] == RESOURCE_ID

    @pytest.mark.asyncio
    async def test_exception_returns_fallback_payload(self, ctx_elicit_exception):
        result = await revoke_principal_access(
            ctx=ctx_elicit_exception,
            resource_id=RESOURCE_ID,
            principal_id=PRINCIPAL_ID,
        )

        assert result["confirmation_required"] is True
        assert PRINCIPAL_ID in result["message"]

    @pytest.mark.asyncio
    async def test_mcp_error_method_not_found_returns_fallback(self, ctx_elicit_mcp_error_method_not_found):
        result = await revoke_principal_access(
            ctx=ctx_elicit_mcp_error_method_not_found,
            resource_id=RESOURCE_ID,
            principal_id=PRINCIPAL_ID,
        )

        assert result["confirmation_required"] is True


# ---------------------------------------------------------------------------
# cancel_access_request — elicitation flows
# ---------------------------------------------------------------------------

class TestCancelAccessRequestElicitation:
    @pytest.mark.asyncio
    @patch(PATCH_ACCESS_REQUESTS)
    async def test_accept_confirmed_cancels(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await cancel_access_request(ctx=ctx_elicit_accept_true, request_id=REQUEST_ID)

        assert "cancelled" in result["message"].lower() or "canceled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_accept_not_confirmed_cancels(self, ctx_elicit_accept_false):
        result = await cancel_access_request(ctx=ctx_elicit_accept_false, request_id=REQUEST_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_decline_cancels(self, ctx_elicit_decline):
        result = await cancel_access_request(ctx=ctx_elicit_decline, request_id=REQUEST_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_cancels(self, ctx_elicit_cancel):
        result = await cancel_access_request(ctx=ctx_elicit_cancel, request_id=REQUEST_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_ACCESS_REQUESTS)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Request not found")
        mock_get_client.return_value = client

        result = await cancel_access_request(ctx=ctx_elicit_accept_true, request_id=REQUEST_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_ACCESS_REQUESTS)
    async def test_exception_during_cancel(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await cancel_access_request(ctx=ctx_elicit_accept_true, request_id=REQUEST_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# cancel_access_request — fallback flows
# ---------------------------------------------------------------------------

class TestCancelAccessRequestFallback:
    @pytest.mark.asyncio
    async def test_no_elicitation_returns_fallback_payload(self, ctx_no_elicitation):
        result = await cancel_access_request(ctx=ctx_no_elicitation, request_id=REQUEST_ID)

        assert result["confirmation_required"] is True
        assert REQUEST_ID in result["message"]
        assert result["request_id"] == REQUEST_ID

    @pytest.mark.asyncio
    async def test_exception_returns_fallback_payload(self, ctx_elicit_exception):
        result = await cancel_access_request(ctx=ctx_elicit_exception, request_id=REQUEST_ID)

        assert result["confirmation_required"] is True
        assert REQUEST_ID in result["message"]

    @pytest.mark.asyncio
    async def test_mcp_error_method_not_found_returns_fallback(self, ctx_elicit_mcp_error_method_not_found):
        result = await cancel_access_request(
            ctx=ctx_elicit_mcp_error_method_not_found, request_id=REQUEST_ID
        )

        assert result["confirmation_required"] is True


# ---------------------------------------------------------------------------
# delete_request_condition — elicitation flows
# ---------------------------------------------------------------------------

class TestDeleteRequestConditionElicitation:
    @pytest.mark.asyncio
    @patch(PATCH_ACCESS_REQUESTS)
    async def test_accept_confirmed_deletes(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await delete_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "deleted successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_accept_not_confirmed_cancels(self, ctx_elicit_accept_false):
        result = await delete_request_condition(
            ctx=ctx_elicit_accept_false, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_decline_cancels(self, ctx_elicit_decline):
        result = await delete_request_condition(
            ctx=ctx_elicit_decline, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_cancels(self, ctx_elicit_cancel):
        result = await delete_request_condition(
            ctx=ctx_elicit_cancel, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_ACCESS_REQUESTS)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Condition not found")
        mock_get_client.return_value = client

        result = await delete_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_ACCESS_REQUESTS)
    async def test_exception_during_delete(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await delete_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# delete_request_condition — fallback flows
# ---------------------------------------------------------------------------

class TestDeleteRequestConditionFallback:
    @pytest.mark.asyncio
    async def test_no_elicitation_returns_fallback_payload(self, ctx_no_elicitation):
        result = await delete_request_condition(
            ctx=ctx_no_elicitation, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert result["confirmation_required"] is True
        assert CONDITION_ID in result["message"]
        assert result["condition_id"] == CONDITION_ID
        assert result["resource_id"] == RESOURCE_ID

    @pytest.mark.asyncio
    async def test_exception_returns_fallback_payload(self, ctx_elicit_exception):
        result = await delete_request_condition(
            ctx=ctx_elicit_exception, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert result["confirmation_required"] is True
        assert CONDITION_ID in result["message"]

    @pytest.mark.asyncio
    async def test_mcp_error_method_not_found_returns_fallback(self, ctx_elicit_mcp_error_method_not_found):
        result = await delete_request_condition(
            ctx=ctx_elicit_mcp_error_method_not_found, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert result["confirmation_required"] is True
