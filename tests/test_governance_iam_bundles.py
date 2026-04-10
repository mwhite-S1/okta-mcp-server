# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for Admin IAM governance bundle tools and user role governance sources."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.governance.iam_bundles import (
    create_iam_governance_bundle,
    delete_iam_governance_bundle,
    get_iam_governance_bundle,
    get_iam_governance_opt_in_status,
    get_user_role_governance_grant,
    get_user_role_governance_grant_resources,
    get_user_role_governance_sources,
    list_iam_bundle_entitlements,
    list_iam_bundle_entitlement_values,
    list_iam_governance_bundles,
    opt_in_iam_governance,
    opt_out_iam_governance,
    replace_iam_governance_bundle,
)

PATCH_CLIENT = "okta_mcp_server.tools.governance.iam_bundles.get_okta_client"

BUNDLE_ID = "bnd0001testABCDEF"
ENTITLEMENT_ID = "ent0001testABCDEF"
USER_ID = "00u0001testABCDEF"
ROLE_ASSIGNMENT_ID = "ra0001testABCDEF"
GRANT_ID = "grnt0001testABCDEF"

BUNDLE_DICT = {
    "id": BUNDLE_ID,
    "name": "Admin Bundle",
    "description": "Test bundle",
    "orn": "orn:okta:idp:test:governance-bundles:bnd0001testABCDEF",
    "status": "ACTIVE",
}
ENTITLEMENT_DICT = {
    "id": ENTITLEMENT_ID,
    "name": "Super Admin Role",
    "role": "SUPER_ADMIN",
}
GRANT_DICT = {
    "grantId": GRANT_ID,
    "bundleId": BUNDLE_ID,
    "type": "ENTITLEMENT-BUNDLE",
}


def _make_executor(body=None, execute_error=None, no_content=False):
    executor = AsyncMock()
    executor.create_request.return_value = (MagicMock(), None)
    if execute_error:
        executor.execute.return_value = (MagicMock(), execute_error)
    elif no_content:
        executor.execute.return_value = (None, None)
    else:
        resp = MagicMock()
        resp.get_body.return_value = body
        executor.execute.return_value = (resp, None)
    return executor


def _make_client(body=None, execute_error=None, no_content=False):
    executor = _make_executor(body=body, execute_error=execute_error, no_content=no_content)
    client = MagicMock()
    client.get_request_executor.return_value = executor
    client.get_base_url.return_value = "https://test.okta.com"
    return client


# ---------------------------------------------------------------------------
# list_iam_governance_bundles
# ---------------------------------------------------------------------------

class TestListIamGovernanceBundles:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_bundles(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"bundles": [BUNDLE_DICT]})
        mock_get_client.return_value = client

        result = await list_iam_governance_bundles(ctx=ctx_elicit_accept_true)

        assert result["bundles"][0]["id"] == BUNDLE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_iam_governance_bundles(ctx=ctx_elicit_accept_true)

        assert result == {}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="forbidden")
        mock_get_client.return_value = client

        result = await list_iam_governance_bundles(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("connection failed")

        result = await list_iam_governance_bundles(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_pagination_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"bundles": []})
        mock_get_client.return_value = client

        await list_iam_governance_bundles(ctx=ctx_elicit_accept_true, after="cursor123", limit=5)

        url = client.get_request_executor().create_request.call_args[0][1]
        assert "after=cursor123" in url
        assert "limit=5" in url


# ---------------------------------------------------------------------------
# create_iam_governance_bundle
# ---------------------------------------------------------------------------

