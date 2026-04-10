# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for end-user governance tools: my catalog, my requests, my SARs, my settings."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.governance.enduser import (
    add_my_security_access_review_comment,
    create_my_access_request,
    create_my_security_access_review_access_summary,
    create_my_security_access_review_summary,
    get_my_access_request,
    get_my_agent_managed_connections,
    get_my_catalog_entry,
    get_my_catalog_entry_request_fields,
    get_my_catalog_entry_user_request_fields,
    get_my_governance_settings,
    get_my_security_access_review,
    get_my_security_access_review_access_anomalies,
    get_my_security_access_review_history,
    get_my_security_access_review_principal,
    get_my_security_access_review_stats,
    list_my_catalog_entries,
    list_my_catalog_entry_users,
    list_my_delegate_users,
    list_my_security_access_review_accesses,
    list_my_security_access_review_actions,
    list_my_security_access_review_sub_accesses,
    list_my_security_access_reviews,
    submit_my_security_access_review_access_action,
    submit_my_security_access_review_action,
    update_my_governance_settings,
)


PATCH_CLIENT = "okta_mcp_server.tools.governance.enduser.get_okta_client"

ENTRY_ID = "cen385AlcdqGaY8HE0g2"
REQUEST_ID = "req001testABCDEFGHIJ"
REVIEW_ID = "sarABCDEF1234567890ab"
ACCESS_ID = "sarAccess1234567890ab"
TARGET_ID = "sarTarget1234567890ab"
USER_ID = "00u1234567890ABCDEF"
CAMPAIGN_ID = "icit001testABCDEFGHIJ"
AGENT_ID = "agnt001testABCDEFGHIJ"


def _make_client(body=None, execute_error=None, no_content=False):
    executor = AsyncMock()
    executor.create_request.return_value = (MagicMock(), None)
    if execute_error:
        executor.execute.return_value = (None, None, execute_error)
    else:
        executor.execute.return_value = (MagicMock(), body, None)
    client = MagicMock()
    client.get_request_executor.return_value = executor
    client.get_base_url.return_value = "https://test.okta.com"
    return client


# ---------------------------------------------------------------------------
# list_my_catalog_entries
# ---------------------------------------------------------------------------

