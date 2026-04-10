# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for access request tools: catalog, requests, conditions, sequences, settings."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.governance.access_requests import (
    activate_request_condition,
    add_request_message,
    cancel_access_request,
    create_access_request,
    create_request_condition,
    deactivate_request_condition,
    delete_request_condition,
    delete_request_sequence,
    get_access_catalog_entry,
    get_access_request,
    get_catalog_entry_request_fields,
    get_request_condition,
    get_request_sequence,
    get_resource_request_settings,
    list_access_catalog_entries,
    list_access_requests,
    list_request_conditions,
    list_request_sequences,
    list_request_settings,
    list_user_catalog_entries,
    update_request_condition,
    update_request_settings,
    update_resource_request_settings,
)


PATCH_CLIENT = "okta_mcp_server.tools.governance.access_requests.get_okta_client"

ENTRY_ID = "cat0001testABCDEF"
REQUEST_ID = "req0001testABCDEF"
USER_ID = "00u1234567890abcdef"
RESOURCE_ID = "res0001testABCDEF"
CONDITION_ID = "cond001testABCDEF"
SEQUENCE_ID = "seq0001testABCDEF"

CATALOG_ENTRY_DICT = {"id": ENTRY_ID, "name": "Salesforce Admin", "resourceType": "APP"}
ACCESS_REQUEST_DICT = {"id": REQUEST_ID, "requesterId": USER_ID, "status": "PENDING"}
CONDITION_DICT = {"id": CONDITION_ID, "resourceId": RESOURCE_ID, "type": "AUTO_APPROVE"}
SEQUENCE_DICT = {"id": SEQUENCE_ID, "resourceId": RESOURCE_ID, "name": "Standard Approval"}


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
# list_access_catalog_entries
# ---------------------------------------------------------------------------

FILTER_TOP_LEVEL = "not(parent pr)"
FILTER_CHILDREN = f'parent eq "{ENTRY_ID}"'


