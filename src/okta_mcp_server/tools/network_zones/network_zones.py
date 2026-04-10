# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import json as _json
import re
from typing import Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import DELETE_NETWORK_ZONE
from okta_mcp_server.utils.validation import validate_ids


async def _execute(client, method: str, path: str, body: dict = None):
    """Make a direct API call bypassing SDK Pydantic deserialization.

    Returns (response, body, error). response carries HTTP headers (e.g. Link
    for pagination cursors); body is the parsed JSON dict or list.
    """
    request_executor = client.get_request_executor()
    url = f"{client.get_base_url()}{path}"
    request, error = await request_executor.create_request(method, url, body or {})
    if error:
        return None, None, error
    response, response_body, error = await request_executor.execute(request)
    if error:
        return None, None, error
    if not response_body:
        return response, None, None
    if isinstance(response_body, str):
        try:
            response_body = _json.loads(response_body)
        except Exception:
            pass
    return response, response_body, None


def _parse_next_cursor(response) -> Optional[str]:
    """Extract the 'after' cursor from the Link: <URL>; rel="next" response header."""
    if response is None:
        return None
    try:
        link = response.headers.get("link") or response.headers.get("Link") or ""
        match = re.search(r'<([^>]+)>;\s*rel="next"', link)
        if not match:
            return None
        params = parse_qs(urlparse(match.group(1)).query)
        values = params.get("after", [])
        return values[0] if values else None
    except Exception:
        return None