class TestListMyCatalogEntries:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_entries(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": [{"id": ENTRY_ID}]})
        mock_get_client.return_value = client

        result = await list_my_catalog_entries(ctx=ctx_elicit_accept_true, filter="not(parent pr)")

        assert result["data"][0]["id"] == ENTRY_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_my_catalog_entries(ctx=ctx_elicit_accept_true, filter="not(parent pr)")

        assert result == {"data": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Unauthorized")
        mock_get_client.return_value = client

        result = await list_my_catalog_entries(ctx=ctx_elicit_accept_true, filter="not(parent pr)")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_my_catalog_entries(ctx=ctx_elicit_accept_true, filter="not(parent pr)")

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_my_catalog_entries(ctx=ctx_elicit_accept_true, filter="not(parent pr)")

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "filter=" in url_arg
        assert "/my/catalogs/default/entries" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_optional_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_my_catalog_entries(
            ctx=ctx_elicit_accept_true, filter="not(parent pr)", match="Sales", after="cursor1", limit=50
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "match=Sales" in url_arg
        assert "after=cursor1" in url_arg
        assert "limit=50" in url_arg


# ---------------------------------------------------------------------------
# get_my_catalog_entry
# ---------------------------------------------------------------------------

class TestGetMyCatalogEntry:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_entry(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": ENTRY_ID})
        mock_get_client.return_value = client

        result = await get_my_catalog_entry(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert result["id"] == ENTRY_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not Found")
        mock_get_client.return_value = client

        result = await get_my_catalog_entry(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_catalog_entry(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_entry_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": ENTRY_ID})
        mock_get_client.return_value = client

        await get_my_catalog_entry(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert ENTRY_ID in url_arg


# ---------------------------------------------------------------------------
# get_my_catalog_entry_request_fields
# ---------------------------------------------------------------------------

class TestGetMyCatalogEntryRequestFields:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_fields(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": [{"id": "field1"}]})
        mock_get_client.return_value = client

        result = await get_my_catalog_entry_request_fields(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert "data" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await get_my_catalog_entry_request_fields(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert result == {"data": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await get_my_catalog_entry_request_fields(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_catalog_entry_request_fields(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await get_my_catalog_entry_request_fields(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "request-fields" in url_arg
        assert ENTRY_ID in url_arg


# ---------------------------------------------------------------------------
# list_my_catalog_entry_users
# ---------------------------------------------------------------------------

class TestListMyCatalogEntryUsers:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_users(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": [{"id": USER_ID}]})
        mock_get_client.return_value = client

        result = await list_my_catalog_entry_users(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, filter=f'id eq "{USER_ID}"'
        )

        assert result["data"][0]["id"] == USER_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_my_catalog_entry_users(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, filter="id eq \"x\""
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_my_catalog_entry_users(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, filter="id eq \"x\""
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path_and_params(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_my_catalog_entry_users(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, filter="id eq \"x\"", limit=10
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert ENTRY_ID in url_arg
        assert "users" in url_arg
        assert "filter=" in url_arg
        assert "limit=10" in url_arg


# ---------------------------------------------------------------------------
# get_my_catalog_entry_user_request_fields
# ---------------------------------------------------------------------------

class TestGetMyCatalogEntryUserRequestFields:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_fields(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": [{"id": "field1"}]})
        mock_get_client.return_value = client

        result = await get_my_catalog_entry_user_request_fields(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, user_id=USER_ID
        )

        assert "data" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not Found")
        mock_get_client.return_value = client

        result = await get_my_catalog_entry_user_request_fields(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, user_id=USER_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_catalog_entry_user_request_fields(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, user_id=USER_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_entry_and_user_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await get_my_catalog_entry_user_request_fields(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, user_id=USER_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert ENTRY_ID in url_arg
        assert USER_ID in url_arg
        assert "request-fields" in url_arg


# ---------------------------------------------------------------------------
# create_my_access_request
# ---------------------------------------------------------------------------

class TestCreateMyAccessRequest:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_request(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": REQUEST_ID, "status": "PENDING"})
        mock_get_client.return_value = client

        result = await create_my_access_request(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert result["id"] == REQUEST_ID
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_with_field_values(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": REQUEST_ID})
        mock_get_client.return_value = client

        field_values = [{"id": "field1", "value": "answer"}]
        await create_my_access_request(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, requester_field_values=field_values
        )

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["requesterFieldValues"] == field_values

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Bad Request")
        mock_get_client.return_value = client

        result = await create_my_access_request(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_my_access_request(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_entry_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": REQUEST_ID})
        mock_get_client.return_value = client

        await create_my_access_request(ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert ENTRY_ID in url_arg
        assert "requests" in url_arg


# ---------------------------------------------------------------------------
# get_my_access_request
# ---------------------------------------------------------------------------

class TestGetMyAccessRequest:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_request(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": REQUEST_ID})
        mock_get_client.return_value = client

        result = await get_my_access_request(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, request_id=REQUEST_ID
        )

        assert result["id"] == REQUEST_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not Found")
        mock_get_client.return_value = client

        result = await get_my_access_request(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, request_id=REQUEST_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_access_request(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, request_id=REQUEST_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_ids_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": REQUEST_ID})
        mock_get_client.return_value = client

        await get_my_access_request(
            ctx=ctx_elicit_accept_true, entry_id=ENTRY_ID, request_id=REQUEST_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert ENTRY_ID in url_arg
        assert REQUEST_ID in url_arg


# ---------------------------------------------------------------------------
# list_my_security_access_reviews
# ---------------------------------------------------------------------------

class TestListMySecurityAccessReviews:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_reviews(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [{"id": REVIEW_ID}]})
        mock_get_client.return_value = client

        result = await list_my_security_access_reviews(ctx=ctx_elicit_accept_true)

        assert result["items"][0]["id"] == REVIEW_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_my_security_access_reviews(ctx=ctx_elicit_accept_true)

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_my_security_access_reviews(ctx=ctx_elicit_accept_true, filter='status eq "ACTIVE"')

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "filter=" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_order_by_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_my_security_access_reviews(ctx=ctx_elicit_accept_true, order_by="created desc")

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "orderBy=" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_my_security_access_reviews(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_my_security_access_reviews(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_my_security_access_reviews(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/my/security-access-reviews" in url_arg


# ---------------------------------------------------------------------------
# get_my_security_access_review_stats
# ---------------------------------------------------------------------------

class TestGetMySecurityAccessReviewStats:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_stats(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"active": 3, "completed": 10})
        mock_get_client.return_value = client

        result = await get_my_security_access_review_stats(ctx=ctx_elicit_accept_true)

        assert result["active"] == 3

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await get_my_security_access_review_stats(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_security_access_review_stats(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await get_my_security_access_review_stats(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/my/security-access-reviews/stats" in url_arg


# ---------------------------------------------------------------------------
# get_my_security_access_review
# ---------------------------------------------------------------------------

class TestGetMySecurityAccessReview:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_review(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": REVIEW_ID})
        mock_get_client.return_value = client

        result = await get_my_security_access_review(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert result["id"] == REVIEW_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not Found")
        mock_get_client.return_value = client

        result = await get_my_security_access_review(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_security_access_review(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_review_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": REVIEW_ID})
        mock_get_client.return_value = client

        await get_my_security_access_review(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REVIEW_ID in url_arg


# ---------------------------------------------------------------------------
# list_my_security_access_review_accesses
# ---------------------------------------------------------------------------

class TestListMySecurityAccessReviewAccesses:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_accesses(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [{"id": ACCESS_ID}]})
        mock_get_client.return_value = client

        result = await list_my_security_access_review_accesses(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert result["items"][0]["id"] == ACCESS_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_my_security_access_review_accesses(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_optional_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_my_security_access_review_accesses(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID,
            filter='status eq "PENDING"', order_by="created asc", after="cur1", limit=25
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "filter=" in url_arg
        assert "orderBy=" in url_arg
        assert "after=cur1" in url_arg
        assert "limit=25" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_my_security_access_review_accesses(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_my_security_access_review_accesses(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_my_security_access_review_accesses(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REVIEW_ID in url_arg
        assert "accesses" in url_arg


# ---------------------------------------------------------------------------
# list_my_security_access_review_sub_accesses
# ---------------------------------------------------------------------------

class TestListMySecurityAccessReviewSubAccesses:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_sub_accesses(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [{"id": "sub1"}]})
        mock_get_client.return_value = client

        result = await list_my_security_access_review_sub_accesses(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, access_id=ACCESS_ID
        )

        assert result["items"][0]["id"] == "sub1"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_my_security_access_review_sub_accesses(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, access_id=ACCESS_ID
        )

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not Found")
        mock_get_client.return_value = client

        result = await list_my_security_access_review_sub_accesses(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, access_id=ACCESS_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_my_security_access_review_sub_accesses(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, access_id=ACCESS_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_ids_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_my_security_access_review_sub_accesses(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, access_id=ACCESS_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REVIEW_ID in url_arg
        assert ACCESS_ID in url_arg
        assert "sub-accesses" in url_arg


# ---------------------------------------------------------------------------
# submit_my_security_access_review_access_action
# ---------------------------------------------------------------------------

class TestSubmitMySecurityAccessReviewAccessAction:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_submits_action(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"status": "REVOKE_ACCESS"})
        mock_get_client.return_value = client

        result = await submit_my_security_access_review_access_action(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID,
            action_type="REVOKE_ACCESS"
        )

        assert "error" not in result
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_action_type_in_body(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await submit_my_security_access_review_access_action(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID,
            action_type="RESTORE_ACCESS"
        )

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["type"] == "RESTORE_ACCESS"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Bad Request")
        mock_get_client.return_value = client

        result = await submit_my_security_access_review_access_action(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID,
            action_type="REVOKE_ACCESS"
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await submit_my_security_access_review_access_action(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID,
            action_type="REVOKE_ACCESS"
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_ids_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await submit_my_security_access_review_access_action(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID,
            action_type="REVOKE_ACCESS"
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REVIEW_ID in url_arg
        assert TARGET_ID in url_arg
        assert "actions" in url_arg


# ---------------------------------------------------------------------------
# get_my_security_access_review_access_anomalies
# ---------------------------------------------------------------------------

class TestGetMySecurityAccessReviewAccessAnomalies:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_anomalies(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"anomalies": []})
        mock_get_client.return_value = client

        result = await get_my_security_access_review_access_anomalies(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID
        )

        assert "anomalies" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not Found")
        mock_get_client.return_value = client

        result = await get_my_security_access_review_access_anomalies(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_security_access_review_access_anomalies(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_ids_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await get_my_security_access_review_access_anomalies(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REVIEW_ID in url_arg
        assert TARGET_ID in url_arg
        assert "anomalies" in url_arg


# ---------------------------------------------------------------------------
# create_my_security_access_review_access_summary
# ---------------------------------------------------------------------------

class TestCreateMySecurityAccessReviewAccessSummary:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_summary(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"status": "CREATED"})
        mock_get_client.return_value = client

        result = await create_my_security_access_review_access_summary(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID
        )

        assert "error" not in result
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await create_my_security_access_review_access_summary(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Bad Request")
        mock_get_client.return_value = client

        result = await create_my_security_access_review_access_summary(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_my_security_access_review_access_summary(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, target_id=TARGET_ID
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# list_my_security_access_review_actions
# ---------------------------------------------------------------------------

class TestListMySecurityAccessReviewActions:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_actions(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [{"type": "CLOSE_REVIEW"}]})
        mock_get_client.return_value = client

        result = await list_my_security_access_review_actions(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert result["items"][0]["type"] == "CLOSE_REVIEW"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_my_security_access_review_actions(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_my_security_access_review_actions(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_my_security_access_review_actions(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_my_security_access_review_actions(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REVIEW_ID in url_arg
        assert "actions" in url_arg


# ---------------------------------------------------------------------------
# submit_my_security_access_review_action
# ---------------------------------------------------------------------------

class TestSubmitMySecurityAccessReviewAction:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_submits_close_review(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"status": "CLOSED"})
        mock_get_client.return_value = client

        result = await submit_my_security_access_review_action(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, action_type="CLOSE_REVIEW"
        )

        assert "error" not in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_action_type_in_body(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await submit_my_security_access_review_action(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, action_type="RESTORE_ALL_ACCESS"
        )

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["actionType"] == "RESTORE_ALL_ACCESS"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await submit_my_security_access_review_action(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, action_type="CLOSE_REVIEW"
        )

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Bad Request")
        mock_get_client.return_value = client

        result = await submit_my_security_access_review_action(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, action_type="CLOSE_REVIEW"
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await submit_my_security_access_review_action(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, action_type="CLOSE_REVIEW"
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# add_my_security_access_review_comment
# ---------------------------------------------------------------------------

class TestAddMySecurityAccessReviewComment:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_adds_comment(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": "cmt001"})
        mock_get_client.return_value = client

        result = await add_my_security_access_review_comment(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, comment="LGTM"
        )

        assert "error" not in result
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_comment_in_body(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await add_my_security_access_review_comment(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, comment="Needs more review"
        )

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["comment"] == "Needs more review"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Bad Request")
        mock_get_client.return_value = client

        result = await add_my_security_access_review_comment(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, comment="test"
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await add_my_security_access_review_comment(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, comment="test"
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await add_my_security_access_review_comment(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, comment="test"
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REVIEW_ID in url_arg
        assert "comment" in url_arg


# ---------------------------------------------------------------------------
# get_my_security_access_review_history
# ---------------------------------------------------------------------------

class TestGetMySecurityAccessReviewHistory:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_history(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [{"event": "CREATED"}]})
        mock_get_client.return_value = client

        result = await get_my_security_access_review_history(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert result["items"][0]["event"] == "CREATED"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await get_my_security_access_review_history(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_pagination_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await get_my_security_access_review_history(
            ctx=ctx_elicit_accept_true, review_id=REVIEW_ID, after="cursor1", limit=10
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "after=cursor1" in url_arg
        assert "limit=10" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not Found")
        mock_get_client.return_value = client

        result = await get_my_security_access_review_history(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_security_access_review_history(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# get_my_security_access_review_principal
# ---------------------------------------------------------------------------

class TestGetMySecurityAccessReviewPrincipal:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_principal(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": USER_ID, "profile": {}})
        mock_get_client.return_value = client

        result = await get_my_security_access_review_principal(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert result["id"] == USER_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not Found")
        mock_get_client.return_value = client

        result = await get_my_security_access_review_principal(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_security_access_review_principal(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": USER_ID})
        mock_get_client.return_value = client

        await get_my_security_access_review_principal(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REVIEW_ID in url_arg
        assert "principal" in url_arg


# ---------------------------------------------------------------------------
# create_my_security_access_review_summary
# ---------------------------------------------------------------------------

class TestCreateMySecurityAccessReviewSummary:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_summary(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"status": "CREATED"})
        mock_get_client.return_value = client

        result = await create_my_security_access_review_summary(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" not in result
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await create_my_security_access_review_summary(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Bad Request")
        mock_get_client.return_value = client

        result = await create_my_security_access_review_summary(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_my_security_access_review_summary(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await create_my_security_access_review_summary(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REVIEW_ID in url_arg
        assert "summary" in url_arg


# ---------------------------------------------------------------------------
# get_my_agent_managed_connections
# ---------------------------------------------------------------------------

class TestGetMyAgentManagedConnections:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_connections(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": [{"id": "conn1"}]})
        mock_get_client.return_value = client

        result = await get_my_agent_managed_connections(
            ctx=ctx_elicit_accept_true,
            campaign_id=CAMPAIGN_ID, review_id=REVIEW_ID, agent_id=AGENT_ID
        )

        assert result["data"][0]["id"] == "conn1"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await get_my_agent_managed_connections(
            ctx=ctx_elicit_accept_true,
            campaign_id=CAMPAIGN_ID, review_id=REVIEW_ID, agent_id=AGENT_ID
        )

        assert result == {"data": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_pagination_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await get_my_agent_managed_connections(
            ctx=ctx_elicit_accept_true,
            campaign_id=CAMPAIGN_ID, review_id=REVIEW_ID, agent_id=AGENT_ID,
            after="cursor1", limit=15
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "after=cursor1" in url_arg
        assert "limit=15" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Not Found")
        mock_get_client.return_value = client

        result = await get_my_agent_managed_connections(
            ctx=ctx_elicit_accept_true,
            campaign_id=CAMPAIGN_ID, review_id=REVIEW_ID, agent_id=AGENT_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_agent_managed_connections(
            ctx=ctx_elicit_accept_true,
            campaign_id=CAMPAIGN_ID, review_id=REVIEW_ID, agent_id=AGENT_ID
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_ids_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await get_my_agent_managed_connections(
            ctx=ctx_elicit_accept_true,
            campaign_id=CAMPAIGN_ID, review_id=REVIEW_ID, agent_id=AGENT_ID
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert CAMPAIGN_ID in url_arg
        assert REVIEW_ID in url_arg
        assert AGENT_ID in url_arg
        assert "agent-managed-connections" in url_arg


# ---------------------------------------------------------------------------
# get_my_governance_settings
# ---------------------------------------------------------------------------

class TestGetMyGovernanceSettings:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_settings(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"delegates": {"appointments": []}})
        mock_get_client.return_value = client

        result = await get_my_governance_settings(ctx=ctx_elicit_accept_true)

        assert "delegates" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Unauthorized")
        mock_get_client.return_value = client

        result = await get_my_governance_settings(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_my_governance_settings(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await get_my_governance_settings(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/my/settings" in url_arg
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "GET"


# ---------------------------------------------------------------------------
# update_my_governance_settings
# ---------------------------------------------------------------------------

class TestUpdateMyGovernanceSettings:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_updates_settings(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"delegates": {"appointments": [{"delegateId": USER_ID}]}})
        mock_get_client.return_value = client

        delegates = {"appointments": [{"delegateId": USER_ID}]}
        result = await update_my_governance_settings(ctx=ctx_elicit_accept_true, delegates=delegates)

        assert "error" not in result
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "PATCH"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_delegates_in_body(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        delegates = {"appointments": []}
        await update_my_governance_settings(ctx=ctx_elicit_accept_true, delegates=delegates)

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["delegates"] == delegates

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_no_delegates_sends_empty(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={})
        mock_get_client.return_value = client

        await update_my_governance_settings(ctx=ctx_elicit_accept_true)

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg == {}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await update_my_governance_settings(ctx=ctx_elicit_accept_true)

        assert "message" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Bad Request")
        mock_get_client.return_value = client

        result = await update_my_governance_settings(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await update_my_governance_settings(ctx=ctx_elicit_accept_true)

        assert "error" in result


# ---------------------------------------------------------------------------
# list_my_delegate_users
# ---------------------------------------------------------------------------

class TestListMyDelegateUsers:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_users(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": [{"id": USER_ID}]})
        mock_get_client.return_value = client

        result = await list_my_delegate_users(ctx=ctx_elicit_accept_true)

        assert result["data"][0]["id"] == USER_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_response(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_my_delegate_users(ctx=ctx_elicit_accept_true)

        assert result == {"data": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_my_delegate_users(ctx=ctx_elicit_accept_true, filter='firstName sw "John"')

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "filter=" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_pagination_params_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_my_delegate_users(ctx=ctx_elicit_accept_true, after="cursor1", limit=50)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "after=cursor1" in url_arg
        assert "limit=50" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_my_delegate_users(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_my_delegate_users(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_my_delegate_users(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/my/settings/delegate/users" in url_arg
