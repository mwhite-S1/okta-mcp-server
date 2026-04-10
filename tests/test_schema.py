# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for schema tools: user schema, group schema, application user schema."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.schema.schema import (
    get_application_user_schema,
    get_group_schema,
    get_user_schema,
    update_application_user_profile,
    update_group_schema,
    update_user_profile,
)


APP_ID = "0oa1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.schema.schema.get_okta_client"

CUSTOM_PROPERTIES = {
    "department": {
        "title": "Department",
        "type": "string",
    }
}


def _make_schema(schema_id="default"):
    s = MagicMock()
    s.id = schema_id
    s.to_dict.return_value = {
        "id": schema_id,
        "name": "user",
        "definitions": {"custom": {"properties": {}}},
    }
    return s


# ---------------------------------------------------------------------------
# get_user_schema
# ---------------------------------------------------------------------------

class TestGetUserSchema:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        schema = _make_schema()
        client = AsyncMock()
        client.get_user_schema.return_value = (schema, None, None)
        mock_get_client.return_value = client

        result = await get_user_schema(ctx=ctx_elicit_accept_true)

        client.get_user_schema.assert_called_once_with("default")
        assert result["id"] == "default"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_user_schema.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await get_user_schema(ctx=ctx_elicit_accept_true)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_user_schema.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await get_user_schema(ctx=ctx_elicit_accept_true)
        assert "error" in result


# ---------------------------------------------------------------------------
# update_user_profile
# ---------------------------------------------------------------------------

class TestUpdateUserProfile:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        schema = _make_schema()
        client = AsyncMock()
        client.update_user_profile.return_value = (schema, None, None)
        mock_get_client.return_value = client

        result = await update_user_profile(ctx=ctx_elicit_accept_true, properties=CUSTOM_PROPERTIES)

        call_args = client.update_user_profile.call_args
        assert call_args[0][0] == "default"
        body = call_args[0][1]
        assert "definitions" in body
        assert body["definitions"]["custom"]["properties"] == CUSTOM_PROPERTIES
        assert result["id"] == "default"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_user_profile.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await update_user_profile(ctx=ctx_elicit_accept_true, properties=CUSTOM_PROPERTIES)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_user_profile.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await update_user_profile(ctx=ctx_elicit_accept_true, properties=CUSTOM_PROPERTIES)
        assert "error" in result


# ---------------------------------------------------------------------------
# get_group_schema
# ---------------------------------------------------------------------------

class TestGetGroupSchema:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        schema = _make_schema()
        client = AsyncMock()
        client.get_group_schema.return_value = (schema, None, None)
        mock_get_client.return_value = client

        result = await get_group_schema(ctx=ctx_elicit_accept_true)

        client.get_group_schema.assert_called_once_with()
        assert "id" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_group_schema.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await get_group_schema(ctx=ctx_elicit_accept_true)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_group_schema.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await get_group_schema(ctx=ctx_elicit_accept_true)
        assert "error" in result


# ---------------------------------------------------------------------------
# update_group_schema
# ---------------------------------------------------------------------------

class TestUpdateGroupSchema:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        schema = _make_schema()
        client = AsyncMock()
        client.update_group_schema.return_value = (schema, None, None)
        mock_get_client.return_value = client

        result = await update_group_schema(ctx=ctx_elicit_accept_true, properties=CUSTOM_PROPERTIES)

        call_args = client.update_group_schema.call_args
        body = call_args[0][0]
        assert body["definitions"]["custom"]["properties"] == CUSTOM_PROPERTIES
        assert "id" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_group_schema.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await update_group_schema(ctx=ctx_elicit_accept_true, properties=CUSTOM_PROPERTIES)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_group_schema.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await update_group_schema(ctx=ctx_elicit_accept_true, properties=CUSTOM_PROPERTIES)
        assert "error" in result


# ---------------------------------------------------------------------------
# get_application_user_schema
# ---------------------------------------------------------------------------

class TestGetApplicationUserSchema:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        schema = _make_schema(schema_id=APP_ID)
        client = AsyncMock()
        client.get_application_user_schema.return_value = (schema, None, None)
        mock_get_client.return_value = client

        result = await get_application_user_schema(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        client.get_application_user_schema.assert_called_once_with(APP_ID)
        assert result["id"] == APP_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_application_user_schema.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await get_application_user_schema(ctx=ctx_elicit_accept_true, app_id=APP_ID)
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_application_user_schema.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await get_application_user_schema(ctx=ctx_elicit_accept_true, app_id=APP_ID)
        assert "error" in result


# ---------------------------------------------------------------------------
# update_application_user_profile
# ---------------------------------------------------------------------------

class TestUpdateApplicationUserProfile:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        schema = _make_schema(schema_id=APP_ID)
        client = AsyncMock()
        client.update_application_user_profile.return_value = (schema, None, None)
        mock_get_client.return_value = client

        result = await update_application_user_profile(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            properties=CUSTOM_PROPERTIES,
        )

        call_args = client.update_application_user_profile.call_args
        assert call_args[0][0] == APP_ID
        body = call_args[0][1]
        assert body["definitions"]["custom"]["properties"] == CUSTOM_PROPERTIES
        assert result["id"] == APP_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_application_user_profile.return_value = (None, None, Exception("err"))
        mock_get_client.return_value = client

        result = await update_application_user_profile(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            properties=CUSTOM_PROPERTIES,
        )
        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_application_user_profile.side_effect = RuntimeError("boom")
        mock_get_client.return_value = client

        result = await update_application_user_profile(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            properties=CUSTOM_PROPERTIES,
        )
        assert "error" in result
