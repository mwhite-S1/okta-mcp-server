# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for governance delegate tools: org settings, delegates list, principal settings."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.governance.delegates import (
    get_governance_delegate_settings,
    get_principal_governance_settings,
    list_governance_delegates,
    update_principal_governance_settings,
)


PATCH_CLIENT = "okta_mcp_server.tools.governance.delegates.get_okta_client"

PRINCIPAL_ID = "00u1234567890abcdef"
DELEGATE_ID = "00u9876543210fedcba"

SETTINGS_DICT = {
    "allowEndUserDelegation": True,
    "restrictDelegationTypes": False,
}
DELEGATE_DICT = {
    "id": "del001",
    "principalId": PRINCIPAL_ID,
    "delegateId": DELEGATE_ID,
    "type": "ACCESS_CERTIFICATIONS",
}
PRINCIPAL_SETTINGS_DICT = {
    "principalId": PRINCIPAL_ID,
    "delegateAppointments": [DELEGATE_DICT],
}


def _make_executor(body=None, execute_error=None, no_content=False):
    executor = AsyncMock()
    executor.create_request.return_value = (MagicMock(), None)
    if execute_error:
        executor.execute.return_value = (None, None, execute_error)
    else:
        executor.execute.return_value = (MagicMock(), body, None)
    return executor


def _make_client(body=None, execute_error=None, no_content=False):
    executor = _make_executor(body=body, execute_error=execute_error, no_content=no_content)
    client = MagicMock()
    client.get_request_executor.return_value = executor
    client.get_base_url.return_value = "https://test.okta.com"
    return client


# ---------------------------------------------------------------------------
# get_governance_delegate_settings
# ---------------------------------------------------------------------------

class TestGetGovernanceDelegateSettings:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_settings(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=SETTINGS_DICT)
        mock_get_client.return_value = client

        result = await get_governance_delegate_settings(ctx=ctx_elicit_accept_true)

        assert result["allowEndUserDelegation"] is True

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=SETTINGS_DICT)
        mock_get_client.return_value = client

        await get_governance_delegate_settings(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/governance/api/v1/settings" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await get_governance_delegate_settings(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await get_governance_delegate_settings(ctx=ctx_elicit_accept_true)

        assert "error" in result


# ---------------------------------------------------------------------------
# list_governance_delegates
# ---------------------------------------------------------------------------

class TestListGovernanceDelegates:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_delegates(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [DELEGATE_DICT]})
        mock_get_client.return_value = client

        result = await list_governance_delegates(ctx=ctx_elicit_accept_true)

        assert result["items"][0]["principalId"] == PRINCIPAL_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_governance_delegates(ctx=ctx_elicit_accept_true)

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_principal_id_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_governance_delegates(ctx=ctx_elicit_accept_true, principal_id=PRINCIPAL_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "principalId" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_delegate_id_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_governance_delegates(ctx=ctx_elicit_accept_true, delegate_id=DELEGATE_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "delegateId" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_governance_delegates(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_governance_delegates(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_governance_delegates(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/governance/api/v1/delegates" in url_arg


# ---------------------------------------------------------------------------
# get_principal_governance_settings
# ---------------------------------------------------------------------------

class TestGetPrincipalGovernanceSettings:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_settings(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=PRINCIPAL_SETTINGS_DICT)
        mock_get_client.return_value = client

        result = await get_principal_governance_settings(ctx=ctx_elicit_accept_true, principal_id=PRINCIPAL_ID)

        assert result["principalId"] == PRINCIPAL_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_principal_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=PRINCIPAL_SETTINGS_DICT)
        mock_get_client.return_value = client

        await get_principal_governance_settings(ctx=ctx_elicit_accept_true, principal_id=PRINCIPAL_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert PRINCIPAL_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Principal not found")
        mock_get_client.return_value = client

        result = await get_principal_governance_settings(ctx=ctx_elicit_accept_true, principal_id=PRINCIPAL_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_principal_governance_settings(ctx=ctx_elicit_accept_true, principal_id=PRINCIPAL_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# update_principal_governance_settings
# ---------------------------------------------------------------------------

class TestUpdatePrincipalGovernanceSettings:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_settings(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=PRINCIPAL_SETTINGS_DICT)
        mock_get_client.return_value = client

        appointments = [{"type": "ACCESS_CERTIFICATIONS", "externalId": DELEGATE_ID}]
        result = await update_principal_governance_settings(
            ctx=ctx_elicit_accept_true,
            principal_id=PRINCIPAL_ID,
            delegate_appointments=appointments,
        )

        assert result["principalId"] == PRINCIPAL_ID
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "PATCH"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_payload_structure(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=PRINCIPAL_SETTINGS_DICT)
        mock_get_client.return_value = client

        appointments = [{"type": "ACCESS_REQUESTS", "externalId": DELEGATE_ID}]
        await update_principal_governance_settings(
            ctx=ctx_elicit_accept_true,
            principal_id=PRINCIPAL_ID,
            delegate_appointments=appointments,
        )

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["delegateAppointments"] == appointments

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_no_content_returns_message(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await update_principal_governance_settings(
            ctx=ctx_elicit_accept_true,
            principal_id=PRINCIPAL_ID,
            delegate_appointments=[],
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Invalid settings")
        mock_get_client.return_value = client

        result = await update_principal_governance_settings(
            ctx=ctx_elicit_accept_true,
            principal_id=PRINCIPAL_ID,
            delegate_appointments=[],
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await update_principal_governance_settings(
            ctx=ctx_elicit_accept_true,
            principal_id=PRINCIPAL_ID,
            delegate_appointments=[],
        )

        assert "error" in result
