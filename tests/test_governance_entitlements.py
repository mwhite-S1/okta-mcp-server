# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for governance entitlement tools: entitlements, values, bundles, grants, principal entitlements."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.governance.entitlements import (
    create_entitlement,
    create_entitlement_bundle,
    create_grant,
    delete_entitlement,
    delete_entitlement_bundle,
    get_entitlement,
    get_entitlement_bundle,
    get_entitlement_value,
    get_grant,
    get_principal_access,
    get_principal_entitlement_history,
    get_principal_entitlements_change,
    list_entitlement_bundles,
    list_entitlement_values,
    list_entitlements,
    list_grants,
    list_principal_entitlements,
    patch_grant,
    update_entitlement_bundle,
    update_grant,
)


PATCH_CLIENT = "okta_mcp_server.tools.governance.entitlements.get_okta_client"

ENTITLEMENT_ID = "ent0001testABCDEF"
BUNDLE_ID = "bnd0001testABCDEF"
GRANT_ID = "grn0001testABCDEF"
PRINCIPAL_ID = "00u1234567890abcdef"
RESOURCE_ID = "res0001testABCDEF"
VALUE_ID = "val0001testABCDEF"
CHANGE_ID = "chg0001testABCDEF"

FILTER_RESOURCE = f'resourceId eq "{RESOURCE_ID}"'
FILTER_PRINCIPAL = f'principalId eq "{PRINCIPAL_ID}"'

ENTITLEMENT_DICT = {"id": ENTITLEMENT_ID, "name": "Admin", "resourceId": RESOURCE_ID}
BUNDLE_DICT = {"id": BUNDLE_ID, "name": "Dev Bundle"}
GRANT_DICT = {"id": GRANT_ID, "principalId": PRINCIPAL_ID, "entitlementId": ENTITLEMENT_ID}


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


def _url(client):
    return client.get_request_executor.return_value.create_request.call_args[0][1]


# ---------------------------------------------------------------------------
# list_entitlements
# ---------------------------------------------------------------------------

