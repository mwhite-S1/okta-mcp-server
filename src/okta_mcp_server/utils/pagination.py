# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from loguru import logger


def _has_next(response) -> bool:
    """Check whether there is a next page, supporting both SDK v2 and v3."""
    if response is None:
        return False
    # SDK v2: OktaAPIResponse with has_next()
    if hasattr(response, "has_next"):
        return bool(response.has_next())
    # SDK v3: aiohttp ClientResponse with Link headers
    if hasattr(response, "links"):
        return bool(response.links.get("next"))
    return False


def extract_after_cursor(response) -> Optional[str]:
    """Extract the 'after' cursor from the next page URL in Okta API response.

    Supports both SDK v2 (OktaAPIResponse._next) and SDK v3 (ClientResponse.links).
    """
    if not response:
        return None

    # SDK v2: _next attribute contains the next URL
    if hasattr(response, "_next") and response._next:
        try:
            parsed = urlparse(response._next)
            params = parse_qs(parsed.query)
            return params.get("after", [None])[0]
        except Exception as e:
            logger.warning(f"Failed to extract after cursor from _next: {e}")

    # SDK v3: Link headers via aiohttp ClientResponse.links
    if hasattr(response, "links"):
        try:
            next_link = response.links.get("next", {})
            url = next_link.get("url") if next_link else None
            if url:
                parsed = urlparse(str(url))
                params = parse_qs(parsed.query)
                return params.get("after", [None])[0]
        except Exception as e:
            logger.warning(f"Failed to extract after cursor from links: {e}")

    return None


async def paginate_all_results(
    initial_response,
    initial_items: List,
    client_method: Optional[Callable] = None,
    base_kwargs: Optional[Dict] = None,
    max_pages: int = 50,
    delay_between_requests: float = 0.1,
) -> Tuple[List, Dict[str, Any]]:
    """Auto-paginate through all pages of results.

    Supports both SDK v2 (response.next()) and SDK v3 (re-calling client_method
    with updated 'after' cursor extracted from Link headers).

    Args:
        initial_response: The first API response object.
        initial_items: The first page of items.
        client_method: (SDK v3) The async client method to call for subsequent pages.
        base_kwargs: (SDK v3) Keyword args to pass to client_method; 'after' is
            overridden with the cursor for each page.
        max_pages: Maximum number of pages to fetch (safety limit).
        delay_between_requests: Delay in seconds between requests.

    Returns:
        Tuple of (all_items, pagination_info)
    """
    all_items = list(initial_items) if initial_items else []
    pages_fetched = 1
    response = initial_response

    pagination_info = {
        "pages_fetched": 1,
        "total_items": len(all_items),
        "stopped_early": False,
        "stop_reason": None,
    }

    if not _has_next(response):
        return all_items, pagination_info

    use_sdk_v2 = hasattr(response, "next")

    try:
        while _has_next(response) and pages_fetched < max_pages:
            if delay_between_requests > 0:
                await asyncio.sleep(delay_between_requests)

            try:
                if use_sdk_v2:
                    # SDK v2: response.next() returns (items, error)
                    next_items, next_err = await response.next()
                else:
                    # SDK v3: extract cursor, re-call client_method
                    if client_method is None:
                        logger.warning("paginate_all_results: SDK v3 requires client_method for pagination")
                        pagination_info["stopped_early"] = True
                        pagination_info["stop_reason"] = "client_method required for SDK v3 pagination"
                        break

                    cursor = extract_after_cursor(response)
                    if not cursor:
                        break

                    kwargs = {**(base_kwargs or {}), "after": cursor}
                    next_items, response, next_err = await client_method(**kwargs)

                if next_err:
                    logger.warning(f"Error fetching page {pages_fetched + 1}: {next_err}")
                    pagination_info["stopped_early"] = True
                    pagination_info["stop_reason"] = f"API error: {next_err}"
                    break

                if next_items:
                    all_items.extend(next_items)
                    pages_fetched += 1
                    logger.debug(f"Fetched page {pages_fetched}, total items: {len(all_items)}")
                else:
                    break

                if use_sdk_v2:
                    # response object is the same for v2 (has_next updates in place)
                    pass

            except Exception as e:
                logger.error(f"Exception during pagination on page {pages_fetched + 1}: {e}")
                pagination_info["stopped_early"] = True
                pagination_info["stop_reason"] = f"Exception: {e}"
                break

        if pages_fetched >= max_pages and _has_next(response):
            pagination_info["stopped_early"] = True
            pagination_info["stop_reason"] = f"Reached maximum page limit ({max_pages})"
            logger.warning(f"Stopped pagination at {max_pages} pages limit")

    except Exception as e:
        logger.error(f"Unexpected error during pagination: {e}")
        pagination_info["stopped_early"] = True
        pagination_info["stop_reason"] = f"Unexpected error: {e}"

    pagination_info["pages_fetched"] = pages_fetched
    pagination_info["total_items"] = len(all_items)

    return all_items, pagination_info


def create_paginated_response(
    items: List, response, fetch_all_used: bool = False, pagination_info: Optional[Dict] = None
) -> Dict[str, Any]:
    """Create a standardized paginated response format.

    Supports both SDK v2 (OktaAPIResponse) and SDK v3 (ClientResponse).
    """
    result = {
        "items": items,
        "total_fetched": len(items),
        "has_more": False,
        "next_cursor": None,
        "fetch_all_used": fetch_all_used,
    }

    if not fetch_all_used and response:
        result["has_more"] = _has_next(response)
        result["next_cursor"] = extract_after_cursor(response)

    if pagination_info:
        result["pagination_info"] = pagination_info

    return result


def build_query_params(
    search: str = "",
    filter: Optional[str] = None,
    q: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Build query parameters dict for Okta API calls.

    Values are kept in their native types (int for limit) so they pass
    Pydantic validation in SDK v3 when unpacked as **kwargs.
    """
    query_params: Dict[str, Any] = {}

    if search:
        query_params["search"] = search
    if filter:
        query_params["filter"] = filter
    if q:
        query_params["q"] = q
    if after:
        query_params["after"] = after
    if limit is not None:
        query_params["limit"] = limit  # Keep as int — SDK v3 validates types

    for key, value in kwargs.items():
        if value is not None and value != "":
            query_params[key] = value

    return query_params
