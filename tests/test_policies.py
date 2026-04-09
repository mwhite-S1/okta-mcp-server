# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for all policy tools: list, get, create, update, activate, rules."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.policies.policies import (
    activate_policy,
    activate_policy_rule,
    create_policy,
    create_policy_rule,
    get_policy,
    get_policy_rule,
    list_policies,
    list_policy_rules,
    update_policy,
    update_policy_rule,
)


POLICY_ID = "00p1234567890ABCDEF"
RULE_ID = "0pr1234567890ABCDEF"
PATCH_CLIENT = "okta_mcp_server.tools.policies.policies.get_okta_client"


def _make_policy(policy_id=POLICY_ID, name="Test Policy", policy_type="OKTA_SIGN_ON"):
    policy = MagicMock()
    policy.id = policy_id
    policy.name = name
    policy.type = policy_type
    policy.as_dict.return_value = {"id": policy_id, "name": name, "type": policy_type, "status": "ACTIVE"}
    return policy


def _make_rule(rule_id=RULE_ID, name="Test Rule"):
    rule = MagicMock()
    rule.id = rule_id
    rule.name = name
    rule.as_dict.return_value = {"id": rule_id, "name": name, "status": "ACTIVE"}
    return rule


def _make_resp(has_next=False, next_token=None):
    resp = MagicMock()
    resp.has_next.return_value = has_next
    resp.get_next_page_token.return_value = next_token
    return resp


# ---------------------------------------------------------------------------
# list_policies
# ---------------------------------------------------------------------------