class TestListEntitlements:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_entitlements(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [ENTITLEMENT_DICT]})
        mock_get_client.return_value = client

        result = await list_entitlements(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert result["items"][0]["id"] == ENTITLEMENT_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_entitlements(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_entitlements(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert "filter" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_entitlements(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert "/governance/api/v1/entitlements" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_entitlements(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_entitlements(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert "error" in result


# ---------------------------------------------------------------------------
# create_entitlement
# ---------------------------------------------------------------------------

class TestCreateEntitlement:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_and_returns(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=ENTITLEMENT_DICT)
        mock_get_client.return_value = client

        result = await create_entitlement(ctx=ctx_elicit_accept_true, entitlement=ENTITLEMENT_DICT)

        assert result["id"] == ENTITLEMENT_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Bad request")
        mock_get_client.return_value = client

        result = await create_entitlement(ctx=ctx_elicit_accept_true, entitlement=ENTITLEMENT_DICT)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_entitlement(ctx=ctx_elicit_accept_true, entitlement=ENTITLEMENT_DICT)

        assert "error" in result


# ---------------------------------------------------------------------------
# get_entitlement
# ---------------------------------------------------------------------------

class TestGetEntitlement:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_entitlement(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=ENTITLEMENT_DICT)
        mock_get_client.return_value = client

        result = await get_entitlement(ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID)

        assert result["id"] == ENTITLEMENT_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=ENTITLEMENT_DICT)
        mock_get_client.return_value = client

        await get_entitlement(ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID)

        assert ENTITLEMENT_ID in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not found")
        mock_get_client.return_value = client

        result = await get_entitlement(ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# delete_entitlement
# ---------------------------------------------------------------------------

class TestDeleteEntitlement:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_success_message(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await delete_entitlement(ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID)

        assert "deleted successfully" in result["message"]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not found")
        mock_get_client.return_value = client

        result = await delete_entitlement(ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# list_entitlement_values / get_entitlement_value
# ---------------------------------------------------------------------------

class TestListEntitlementValues:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_values(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [{"id": "ev001", "name": "Admin"}]})
        mock_get_client.return_value = client

        result = await list_entitlement_values(
            ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID
        )

        assert len(result["items"]) == 1

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_entitlement_id_in_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_entitlement_values(ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID)

        assert ENTITLEMENT_ID in _url(client)
        assert "values" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not found")
        mock_get_client.return_value = client

        result = await list_entitlement_values(
            ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_entitlement_values(
            ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID
        )

        assert "error" in result


class TestGetEntitlementValue:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_value(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": VALUE_ID, "name": "Admin"})
        mock_get_client.return_value = client

        result = await get_entitlement_value(
            ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID, value_id=VALUE_ID
        )

        assert result["id"] == VALUE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": VALUE_ID})
        mock_get_client.return_value = client

        await get_entitlement_value(
            ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID, value_id=VALUE_ID
        )

        assert ENTITLEMENT_ID in _url(client)
        assert VALUE_ID in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not found")
        mock_get_client.return_value = client

        result = await get_entitlement_value(
            ctx=ctx_elicit_accept_true, entitlement_id=ENTITLEMENT_ID, value_id=VALUE_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# list_entitlement_bundles / create / get / update / delete
# ---------------------------------------------------------------------------

class TestListEntitlementBundles:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_bundles(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [BUNDLE_DICT]})
        mock_get_client.return_value = client

        result = await list_entitlement_bundles(ctx=ctx_elicit_accept_true)

        assert result["items"][0]["id"] == BUNDLE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_entitlement_bundles(ctx=ctx_elicit_accept_true)

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_entitlement_bundles(ctx=ctx_elicit_accept_true)

        assert "entitlement-bundles" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_entitlement_bundles(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_entitlement_bundles(ctx=ctx_elicit_accept_true)

        assert "error" in result


class TestCreateEntitlementBundle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_and_returns(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=BUNDLE_DICT)
        mock_get_client.return_value = client

        result = await create_entitlement_bundle(ctx=ctx_elicit_accept_true, bundle=BUNDLE_DICT)

        assert result["id"] == BUNDLE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Bad request")
        mock_get_client.return_value = client

        result = await create_entitlement_bundle(ctx=ctx_elicit_accept_true, bundle=BUNDLE_DICT)

        assert "error" in result


class TestGetEntitlementBundle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_bundle(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=BUNDLE_DICT)
        mock_get_client.return_value = client

        result = await get_entitlement_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert result["id"] == BUNDLE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=BUNDLE_DICT)
        mock_get_client.return_value = client

        await get_entitlement_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert BUNDLE_ID in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not found")
        mock_get_client.return_value = client

        result = await get_entitlement_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert "error" in result


class TestUpdateEntitlementBundle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_updated(self, mock_get_client, ctx_elicit_accept_true):
        updated = {**BUNDLE_DICT, "name": "Updated Bundle"}
        client = _make_client(body=updated)
        mock_get_client.return_value = client

        result = await update_entitlement_bundle(
            ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID, bundle=updated
        )

        assert result["name"] == "Updated Bundle"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not found")
        mock_get_client.return_value = client

        result = await update_entitlement_bundle(
            ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID, bundle=BUNDLE_DICT
        )

        assert "error" in result


class TestDeleteEntitlementBundle:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_success_message(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await delete_entitlement_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert "deleted successfully" in result["message"]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not found")
        mock_get_client.return_value = client

        result = await delete_entitlement_bundle(ctx=ctx_elicit_accept_true, bundle_id=BUNDLE_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# list_grants / create / get / update / patch
# ---------------------------------------------------------------------------

class TestListGrants:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_grants(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [GRANT_DICT]})
        mock_get_client.return_value = client

        result = await list_grants(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert result["items"][0]["principalId"] == PRINCIPAL_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_grants(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert "filter" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_resource_id_in_filter(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_grants(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert "resourceId" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_principal_id_in_filter(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_grants(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert "principalId" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_grants(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_grants(ctx=ctx_elicit_accept_true, filter=FILTER_RESOURCE)

        assert "error" in result


class TestCreateGrant:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_and_returns(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=GRANT_DICT)
        mock_get_client.return_value = client

        result = await create_grant(ctx=ctx_elicit_accept_true, grant=GRANT_DICT)

        assert result["id"] == GRANT_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Bad request")
        mock_get_client.return_value = client

        result = await create_grant(ctx=ctx_elicit_accept_true, grant=GRANT_DICT)

        assert "error" in result


class TestGetGrant:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_grant(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=GRANT_DICT)
        mock_get_client.return_value = client

        result = await get_grant(ctx=ctx_elicit_accept_true, grant_id=GRANT_ID)

        assert result["id"] == GRANT_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=GRANT_DICT)
        mock_get_client.return_value = client

        await get_grant(ctx=ctx_elicit_accept_true, grant_id=GRANT_ID)

        assert GRANT_ID in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not found")
        mock_get_client.return_value = client

        result = await get_grant(ctx=ctx_elicit_accept_true, grant_id=GRANT_ID)

        assert "error" in result


class TestUpdateGrant:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_updated(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=GRANT_DICT)
        mock_get_client.return_value = client

        result = await update_grant(ctx=ctx_elicit_accept_true, grant_id=GRANT_ID, grant=GRANT_DICT)

        assert result["id"] == GRANT_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not found")
        mock_get_client.return_value = client

        result = await update_grant(ctx=ctx_elicit_accept_true, grant_id=GRANT_ID, grant=GRANT_DICT)

        assert "error" in result


class TestPatchGrant:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_patched(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=GRANT_DICT)
        mock_get_client.return_value = client

        result = await patch_grant(
            ctx=ctx_elicit_accept_true,
            grant_id=GRANT_ID,
            operations=[{"op": "replace", "path": "/status", "value": "ACTIVE"}],
        )

        assert result["id"] == GRANT_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await patch_grant(ctx=ctx_elicit_accept_true, grant_id=GRANT_ID, operations=[])

        assert "error" in result


# ---------------------------------------------------------------------------
# list_principal_entitlements
# ---------------------------------------------------------------------------

class TestListPrincipalEntitlements:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_entitlements(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [{"principalId": PRINCIPAL_ID}]})
        mock_get_client.return_value = client

        result = await list_principal_entitlements(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert result["items"][0]["principalId"] == PRINCIPAL_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_principal_entitlements(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert "principalId" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_principal_entitlements(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_principal_entitlements(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert "error" in result


# ---------------------------------------------------------------------------
# get_principal_entitlement_history
# ---------------------------------------------------------------------------

class TestGetPrincipalEntitlementHistory:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_history(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [{"action": "GRANT", "principalId": PRINCIPAL_ID}]})
        mock_get_client.return_value = client

        result = await get_principal_entitlement_history(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert result["items"][0]["action"] == "GRANT"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await get_principal_entitlement_history(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert "principalId" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await get_principal_entitlement_history(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert "principal-entitlements/history" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await get_principal_entitlement_history(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_principal_entitlement_history(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert "error" in result


# ---------------------------------------------------------------------------
# get_principal_entitlements_change
# ---------------------------------------------------------------------------

class TestGetPrincipalEntitlementsChange:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_change(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": CHANGE_ID, "action": "GRANT"})
        mock_get_client.return_value = client

        result = await get_principal_entitlements_change(ctx=ctx_elicit_accept_true, change_id=CHANGE_ID)

        assert result["id"] == CHANGE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": CHANGE_ID})
        mock_get_client.return_value = client

        await get_principal_entitlements_change(ctx=ctx_elicit_accept_true, change_id=CHANGE_ID)

        assert "principal-entitlements-changes" in _url(client)
        assert CHANGE_ID in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not found")
        mock_get_client.return_value = client

        result = await get_principal_entitlements_change(ctx=ctx_elicit_accept_true, change_id=CHANGE_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# get_principal_access
# ---------------------------------------------------------------------------

class TestGetPrincipalAccess:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_access_summary(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [{"principalId": PRINCIPAL_ID, "resourceId": RESOURCE_ID}]})
        mock_get_client.return_value = client

        result = await get_principal_access(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert result["items"][0]["principalId"] == PRINCIPAL_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await get_principal_access(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert "principal-access" in _url(client)

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await get_principal_access(ctx=ctx_elicit_accept_true, filter=FILTER_PRINCIPAL)

        assert "error" in result
