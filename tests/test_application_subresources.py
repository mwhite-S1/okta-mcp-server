# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for application sub-resource tools: users, groups, grants, tokens, connections, features, push."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from okta_mcp_server.tools.applications.application_users import (
    assign_user_to_application,
    get_application_user,
    list_application_users,
    unassign_user_from_application,
    update_application_user,
)
from okta_mcp_server.tools.applications.application_groups import (
    assign_group_to_application,
    get_application_group_assignment,
    list_application_group_assignments,
    unassign_group_from_application,
    update_application_group_assignment,
)
from okta_mcp_server.tools.applications.application_grants import (
    get_scope_consent_grant,
    grant_consent_to_scope,
    list_scope_consent_grants,
    revoke_scope_consent_grant,
)
from okta_mcp_server.tools.applications.application_tokens import (
    get_application_token,
    list_application_tokens,
    revoke_all_application_tokens,
    revoke_application_token,
)
from okta_mcp_server.tools.applications.application_connections import (
    activate_provisioning_connection,
    deactivate_provisioning_connection,
    get_default_provisioning_connection,
    get_provisioning_connection_jwks,
    update_default_provisioning_connection,
    verify_provisioning_connection,
)
from okta_mcp_server.tools.applications.application_features import (
    assign_application_policy,
    get_application_feature,
    list_application_features,
    preview_saml_metadata,
    update_application_feature,
    upload_application_logo,
)
from okta_mcp_server.tools.applications.application_push import (
    create_group_push_mapping,
    delete_group_push_mapping,
    get_group_push_mapping,
    list_group_push_mappings,
    update_group_push_mapping,
)


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

APP_ID = "0oa1abc123def456"
USER_ID = "00u1abc123def456"
GROUP_ID = "00g1abc123def456"
GRANT_ID = "0oag1abc123def456"
TOKEN_ID = "oar1abc123def456"
MAPPING_ID = "1fm1abc123def456"
POLICY_ID = "00p1abc123def456"
KID = "SIMcCQNY3uwXoW3y0vf6VxiBb5n9pf8L2fK8d-FIbm4"

PATCH_USERS = "okta_mcp_server.tools.applications.application_users.get_okta_client"
PATCH_GROUPS = "okta_mcp_server.tools.applications.application_groups.get_okta_client"
PATCH_GRANTS = "okta_mcp_server.tools.applications.application_grants.get_okta_client"
PATCH_TOKENS = "okta_mcp_server.tools.applications.application_tokens.get_okta_client"
PATCH_CONNS = "okta_mcp_server.tools.applications.application_connections.get_okta_client"
PATCH_FEATS = "okta_mcp_server.tools.applications.application_features.get_okta_client"
PATCH_PUSH = "okta_mcp_server.tools.applications.application_push.get_okta_client"


# ---------------------------------------------------------------------------
# Helper: build mock model objects
# ---------------------------------------------------------------------------

def _mock_model(**fields):
    """Return a MagicMock whose .to_dict() returns the supplied fields."""
    m = MagicMock()
    m.to_dict.return_value = fields
    return m


def _mock_client(patch_target):
    """Context manager that patches *patch_target* with a fresh AsyncMock client."""
    client = AsyncMock()
    return patch(patch_target, return_value=client), client


# ===========================================================================
# application_users
# ===========================================================================