@mcp.tool()
async def list_network_zones(
    ctx: Context,
    filter: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all network zones in the organization.

    Network zones define IP address ranges or geographic locations used in
    policy rules to allow or restrict access.

    Parameters:
        filter (str, optional): Filter expression (e.g. 'status eq "ACTIVE"').
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max results per page.

    Returns:
        Dict with items (list of NetworkZone objects) and total_fetched.
    """
    logger.info("Listing network zones")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        params = {}
        if filter:
            params["filter"] = filter
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/api/v1/zones?{urlencode(params)}" if params else "/api/v1/zones"
        response, zones, err = await _execute(client, "GET", path)

        if err:
            logger.error(f"Error listing network zones: {err}")
            return {"error": str(err)}

        items = zones if isinstance(zones, list) else ([zones] if zones else [])
        next_cursor = _parse_next_cursor(response)
        logger.info(f"Retrieved {len(items)} network zone(s) (has_more={next_cursor is not None})")
        return {
            "items": items,
            "total_fetched": len(items),
            "has_more": next_cursor is not None,
            "next_cursor": next_cursor,
        }

    except Exception as e:
        logger.error(f"Exception listing network zones: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_network_zone(
    ctx: Context,
    zone: Dict,
) -> dict:
    """Create a new network zone.

    Network zones can be of type IP (list of IP ranges/CIDR blocks) or
    DYNAMIC (geographic/ASN-based). The zone dict must include at minimum:
      - type: "IP" or "DYNAMIC"
      - name: display name
      - For IP zones: gateways (list of {type, value}) and proxies

    Parameters:
        zone (dict, required): Network zone definition. Must include 'type' and 'name'.

    Returns:
        Dict containing the created NetworkZone.
    """
    logger.info(f"Creating network zone: {zone.get('name', 'unknown')}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, created, err = await _execute(client, "POST", "/api/v1/zones", body=zone)

        if err:
            logger.error(f"Error creating network zone: {err}")
            return {"error": str(err)}

        result = created if isinstance(created, dict) else (created.to_dict() if hasattr(created, "to_dict") else created)
        logger.info(f"Created network zone: {result.get('id', 'unknown') if isinstance(result, dict) else 'unknown'}")
        return result

    except Exception as e:
        logger.error(f"Exception creating network zone: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("zone_id", error_return_type="dict")
async def get_network_zone(
    ctx: Context,
    zone_id: str,
) -> dict:
    """Retrieve a network zone by ID.

    Parameters:
        zone_id (str, required): The ID of the network zone.

    Returns:
        Dict containing the NetworkZone details.
    """
    logger.info(f"Getting network zone {zone_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        zone, _, err = await client.get_network_zone(zone_id)

        if err:
            logger.error(f"Error getting network zone {zone_id}: {err}")
            return {"error": str(err)}

        return zone.to_dict() if hasattr(zone, "to_dict") else zone

    except Exception as e:
        logger.error(f"Exception getting network zone {zone_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("zone_id", error_return_type="dict")
async def replace_network_zone(
    ctx: Context,
    zone_id: str,
    zone: Dict,
) -> dict:
    """Replace (full update) a network zone.

    Replaces all properties of the network zone with the provided values.
    All required fields must be included in the zone dict.

    Parameters:
        zone_id (str, required): The ID of the network zone to update.
        zone (dict, required): Complete network zone definition (all fields required).

    Returns:
        Dict containing the updated NetworkZone.
    """
    logger.info(f"Replacing network zone {zone_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, updated, err = await _execute(client, "PUT", f"/api/v1/zones/{zone_id}", body=zone)

        if err:
            logger.error(f"Error replacing network zone {zone_id}: {err}")
            return {"error": str(err)}

        result = updated if isinstance(updated, dict) else (updated.to_dict() if hasattr(updated, "to_dict") else updated)
        logger.info(f"Replaced network zone {zone_id}")
        return result

    except Exception as e:
        logger.error(f"Exception replacing network zone {zone_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("zone_id", error_return_type="dict")
async def delete_network_zone(
    ctx: Context,
    zone_id: str,
) -> dict:
    """Delete a network zone.

    The zone must be deactivated before it can be deleted. Any policies
    referencing this zone will be affected. Requires confirmation.

    Parameters:
        zone_id (str, required): The ID of the network zone to delete.

    Returns:
        Dict confirming the zone was deleted.
    """
    logger.warning(f"Deletion requested for network zone {zone_id}")

    fallback_payload = {
        "confirmation_required": True,
        "message": (
            f"To confirm deleting network zone {zone_id}, please explicitly confirm. "
            "Any policies referencing this zone will be affected."
        ),
        "zone_id": zone_id,
    }

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_NETWORK_ZONE.format(zone_id=zone_id),
        schema=DeleteConfirmation,
        fallback_payload=fallback_payload,
    )

    if not outcome.used_elicitation:
        logger.info(f"Elicitation unavailable for network zone deletion {zone_id} — returning fallback")
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Network zone deletion cancelled for {zone_id}")
        return {"message": "Network zone deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.delete_network_zone(zone_id)

        if err:
            logger.error(f"Error deleting network zone {zone_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Deleted network zone {zone_id}")
        return {"message": f"Network zone {zone_id} deleted."}

    except Exception as e:
        logger.error(f"Exception deleting network zone {zone_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("zone_id", error_return_type="dict")
async def activate_network_zone(
    ctx: Context,
    zone_id: str,
) -> dict:
    """Activate a network zone.

    Parameters:
        zone_id (str, required): The ID of the network zone to activate.

    Returns:
        Dict containing the updated NetworkZone.
    """
    logger.info(f"Activating network zone {zone_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        zone, _, err = await client.activate_network_zone(zone_id)

        if err:
            logger.error(f"Error activating network zone {zone_id}: {err}")
            return {"error": str(err)}

        result = zone.to_dict() if hasattr(zone, "to_dict") else zone
        logger.info(f"Activated network zone {zone_id}")
        return result

    except Exception as e:
        logger.error(f"Exception activating network zone {zone_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("zone_id", error_return_type="dict")
async def deactivate_network_zone(
    ctx: Context,
    zone_id: str,
) -> dict:
    """Deactivate a network zone.

    Deactivated zones are not applied in policy evaluation. A zone must be
    deactivated before it can be deleted.

    Parameters:
        zone_id (str, required): The ID of the network zone to deactivate.

    Returns:
        Dict containing the updated NetworkZone.
    """
    logger.info(f"Deactivating network zone {zone_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        zone, _, err = await client.deactivate_network_zone(zone_id)

        if err:
            logger.error(f"Error deactivating network zone {zone_id}: {err}")
            return {"error": str(err)}

        result = zone.to_dict() if hasattr(zone, "to_dict") else zone
        logger.info(f"Deactivated network zone {zone_id}")
        return result

    except Exception as e:
        logger.error(f"Exception deactivating network zone {zone_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
