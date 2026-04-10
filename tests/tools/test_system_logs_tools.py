# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Tool integration tests for system log tools.

Regression coverage for:
  - Correct SDK method name: client.list_log_events (was mistakenly client.get_logs)
  - Parameter handling: since, until, filter, q, limit, after
  - Response shape: dict with 'items' and 'total_fetched' keys
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from okta_mcp_server.tools.system_logs.system_logs import get_logs


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


class TestGetLogs:
    @pytest.mark.asyncio
    async def test_bare_call_no_params(self, real_ctx):
        """get_logs() with no optional params must work — catches empty query_params SDK bugs."""
        result = await get_logs(ctx=real_ctx)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert "total_fetched" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_basic_call_returns_response(self, real_ctx):
        """get_logs() must not raise and must return the expected response shape."""
        result = await get_logs(ctx=real_ctx, limit=20)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert "error" not in result, result.get("error")
        assert "items" in result
        assert "total_fetched" in result
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_since_param(self, real_ctx):
        """since= parameter must be accepted without raising a type error."""
        one_hour_ago = _iso(datetime.now(timezone.utc) - timedelta(hours=1))
        result = await get_logs(ctx=real_ctx, since=one_hour_ago, limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result

    @pytest.mark.asyncio
    async def test_until_param(self, real_ctx):
        """until= parameter must be accepted without raising a type error."""
        now = _iso(datetime.now(timezone.utc))
        result = await get_logs(ctx=real_ctx, until=now, limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result

    @pytest.mark.asyncio
    async def test_since_and_until_range(self, real_ctx):
        """since= and until= together define a time window."""
        until = datetime.now(timezone.utc)
        since = until - timedelta(hours=2)
        result = await get_logs(ctx=real_ctx, since=_iso(since), until=_iso(until), limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result

    @pytest.mark.asyncio
    async def test_filter_param(self, real_ctx):
        """filter= expression must be accepted without raising."""
        result = await get_logs(ctx=real_ctx, filter='eventType eq "user.session.start"', limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result

    @pytest.mark.asyncio
    async def test_q_param(self, real_ctx):
        """q= text search must be accepted without raising."""
        result = await get_logs(ctx=real_ctx, q="login", limit=20)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")
        assert "items" in result

    @pytest.mark.asyncio
    async def test_limit_clamped_to_minimum(self, real_ctx):
        """limit below 20 is clamped to 20 — no error."""
        result = await get_logs(ctx=real_ctx, limit=5)
        assert isinstance(result, dict)
        assert "error" not in result, result.get("error")

    @pytest.mark.asyncio
    async def test_has_more_is_bool(self, real_ctx):
        """Response 'has_more' field must be a bool."""
        result = await get_logs(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert isinstance(result.get("has_more"), bool)

    @pytest.mark.asyncio
    async def test_fetch_all_used_flag(self, real_ctx):
        """fetch_all_used must reflect whether fetch_all was requested."""
        result = await get_logs(ctx=real_ctx, limit=20)
        assert "error" not in result, result.get("error")
        assert result.get("fetch_all_used") is False
