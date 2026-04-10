# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for non-destructive device tools: list, get, list_device_users, activate, unsuspend."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.devices.devices import (
    activate_device,
    get_device,
    list_device_users,
    list_devices,
    unsuspend_device,
)


DEVICE_ID = "guo1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.devices.devices.get_okta_client"

DEVICE_DICT = {
    "id": DEVICE_ID,
    "status": "ACTIVE",
    "profile": {"displayName": "Test MacBook", "platform": "MACOS"},
}


def _make_executor(body=None, execute_error=None, create_error=None, no_content=False):
    """Create a mock request executor for device API calls.

    Parameters:
        body: The response body (dict or list) for successful calls with content.
        execute_error: Error to return from execute().
        create_error: Error to return from create_request().
        no_content: If True, simulate 204 No Content (response=None, error=None).
    """
    executor = AsyncMock()

    if create_error:
        executor.create_request.return_value = (None, create_error)
    else:
        executor.create_request.return_value = (MagicMock(), None)

    if execute_error:
        executor.execute.return_value = (None, None, execute_error)
    else:
        executor.execute.return_value = (MagicMock(), body, None)

    return executor


def _make_device_client(body=None, execute_error=None, create_error=None, no_content=False):
    """Create a mock Okta client that routes through the request executor."""
    executor = _make_executor(
        body=body,
        execute_error=execute_error,
        create_error=create_error,
        no_content=no_content,
    )
    client = MagicMock()
    client.get_request_executor.return_value = executor
    client.get_base_url.return_value = "https://test.okta.com"
    return client


# ---------------------------------------------------------------------------
# list_devices
# ---------------------------------------------------------------------------