class TestListAccessCatalogEntries:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_entries(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": [CATALOG_ENTRY_DICT]})
        mock_get_client.return_value = client

        result = await list_access_catalog_entries(
            ctx=ctx_elicit_accept_true, filter=FILTER_TOP_LEVEL
        )

        assert result["data"][0]["id"] == ENTRY_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_access_catalog_entries(
            ctx=ctx_elicit_accept_true, filter=FILTER_TOP_LEVEL
        )

        assert result == {"data": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_access_catalog_entries(
            ctx=ctx_elicit_accept_true, filter=FILTER_TOP_LEVEL
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "filter=" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_match_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_access_catalog_entries(
            ctx=ctx_elicit_accept_true, filter=FILTER_TOP_LEVEL, match="figma"
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "match=figma" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_after_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_access_catalog_entries(
            ctx=ctx_elicit_accept_true, filter=FILTER_TOP_LEVEL, after="cursor456"
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "after=cursor456" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_access_catalog_entries(
            ctx=ctx_elicit_accept_true, filter=FILTER_TOP_LEVEL
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/governance/api/v2/catalogs/default/entries" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_access_catalog_entries(
            ctx=ctx_elicit_accept_true, filter=FILTER_TOP_LEVEL
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_access_catalog_entries(
            ctx=ctx_elicit_accept_true, filter=FILTER_TOP_LEVEL
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# get_access_catalog_entry
# ---------------------------------------------------------------------------

class TestGetAccessCatalogEntry:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_entry(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=CATALOG_ENTRY_DICT)
        mock_get_client.return_value = client

        result = await get_access_catalog_entry(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert result["id"] == ENTRY_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_entry_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=CATALOG_ENTRY_DICT)
        mock_get_client.return_value = client

        await get_access_catalog_entry(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert ENTRY_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Entry not found")
        mock_get_client.return_value = client

        result = await get_access_catalog_entry(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_access_catalog_entry(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# get_catalog_entry_request_fields
# ---------------------------------------------------------------------------

class TestGetCatalogEntryRequestFields:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_request_fields(self, mock_get_client, ctx_elicit_accept_true):
        fields = {"data": [{"id": "fld001", "type": "TEXT", "label": "Justification"}]}
        client = _make_client(body=fields)
        mock_get_client.return_value = client

        result = await get_catalog_entry_request_fields(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, user_id=USER_ID
        )

        assert result["data"][0]["id"] == "fld001"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_both_ids_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await get_catalog_entry_request_fields(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, user_id=USER_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert ENTRY_ID in url_arg
        assert USER_ID in url_arg
        assert "request-fields" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_metadata_risk_assessment(self, mock_get_client, ctx_elicit_accept_true):
        body = {
            "data": [],
            "metadata": {"riskAssessment": {"allowed": False, "rules": []}},
        }
        client = _make_client(body=body)
        mock_get_client.return_value = client

        result = await get_catalog_entry_request_fields(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, user_id=USER_ID
        )

        assert result["metadata"]["riskAssessment"]["allowed"] is False

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await get_catalog_entry_request_fields(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, user_id=USER_ID
        )

        assert result == {"data": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Entry not found")
        mock_get_client.return_value = client

        result = await get_catalog_entry_request_fields(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, user_id=USER_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_catalog_entry_request_fields(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, user_id=USER_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# list_user_catalog_entries
# ---------------------------------------------------------------------------

class TestListUserCatalogEntries:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_entries(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": [CATALOG_ENTRY_DICT]})
        mock_get_client.return_value = client

        result = await list_user_catalog_entries(
            ctx=ctx_elicit_accept_true, user_id=USER_ID, filter=FILTER_TOP_LEVEL
        )

        assert result["data"][0]["id"] == ENTRY_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_user_catalog_entries(
            ctx=ctx_elicit_accept_true, user_id=USER_ID, filter=FILTER_TOP_LEVEL
        )

        assert result == {"data": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_user_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_user_catalog_entries(
            ctx=ctx_elicit_accept_true, user_id=USER_ID, filter=FILTER_TOP_LEVEL
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert USER_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_user_catalog_entries(
            ctx=ctx_elicit_accept_true, user_id=USER_ID, filter=FILTER_TOP_LEVEL
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "filter=" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_match_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_user_catalog_entries(
            ctx=ctx_elicit_accept_true, user_id=USER_ID, filter=FILTER_TOP_LEVEL, match="figma"
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "match=figma" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="User not found")
        mock_get_client.return_value = client

        result = await list_user_catalog_entries(
            ctx=ctx_elicit_accept_true, user_id=USER_ID, filter=FILTER_TOP_LEVEL
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_user_catalog_entries(
            ctx=ctx_elicit_accept_true, user_id=USER_ID, filter=FILTER_TOP_LEVEL
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# list_access_requests
# ---------------------------------------------------------------------------

class TestListAccessRequests:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_requests(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [ACCESS_REQUEST_DICT]})
        mock_get_client.return_value = client

        result = await list_access_requests(ctx=ctx_elicit_accept_true)

        assert result["items"][0]["id"] == REQUEST_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_access_requests(ctx=ctx_elicit_accept_true)

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_access_requests(ctx=ctx_elicit_accept_true, filter=f'requesterId eq "{USER_ID}"')

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "filter=" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_order_by_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_access_requests(ctx=ctx_elicit_accept_true, order_by="created desc")

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "orderBy=" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_access_requests(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/governance/api/v2/requests" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_access_requests(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_access_requests(ctx=ctx_elicit_accept_true)

        assert "error" in result


# ---------------------------------------------------------------------------
# get_access_request
# ---------------------------------------------------------------------------

class TestGetAccessRequest:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_request(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=ACCESS_REQUEST_DICT)
        mock_get_client.return_value = client

        result = await get_access_request(ctx=ctx_elicit_accept_true, request_id=REQUEST_ID)

        assert result["id"] == REQUEST_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_request_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=ACCESS_REQUEST_DICT)
        mock_get_client.return_value = client

        await get_access_request(ctx=ctx_elicit_accept_true, request_id=REQUEST_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REQUEST_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Request not found")
        mock_get_client.return_value = client

        result = await get_access_request(ctx=ctx_elicit_accept_true, request_id=REQUEST_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_access_request(ctx=ctx_elicit_accept_true, request_id=REQUEST_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# create_access_request
# ---------------------------------------------------------------------------

class TestCreateAccessRequest:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_request(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=ACCESS_REQUEST_DICT)
        mock_get_client.return_value = client

        result = await create_access_request(
            ctx=ctx_elicit_accept_true,
            catalog_entry_id=ENTRY_ID,
            requester_id=USER_ID,
        )

        assert result["id"] == REQUEST_ID
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_payload_structure(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=ACCESS_REQUEST_DICT)
        mock_get_client.return_value = client

        await create_access_request(
            ctx=ctx_elicit_accept_true,
            catalog_entry_id=ENTRY_ID,
            requester_id=USER_ID,
            justification="Need for project X",
        )

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["catalogEntryId"] == ENTRY_ID
        assert body_arg["requesterId"] == USER_ID
        assert body_arg["justification"] == "Need for project X"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=ACCESS_REQUEST_DICT)
        mock_get_client.return_value = client

        await create_access_request(
            ctx=ctx_elicit_accept_true, catalog_entry_id=ENTRY_ID, requester_id=USER_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/governance/api/v2/requests" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Invalid request")
        mock_get_client.return_value = client

        result = await create_access_request(
            ctx=ctx_elicit_accept_true, catalog_entry_id=ENTRY_ID, requester_id=USER_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_access_request(
            ctx=ctx_elicit_accept_true, catalog_entry_id=ENTRY_ID, requester_id=USER_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# add_request_message
# ---------------------------------------------------------------------------

class TestAddRequestMessage:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_adds_message(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": "msg001", "body": "Please approve"})
        mock_get_client.return_value = client

        result = await add_request_message(
            ctx=ctx_elicit_accept_true,
            request_id=REQUEST_ID,
            message_body="Please approve",
        )

        assert result["body"] == "Please approve"
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_request_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": "msg001"})
        mock_get_client.return_value = client

        await add_request_message(
            ctx=ctx_elicit_accept_true, request_id=REQUEST_ID, message_body="Hello"
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REQUEST_ID in url_arg
        assert "messages" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_sender_id_in_payload(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": "msg001"})
        mock_get_client.return_value = client

        await add_request_message(
            ctx=ctx_elicit_accept_true,
            request_id=REQUEST_ID,
            message_body="Hello",
            sender_id=USER_ID,
        )

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["senderId"] == USER_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_no_content_returns_message(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await add_request_message(
            ctx=ctx_elicit_accept_true, request_id=REQUEST_ID, message_body="Hi"
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Request not found")
        mock_get_client.return_value = client

        result = await add_request_message(
            ctx=ctx_elicit_accept_true, request_id=REQUEST_ID, message_body="Hi"
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await add_request_message(
            ctx=ctx_elicit_accept_true, request_id=REQUEST_ID, message_body="Hi"
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# list_request_conditions  (resource-scoped)
# ---------------------------------------------------------------------------

class TestListRequestConditions:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_conditions(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [CONDITION_DICT]})
        mock_get_client.return_value = client

        result = await list_request_conditions(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        assert result["items"][0]["id"] == CONDITION_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_resource_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_request_conditions(ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert RESOURCE_ID in url_arg
        assert "request-conditions" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_request_conditions(ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert f"/governance/api/v2/resources/{RESOURCE_ID}/request-conditions" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_request_conditions(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_request_conditions(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# get_request_condition  (resource-scoped)
# ---------------------------------------------------------------------------

class TestGetRequestCondition:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_condition(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=CONDITION_DICT)
        mock_get_client.return_value = client

        result = await get_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert result["id"] == CONDITION_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_both_ids_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=CONDITION_DICT)
        mock_get_client.return_value = client

        await get_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert RESOURCE_ID in url_arg
        assert CONDITION_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Condition not found")
        mock_get_client.return_value = client

        result = await get_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# create_request_condition  (resource-scoped)
# ---------------------------------------------------------------------------

class TestCreateRequestCondition:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_condition(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=CONDITION_DICT)
        mock_get_client.return_value = client

        result = await create_request_condition(
            ctx=ctx_elicit_accept_true,
            resource_id=RESOURCE_ID,
            condition_config={"requestSequenceId": SEQUENCE_ID},
        )

        assert result["id"] == CONDITION_ID
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_resource_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=CONDITION_DICT)
        mock_get_client.return_value = client

        await create_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_config={}
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert RESOURCE_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_payload_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=CONDITION_DICT)
        mock_get_client.return_value = client

        config = {"requestSequenceId": SEQUENCE_ID, "priority": 1}
        await create_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_config=config
        )

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["requestSequenceId"] == SEQUENCE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Invalid condition")
        mock_get_client.return_value = client

        result = await create_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_config={}
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_config={}
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# update_request_condition  (resource-scoped)
# ---------------------------------------------------------------------------

class TestUpdateRequestCondition:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_condition(self, mock_get_client, ctx_elicit_accept_true):
        updated = {**CONDITION_DICT, "priority": 2}
        client = _make_client(body=updated)
        mock_get_client.return_value = client

        result = await update_request_condition(
            ctx=ctx_elicit_accept_true,
            resource_id=RESOURCE_ID,
            condition_id=CONDITION_ID,
            updates={"priority": 2},
        )

        assert result["priority"] == 2
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "PATCH"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_both_ids_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=CONDITION_DICT)
        mock_get_client.return_value = client

        await update_request_condition(
            ctx=ctx_elicit_accept_true,
            resource_id=RESOURCE_ID,
            condition_id=CONDITION_ID,
            updates={},
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert RESOURCE_ID in url_arg
        assert CONDITION_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_no_content_returns_message(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await update_request_condition(
            ctx=ctx_elicit_accept_true,
            resource_id=RESOURCE_ID,
            condition_id=CONDITION_ID,
            updates={},
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Condition not found")
        mock_get_client.return_value = client

        result = await update_request_condition(
            ctx=ctx_elicit_accept_true,
            resource_id=RESOURCE_ID,
            condition_id=CONDITION_ID,
            updates={},
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await update_request_condition(
            ctx=ctx_elicit_accept_true,
            resource_id=RESOURCE_ID,
            condition_id=CONDITION_ID,
            updates={},
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# activate_request_condition
# ---------------------------------------------------------------------------

class TestActivateRequestCondition:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_activates_condition(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await activate_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "message" in result
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_activate_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        await activate_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "activate" in url_arg
        assert RESOURCE_ID in url_arg
        assert CONDITION_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Condition not found")
        mock_get_client.return_value = client

        result = await activate_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await activate_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# deactivate_request_condition
# ---------------------------------------------------------------------------

class TestDeactivateRequestCondition:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_deactivates_condition(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await deactivate_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "message" in result
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_deactivate_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        await deactivate_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "deactivate" in url_arg
        assert RESOURCE_ID in url_arg
        assert CONDITION_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Condition not found")
        mock_get_client.return_value = client

        result = await deactivate_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await deactivate_request_condition(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, condition_id=CONDITION_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# list_request_sequences
# ---------------------------------------------------------------------------

class TestListRequestSequences:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_sequences(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [SEQUENCE_DICT]})
        mock_get_client.return_value = client

        result = await list_request_sequences(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        assert result["items"][0]["id"] == SEQUENCE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_resource_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_request_sequences(ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert RESOURCE_ID in url_arg
        assert "request-sequences" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_request_sequences(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_request_sequences(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_request_sequences(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# get_request_sequence
# ---------------------------------------------------------------------------

class TestGetRequestSequence:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_sequence(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=SEQUENCE_DICT)
        mock_get_client.return_value = client

        result = await get_request_sequence(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, sequence_id=SEQUENCE_ID
        )

        assert result["id"] == SEQUENCE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_both_ids_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=SEQUENCE_DICT)
        mock_get_client.return_value = client

        await get_request_sequence(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, sequence_id=SEQUENCE_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert RESOURCE_ID in url_arg
        assert SEQUENCE_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Sequence not found")
        mock_get_client.return_value = client

        result = await get_request_sequence(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, sequence_id=SEQUENCE_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_request_sequence(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, sequence_id=SEQUENCE_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# delete_request_sequence
# ---------------------------------------------------------------------------

class TestDeleteRequestSequence:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_deletes_sequence(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await delete_request_sequence(
            ctx=ctx_elicit_accept_true, sequence_id=SEQUENCE_ID
        )

        assert "deleted successfully" in result["message"]
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "DELETE"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_sequence_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        await delete_request_sequence(ctx=ctx_elicit_accept_true, sequence_id=SEQUENCE_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert SEQUENCE_ID in url_arg
        assert "request-sequences" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Sequence in use")
        mock_get_client.return_value = client

        result = await delete_request_sequence(
            ctx=ctx_elicit_accept_true, sequence_id=SEQUENCE_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await delete_request_sequence(
            ctx=ctx_elicit_accept_true, sequence_id=SEQUENCE_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# list_request_settings  (org-level)
# ---------------------------------------------------------------------------

class TestListRequestSettings:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_settings(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"approvalTimeout": 7, "escalationEnabled": True})
        mock_get_client.return_value = client

        result = await list_request_settings(ctx=ctx_elicit_accept_true)

        assert result["approvalTimeout"] == 7

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await list_request_settings(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/governance/api/v2/request-settings" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_request_settings(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_request_settings(ctx=ctx_elicit_accept_true)

        assert "error" in result


# ---------------------------------------------------------------------------
# update_request_settings  (org-level)
# ---------------------------------------------------------------------------

class TestUpdateRequestSettings:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_settings(self, mock_get_client, ctx_elicit_accept_true):
        updated = {"approvalTimeout": 14, "escalationEnabled": False}
        client = _make_client(body=updated)
        mock_get_client.return_value = client

        result = await update_request_settings(
            ctx=ctx_elicit_accept_true, settings={"approvalTimeout": 14}
        )

        assert result["approvalTimeout"] == 14
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "PATCH"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await update_request_settings(ctx=ctx_elicit_accept_true, settings={})

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/governance/api/v2/request-settings" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_no_content_returns_message(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await update_request_settings(ctx=ctx_elicit_accept_true, settings={})

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await update_request_settings(ctx=ctx_elicit_accept_true, settings={})

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await update_request_settings(ctx=ctx_elicit_accept_true, settings={})

        assert "error" in result


# ---------------------------------------------------------------------------
# get_resource_request_settings
# ---------------------------------------------------------------------------

class TestGetResourceRequestSettings:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_settings(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"resourceId": RESOURCE_ID, "enabled": True})
        mock_get_client.return_value = client

        result = await get_resource_request_settings(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        assert result["resourceId"] == RESOURCE_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_resource_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await get_resource_request_settings(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert RESOURCE_ID in url_arg
        assert "request-settings" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Resource not found")
        mock_get_client.return_value = client

        result = await get_resource_request_settings(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_resource_request_settings(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# update_resource_request_settings
# ---------------------------------------------------------------------------

class TestUpdateResourceRequestSettings:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_settings(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"resourceId": RESOURCE_ID, "enabled": False})
        mock_get_client.return_value = client

        result = await update_resource_request_settings(
            ctx=ctx_elicit_accept_true,
            resource_id=RESOURCE_ID,
            settings={"enabled": False},
        )

        assert result["resourceId"] == RESOURCE_ID
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "PATCH"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_resource_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await update_resource_request_settings(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, settings={}
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert RESOURCE_ID in url_arg
        assert "request-settings" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_no_content_returns_message(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(no_content=True)
        mock_get_client.return_value = client

        result = await update_resource_request_settings(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, settings={}
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await update_resource_request_settings(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, settings={}
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await update_resource_request_settings(
            ctx=ctx_elicit_accept_true, resource_id=RESOURCE_ID, settings={}
        )

        assert "error" in result
