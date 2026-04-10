# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for access certification tools: campaigns, reviews, security access reviews."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.governance.certifications import (
    create_security_access_review,
    get_certification_review,
    list_certification_campaigns,
    list_certification_reviews,
    list_security_access_reviews,
)


PATCH_CLIENT = "okta_mcp_server.tools.governance.certifications.get_okta_client"

CAMPAIGN_ID = "cmp0001testABCDEF"
REVIEW_ID = "rev0001testABCDEF"
PRINCIPAL_ID = "00u1234567890abcdef"

CAMPAIGN_DICT = {"id": CAMPAIGN_ID, "name": "Q1 Review", "status": "ACTIVE"}
REVIEW_DICT = {"id": REVIEW_ID, "campaignId": CAMPAIGN_ID, "status": "ACTIVE"}


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
# list_certification_campaigns
# ---------------------------------------------------------------------------

class TestListCertificationCampaigns:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_campaigns(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [CAMPAIGN_DICT]})
        mock_get_client.return_value = client

        result = await list_certification_campaigns(ctx=ctx_elicit_accept_true)

        assert result["items"][0]["id"] == CAMPAIGN_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_certification_campaigns(ctx=ctx_elicit_accept_true)

        assert result == {"data": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_certification_campaigns(ctx=ctx_elicit_accept_true, filter='status eq "ACTIVE"')

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "filter=" in url_arg
        assert "ACTIVE" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_certification_campaigns(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await list_certification_campaigns(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_certification_campaigns(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/governance/api/v1/campaigns" in url_arg


# ---------------------------------------------------------------------------
# list_certification_reviews
# ---------------------------------------------------------------------------

class TestListCertificationReviews:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_reviews(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": [REVIEW_DICT]})
        mock_get_client.return_value = client

        result = await list_certification_reviews(ctx=ctx_elicit_accept_true)

        assert result["data"][0]["id"] == REVIEW_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=None)
        mock_get_client.return_value = client

        result = await list_certification_reviews(ctx=ctx_elicit_accept_true)

        assert result == {"data": []}

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_certification_reviews(
            ctx=ctx_elicit_accept_true,
            filter=f'campaignId eq "{CAMPAIGN_ID}"',
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "filter=" in url_arg
        assert "campaignId" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_decision_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"data": []})
        mock_get_client.return_value = client

        await list_certification_reviews(
            ctx=ctx_elicit_accept_true,
            filter='decision eq "UNREVIEWED"',
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "decision" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_certification_reviews(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_certification_reviews(ctx=ctx_elicit_accept_true)

        assert "error" in result


# ---------------------------------------------------------------------------
# get_certification_review
# ---------------------------------------------------------------------------

class TestGetCertificationReview:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_review(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=REVIEW_DICT)
        mock_get_client.return_value = client

        result = await get_certification_review(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert result["id"] == REVIEW_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_review_id_in_url(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body=REVIEW_DICT)
        mock_get_client.return_value = client

        await get_certification_review(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert REVIEW_ID in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Review not found")
        mock_get_client.return_value = client

        result = await get_certification_review(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await get_certification_review(ctx=ctx_elicit_accept_true, review_id=REVIEW_ID)

        assert "error" in result


# ---------------------------------------------------------------------------
# list_security_access_reviews
# ---------------------------------------------------------------------------

class TestListSecurityAccessReviews:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_reviews(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": [{"id": "sar001", "principalId": PRINCIPAL_ID}]})
        mock_get_client.return_value = client

        result = await list_security_access_reviews(ctx=ctx_elicit_accept_true)

        assert result["items"][0]["principalId"] == PRINCIPAL_ID

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_security_access_reviews(ctx=ctx_elicit_accept_true, filter='status eq "ACTIVE"')

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "filter=" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_order_by_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_security_access_reviews(ctx=ctx_elicit_accept_true, order_by="created desc")

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "orderBy=" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Forbidden")
        mock_get_client.return_value = client

        result = await list_security_access_reviews(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await list_security_access_reviews(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_correct_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"items": []})
        mock_get_client.return_value = client

        await list_security_access_reviews(ctx=ctx_elicit_accept_true)

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "security-access-reviews" in url_arg


# ---------------------------------------------------------------------------
# create_security_access_review
# ---------------------------------------------------------------------------

class TestCreateSecurityAccessReview:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_creates_review(self, mock_get_client, ctx_elicit_accept_true):
        review = {"id": "sar001", "principalId": PRINCIPAL_ID, "status": "PENDING"}
        client = _make_client(body=review)
        mock_get_client.return_value = client

        result = await create_security_access_review(
            ctx=ctx_elicit_accept_true,
            principal_id=PRINCIPAL_ID,
            name="Suspicious Login Review",
            reviewer_user_ids=["00u9876543210fedcba"],
        )

        assert result["principalId"] == PRINCIPAL_ID
        method_arg = client.get_request_executor.return_value.create_request.call_args[0][0]
        assert method_arg == "POST"

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_payload_structure(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": "sar001"})
        mock_get_client.return_value = client

        reviewer_ids = ["00u9876543210fedcba"]
        await create_security_access_review(
            ctx=ctx_elicit_accept_true,
            principal_id=PRINCIPAL_ID,
            name="Test Review",
            reviewer_user_ids=reviewer_ids,
        )

        body_arg = client.get_request_executor.return_value.create_request.call_args[0][2]
        assert body_arg["principalId"] == PRINCIPAL_ID
        assert body_arg["name"] == "Test Review"
        assert body_arg["reviewerSettings"]["type"] == "USER"
        assert body_arg["reviewerSettings"]["userSettings"]["includedUserIds"] == reviewer_ids

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_uses_v2_path(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(body={"id": "sar001"})
        mock_get_client.return_value = client

        await create_security_access_review(
            ctx=ctx_elicit_accept_true,
            principal_id=PRINCIPAL_ID,
            name="Test",
            reviewer_user_ids=[],
        )

        url_arg = client.get_request_executor.return_value.create_request.call_args[0][1]
        assert "/governance/api/v2/security-access-reviews" in url_arg

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = _make_client(execute_error="Invalid request")
        mock_get_client.return_value = client

        result = await create_security_access_review(
            ctx=ctx_elicit_accept_true,
            principal_id=PRINCIPAL_ID,
            name="Test",
            reviewer_user_ids=[],
        )

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection error")

        result = await create_security_access_review(
            ctx=ctx_elicit_accept_true,
            principal_id=PRINCIPAL_ID,
            name="Test",
            reviewer_user_ids=[],
        )

        assert "error" in result