class TestCreateIamGovernanceBundle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_bundle(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=BUNDLE_DICT)
        mock_get_client.return_value = client

        result = await create_iam_governance_bundle(
            ctx=ctx_elicit_accept_true,
            name="Admin Bundle",
            description="Test bundle",
        )

        assert result["id"] == BUNDLE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_payload_contains_name(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=BUNDLE_DICT)
        mock_get_client.return_value = client

        await create_iam_governance_bundle(
            ctx=ctx_elicit_accept_true,
            name="My Bundle",
            entitlements=[{"role": "SUPER_ADMIN"}],
        )

        body = client.get_request_executor().create_request.call_args[0][2]
        assert body["name"] == "My Bundle"
        assert body["entitlements"] == [{"role": "SUPER_ADMIN"}]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="validation error")
        mock_get_client.return_value = client

        result = await create_iam_governance_bundle(ctx=ctx_elicit_accept_true, name="X")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await create_iam_governance_bundle(ctx=ctx_elicit_accept_true, name="X")

        assert "error" in result


# ---------------------------------------------------------------------------
# get_iam_governance_bundle
# ---------------------------------------------------------------------------

class TestGetIamGovernanceBundle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_bundle(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=BUNDLE_DICT)
        mock_get_client.return_value = client

        result = await get_iam_governance_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert result["id"] == BUNDLE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=BUNDLE_DICT)
        mock_get_client.return_value = client

        await get_iam_governance_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        url = client.get_request_executor().create_request.call_args[0][1]
        assert f"/api/v1/iam/governance/bundles/{BUNDLE_ID}" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="not found")
        mock_get_client.return_value = client

        result = await get_iam_governance_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await get_iam_governance_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# replace_iam_governance_bundle
# ---------------------------------------------------------------------------