class TestListDevices:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_devices(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(body=[DEVICE_DICT])
        mock_get_client.return_value = client

        result = await list_devices(ctx=ctx_elicit_accept_true)

        assert len(result) == 1
        assert result[0]["id"] == DEVICE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(body=None)
        mock_get_client.return_value = client

        result = await list_devices(ctx=ctx_elicit_accept_true)

        assert result == []

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(execute_error="API Error: Forbidden")
        mock_get_client.return_value = client

        result = await list_devices(ctx=ctx_elicit_accept_true)

        assert "error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_devices(ctx=ctx_elicit_accept_true)

        assert "error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_limit_clamped_above_maximum(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(body=[])
        mock_get_client.return_value = client

        # limit=300 exceeds max of 200; should be clamped
        await list_devices(ctx=ctx_elicit_accept_true, limit=300)
        executor = client.get_request_executor.return_value
        url_arg = executor.create_request.call_args[0][1]
        assert "limit=200" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_search_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(body=[])
        mock_get_client.return_value = client

        await list_devices(ctx=ctx_elicit_accept_true, search='status eq "ACTIVE"')
        executor = client.get_request_executor.return_value
        url_arg = executor.create_request.call_args[0][1]
        assert "search=" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_expand_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(body=[DEVICE_DICT])
        mock_get_client.return_value = client

        await list_devices(ctx=ctx_elicit_accept_true, expand="user")
        executor = client.get_request_executor.return_value
        url_arg = executor.create_request.call_args[0][1]
        assert "expand=user" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_multiple_devices_returned(self, mock_get_client, ctx_elicit_accept_true):
        devices = [{"id": f"guo{i}", "status": "ACTIVE"} for i in range(3)]
        client = _make_device_client(body=devices)
        mock_get_client.return_value = client

        result = await list_devices(ctx=ctx_elicit_accept_true)

        assert len(result) == 3


# ---------------------------------------------------------------------------
# get_device
# ---------------------------------------------------------------------------

class TestGetDevice:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_device(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(body=DEVICE_DICT)
        mock_get_client.return_value = client

        result = await get_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert result["id"] == DEVICE_ID

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await get_device(ctx=ctx_elicit_accept_true, device_id="bad/id")

        assert "error" in result or "Error" in str(result)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(execute_error="Device not found")
        mock_get_client.return_value = client

        result = await get_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path_used(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(body=DEVICE_DICT)
        mock_get_client.return_value = client

        await get_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        executor = client.get_request_executor.return_value
        url_arg = executor.create_request.call_args[0][1]
        assert DEVICE_ID in url_arg


# ---------------------------------------------------------------------------
# list_device_users
# ---------------------------------------------------------------------------

class TestListDeviceUsers:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_users(self, mock_get_client, ctx_elicit_accept_true):
        users = [{"user": {"id": "00u123", "profile": {"login": "test@example.com"}}}]
        client = _make_device_client(body=users)
        mock_get_client.return_value = client

        result = await list_device_users(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert len(result) == 1

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(body=None)
        mock_get_client.return_value = client

        result = await list_device_users(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert result == []

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(execute_error="Device not found")
        mock_get_client.return_value = client

        result = await list_device_users(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_device_users(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result[0]

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await list_device_users(ctx=ctx_elicit_accept_true, device_id="bad/id")

        assert "error" in result[0] or "Error" in str(result[0])


# ---------------------------------------------------------------------------
# activate_device
# ---------------------------------------------------------------------------

class TestActivateDevice:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_activates_device(self, mock_get_client, ctx_elicit_accept_true):
        # Lifecycle endpoints return 204 No Content
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        result = await activate_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "activated successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await activate_device(ctx=ctx_elicit_accept_true, device_id="bad/id")

        assert "error" in result or "Error" in str(result)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(execute_error="Device cannot be activated")
        mock_get_client.return_value = client

        result = await activate_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await activate_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_lifecycle_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        await activate_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        executor = client.get_request_executor.return_value
        method_arg = executor.create_request.call_args[0][0]
        url_arg = executor.create_request.call_args[0][1]
        assert method_arg == "POST"
        assert "activate" in url_arg
        assert DEVICE_ID in url_arg


# ---------------------------------------------------------------------------
# unsuspend_device
# ---------------------------------------------------------------------------

class TestUnsuspendDevice:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_unsuspends_device(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        result = await unsuspend_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "unsuspended successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await unsuspend_device(ctx=ctx_elicit_accept_true, device_id="bad/id")

        assert "error" in result or "Error" in str(result)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(execute_error="Device not suspended")
        mock_get_client.return_value = client

        result = await unsuspend_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await unsuspend_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_lifecycle_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_device_client(no_content=True)
        mock_get_client.return_value = client

        await unsuspend_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)

        executor = client.get_request_executor.return_value
        method_arg = executor.create_request.call_args[0][0]
        url_arg = executor.create_request.call_args[0][1]
        assert method_arg == "POST"
        assert "unsuspend" in url_arg
        assert DEVICE_ID in url_arg


# ---------------------------------------------------------------------------
# Device read lifecycle: list → get → list_device_users
# ---------------------------------------------------------------------------

class TestDeviceReadLifecycle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_list_get_list_users(self, mock_get_client, ctx_elicit_accept_true):
        device_list = [DEVICE_DICT]
        device_users = [{"user": {"id": "00u123", "profile": {"login": "user@example.com"}}}]

        # Each call gets a fresh executor mock to return the appropriate body
        list_client = _make_device_client(body=device_list)
        get_client = _make_device_client(body=DEVICE_DICT)
        users_client = _make_device_client(body=device_users)
        # Return a different client on each get_okta_client call
        mock_get_client.side_effect = [list_client, get_client, users_client]

        # Step 1: list
        list_result = await list_devices(ctx=ctx_elicit_accept_true)
        assert len(list_result) == 1
        assert list_result[0]["id"] == DEVICE_ID

        # Step 2: get
        get_result = await get_device(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)
        assert get_result["id"] == DEVICE_ID

        # Step 3: list device users
        users_result = await list_device_users(ctx=ctx_elicit_accept_true, device_id=DEVICE_ID)
        assert len(users_result) == 1
