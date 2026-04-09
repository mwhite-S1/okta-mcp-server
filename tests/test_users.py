# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for all user tools: list, get_profile_attributes, get, create, update."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.users.users import (
    create_user,
    get_user,
    get_user_profile_attributes,
    list_users,
    update_user,
)


USER_ID = "00u1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.users.users.get_okta_client"


def _make_user(user_id=USER_ID, email="test@example.com", login="test@example.com"):
    profile = MagicMock()
    profile.email = email
    profile.login = login
    user = MagicMock()
    user.id = user_id
    user.profile = profile
    return user


def _make_paginated_response(has_next=False):
    response = MagicMock()
    response.has_next.return_value = has_next
    return response


# ---------------------------------------------------------------------------
# list_users
# ---------------------------------------------------------------------------

class TestListUsers:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_users(self, mock_get_client, ctx_elicit_accept_true):
        user = _make_user()
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_users.return_value = ([user], response, None)
        mock_get_client.return_value = client

        result = await list_users(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 1
        assert result["has_more"] is False

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_users.return_value = ([], response, None)
        mock_get_client.return_value = client

        result = await list_users(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_users.return_value = (None, None, "API Error")
        mock_get_client.return_value = client

        result = await list_users(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_users(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_limit_clamped_below_minimum(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_users.return_value = ([], response, None)
        mock_get_client.return_value = client

        # limit=5 should be clamped to 20
        await list_users(ctx=ctx_elicit_accept_true, limit=5)
        call_params = client.list_users.call_args[0][0]
        assert call_params.get("limit") == "20"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_limit_clamped_above_maximum(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_users.return_value = ([], response, None)
        mock_get_client.return_value = client

        await list_users(ctx=ctx_elicit_accept_true, limit=500)
        call_params = client.list_users.call_args[0][0]
        assert call_params.get("limit") == "100"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_search_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_users.return_value = ([], response, None)
        mock_get_client.return_value = client

        await list_users(ctx=ctx_elicit_accept_true, search='profile.department eq "Engineering"')
        call_params = client.list_users.call_args[0][0]
        assert "search" in call_params


# ---------------------------------------------------------------------------
# get_user_profile_attributes
# ---------------------------------------------------------------------------

class TestGetUserProfileAttributes:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_profile_attributes(self, mock_get_client, ctx_elicit_accept_true):
        user = _make_user()
        user.profile = MagicMock(firstName="Test", lastName="User", email="test@example.com")
        client = AsyncMock()
        client.list_users.return_value = ([user], None, None)
        mock_get_client.return_value = client

        result = await get_user_profile_attributes(ctx=ctx_elicit_accept_true)

        assert result is not None

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_users.return_value = (None, None, "API Error")
        mock_get_client.return_value = client

        result = await get_user_profile_attributes(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_no_users_returns_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_users.return_value = ([], None, None)
        mock_get_client.return_value = client

        result = await get_user_profile_attributes(ctx=ctx_elicit_accept_true)

        assert result == []


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------

class TestGetUser:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_user(self, mock_get_client, ctx_elicit_accept_true):
        user = _make_user()
        client = AsyncMock()
        client.get_user.return_value = user
        mock_get_client.return_value = client

        result = await get_user(user_id=USER_ID, ctx=ctx_elicit_accept_true)

        assert result == [user]
        client.get_user.assert_awaited_once_with(USER_ID)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await get_user(user_id="bad/id", ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Not found")

        result = await get_user(user_id=USER_ID, ctx=ctx_elicit_accept_true)

        assert "Exception" in result[0]


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

class TestCreateUser:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_user(self, mock_get_client, ctx_elicit_accept_true):
        user = _make_user()
        client = AsyncMock()
        client.create_user.return_value = (user, None, None)
        mock_get_client.return_value = client

        profile = {"firstName": "Test", "lastName": "User", "email": "test@example.com", "login": "test@example.com"}
        result = await create_user(profile=profile, ctx=ctx_elicit_accept_true)

        assert result == [user]
        client.create_user.assert_awaited_once_with({"profile": profile})

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_user.return_value = (None, None, "Login already in use")
        mock_get_client.return_value = client

        result = await create_user(profile={"email": "dup@example.com"}, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_user(profile={}, ctx=ctx_elicit_accept_true)

        assert "Exception" in result[0]


# ---------------------------------------------------------------------------
# update_user
# ---------------------------------------------------------------------------

class TestUpdateUser:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_user(self, mock_get_client, ctx_elicit_accept_true):
        user = _make_user()
        client = AsyncMock()
        client.update_user.return_value = (user, None, None)
        mock_get_client.return_value = client

        profile = {"firstName": "Updated"}
        result = await update_user(user_id=USER_ID, profile=profile, ctx=ctx_elicit_accept_true)

        assert result == [user]
        client.update_user.assert_awaited_once_with(USER_ID, {"profile": profile})

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await update_user(user_id="../bad", profile={}, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_user.return_value = (None, None, "User not found")
        mock_get_client.return_value = client

        result = await update_user(user_id=USER_ID, profile={}, ctx=ctx_elicit_accept_true)

        assert "Error" in result[0]


# ---------------------------------------------------------------------------
# User lifecycle: create → get → update → (deactivate & delete tested in elicitation tests)
# ---------------------------------------------------------------------------

class TestUserLifecycle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_create_then_get_then_update(self, mock_get_client, ctx_elicit_accept_true):
        created_user = _make_user(user_id="00unew123", email="new@example.com")
        updated_user = _make_user(user_id="00unew123", email="new@example.com")
        updated_user.profile.firstName = "Updated"

        client = AsyncMock()
        client.create_user.return_value = (created_user, None, None)
        client.get_user.return_value = created_user
        client.update_user.return_value = (updated_user, None, None)
        mock_get_client.return_value = client

        # Step 1: create
        profile = {"firstName": "New", "lastName": "User", "email": "new@example.com", "login": "new@example.com"}
        create_result = await create_user(profile=profile, ctx=ctx_elicit_accept_true)
        assert create_result == [created_user]

        # Step 2: get
        get_result = await get_user(user_id="00unew123", ctx=ctx_elicit_accept_true)
        assert get_result == [created_user]

        # Step 3: update
        update_result = await update_user(user_id="00unew123", profile={"firstName": "Updated"}, ctx=ctx_elicit_accept_true)
        assert update_result == [updated_user]