class TestListApplicationUsers:
    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        user = _mock_model(id=USER_ID, scope="USER")
        client.list_application_users.return_value = ([user], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_application_users(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "items" in result
        assert result["total_fetched"] == 1
        assert result["items"][0]["id"] == USER_ID

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_application_users.return_value = (None, None, "Not Found")
        mock_get_client.return_value = client

        result = await list_application_users(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_application_users.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_application_users(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert result["total_fetched"] == 0
        assert result["items"] == []

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_optional_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_application_users.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        await list_application_users(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            after="cursor1",
            limit=50,
            q="alice",
            expand="user",
        )

        _, kwargs = client.list_application_users.call_args
        assert kwargs.get("after") == "cursor1"
        assert kwargs.get("limit") == 50
        assert kwargs.get("q") == "alice"
        assert kwargs.get("expand") == "user"

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("connection refused")

        result = await list_application_users(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result


class TestAssignUserToApplication:
    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        user = _mock_model(id=USER_ID, scope="USER")
        client.assign_user_to_application.return_value = (user, MagicMock(), None)
        mock_get_client.return_value = client

        result = await assign_user_to_application(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            app_user={"id": USER_ID},
        )

        assert result["id"] == USER_ID

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.assign_user_to_application.return_value = (None, None, "User already assigned")
        mock_get_client.return_value = client

        result = await assign_user_to_application(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            app_user={"id": USER_ID},
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_with_credentials_and_profile(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        user = _mock_model(id=USER_ID, scope="USER")
        client.assign_user_to_application.return_value = (user, MagicMock(), None)
        mock_get_client.return_value = client

        app_user = {
            "id": USER_ID,
            "credentials": {"userName": "alice@example.com"},
            "profile": {"salesforceGroups": ["Employee"]},
        }
        result = await assign_user_to_application(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            app_user=app_user,
        )

        client.assign_user_to_application.assert_awaited_once_with(APP_ID, app_user)
        assert result["id"] == USER_ID

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("network error")

        result = await assign_user_to_application(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            app_user={"id": USER_ID},
        )

        assert "error" in result


class TestGetApplicationUser:
    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        user = _mock_model(id=USER_ID, scope="USER")
        client.get_application_user.return_value = (user, MagicMock(), None)
        mock_get_client.return_value = client

        result = await get_application_user(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, user_id=USER_ID
        )

        assert result["id"] == USER_ID

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_application_user.return_value = (None, None, "Not Found")
        mock_get_client.return_value = client

        result = await get_application_user(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, user_id=USER_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_expand_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        user = _mock_model(id=USER_ID, scope="USER")
        client.get_application_user.return_value = (user, MagicMock(), None)
        mock_get_client.return_value = client

        await get_application_user(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, user_id=USER_ID, expand="user"
        )

        _, kwargs = client.get_application_user.call_args
        assert kwargs.get("expand") == "user"

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("timeout")

        result = await get_application_user(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, user_id=USER_ID
        )

        assert "error" in result


class TestUpdateApplicationUser:
    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        user = _mock_model(id=USER_ID, scope="USER")
        client.update_application_user.return_value = (user, MagicMock(), None)
        mock_get_client.return_value = client

        result = await update_application_user(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            user_id=USER_ID,
            app_user={"profile": {"firstName": "Alice"}},
        )

        assert result["id"] == USER_ID

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_application_user.return_value = (None, None, "Validation error")
        mock_get_client.return_value = client

        result = await update_application_user(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            user_id=USER_ID,
            app_user={},
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        user = _mock_model(id=USER_ID)
        client.update_application_user.return_value = (user, MagicMock(), None)
        mock_get_client.return_value = client

        app_user = {"credentials": {"userName": "alice@example.com"}}
        await update_application_user(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            user_id=USER_ID,
            app_user=app_user,
        )

        client.update_application_user.assert_awaited_once_with(APP_ID, USER_ID, app_user)

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await update_application_user(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            user_id=USER_ID,
            app_user={},
        )

        assert "error" in result


class TestUnassignUserFromApplication:
    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unassign_user_from_application.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await unassign_user_from_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, user_id=USER_ID
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unassign_user_from_application.return_value = (None, None, "Forbidden")
        mock_get_client.return_value = client

        result = await unassign_user_from_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, user_id=USER_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_send_email_default_false(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unassign_user_from_application.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        await unassign_user_from_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, user_id=USER_ID
        )

        _, kwargs = client.unassign_user_from_application.call_args
        assert kwargs.get("send_email") is False

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_send_email_true(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unassign_user_from_application.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await unassign_user_from_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, user_id=USER_ID, send_email=True
        )

        _, kwargs = client.unassign_user_from_application.call_args
        assert kwargs.get("send_email") is True
        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_USERS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("connection error")

        result = await unassign_user_from_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, user_id=USER_ID
        )

        assert "error" in result


# ===========================================================================
# application_groups
# ===========================================================================

class TestListApplicationGroupAssignments:
    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        assignment = _mock_model(id=GROUP_ID, priority=1)
        client.list_application_group_assignments.return_value = ([assignment], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_application_group_assignments(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "items" in result
        assert result["total_fetched"] == 1
        assert result["items"][0]["id"] == GROUP_ID

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_application_group_assignments.return_value = (None, None, "Forbidden")
        mock_get_client.return_value = client

        result = await list_application_group_assignments(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_application_group_assignments.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_application_group_assignments(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_optional_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_application_group_assignments.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        await list_application_group_assignments(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            q="Engineers",
            after="cursor2",
            limit=25,
            expand="group",
        )

        _, kwargs = client.list_application_group_assignments.call_args
        assert kwargs.get("q") == "Engineers"
        assert kwargs.get("after") == "cursor2"
        assert kwargs.get("limit") == 25
        assert kwargs.get("expand") == "group"

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("timeout")

        result = await list_application_group_assignments(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result


class TestGetApplicationGroupAssignment:
    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        assignment = _mock_model(id=GROUP_ID, priority=1)
        client.get_application_group_assignment.return_value = (assignment, MagicMock(), None)
        mock_get_client.return_value = client

        result = await get_application_group_assignment(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        assert result["id"] == GROUP_ID

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_application_group_assignment.return_value = (None, None, "Not Found")
        mock_get_client.return_value = client

        result = await get_application_group_assignment(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_expand_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        assignment = _mock_model(id=GROUP_ID)
        client.get_application_group_assignment.return_value = (assignment, MagicMock(), None)
        mock_get_client.return_value = client

        await get_application_group_assignment(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID, expand="group"
        )

        _, kwargs = client.get_application_group_assignment.call_args
        assert kwargs.get("expand") == "group"

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await get_application_group_assignment(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        assert "error" in result


class TestAssignGroupToApplication:
    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        result_obj = _mock_model(id=GROUP_ID, priority=1)
        client.assign_group_to_application.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        result = await assign_group_to_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        assert result["id"] == GROUP_ID

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.assign_group_to_application.return_value = (None, None, "Already assigned")
        mock_get_client.return_value = client

        result = await assign_group_to_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_default_empty_assignment(self, mock_get_client, ctx_elicit_accept_true):
        """When assignment is None, the tool should pass {} to the SDK."""
        client = AsyncMock()
        result_obj = _mock_model(id=GROUP_ID)
        client.assign_group_to_application.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        await assign_group_to_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        args, _ = client.assign_group_to_application.call_args
        assert args[2] == {}

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_custom_assignment_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        result_obj = _mock_model(id=GROUP_ID)
        client.assign_group_to_application.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        custom = {"priority": 1, "profile": {"role": "admin"}}
        await assign_group_to_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID, assignment=custom
        )

        args, _ = client.assign_group_to_application.call_args
        assert args[2] == custom

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("network failure")

        result = await assign_group_to_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        assert "error" in result


class TestUpdateApplicationGroupAssignment:
    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        result_obj = _mock_model(id=GROUP_ID, priority=2)
        client.update_group_assignment_to_application.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        patch_ops = [{"op": "replace", "path": "/priority", "value": 2}]
        result = await update_application_group_assignment(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            group_id=GROUP_ID,
            patch_operations=patch_ops,
        )

        assert result["id"] == GROUP_ID
        assert result["priority"] == 2

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_group_assignment_to_application.return_value = (None, None, "Bad Request")
        mock_get_client.return_value = client

        result = await update_application_group_assignment(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            group_id=GROUP_ID,
            patch_operations=[],
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_patch_operations_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        result_obj = _mock_model(id=GROUP_ID)
        client.update_group_assignment_to_application.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        ops = [{"op": "add", "path": "/profile/role", "value": "admin"}]
        await update_application_group_assignment(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            group_id=GROUP_ID,
            patch_operations=ops,
        )

        args, _ = client.update_group_assignment_to_application.call_args
        assert args[2] == ops

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("server error")

        result = await update_application_group_assignment(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            group_id=GROUP_ID,
            patch_operations=[],
        )

        assert "error" in result


class TestUnassignGroupFromApplication:
    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unassign_application_from_group.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await unassign_group_from_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unassign_application_from_group.return_value = (None, None, "Forbidden")
        mock_get_client.return_value = client

        result = await unassign_group_from_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.unassign_application_from_group.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        await unassign_group_from_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        client.unassign_application_from_group.assert_awaited_once_with(APP_ID, GROUP_ID)

    @pytest.mark.asyncio
    @patch(PATCH_GROUPS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("connection reset")

        result = await unassign_group_from_application(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, group_id=GROUP_ID
        )

        assert "error" in result


# ===========================================================================
# application_grants
# ===========================================================================

class TestListScopeConsentGrants:
    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        grant = _mock_model(id=GRANT_ID, scopeId="okta.users.read")
        client.list_scope_consent_grants.return_value = ([grant], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_scope_consent_grants(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "items" in result
        assert result["total_fetched"] == 1
        assert result["items"][0]["id"] == GRANT_ID

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_scope_consent_grants.return_value = (None, None, "Unauthorized")
        mock_get_client.return_value = client

        result = await list_scope_consent_grants(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_scope_consent_grants.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_scope_consent_grants(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_expand_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_scope_consent_grants.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        await list_scope_consent_grants(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, expand="scope"
        )

        _, kwargs = client.list_scope_consent_grants.call_args
        assert kwargs.get("expand") == "scope"

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await list_scope_consent_grants(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result


class TestGrantConsentToScope:
    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        result_obj = _mock_model(id=GRANT_ID, scopeId="okta.users.read")
        client.grant_consent_to_scope.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        grant_body = {"issuer": "https://example.okta.com", "scopeId": "okta.users.read"}
        result = await grant_consent_to_scope(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant=grant_body
        )

        assert result["id"] == GRANT_ID

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.grant_consent_to_scope.return_value = (None, None, "Invalid scope")
        mock_get_client.return_value = client

        result = await grant_consent_to_scope(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant={}
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_grant_body_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        result_obj = _mock_model(id=GRANT_ID)
        client.grant_consent_to_scope.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        grant_body = {"issuer": "https://example.okta.com", "scopeId": "okta.users.manage"}
        await grant_consent_to_scope(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant=grant_body
        )

        client.grant_consent_to_scope.assert_awaited_once_with(APP_ID, grant_body)

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("network error")

        result = await grant_consent_to_scope(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant={}
        )

        assert "error" in result


class TestGetScopeConsentGrant:
    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        grant = _mock_model(id=GRANT_ID, scopeId="okta.users.read")
        client.get_scope_consent_grant.return_value = (grant, MagicMock(), None)
        mock_get_client.return_value = client

        result = await get_scope_consent_grant(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant_id=GRANT_ID
        )

        assert result["id"] == GRANT_ID

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_scope_consent_grant.return_value = (None, None, "Not Found")
        mock_get_client.return_value = client

        result = await get_scope_consent_grant(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant_id=GRANT_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_expand_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        grant = _mock_model(id=GRANT_ID)
        client.get_scope_consent_grant.return_value = (grant, MagicMock(), None)
        mock_get_client.return_value = client

        await get_scope_consent_grant(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant_id=GRANT_ID, expand="scope"
        )

        _, kwargs = client.get_scope_consent_grant.call_args
        assert kwargs.get("expand") == "scope"

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("timeout")

        result = await get_scope_consent_grant(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant_id=GRANT_ID
        )

        assert "error" in result


class TestRevokeScopeConsentGrant:
    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_scope_consent_grant.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await revoke_scope_consent_grant(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant_id=GRANT_ID
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_scope_consent_grant.return_value = (None, None, "Not Found")
        mock_get_client.return_value = client

        result = await revoke_scope_consent_grant(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant_id=GRANT_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_scope_consent_grant.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        await revoke_scope_consent_grant(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant_id=GRANT_ID
        )

        client.revoke_scope_consent_grant.assert_awaited_once_with(APP_ID, GRANT_ID)

    @pytest.mark.asyncio
    @patch(PATCH_GRANTS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("server down")

        result = await revoke_scope_consent_grant(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, grant_id=GRANT_ID
        )

        assert "error" in result


# ===========================================================================
# application_tokens
# ===========================================================================

class TestListApplicationTokens:
    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        token = _mock_model(id=TOKEN_ID, clientId=APP_ID)
        client.list_o_auth2_tokens_for_application.return_value = ([token], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_application_tokens(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "items" in result
        assert result["total_fetched"] == 1
        assert result["items"][0]["id"] == TOKEN_ID

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_o_auth2_tokens_for_application.return_value = (None, None, "Unauthorized")
        mock_get_client.return_value = client

        result = await list_application_tokens(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_o_auth2_tokens_for_application.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_application_tokens(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_optional_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_o_auth2_tokens_for_application.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        await list_application_tokens(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            expand="scope",
            after="cur3",
            limit=10,
        )

        _, kwargs = client.list_o_auth2_tokens_for_application.call_args
        assert kwargs.get("expand") == "scope"
        assert kwargs.get("after") == "cur3"
        assert kwargs.get("limit") == 10

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await list_application_tokens(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result


class TestGetApplicationToken:
    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        token = _mock_model(id=TOKEN_ID, clientId=APP_ID)
        client.get_o_auth2_token_for_application.return_value = (token, MagicMock(), None)
        mock_get_client.return_value = client

        result = await get_application_token(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, token_id=TOKEN_ID
        )

        assert result["id"] == TOKEN_ID

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_o_auth2_token_for_application.return_value = (None, None, "Not Found")
        mock_get_client.return_value = client

        result = await get_application_token(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, token_id=TOKEN_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_expand_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        token = _mock_model(id=TOKEN_ID)
        client.get_o_auth2_token_for_application.return_value = (token, MagicMock(), None)
        mock_get_client.return_value = client

        await get_application_token(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, token_id=TOKEN_ID, expand="scope"
        )

        _, kwargs = client.get_o_auth2_token_for_application.call_args
        assert kwargs.get("expand") == "scope"

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("timeout")

        result = await get_application_token(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, token_id=TOKEN_ID
        )

        assert "error" in result


class TestRevokeApplicationToken:
    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_o_auth2_token_for_application.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await revoke_application_token(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, token_id=TOKEN_ID
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_o_auth2_token_for_application.return_value = (None, None, "Not Found")
        mock_get_client.return_value = client

        result = await revoke_application_token(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, token_id=TOKEN_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_o_auth2_token_for_application.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        await revoke_application_token(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, token_id=TOKEN_ID
        )

        client.revoke_o_auth2_token_for_application.assert_awaited_once_with(APP_ID, TOKEN_ID)

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("server error")

        result = await revoke_application_token(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, token_id=TOKEN_ID
        )

        assert "error" in result


class TestRevokeAllApplicationTokens:
    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_o_auth2_tokens_for_application.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await revoke_all_application_tokens(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_o_auth2_tokens_for_application.return_value = (None, None, "Forbidden")
        mock_get_client.return_value = client

        result = await revoke_all_application_tokens(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_only_app_id_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.revoke_o_auth2_tokens_for_application.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        await revoke_all_application_tokens(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        client.revoke_o_auth2_tokens_for_application.assert_awaited_once_with(APP_ID)

    @pytest.mark.asyncio
    @patch(PATCH_TOKENS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("connection refused")

        result = await revoke_all_application_tokens(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result


# ===========================================================================
# application_connections
# ===========================================================================

class TestGetDefaultProvisioningConnection:
    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        conn = _mock_model(authScheme="TOKEN", status="ENABLED")
        client.get_default_provisioning_connection_for_application.return_value = (
            conn, MagicMock(), None
        )
        mock_get_client.return_value = client

        result = await get_default_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert result["authScheme"] == "TOKEN"

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_default_provisioning_connection_for_application.return_value = (
            None, None, "Not Found"
        )
        mock_get_client.return_value = client

        result = await get_default_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        conn = _mock_model(authScheme="OAUTH2")
        client.get_default_provisioning_connection_for_application.return_value = (
            conn, MagicMock(), None
        )
        mock_get_client.return_value = client

        await get_default_provisioning_connection(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        client.get_default_provisioning_connection_for_application.assert_awaited_once_with(APP_ID)

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("timeout")

        result = await get_default_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result


class TestUpdateDefaultProvisioningConnection:
    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        conn = _mock_model(authScheme="TOKEN", status="ENABLED")
        client.update_default_provisioning_connection_for_application.return_value = (
            conn, MagicMock(), None
        )
        mock_get_client.return_value = client

        result = await update_default_provisioning_connection(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            connection={"authScheme": "TOKEN", "token": "secret-token"},
        )

        assert result["authScheme"] == "TOKEN"

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_default_provisioning_connection_for_application.return_value = (
            None, None, "Validation error"
        )
        mock_get_client.return_value = client

        result = await update_default_provisioning_connection(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            connection={},
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_activate_false_by_default(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        conn = _mock_model(authScheme="TOKEN")
        client.update_default_provisioning_connection_for_application.return_value = (
            conn, MagicMock(), None
        )
        mock_get_client.return_value = client

        connection = {"authScheme": "TOKEN", "token": "secret"}
        await update_default_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, connection=connection
        )

        args, kwargs = client.update_default_provisioning_connection_for_application.call_args
        assert kwargs.get("activate") is False

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_activate_true_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        conn = _mock_model(authScheme="TOKEN", status="ENABLED")
        client.update_default_provisioning_connection_for_application.return_value = (
            conn, MagicMock(), None
        )
        mock_get_client.return_value = client

        await update_default_provisioning_connection(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            connection={"authScheme": "TOKEN", "token": "secret"},
            activate=True,
        )

        _, kwargs = client.update_default_provisioning_connection_for_application.call_args
        assert kwargs.get("activate") is True

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("network error")

        result = await update_default_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, connection={}
        )

        assert "error" in result


class TestGetProvisioningConnectionJwks:
    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        jwks = _mock_model(keys=[{"kty": "RSA", "use": "sig"}])
        client.get_user_provisioning_connection_jwks.return_value = (jwks, MagicMock(), None)
        mock_get_client.return_value = client

        result = await get_provisioning_connection_jwks(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "keys" in result

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_user_provisioning_connection_jwks.return_value = (None, None, "Not Found")
        mock_get_client.return_value = client

        result = await get_provisioning_connection_jwks(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        jwks = _mock_model(keys=[])
        client.get_user_provisioning_connection_jwks.return_value = (jwks, MagicMock(), None)
        mock_get_client.return_value = client

        await get_provisioning_connection_jwks(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        client.get_user_provisioning_connection_jwks.assert_awaited_once_with(APP_ID)

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("server error")

        result = await get_provisioning_connection_jwks(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result


class TestActivateProvisioningConnection:
    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_default_provisioning_connection_for_application.return_value = (
            None, MagicMock(), None
        )
        mock_get_client.return_value = client

        result = await activate_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_default_provisioning_connection_for_application.return_value = (
            None, None, "Already active"
        )
        mock_get_client.return_value = client

        result = await activate_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_default_provisioning_connection_for_application.return_value = (
            None, MagicMock(), None
        )
        mock_get_client.return_value = client

        await activate_provisioning_connection(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        client.activate_default_provisioning_connection_for_application.assert_awaited_once_with(
            APP_ID
        )

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("timeout")

        result = await activate_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result


class TestDeactivateProvisioningConnection:
    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.deactivate_default_provisioning_connection_for_application.return_value = (
            None, MagicMock(), None
        )
        mock_get_client.return_value = client

        result = await deactivate_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.deactivate_default_provisioning_connection_for_application.return_value = (
            None, None, "Already inactive"
        )
        mock_get_client.return_value = client

        result = await deactivate_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.deactivate_default_provisioning_connection_for_application.return_value = (
            None, MagicMock(), None
        )
        mock_get_client.return_value = client

        await deactivate_provisioning_connection(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        client.deactivate_default_provisioning_connection_for_application.assert_awaited_once_with(
            APP_ID
        )

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("connection reset")

        result = await deactivate_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID
        )

        assert "error" in result


class TestVerifyProvisioningConnection:
    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.verify_provisioning_connection_for_application.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await verify_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, app_name="office365"
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.verify_provisioning_connection_for_application.return_value = (None, None, "invalid code")
        mock_get_client.return_value = client

        result = await verify_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, app_name="google"
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_code_and_state_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.verify_provisioning_connection_for_application.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        await verify_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, app_name="slack",
            code="abc123", state="xyz789"
        )

        client.verify_provisioning_connection_for_application.assert_awaited_once_with(
            "slack", APP_ID, code="abc123", state="xyz789"
        )

    @pytest.mark.asyncio
    @patch(PATCH_CONNS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("network error")

        result = await verify_provisioning_connection(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, app_name="google"
        )

        assert "error" in result


# ===========================================================================
# application_features
# ===========================================================================

class TestListApplicationFeatures:
    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        feature = _mock_model(name="PUSH_NEW_USERS", status="ENABLED")
        client.list_features_for_application.return_value = ([feature], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_application_features(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "items" in result
        assert result["total_fetched"] == 1
        assert result["items"][0]["name"] == "PUSH_NEW_USERS"

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_features_for_application.return_value = (None, None, "Provisioning not enabled")
        mock_get_client.return_value = client

        result = await list_application_features(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_features_for_application.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_application_features(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("timeout")

        result = await list_application_features(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result


class TestGetApplicationFeature:
    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        feature = _mock_model(name="PUSH_NEW_USERS", status="ENABLED")
        client.get_feature_for_application.return_value = (feature, MagicMock(), None)
        mock_get_client.return_value = client

        result = await get_application_feature(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, feature_name="PUSH_NEW_USERS"
        )

        assert result["name"] == "PUSH_NEW_USERS"

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_feature_for_application.return_value = (None, None, "Not Found")
        mock_get_client.return_value = client

        result = await get_application_feature(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, feature_name="PUSH_NEW_USERS"
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        feature = _mock_model(name="PUSH_GROUPS")
        client.get_feature_for_application.return_value = (feature, MagicMock(), None)
        mock_get_client.return_value = client

        await get_application_feature(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, feature_name="PUSH_GROUPS"
        )

        client.get_feature_for_application.assert_awaited_once_with(APP_ID, "PUSH_GROUPS")

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await get_application_feature(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, feature_name="PUSH_NEW_USERS"
        )

        assert "error" in result


class TestUpdateApplicationFeature:
    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        feature = _mock_model(name="PUSH_NEW_USERS", status="ENABLED")
        client.update_feature_for_application.return_value = (feature, MagicMock(), None)
        mock_get_client.return_value = client

        caps = {"create": {"lifecycleCreate": {"status": "ACTIVE"}}}
        result = await update_application_feature(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            feature_name="PUSH_NEW_USERS",
            capabilities=caps,
        )

        assert result["name"] == "PUSH_NEW_USERS"

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_feature_for_application.return_value = (None, None, "Validation error")
        mock_get_client.return_value = client

        result = await update_application_feature(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            feature_name="PUSH_NEW_USERS",
            capabilities={},
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        feature = _mock_model(name="PUSH_PROFILE_UPDATES")
        client.update_feature_for_application.return_value = (feature, MagicMock(), None)
        mock_get_client.return_value = client

        caps = {"update": {"profile": {"action": "AUTOMATIC"}}}
        await update_application_feature(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            feature_name="PUSH_PROFILE_UPDATES",
            capabilities=caps,
        )

        client.update_feature_for_application.assert_awaited_once_with(
            APP_ID, "PUSH_PROFILE_UPDATES", caps
        )

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("server error")

        result = await update_application_feature(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            feature_name="PUSH_NEW_USERS",
            capabilities={},
        )

        assert "error" in result


class TestUploadApplicationLogo:
    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    @patch("builtins.open", mock_open(read_data=b"fake-png-bytes"))
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.upload_application_logo.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await upload_application_logo(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, file_path="/tmp/logo.png"
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    @patch("builtins.open", mock_open(read_data=b"fake-png-bytes"))
    async def test_sdk_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.upload_application_logo.return_value = (None, None, "Unsupported format")
        mock_get_client.return_value = client

        result = await upload_application_logo(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, file_path="/tmp/logo.png"
        )

        assert "error" in result

    @pytest.mark.asyncio
    async def test_file_not_found(self, ctx_elicit_accept_true):
        result = await upload_application_logo(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            file_path="/nonexistent/path/logo.png",
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    @patch("builtins.open", mock_open(read_data=b"\x89PNG\r\n"))
    async def test_file_bytes_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.upload_application_logo.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        await upload_application_logo(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, file_path="/tmp/logo.png"
        )

        args, _ = client.upload_application_logo.call_args
        assert args[0] == APP_ID
        assert args[1] == b"\x89PNG\r\n"

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    @patch("builtins.open", mock_open(read_data=b"bytes"))
    async def test_sdk_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("upload failed")

        result = await upload_application_logo(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, file_path="/tmp/logo.png"
        )

        assert "error" in result


class TestAssignApplicationPolicy:
    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.assign_application_policy.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await assign_application_policy(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, policy_id=POLICY_ID
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.assign_application_policy.return_value = (None, None, "Policy not found")
        mock_get_client.return_value = client

        result = await assign_application_policy(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, policy_id=POLICY_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.assign_application_policy.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        await assign_application_policy(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, policy_id=POLICY_ID
        )

        client.assign_application_policy.assert_awaited_once_with(APP_ID, POLICY_ID)

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("server error")

        result = await assign_application_policy(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, policy_id=POLICY_ID
        )

        assert "error" in result


class TestPreviewSamlMetadata:
    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        xml_str = '<?xml version="1.0"?><EntityDescriptor/>'
        client.preview_sam_lmetadata_for_application.return_value = (
            xml_str, MagicMock(), None
        )
        mock_get_client.return_value = client

        result = await preview_saml_metadata(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, kid=KID
        )

        assert "metadata" in result
        assert result["metadata"] == xml_str

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.preview_sam_lmetadata_for_application.return_value = (None, None, "Not a SAML app")
        mock_get_client.return_value = client

        result = await preview_saml_metadata(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, kid=KID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.preview_sam_lmetadata_for_application.return_value = ("<xml/>", MagicMock(), None)
        mock_get_client.return_value = client

        await preview_saml_metadata(ctx=ctx_elicit_accept_true, app_id=APP_ID, kid=KID)

        client.preview_sam_lmetadata_for_application.assert_awaited_once_with(APP_ID, KID)

    @pytest.mark.asyncio
    @patch(PATCH_FEATS)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("connection error")

        result = await preview_saml_metadata(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, kid=KID
        )

        assert "error" in result


# ===========================================================================
# application_push
# ===========================================================================

class TestListGroupPushMappings:
    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        mapping = _mock_model(mappingId=MAPPING_ID, status="ACTIVE")
        client.list_group_push_mappings.return_value = ([mapping], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_group_push_mappings(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "items" in result
        assert result["total_fetched"] == 1
        assert result["items"][0]["mappingId"] == MAPPING_ID

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_group_push_mappings.return_value = (None, None, "Unauthorized")
        mock_get_client.return_value = client

        result = await list_group_push_mappings(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_group_push_mappings.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        result = await list_group_push_mappings(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_filter_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_group_push_mappings.return_value = ([], MagicMock(), None)
        mock_get_client.return_value = client

        await list_group_push_mappings(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            after="cur4",
            limit=20,
            last_updated="2025-01-01T00:00:00Z",
            source_group_id=GROUP_ID,
            status="ACTIVE",
        )

        _, kwargs = client.list_group_push_mappings.call_args
        assert kwargs.get("after") == "cur4"
        assert kwargs.get("limit") == 20
        assert kwargs.get("last_updated") == "2025-01-01T00:00:00Z"
        assert kwargs.get("source_group_id") == GROUP_ID
        assert kwargs.get("status") == "ACTIVE"

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("timeout")

        result = await list_group_push_mappings(ctx=ctx_elicit_accept_true, app_id=APP_ID)

        assert "error" in result


class TestCreateGroupPushMapping:
    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        result_obj = _mock_model(mappingId=MAPPING_ID, status="ACTIVE")
        client.create_group_push_mapping.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        mapping = {"sourceGroupId": GROUP_ID, "targetGroupName": "Engineers-Pushed"}
        result = await create_group_push_mapping(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, mapping=mapping
        )

        assert result["mappingId"] == MAPPING_ID

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_group_push_mapping.return_value = (None, None, "Conflict")
        mock_get_client.return_value = client

        result = await create_group_push_mapping(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            mapping={"sourceGroupId": GROUP_ID},
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_mapping_body_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        result_obj = _mock_model(mappingId=MAPPING_ID)
        client.create_group_push_mapping.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        mapping = {"sourceGroupId": GROUP_ID, "targetGroupId": "00g9abc999xyz"}
        await create_group_push_mapping(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, mapping=mapping
        )

        client.create_group_push_mapping.assert_awaited_once_with(APP_ID, mapping)

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("network error")

        result = await create_group_push_mapping(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            mapping={"sourceGroupId": GROUP_ID},
        )

        assert "error" in result


class TestGetGroupPushMapping:
    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        mapping = _mock_model(mappingId=MAPPING_ID, status="ACTIVE")
        client.get_group_push_mapping.return_value = (mapping, MagicMock(), None)
        mock_get_client.return_value = client

        result = await get_group_push_mapping(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, mapping_id=MAPPING_ID
        )

        assert result["mappingId"] == MAPPING_ID

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_group_push_mapping.return_value = (None, None, "Not Found")
        mock_get_client.return_value = client

        result = await get_group_push_mapping(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, mapping_id=MAPPING_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_correct_args_passed(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        mapping = _mock_model(mappingId=MAPPING_ID)
        client.get_group_push_mapping.return_value = (mapping, MagicMock(), None)
        mock_get_client.return_value = client

        await get_group_push_mapping(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, mapping_id=MAPPING_ID
        )

        client.get_group_push_mapping.assert_awaited_once_with(APP_ID, MAPPING_ID)

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await get_group_push_mapping(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, mapping_id=MAPPING_ID
        )

        assert "error" in result


class TestUpdateGroupPushMapping:
    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        result_obj = _mock_model(mappingId=MAPPING_ID, status="INACTIVE")
        client.update_group_push_mapping.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        result = await update_group_push_mapping(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            mapping_id=MAPPING_ID,
            update={"status": "INACTIVE"},
        )

        assert result["mappingId"] == MAPPING_ID
        assert result["status"] == "INACTIVE"

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_group_push_mapping.return_value = (None, None, "Bad Request")
        mock_get_client.return_value = client

        result = await update_group_push_mapping(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            mapping_id=MAPPING_ID,
            update={},
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_update_body_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        result_obj = _mock_model(mappingId=MAPPING_ID)
        client.update_group_push_mapping.return_value = (result_obj, MagicMock(), None)
        mock_get_client.return_value = client

        update_body = {"status": "ACTIVE"}
        await update_group_push_mapping(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            mapping_id=MAPPING_ID,
            update=update_body,
        )

        client.update_group_push_mapping.assert_awaited_once_with(APP_ID, MAPPING_ID, update_body)

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("server error")

        result = await update_group_push_mapping(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            mapping_id=MAPPING_ID,
            update={},
        )

        assert "error" in result


class TestDeleteGroupPushMapping:
    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_success(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_group_push_mapping.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await delete_group_push_mapping(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, mapping_id=MAPPING_ID
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_group_push_mapping.return_value = (None, None, "Mapping still active")
        mock_get_client.return_value = client

        result = await delete_group_push_mapping(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, mapping_id=MAPPING_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_delete_target_group_default_false(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_group_push_mapping.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        await delete_group_push_mapping(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, mapping_id=MAPPING_ID
        )

        _, kwargs = client.delete_group_push_mapping.call_args
        assert kwargs.get("delete_target_group") is False

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_delete_target_group_true(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.delete_group_push_mapping.return_value = (None, MagicMock(), None)
        mock_get_client.return_value = client

        result = await delete_group_push_mapping(
            ctx=ctx_elicit_accept_true,
            app_id=APP_ID,
            mapping_id=MAPPING_ID,
            delete_target_group=True,
        )

        _, kwargs = client.delete_group_push_mapping.call_args
        assert kwargs.get("delete_target_group") is True
        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_PUSH)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("connection refused")

        result = await delete_group_push_mapping(
            ctx=ctx_elicit_accept_true, app_id=APP_ID, mapping_id=MAPPING_ID
        )

        assert "error" in result