class TestListPolicies:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_policies(self, mock_get_client, ctx_elicit_accept_true):
        policy = _make_policy()
        client = AsyncMock()
        client.list_policies.return_value = ([policy], None, None)
        mock_get_client.return_value = client

        result = await list_policies(ctx=ctx_elicit_accept_true, type="OKTA_SIGN_ON")

        assert "policies" in result
        assert len(result["policies"]) == 1
        assert result["policies"][0]["id"] == POLICY_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_policies.return_value = ([], None, None)
        mock_get_client.return_value = client

        result = await list_policies(ctx=ctx_elicit_accept_true, type="PASSWORD")

        assert result == {"policies": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_policies.return_value = (None, None, "Insufficient permissions")
        mock_get_client.return_value = client

        result = await list_policies(ctx=ctx_elicit_accept_true, type="OKTA_SIGN_ON")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_policies(ctx=ctx_elicit_accept_true, type="OKTA_SIGN_ON")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_limit_clamped_below_minimum(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_policies.return_value = ([], None, None)
        mock_get_client.return_value = client

        await list_policies(ctx=ctx_elicit_accept_true, type="OKTA_SIGN_ON", limit=5)
        call_params = client.list_policies.call_args[0][0]
        assert call_params.get("limit") == 20

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_limit_clamped_above_maximum(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_policies.return_value = ([], None, None)
        mock_get_client.return_value = client

        await list_policies(ctx=ctx_elicit_accept_true, type="OKTA_SIGN_ON", limit=500)
        call_params = client.list_policies.call_args[0][0]
        assert call_params.get("limit") == 100

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_status_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_policies.return_value = ([], None, None)
        mock_get_client.return_value = client

        await list_policies(ctx=ctx_elicit_accept_true, type="OKTA_SIGN_ON", status="ACTIVE")
        call_params = client.list_policies.call_args[0][0]
        assert call_params.get("status") == "ACTIVE"


# ---------------------------------------------------------------------------
# get_policy
# ---------------------------------------------------------------------------

class TestGetPolicy:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_policy(self, mock_get_client, ctx_elicit_accept_true):
        policy = _make_policy()
        client = AsyncMock()
        client.get_policy.return_value = (policy, None, None)
        mock_get_client.return_value = client

        result = await get_policy(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID)

        assert result["id"] == POLICY_ID
        client.get_policy.assert_awaited_once_with(POLICY_ID)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await get_policy(ctx=ctx_elicit_accept_true, policy_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_policy.return_value = (None, None, "Policy not found")
        mock_get_client.return_value = client

        result = await get_policy(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_policy.side_effect = Exception("Connection error")
        mock_get_client.return_value = client

        result = await get_policy(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# create_policy
# ---------------------------------------------------------------------------

class TestCreatePolicy:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_policy(self, mock_get_client, ctx_elicit_accept_true):
        policy = _make_policy()
        client = AsyncMock()
        client.create_policy.return_value = (policy, None, None)
        mock_get_client.return_value = client

        policy_data = {"type": "OKTA_SIGN_ON", "name": "Test Policy", "status": "ACTIVE"}
        result = await create_policy(ctx=ctx_elicit_accept_true, policy_data=policy_data)

        assert result["id"] == POLICY_ID
        client.create_policy.assert_awaited_once_with(policy_data)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_policy.return_value = (None, None, "Policy name already in use")
        mock_get_client.return_value = client

        result = await create_policy(ctx=ctx_elicit_accept_true, policy_data={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_policy.side_effect = Exception("Connection error")
        mock_get_client.return_value = client

        result = await create_policy(ctx=ctx_elicit_accept_true, policy_data={})

        assert "error" in result


# ---------------------------------------------------------------------------
# update_policy
# ---------------------------------------------------------------------------

class TestUpdatePolicy:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_policy(self, mock_get_client, ctx_elicit_accept_true):
        policy = _make_policy(name="Updated Policy")
        policy.as_dict.return_value = {"id": POLICY_ID, "name": "Updated Policy", "type": "OKTA_SIGN_ON", "status": "ACTIVE"}
        client = AsyncMock()
        client.update_policy.return_value = (policy, None, None)
        mock_get_client.return_value = client

        policy_data = {"name": "Updated Policy"}
        result = await update_policy(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, policy_data=policy_data)

        assert result["name"] == "Updated Policy"
        client.update_policy.assert_awaited_once_with(POLICY_ID, policy_data)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await update_policy(ctx=ctx_elicit_accept_true, policy_id="../bad", policy_data={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_policy.return_value = (None, None, "Policy not found")
        mock_get_client.return_value = client

        result = await update_policy(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, policy_data={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_policy.side_effect = Exception("Connection error")
        mock_get_client.return_value = client

        result = await update_policy(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, policy_data={})

        assert "error" in result


# ---------------------------------------------------------------------------
# activate_policy
# ---------------------------------------------------------------------------

class TestActivatePolicy:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_activates_policy(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_policy.return_value = (None, None)
        mock_get_client.return_value = client

        result = await activate_policy(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID)

        assert result["success"] is True
        assert "activated successfully" in result["message"]
        client.activate_policy.assert_awaited_once_with(POLICY_ID)

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await activate_policy(ctx=ctx_elicit_accept_true, policy_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_policy.return_value = (None, "Policy not found")
        mock_get_client.return_value = client

        result = await activate_policy(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_policy.side_effect = Exception("Connection error")
        mock_get_client.return_value = client

        result = await activate_policy(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# list_policy_rules
# ---------------------------------------------------------------------------

class TestListPolicyRules:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_rules(self, mock_get_client, ctx_elicit_accept_true):
        rule = _make_rule()
        resp = _make_resp()
        client = AsyncMock()
        client.list_policy_rules.return_value = ([rule], resp, None)
        mock_get_client.return_value = client

        result = await list_policy_rules(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID)

        assert "rules" in result
        assert len(result["rules"]) == 1
        assert result["rules"][0]["id"] == RULE_ID
        assert result["has_next"] is False

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_policy_rules.return_value = ([], None, None)
        mock_get_client.return_value = client

        result = await list_policy_rules(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID)

        assert result == {"rules": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_policy_rules.return_value = (None, None, "Policy not found")
        mock_get_client.return_value = client

        result = await list_policy_rules(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_policy_rules.side_effect = Exception("Connection error")
        mock_get_client.return_value = client

        result = await list_policy_rules(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_id_rejected(self, ctx_elicit_accept_true):
        result = await list_policy_rules(ctx=ctx_elicit_accept_true, policy_id="bad/id")

        assert "error" in result


# ---------------------------------------------------------------------------
# get_policy_rule
# ---------------------------------------------------------------------------

class TestGetPolicyRule:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_rule(self, mock_get_client, ctx_elicit_accept_true):
        rule = _make_rule()
        client = AsyncMock()
        client.get_policy_rule.return_value = (rule, None, None)
        mock_get_client.return_value = client

        result = await get_policy_rule(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id=RULE_ID)

        assert result["id"] == RULE_ID
        client.get_policy_rule.assert_awaited_once_with(POLICY_ID, RULE_ID)

    @pytest.mark.asyncio
    async def test_invalid_policy_id_rejected(self, ctx_elicit_accept_true):
        result = await get_policy_rule(ctx=ctx_elicit_accept_true, policy_id="bad/id", rule_id=RULE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_rule_id_rejected(self, ctx_elicit_accept_true):
        result = await get_policy_rule(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id="bad/id")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_policy_rule.return_value = (None, None, "Rule not found")
        mock_get_client.return_value = client

        result = await get_policy_rule(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id=RULE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.get_policy_rule.side_effect = Exception("Connection error")
        mock_get_client.return_value = client

        result = await get_policy_rule(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id=RULE_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# create_policy_rule
# ---------------------------------------------------------------------------

class TestCreatePolicyRule:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_rule(self, mock_get_client, ctx_elicit_accept_true):
        rule = _make_rule()
        client = AsyncMock()
        client.create_policy_rule.return_value = (rule, None, None)
        mock_get_client.return_value = client

        rule_data = {"name": "Test Rule", "status": "ACTIVE"}
        result = await create_policy_rule(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_data=rule_data)

        assert result["id"] == RULE_ID
        client.create_policy_rule.assert_awaited_once_with(POLICY_ID, rule_data)

    @pytest.mark.asyncio
    async def test_invalid_policy_id_rejected(self, ctx_elicit_accept_true):
        result = await create_policy_rule(ctx=ctx_elicit_accept_true, policy_id="bad/id", rule_data={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_policy_rule.return_value = (None, None, "Invalid rule config")
        mock_get_client.return_value = client

        result = await create_policy_rule(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_data={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.create_policy_rule.side_effect = Exception("Connection error")
        mock_get_client.return_value = client

        result = await create_policy_rule(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_data={})

        assert "error" in result


# ---------------------------------------------------------------------------
# update_policy_rule
# ---------------------------------------------------------------------------

class TestUpdatePolicyRule:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_rule(self, mock_get_client, ctx_elicit_accept_true):
        rule = _make_rule(name="Updated Rule")
        rule.as_dict.return_value = {"id": RULE_ID, "name": "Updated Rule", "status": "ACTIVE"}
        client = AsyncMock()
        client.update_policy_rule.return_value = (rule, None, None)
        mock_get_client.return_value = client

        rule_data = {"name": "Updated Rule"}
        result = await update_policy_rule(
            ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id=RULE_ID, rule_data=rule_data
        )

        assert result["name"] == "Updated Rule"
        client.update_policy_rule.assert_awaited_once_with(POLICY_ID, RULE_ID, rule_data)

    @pytest.mark.asyncio
    async def test_invalid_policy_id_rejected(self, ctx_elicit_accept_true):
        result = await update_policy_rule(
            ctx=ctx_elicit_accept_true, policy_id="bad/id", rule_id=RULE_ID, rule_data={}
        )

        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_rule_id_rejected(self, ctx_elicit_accept_true):
        result = await update_policy_rule(
            ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id="bad/id", rule_data={}
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_policy_rule.return_value = (None, None, "Rule not found")
        mock_get_client.return_value = client

        result = await update_policy_rule(
            ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id=RULE_ID, rule_data={}
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.update_policy_rule.side_effect = Exception("Connection error")
        mock_get_client.return_value = client

        result = await update_policy_rule(
            ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id=RULE_ID, rule_data={}
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# activate_policy_rule
# ---------------------------------------------------------------------------

class TestActivatePolicyRule:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_activates_rule(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_policy_rule.return_value = (None, None)
        mock_get_client.return_value = client

        result = await activate_policy_rule(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id=RULE_ID)

        assert result["success"] is True
        assert "activated successfully" in result["message"]
        client.activate_policy_rule.assert_awaited_once_with(POLICY_ID, RULE_ID)

    @pytest.mark.asyncio
    async def test_invalid_ids_rejected(self, ctx_elicit_accept_true):
        result = await activate_policy_rule(ctx=ctx_elicit_accept_true, policy_id="bad/id", rule_id=RULE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_policy_rule.return_value = (None, "Rule not found")
        mock_get_client.return_value = client

        result = await activate_policy_rule(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id=RULE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.activate_policy_rule.side_effect = Exception("Connection error")
        mock_get_client.return_value = client

        result = await activate_policy_rule(ctx=ctx_elicit_accept_true, policy_id=POLICY_ID, rule_id=RULE_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# Policy lifecycle: create → get → update → activate → create_rule → activate_rule
# ---------------------------------------------------------------------------

class TestPolicyLifecycle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_policy_and_rule_lifecycle(self, mock_get_client, ctx_elicit_accept_true):
        created_policy = _make_policy(policy_id="00pnew123", name="New Policy")
        updated_policy = _make_policy(policy_id="00pnew123", name="Updated Policy")
        updated_policy.as_dict.return_value = {
            "id": "00pnew123", "name": "Updated Policy", "type": "OKTA_SIGN_ON", "status": "ACTIVE"
        }
        created_rule = _make_rule(rule_id="0prnew123", name="New Rule")

        client = AsyncMock()
        client.create_policy.return_value = (created_policy, None, None)
        client.get_policy.return_value = (created_policy, None, None)
        client.update_policy.return_value = (updated_policy, None, None)
        client.activate_policy.return_value = (None, None)
        client.create_policy_rule.return_value = (created_rule, None, None)
        client.activate_policy_rule.return_value = (None, None)
        mock_get_client.return_value = client

        # Step 1: create policy
        policy_data = {"type": "OKTA_SIGN_ON", "name": "New Policy"}
        create_result = await create_policy(ctx=ctx_elicit_accept_true, policy_data=policy_data)
        assert create_result["id"] == "00pnew123"

        # Step 2: get policy
        get_result = await get_policy(ctx=ctx_elicit_accept_true, policy_id="00pnew123")
        assert get_result["id"] == "00pnew123"

        # Step 3: update policy
        update_result = await update_policy(
            ctx=ctx_elicit_accept_true, policy_id="00pnew123", policy_data={"name": "Updated Policy"}
        )
        assert update_result["name"] == "Updated Policy"

        # Step 4: activate policy
        activate_result = await activate_policy(ctx=ctx_elicit_accept_true, policy_id="00pnew123")
        assert activate_result["success"] is True

        # Step 5: create rule
        rule_data = {"name": "New Rule", "status": "ACTIVE"}
        rule_result = await create_policy_rule(
            ctx=ctx_elicit_accept_true, policy_id="00pnew123", rule_data=rule_data
        )
        assert rule_result["id"] == "0prnew123"

        # Step 6: activate rule
        activate_rule_result = await activate_policy_rule(
            ctx=ctx_elicit_accept_true, policy_id="00pnew123", rule_id="0prnew123"
        )
        assert activate_rule_result["success"] is True
