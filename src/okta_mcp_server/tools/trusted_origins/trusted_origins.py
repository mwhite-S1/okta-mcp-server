# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Dict, List, Optional

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import DELETE_TRUSTED_ORIGIN
from okta_mcp_server.utils.validation import validate_ids


@mcp.tool()
async def list_trusted_origins(
    ctx: Context,
    q: Optional[str] = None,
    filter: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all trusted origins in the organization.

    Trusted origins define allowed domains for CORS (cross-origin resource sharing)
    and iFrame embedding within Okta-hosted pages.

    Parameters:
        q (str, optional): Search query string.
        filter (str, optional): Filter expression (e.g. 'status eq "ACTIVE"').
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max results per page.

    Returns:
        Dict with items (list of TrustedOrigin objects) and total_fetched.
    """
    logger.info("Listing trusted origins")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if q:
            kwargs["q"] = q
        if filter:
            kwargs["filter"] = filter
        if after:
            kwargs["after"] = after
        if limit:
            kwargs["limit"] = limit

        origins, _, err = await client.list_origins(**kwargs)

        if err:
            logger.error(f"Error listing trusted origins: {err}")
            return {"error": str(err)}

        items = [o.to_dict() if hasattr(o, "to_dict") else o for o in (origins or [])]
        logger.info(f"Retrieved {len(items)} trusted origin(s)")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing trusted origins: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_trusted_origin(
    ctx: Context,
    name: str,
    origin: str,
    scopes: List[Dict],
) -> dict:
    """Create a new trusted origin.

    Trusted origins allow cross-origin requests or iFrame embedding from the
    specified domain. Each scope specifies the allowed use.

    Parameters:
        name (str, required): Display name for the trusted origin.
        origin (str, required): The URL of the origin (e.g. "https://example.com").
        scopes (list, required): List of scope dicts. Each dict must have a 'type'
            field: "CORS" (cross-origin requests) or "REDIRECT" (iFrame embedding).
            Example: [{"type": "CORS"}, {"type": "REDIRECT"}]

    Returns:
        Dict containing the created TrustedOrigin.
    """
    logger.info(f"Creating trusted origin: {name} ({origin})")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body = {
            "name": name,
            "origin": origin,
            "scopes": scopes,
        }
        created, _, err = await client.create_origin(body)

        if err:
            logger.error(f"Error creating trusted origin: {err}")
            return {"error": str(err)}

        result = created.to_dict() if hasattr(created, "to_dict") else created
        logger.info(f"Created trusted origin: {result.get('id', 'unknown')}")
        return result

    except Exception as e:
        logger.error(f"Exception creating trusted origin: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("origin_id", error_return_type="dict")
async def get_trusted_origin(
    ctx: Context,
    origin_id: str,
) -> dict:
    """Retrieve a trusted origin by ID.

    Parameters:
        origin_id (str, required): The ID of the trusted origin.

    Returns:
        Dict containing the TrustedOrigin details.
    """
    logger.info(f"Getting trusted origin {origin_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        origin, _, err = await client.get_origin(origin_id)

        if err:
            logger.error(f"Error getting trusted origin {origin_id}: {err}")
            return {"error": str(err)}

        return origin.to_dict() if hasattr(origin, "to_dict") else origin

    except Exception as e:
        logger.error(f"Exception getting trusted origin {origin_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("origin_id", error_return_type="dict")
async def replace_trusted_origin(
    ctx: Context,
    origin_id: str,
    name: str,
    origin: str,
    scopes: List[Dict],
) -> dict:
    """Replace (full update) a trusted origin.

    All fields must be provided. Replaces the entire trusted origin object.

    Parameters:
        origin_id (str, required): The ID of the trusted origin to update.
        name (str, required): Display name for the trusted origin.
        origin (str, required): The URL of the origin.
        scopes (list, required): List of scope dicts (each with 'type': "CORS" or "REDIRECT").

    Returns:
        Dict containing the updated TrustedOrigin.
    """
    logger.info(f"Replacing trusted origin {origin_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body = {
            "name": name,
            "origin": origin,
            "scopes": scopes,
        }
        updated, _, err = await client.replace_origin(origin_id, body)

        if err:
            logger.error(f"Error replacing trusted origin {origin_id}: {err}")
            return {"error": str(err)}

        result = updated.to_dict() if hasattr(updated, "to_dict") else updated
        logger.info(f"Replaced trusted origin {origin_id}")
        return result

    except Exception as e:
        logger.error(f"Exception replacing trusted origin {origin_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("origin_id", error_return_type="dict")
async def delete_trusted_origin(
    ctx: Context,
    origin_id: str,
) -> dict:
    """Delete a trusted origin.

    Requires confirmation. This may break CORS or iFrame embedding for the
    affected origin in Okta-hosted pages.

    Parameters:
        origin_id (str, required): The ID of the trusted origin to delete.

    Returns:
        Dict confirming the trusted origin was deleted.
    """
    logger.warning(f"Deletion requested for trusted origin {origin_id}")

    fallback_payload = {
        "confirmation_required": True,
        "message": (
            f"To confirm deleting trusted origin {origin_id}, please explicitly confirm. "
            "This may break CORS or iFrame embedding for the affected origin."
        ),
        "origin_id": origin_id,
    }

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_TRUSTED_ORIGIN.format(origin_id=origin_id),
        schema=DeleteConfirmation,
        fallback_payload=fallback_payload,
    )

    if not outcome.used_elicitation:
        logger.info(f"Elicitation unavailable for trusted origin deletion {origin_id} — returning fallback")
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Trusted origin deletion cancelled for {origin_id}")
        return {"message": "Trusted origin deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.delete_origin(origin_id)

        if err:
            logger.error(f"Error deleting trusted origin {origin_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Deleted trusted origin {origin_id}")
        return {"message": f"Trusted origin {origin_id} deleted."}

    except Exception as e:
        logger.error(f"Exception deleting trusted origin {origin_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("origin_id", error_return_type="dict")
async def activate_trusted_origin(
    ctx: Context,
    origin_id: str,
) -> dict:
    """Activate a trusted origin.

    Parameters:
        origin_id (str, required): The ID of the trusted origin to activate.

    Returns:
        Dict containing the updated TrustedOrigin.
    """
    logger.info(f"Activating trusted origin {origin_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        origin, _, err = await client.activate_origin(origin_id)

        if err:
            logger.error(f"Error activating trusted origin {origin_id}: {err}")
            return {"error": str(err)}

        result = origin.to_dict() if hasattr(origin, "to_dict") else origin
        logger.info(f"Activated trusted origin {origin_id}")
        return result

    except Exception as e:
        logger.error(f"Exception activating trusted origin {origin_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("origin_id", error_return_type="dict")
async def deactivate_trusted_origin(
    ctx: Context,
    origin_id: str,
) -> dict:
    """Deactivate a trusted origin.

    Deactivated trusted origins are not enforced for CORS or iFrame embedding.

    Parameters:
        origin_id (str, required): The ID of the trusted origin to deactivate.

    Returns:
        Dict containing the updated TrustedOrigin.
    """
    logger.info(f"Deactivating trusted origin {origin_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        origin, _, err = await client.deactivate_origin(origin_id)

        if err:
            logger.error(f"Error deactivating trusted origin {origin_id}: {err}")
            return {"error": str(err)}

        result = origin.to_dict() if hasattr(origin, "to_dict") else origin
        logger.info(f"Deactivated trusted origin {origin_id}")
        return result

    except Exception as e:
        logger.error(f"Exception deactivating trusted origin {origin_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