class TestReplaceIamGovernanceBundle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_replaces_bundle(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={**BUNDLE_DICT, "name": "Updated"})
        mock_get_client.return_value = client

        result = await replace_iam_governance_bundle(
            ctx=ctx_elicit_accept_true,
            bundle_id=BUNDLE_ID,
            name="Updated",
        )

        assert result["name"] == "Updated"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_uses_put_method(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=BUNDLE_DICT)
        mock_get_client.return_value = client

        await replace_iam_governance_bundle(
            ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID, name="X"
        )

        method = client.get_request_executor().create_request.call_args[0][0]
        assert method == "PUT"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="bad request")
        mock_get_client.return_value = client

        result = await replace_iam_governance_bundle(
            ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID, name="X"
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await replace_iam_governance_bundle(
            ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID, name="X"
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# delete_iam_governance_bundle
# ---------------------------------------------------------------------------

class TestDeleteIamGovernanceBundle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_deletes_when_confirmed(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await delete_iam_governance_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert "deleted successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_cancelled_when_declined(self, ctx_elicit_decline):
        result = await delete_iam_governance_bundle(ctx=ctx_elicit_decline, bundle_id=BUNDLE_ID)

        assert "cancelled" in result["message"]

    @pytest.mark.asyncio
    async def test_fallback_when_no_elicitation(self, ctx_no_elicitation):
        result = await delete_iam_governance_bundle(ctx=ctx_no_elicitation, bundle_id=BUNDLE_ID)

        assert "confirmation_required" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="forbidden")
        mock_get_client.return_value = client

        result = await delete_iam_governance_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await delete_iam_governance_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# list_iam_bundle_entitlements
# ---------------------------------------------------------------------------

class TestListIamBundleEntitlements:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_entitlements(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"entitlements": [ENTITLEMENT_DICT]})
        mock_get_client.return_value = client

        result = await list_iam_bundle_entitlements(
            ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID
        )

        assert result["entitlements"][0]["id"] == ENTITLEMENT_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"entitlements": []})
        mock_get_client.return_value = client

        await list_iam_bundle_entitlements(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        url = client.get_request_executor().create_request.call_args[0][1]
        assert f"/api/v1/iam/governance/bundles/{BUNDLE_ID}/entitlements" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_pagination_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"entitlements": []})
        mock_get_client.return_value = client

        await list_iam_bundle_entitlements(
            ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID, after="cur1", limit=10
        )

        url = client.get_request_executor().create_request.call_args[0][1]
        assert "after=cur1" in url
        assert "limit=10" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="not found")
        mock_get_client.return_value = client

        result = await list_iam_bundle_entitlements(
            ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await list_iam_bundle_entitlements(
            ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# list_iam_bundle_entitlement_values
# ---------------------------------------------------------------------------

class TestListIamBundleEntitlementValues:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_values(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"entitlementValues": [{"id": "ev001", "name": "group-a"}]})
        mock_get_client.return_value = client

        result = await list_iam_bundle_entitlement_values(
            ctx=ctx_elicit_accept_true,
            bundle_id=BUNDLE_ID,
            entitlement_id=ENTITLEMENT_ID,
        )

        assert result["entitlementValues"][0]["id"] == "ev001"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"entitlementValues": []})
        mock_get_client.return_value = client

        await list_iam_bundle_entitlement_values(
            ctx=ctx_elicit_accept_true,
            bundle_id=BUNDLE_ID,
            entitlement_id=ENTITLEMENT_ID,
        )

        url = client.get_request_executor().create_request.call_args[0][1]
        assert f"/api/v1/iam/governance/bundles/{BUNDLE_ID}/entitlements/{ENTITLEMENT_ID}/values" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_pagination_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"entitlementValues": []})
        mock_get_client.return_value = client

        await list_iam_bundle_entitlement_values(
            ctx=ctx_elicit_accept_true,
            bundle_id=BUNDLE_ID,
            entitlement_id=ENTITLEMENT_ID,
            after="cur2",
            limit=15,
        )

        url = client.get_request_executor().create_request.call_args[0][1]
        assert "after=cur2" in url
        assert "limit=15" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="forbidden")
        mock_get_client.return_value = client

        result = await list_iam_bundle_entitlement_values(
            ctx=ctx_elicit_accept_true,
            bundle_id=BUNDLE_ID,
            entitlement_id=ENTITLEMENT_ID,
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await list_iam_bundle_entitlement_values(
            ctx=ctx_elicit_accept_true,
            bundle_id=BUNDLE_ID,
            entitlement_id=ENTITLEMENT_ID,
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# get_iam_governance_opt_in_status
# ---------------------------------------------------------------------------

class TestGetIamGovernanceOptInStatus:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_status(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"optInStatus": "OPTED_IN"})
        mock_get_client.return_value = client

        result = await get_iam_governance_opt_in_status(ctx=ctx_elicit_accept_true)

        assert result["optInStatus"] == "OPTED_IN"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"optInStatus": "OPTED_OUT"})
        mock_get_client.return_value = client

        await get_iam_governance_opt_in_status(ctx=ctx_elicit_accept_true)

        url = client.get_request_executor().create_request.call_args[0][1]
        assert "/api/v1/iam/governance/optIn" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="forbidden")
        mock_get_client.return_value = client

        result = await get_iam_governance_opt_in_status(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await get_iam_governance_opt_in_status(ctx=ctx_elicit_accept_true)

        assert "error" in result


# ---------------------------------------------------------------------------
# opt_in_iam_governance
# ---------------------------------------------------------------------------

class TestOptInIamGovernance:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_opts_in(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"optInStatus": "OPTING_IN"})
        mock_get_client.return_value = client

        result = await opt_in_iam_governance(ctx=ctx_elicit_accept_true)

        assert result["optInStatus"] == "OPTING_IN"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_uses_post(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"optInStatus": "OPTING_IN"})
        mock_get_client.return_value = client

        await opt_in_iam_governance(ctx=ctx_elicit_accept_true)

        method = client.get_request_executor().create_request.call_args[0][0]
        assert method == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"optInStatus": "OPTING_IN"})
        mock_get_client.return_value = client

        await opt_in_iam_governance(ctx=ctx_elicit_accept_true)

        url = client.get_request_executor().create_request.call_args[0][1]
        assert "/api/v1/iam/governance/optIn" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="forbidden")
        mock_get_client.return_value = client

        result = await opt_in_iam_governance(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await opt_in_iam_governance(ctx=ctx_elicit_accept_true)

        assert "error" in result


# ---------------------------------------------------------------------------
# opt_out_iam_governance
# ---------------------------------------------------------------------------

class TestOptOutIamGovernance:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_opts_out_when_confirmed(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"optInStatus": "OPTING_OUT"})
        mock_get_client.return_value = client

        result = await opt_out_iam_governance(ctx=ctx_elicit_accept_true)

        assert result["optInStatus"] == "OPTING_OUT"

    @pytest.mark.asyncio
    async def test_cancelled_when_declined(self, ctx_elicit_decline):
        result = await opt_out_iam_governance(ctx=ctx_elicit_decline)

        assert "cancelled" in result["message"]

    @pytest.mark.asyncio
    async def test_fallback_when_no_elicitation(self, ctx_no_elicitation):
        result = await opt_out_iam_governance(ctx=ctx_no_elicitation)

        assert "confirmation_required" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_uses_post_opt_out(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"optInStatus": "OPTING_OUT"})
        mock_get_client.return_value = client

        await opt_out_iam_governance(ctx=ctx_elicit_accept_true)

        url = client.get_request_executor().create_request.call_args[0][1]
        assert "/api/v1/iam/governance/optOut" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="forbidden")
        mock_get_client.return_value = client

        result = await opt_out_iam_governance(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await opt_out_iam_governance(ctx=ctx_elicit_accept_true)

        assert "error" in result


# ---------------------------------------------------------------------------
# get_user_role_governance_sources
# ---------------------------------------------------------------------------

class TestGetUserRoleGovernanceSources:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_grants(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"grants": [GRANT_DICT]})
        mock_get_client.return_value = client

        result = await get_user_role_governance_sources(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
        )

        assert result["grants"][0]["grantId"] == GRANT_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"grants": []})
        mock_get_client.return_value = client

        await get_user_role_governance_sources(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
        )

        url = client.get_request_executor().create_request.call_args[0][1]
        assert f"/api/v1/users/{USER_ID}/roles/{ROLE_ASSIGNMENT_ID}/governance" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="not found")
        mock_get_client.return_value = client

        result = await get_user_role_governance_sources(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await get_user_role_governance_sources(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# get_user_role_governance_grant
# ---------------------------------------------------------------------------

class TestGetUserRoleGovernanceGrant:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_grant(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=GRANT_DICT)
        mock_get_client.return_value = client

        result = await get_user_role_governance_grant(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
            grant_id=GRANT_ID,
        )

        assert result["grantId"] == GRANT_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=GRANT_DICT)
        mock_get_client.return_value = client

        await get_user_role_governance_grant(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
            grant_id=GRANT_ID,
        )

        url = client.get_request_executor().create_request.call_args[0][1]
        assert f"/api/v1/users/{USER_ID}/roles/{ROLE_ASSIGNMENT_ID}/governance/{GRANT_ID}" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="not found")
        mock_get_client.return_value = client

        result = await get_user_role_governance_grant(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
            grant_id=GRANT_ID,
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await get_user_role_governance_grant(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
            grant_id=GRANT_ID,
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# get_user_role_governance_grant_resources
# ---------------------------------------------------------------------------

class TestGetUserRoleGovernanceGrantResources:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_resources(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"resources": [{"label": "My App", "resource": "app001"}]})
        mock_get_client.return_value = client

        result = await get_user_role_governance_grant_resources(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
            grant_id=GRANT_ID,
        )

        assert result["resources"][0]["resource"] == "app001"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"resources": []})
        mock_get_client.return_value = client

        await get_user_role_governance_grant_resources(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
            grant_id=GRANT_ID,
        )

        url = client.get_request_executor().create_request.call_args[0][1]
        assert f"/api/v1/users/{USER_ID}/roles/{ROLE_ASSIGNMENT_ID}/governance/{GRANT_ID}/resources" in url

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="forbidden")
        mock_get_client.return_value = client

        result = await get_user_role_governance_grant_resources(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
            grant_id=GRANT_ID,
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("boom")

        result = await get_user_role_governance_grant_resources(
            ctx=ctx_elicit_accept_true,
            user_id=USER_ID,
            role_assignment_id=ROLE_ASSIGNMENT_ID,
            grant_id=GRANT_ID,
        )

        assert "error" in result
