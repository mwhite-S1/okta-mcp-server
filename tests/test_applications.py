# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for all application tools: list, get, create, update, activate."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.applications.applications import (
    activate_application,
    create_application,
    get_application,
    list_applications,
    update_application,
)


APP_ID = "0oa1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.applications.applications.get_okta_client"
PATCH_EXECUTE = "okta_mcp_server.tools.applications.applications._execute"

APP_DICT = {"id": APP_ID, "label": "Test App", "status": "ACTIVE", "signOnMode": "SAML_2_0"}


def _make_app(app_id=APP_ID, label="Test App", status="ACTIVE"):
    app = MagicMock()
    app.id = app_id
    app.label = label
    app.status = status
    app.as_dict.return_value = {"id": app_id, "label": label, "status": status}
    return app


def _make_response(link_header=None):
    """Build a mock HTTP response; headers.get returns the link header or ''."""
    response = MagicMock()
    response.headers.get = MagicMock(return_value=link_header or "")
    return response


# ---------------------------------------------------------------------------
# list_applications
# ---------------------------------------------------------------------------

class TestListApplications:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_returns_apps(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (_make_response(), [APP_DICT], None)

        result = await list_applications(ctx=ctx_elicit_accept_true)

        assert isinstance(result, dict)
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == APP_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_empty_result(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (_make_response(), None, None)

        result = await list_applications(ctx=ctx_elicit_accept_true)

        assert isinstance(result, dict)
        assert result["items"] == []
        assert result["total_fetched"] == 0
        assert result["has_more"] is False

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_api_error(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (None, None, "API Error")

        result = await list_applications(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_applications(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_limit_clamped_below_minimum(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (_make_response(), None, None)

        await list_applications(ctx=ctx_elicit_accept_true, limit=5)

        # Path should contain limit=20 (clamped from 5)
        call_args = mock_execute.call_args
        path_arg = call_args[0][2]  # positional: (client, method, path)
        assert "limit=20" in path_arg, f"Expected limit=20 in path, got: {path_arg}"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_limit_clamped_above_maximum(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (_make_response(), None, None)

        await list_applications(ctx=ctx_elicit_accept_true, limit=500)

        call_args = mock_execute.call_args
        path_arg = call_args[0][2]
        assert "limit=100" in path_arg, f"Expected limit=100 in path, got: {path_arg}"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_query_param_forwarded(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (_make_response(), None, None)

        await list_applications(ctx=ctx_elicit_accept_true, q="Salesforce")

        call_args = mock_execute.call_args
        path_arg = call_args[0][2]
        assert "q=Salesforce" in path_arg, f"Expected q=Salesforce in path, got: {path_arg}"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_multiple_apps_returned(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        apps = [{"id": f"0oa{i}", "label": f"App {i}", "status": "ACTIVE"} for i in range(3)]
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (_make_response(), apps, None)

        result = await list_applications(ctx=ctx_elicit_accept_true)

        assert isinstance(result, dict)
        assert len(result["items"]) == 3
        assert result["total_fetched"] == 3

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_pagination_metadata_no_next(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        """When no Link header present, has_more is False and next_cursor is None."""
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (_make_response(), [APP_DICT], None)

        result = await list_applications(ctx=ctx_elicit_accept_true)

        assert result["has_more"] is False
        assert result["next_cursor"] is None

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_pagination_metadata_with_next(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        """When Link header with rel=next is present, has_more is True with cursor."""
        link = '<https://example.okta.com/api/v1/apps?after=abc123>; rel="next"'
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (_make_response(link_header=link), [APP_DICT], None)

        result = await list_applications(ctx=ctx_elicit_accept_true)

        assert result["has_more"] is True
        assert result["next_cursor"] == "abc123"


# ---------------------------------------------------------------------------
# get_application
# ---------------------------------------------------------------------------

class TestGetApplication:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_returns_app(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (_make_response(), APP_DICT, None)

        result = await get_application(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert result is not None
        assert isinstance(result, list)
        assert result[0]["id"] == APP_ID

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await get_application(ctx=ctx_elicit_accept_true, app_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_api_error(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (None, None, "App not found")

        result = await get_application(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_application(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_expand_param_forwarded(self, mock_execute, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.return_value = AsyncMock()
        mock_execute.return_value = (_make_response(), APP_DICT, None)

        await get_application(ctx=ctx_elicit_accept_true, app_id=APP_ID, expand="user/groups")

        call_args = mock_execute.call_args
        path_arg = call_args[0][2]
        assert "expand=user" in path_arg, f"Expected expand in path, got: {path_arg}"


# ---------------------------------------------------------------------------
# create_application
# ---------------------------------------------------------------------------

class TestCreateApplication:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_app(self, mock_get_client, ctx_elicit_accept_true):
        app = _make_app()
        client = AsyncMock()
        client.create_application.return_value = (app, None, None)
        mock_get_client.return_value = client

        app_config = {
            "name": "template_saml_2_0",
            "label": "Test App",
            "signOnMode": "SAML_2_0",
        }
        result = await create_application(ctx=ctx_elicit_accept_true, app_config=app_config)

        assert result["id"] == APP_ID
        client.create_application.assert_awaited_once_with(app_config, activate=True)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_app_inactive(self, mock_get_client, ctx_elicit_accept_true):
        app = _make_app(status="INACTIVE")
        client = AsyncMock()
        client.create_application.return_value = (app, None, None)
        mock_get_client.return_value = client

        result = await create_application(ctx=ctx_elicit_accept_true, app_config={}, activate=False)

        client.create_application.assert_awaited_once_with({}, activate=False)
        assert result["status"] == "INACTIVE"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_application.return_value = (None, None, "Invalid app config")
        mock_get_client.return_value = client

        result = await create_application(ctx=ctx_elicit_accept_true, app_config={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_application(ctx=ctx_elicit_accept_true, app_config={})

        assert "error" in result


# ---------------------------------------------------------------------------
# update_application
# ---------------------------------------------------------------------------

class TestUpdateApplication:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_app(self, mock_get_client, ctx_elicit_accept_true):
        updated_app = _make_app(label="Updated App")
        updated_app.as_dict.return_value = {"id": APP_ID, "label": "Updated App", "status": "ACTIVE"}
        client = AsyncMock()
        client.update_application.return_value = (updated_app, None, None)
        mock_get_client.return_value = client

        app_config = {"label": "Updated App"}
        result = await update_application(ctx=ctx_elicit_accept_true, app_id=APP_ID, app_config=app_config)

        assert result["label"] == "Updated App"
        client.update_application.assert_awaited_once_with(APP_ID, app_config)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await update_application(ctx=ctx_elicit_accept_true, app_id="../bad", app_config={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_application.return_value = (None, None, "App not found")
        mock_get_client.return_value = client

        result = await update_application(ctx=ctx_elicit_accept_true, app_id=APP_ID, app_config={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await update_application(ctx=ctx_elicit_accept_true, app_id=APP_ID, app_config={})

        assert "error" in result


# ---------------------------------------------------------------------------
# activate_application
# ---------------------------------------------------------------------------

class TestActivateApplication:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_activates_app(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_application.return_value = (None, None)
        mock_get_client.return_value = client

        result = await activate_application(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "activated successfully" in result[0]
        client.activate_application.assert_awaited_once_with(APP_ID)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await activate_application(ctx=ctx_elicit_accept_true, app_id="bad/id")

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_application.return_value = (None, "Already active")
        mock_get_client.return_value = client

        result = await activate_application(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await activate_application(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "Exception" in result[0]


# ---------------------------------------------------------------------------
# Application lifecycle: create → get → update → activate
# ---------------------------------------------------------------------------

class TestApplicationLifecycle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    @patch(PATCH_EXECUTE, new_callable=AsyncMock)
    async def test_create_then_get_then_update_then_activate(
        self, mock_execute, mock_get_client, ctx_elicit_accept_true
    ):
        created_app = _make_app(app_id="0oanew123", label="New App")
        updated_app = _make_app(app_id="0oanew123", label="Updated App")
        updated_app.as_dict.return_value = {"id": "0oanew123", "label": "Updated App", "status": "ACTIVE"}

        client = AsyncMock()
        client.create_application.return_value = (created_app, None, None)
        client.update_application.return_value = (updated_app, None, None)
        client.activate_application.return_value = (None, None)
        mock_get_client.return_value = client

        # _execute used by get_application
        mock_execute.return_value = (
            _make_response(),
            {"id": "0oanew123", "label": "New App", "status": "ACTIVE"},
            None,
        )

        # Step 1: create
        app_config = {"name": "template_swa", "label": "New App", "signOnMode": "AUTO_LOGIN"}
        create_result = await create_application(ctx=ctx_elicit_accept_true, app_config=app_config)
        assert create_result["id"] == "0oanew123"

        # Step 2: get
        get_result = await get_application(ctx=ctx_elicit_accept_true, app_id="0oanew123")
        assert get_result[0]["id"] == "0oanew123"

        # Step 3: update
        update_result = await update_application(
            ctx=ctx_elicit_accept_true, app_id="0oanew123", app_config={"label": "Updated App"}
        )
        assert update_result["label"] == "Updated App"

        # Step 4: activate
        activate_result = await activate_application(ctx=ctx_elicit_accept_true, app_id="0oanew123")
        assert "activated successfully" in activate_result[0]
