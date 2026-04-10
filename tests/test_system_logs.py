# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Tests for the system logs tool: get_logs."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from okta_mcp_server.tools.system_logs.system_logs import get_logs


PATCH_CLIENT = "okta_mcp_server.tools.system_logs.system_logs.get_okta_client"


def _make_log_entry(event_type="user.session.start"):
    entry = MagicMock()
    entry.published = "2024-01-01T00:00:00.000Z"
    entry.eventType = event_type
    return entry


def _make_paginated_response(has_next=False):
    response = MagicMock()
    response.has_next.return_value = has_next
    return response


# ---------------------------------------------------------------------------
# get_logs
# ---------------------------------------------------------------------------

class TestGetLogs:
    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_returns_logs(self, mock_get_client, ctx_elicit_accept_true):
        entry = _make_log_entry()
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_log_events.return_value = ([entry], response, None)
        mock_get_client.return_value = client

        result = await get_logs(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 1
        assert result["has_more"] is False
        assert entry in result["items"]

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_empty_result(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_log_events.return_value = ([], response, None)
        mock_get_client.return_value = client

        result = await get_logs(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 0
        assert result["items"] == []

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_api_error(self, mock_get_client, ctx_elicit_accept_true):
        client = AsyncMock()
        client.list_log_events.return_value = (None, None, "Insufficient permissions")
        mock_get_client.return_value = client

        result = await get_logs(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_exception(self, mock_get_client, ctx_elicit_accept_true):
        mock_get_client.side_effect = Exception("Connection refused")

        result = await get_logs(ctx=ctx_elicit_accept_true)

        assert "error" in result

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_limit_clamped_below_minimum(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_log_events.return_value = ([], response, None)
        mock_get_client.return_value = client

        await get_logs(ctx=ctx_elicit_accept_true, limit=5)
        call_params = client.list_log_events.call_args.kwargs
        assert call_params.get("limit") == 20

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_limit_clamped_above_maximum(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_log_events.return_value = ([], response, None)
        mock_get_client.return_value = client

        await get_logs(ctx=ctx_elicit_accept_true, limit=500)
        call_params = client.list_log_events.call_args.kwargs
        assert call_params.get("limit") == 100

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_since_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_log_events.return_value = ([], response, None)
        mock_get_client.return_value = client

        await get_logs(ctx=ctx_elicit_accept_true, since="2024-01-01T00:00:00.000Z")
        call_params = client.list_log_events.call_args.kwargs
        assert "since" in call_params

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_until_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_log_events.return_value = ([], response, None)
        mock_get_client.return_value = client

        await get_logs(ctx=ctx_elicit_accept_true, until="2024-12-31T23:59:59.000Z")
        call_params = client.list_log_events.call_args.kwargs
        assert "until" in call_params

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_filter_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_log_events.return_value = ([], response, None)
        mock_get_client.return_value = client

        await get_logs(ctx=ctx_elicit_accept_true, filter='eventType eq "user.session.start"')
        call_params = client.list_log_events.call_args.kwargs
        assert "filter" in call_params

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_query_param_forwarded(self, mock_get_client, ctx_elicit_accept_true):
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_log_events.return_value = ([], response, None)
        mock_get_client.return_value = client

        await get_logs(ctx=ctx_elicit_accept_true, q="user.session")
        call_params = client.list_log_events.call_args.kwargs
        assert "q" in call_params

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_has_more_when_response_has_next(self, mock_get_client, ctx_elicit_accept_true):
        entry = _make_log_entry()
        response = _make_paginated_response(has_next=True)
        client = AsyncMock()
        client.list_log_events.return_value = ([entry], response, None)
        mock_get_client.return_value = client

        result = await get_logs(ctx=ctx_elicit_accept_true)

        assert result["has_more"] is True

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_multiple_log_entries(self, mock_get_client, ctx_elicit_accept_true):
        entries = [_make_log_entry(f"event.type.{i}") for i in range(5)]
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_log_events.return_value = (entries, response, None)
        mock_get_client.return_value = client

        result = await get_logs(ctx=ctx_elicit_accept_true)

        assert result["total_fetched"] == 5

    @pytest.mark.asyncio
    @patch(PATCH_CLIENT)
    async def test_time_range_query(self, mock_get_client, ctx_elicit_accept_true):
        """Test filtering logs by a specific time range."""
        entry = _make_log_entry()
        response = _make_paginated_response()
        client = AsyncMock()
        client.list_log_events.return_value = ([entry], response, None)
        mock_get_client.return_value = client

        result = await get_logs(
            ctx=ctx_elicit_accept_true,
            since="2024-01-01T00:00:00.000Z",
            until="2024-01-02T00:00:00.000Z",
        )

        assert result["total_fetched"] == 1
        call_params = client.list_log_events.call_args.kwargs
        assert "since" in call_params
        assert "until" in call_params
