# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Optional

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.pagination import build_query_params, create_paginated_response, paginate_all_results


@mcp.tool()
async def get_logs(
    ctx: Context = None,
    fetch_all: bool = False,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    filter: Optional[str] = None,
    q: Optional[str] = None,
) -> dict:
    """Retrieve system logs from the Okta organization with pagination support.

    This tool retrieves system logs from the Okta organization.

    Parameters:
        fetch_all (bool, optional): If True, automatically fetch all pages of results. Default: False.
        after (str, optional): Pagination cursor for fetching results after this point.
        limit (int, optional): Maximum number of log entries to return per page (min 20, max 100).
        since (str, optional): Filter logs since this timestamp (ISO 8601 format).
        until (str, optional): Filter logs until this timestamp (ISO 8601 format).
        filter (str, optional): Filter expression for log events.
        q (str, optional): Query string to search log events.

    Examples:
        For pagination:
        - First call: get_logs()
        - Next page: get_logs(after="cursor_value")
        - All pages: get_logs(fetch_all=True)
        - Time range: get_logs(since="2024-01-01T00:00:00.000Z", until="2024-01-02T00:00:00.000Z")

    Returns:
        Dict containing:
        - items: List of log entry objects
        - total_fetched: Number of log entries returned
        - has_more: Boolean indicating if more results are available
        - next_cursor: Cursor for the next page (if has_more is True)
        - fetch_all_used: Boolean indicating if fetch_all was used
        - pagination_info: Additional pagination metadata (when fetch_all=True)
    """
    logger.info("Retrieving system logs from Okta organization")
    logger.debug(f"fetch_all: {fetch_all}, after: '{after}', limit: {limit}, since: '{since}', until: '{until}'")

    # Validate limit parameter range
    if limit is not None:
        if limit < 20:
            logger.warning(f"Limit {limit} is below minimum (20), setting to 20")
            limit = 20
        elif limit > 100:
            logger.warning(f"Limit {limit} exceeds maximum (100), setting to 100")
            limit = 100

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        logger.debug("Calling Okta API to retrieve system logs")

        query_params = build_query_params(after=after, limit=limit, since=since, until=until, filter=filter, q=q)

        logs, response, err = await client.list_log_events(**query_params)

        if err:
            logger.error(f"Okta API error while retrieving system logs: {err}")
            return {"error": f"Error: {err}"}

        if not logs:
            logger.info("No system logs found")
            return create_paginated_response([], response, fetch_all)

        log_count = len(logs)
        logger.debug(f"Retrieved {log_count} system log entries in first page")

        if log_count > 0:
            logger.debug(f"First log entry timestamp: {logs[0].published if hasattr(logs[0], 'published') else 'N/A'}")
            logger.debug(f"Log types found: {set(log.eventType for log in logs[:10] if hasattr(log, 'eventType'))}")

        from okta_mcp_server.utils.pagination import _has_next
        from datetime import datetime, timezone, timedelta

        if fetch_all:
            # The Okta SDK v2 does not reliably expose the Link header cursor for
            # system logs, so _has_next() returns False even when more pages exist.
            # Fall back to timestamp windowing: use the last event's published time
            # as the next `since` and keep fetching until a partial page is returned.
            all_logs = list(logs)
            pages_fetched = 1
            current_logs = logs
            page_limit = limit if limit else 100

            while len(current_logs) >= page_limit:
                last = current_logs[-1]
                last_published = getattr(last, "published", None)
                if not last_published:
                    break
                try:
                    last_dt = datetime.fromisoformat(str(last_published).replace("Z", "+00:00"))
                    next_since = (last_dt + timedelta(milliseconds=1)).strftime("%Y-%m-%dT%H:%M:%S.") + \
                                 f"{(last_dt + timedelta(milliseconds=1)).microsecond // 1000:03d}Z"
                except Exception as e:
                    logger.warning(f"Timestamp windowing failed: {e}")
                    break

                next_params = dict(query_params)
                next_params["since"] = next_since
                next_params.pop("after", None)

                logger.info(f"Timestamp-windowed page {pages_fetched + 1}: since={next_since}, total so far={len(all_logs)}")
                current_logs, response, err = await client.list_log_events(**next_params)

                if err or not current_logs:
                    break

                all_logs.extend(current_logs)
                pages_fetched += 1

            pagination_info = {"pages_fetched": pages_fetched, "total_items": len(all_logs), "stopped_early": False, "stop_reason": None}
            logger.info(f"Successfully retrieved {len(all_logs)} log entries across {pages_fetched} pages")
            return create_paginated_response(all_logs, response, fetch_all_used=True, pagination_info=pagination_info)
        else:
            logger.info(f"Successfully retrieved {log_count} system log entries")
            return create_paginated_response(logs, response, fetch_all_used=fetch_all)

    except Exception as e:
        logger.error(f"Exception while retrieving system logs: {type(e).__name__}: {e}")
        return {"error": f"Exception: {e}"}
