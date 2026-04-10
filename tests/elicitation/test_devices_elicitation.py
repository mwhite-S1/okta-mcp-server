# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for device elicitation flows: deactivate, suspend, and delete."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from okta_mcp_server.tools.devices.devices import (
    deactivate_device,
    delete_device,
    suspend_device,
)


DEVICE_ID = "guo1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.devices.devices.get_okta_client"


def _make_executor(no_content=False, execute_error=None):
    """Return an async mock executor for 204 lifecycle calls."""
    from unittest.mock import AsyncMock
    executor = AsyncMock()
    executor.create_request.return_value = (MagicMock(), None)

    if execute_error:
        executor.execute.return_value = (None, None, execute_error)
    else:
        executor.execute.return_value = (MagicMock(), None, None)

    return executor


def _make_device_client(no_content=True, execute_error=None):
    executor = _make_executor(no_content=no_content, execute_error=execute_error)
    client = MagicMock()
    client.get_request_executor.return_value = executor
    client.get_base_url.return_value = "https://test.okta.com"
    return client


# ---------------------------------------------------------------------------
# deactivate_device — elicitation flows (auto_confirm_on_fallback=True)
# ---------------------------------------------------------------------------

class TestDeactivateDeviceElicitation:
    """Tests for deactivate_device when the client supports elicitation."""

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_accept_confirmed_deactivates(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        result = await deactivate_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "deactivated successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_accept_not_confirmed_cancels(self, ctx_elicit_accept_false):
        result = await deactivate_device(ctx=ctx_elicit_accept_false, device_id=DEVICE_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_decline_cancels(self, ctx_elicit_decline):
        result = await deactivate_device(ctx=ctx_elicit_decline, device_id=DEVICE_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_cancels(self, ctx_elicit_cancel):
        result = await deactivate_device(ctx=ctx_elicit_cancel, device_id=DEVICE_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(execute_error="Device cannot be deactivated")
        mock_get_client.return_value = client

        result = await deactivate_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception_during_deactivation(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await deactivate_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# deactivate_device — fallback flows (auto_confirm_on_fallback=True)
# ---------------------------------------------------------------------------

class TestDeactivateDeviceFallback:
    """Tests for deactivate_device when elicitation is unavailable.

    With auto_confirm_on_fallback=True the operation proceeds automatically.
    """

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_fallback_auto_confirms(self, mock_get_client, ctx_no_elicitation):
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        result = await deactivate_device(ctx=ctx_no_elicitation, device_id=DEVICE_ID)

        assert "deactivated successfully" in result["message"]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception_fallback_auto_confirms(self, mock_get_client, ctx_elicit_exception):
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        result = await deactivate_device(ctx=ctx_elicit_exception, device_id=DEVICE_ID)

        assert "deactivated successfully" in result["message"]


# ---------------------------------------------------------------------------
# suspend_device — elicitation flows (auto_confirm_on_fallback=True)
# ---------------------------------------------------------------------------

class TestSuspendDeviceElicitation:
    """Tests for suspend_device when the client supports elicitation."""

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_accept_confirmed_suspends(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        result = await suspend_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "suspended successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_accept_not_confirmed_cancels(self, ctx_elicit_accept_false):
        result = await suspend_device(ctx=ctx_elicit_accept_false, device_id=DEVICE_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_decline_cancels(self, ctx_elicit_decline):
        result = await suspend_device(ctx=ctx_elicit_decline, device_id=DEVICE_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_cancels(self, ctx_elicit_cancel):
        result = await suspend_device(ctx=ctx_elicit_cancel, device_id=DEVICE_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(execute_error="Device already suspended")
        mock_get_client.return_value = client

        result = await suspend_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception_during_suspension(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await suspend_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# suspend_device — fallback flows (auto_confirm_on_fallback=True)
# ---------------------------------------------------------------------------

class TestSuspendDeviceFallback:
    """Tests for suspend_device when elicitation is unavailable."""

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_fallback_auto_confirms(self, mock_get_client, ctx_no_elicitation):
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        result = await suspend_device(ctx=ctx_no_elicitation, device_id=DEVICE_ID)

        assert "suspended successfully" in result["message"]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception_fallback_auto_confirms(self, mock_get_client, ctx_elicit_exception):
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        result = await suspend_device(ctx=ctx_elicit_exception, device_id=DEVICE_ID)

        assert "suspended successfully" in result["message"]


# ---------------------------------------------------------------------------
# delete_device — elicitation flows (NO auto_confirm_on_fallback; fallback_payload)
# ---------------------------------------------------------------------------

class TestDeleteDeviceElicitation:
    """Tests for delete_device when the client supports elicitation."""

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_accept_confirmed_deletes(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        result = await delete_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "deleted successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_accept_not_confirmed_cancels(self, ctx_elicit_accept_false):
        result = await delete_device(ctx=ctx_elicit_accept_false, device_id=DEVICE_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_decline_cancels(self, ctx_elicit_decline):
        result = await delete_device(ctx=ctx_elicit_decline, device_id=DEVICE_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_cancels(self, ctx_elicit_cancel):
        result = await delete_device(ctx=ctx_elicit_cancel, device_id=DEVICE_ID)

        assert "cancelled" in result["message"].lower()

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(execute_error="Device must be deactivated first")
        mock_get_client.return_value = client

        result = await delete_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception_during_delete(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await delete_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# delete_device — fallback flows (returns fallback_payload, no auto-confirm)
# ---------------------------------------------------------------------------

class TestDeleteDeviceFallback:
    """Tests for delete_device when elicitation is unavailable.

    Unlike deactivate/suspend, delete_device does NOT auto-confirm on fallback.
    It returns a structured fallback payload requiring explicit confirmation.
    """

    @pytest.mark.asyncio
    async def test_no_elicitation_returns_fallback_payload(self, ctx_no_elicitation):
        result = await delete_device(ctx=ctx_no_elicitation, device_id=DEVICE_ID)

        assert result["confirmation_required"] is True
        assert DEVICE_ID in result["message"]
        assert DEVICE_ID == result["device_id"]

    @pytest.mark.asyncio
    async def test_exception_returns_fallback_payload(self, ctx_elicit_exception):
        result = await delete_device(ctx=ctx_elicit_exception, device_id=DEVICE_ID)

        assert result["confirmation_required"] is True
        assert DEVICE_ID in result["message"]

    @pytest.mark.asyncio
    async def test_mcp_error_method_not_found_returns_fallback(self, ctx_elicit_mcp_error_method_not_found):
        result = await delete_device(ctx=ctx_elicit_mcp_error_method_not_found, device_id=DEVICE_ID)

        assert result["confirmation_required"] is True
        assert DEVICE_ID in result["message"]
