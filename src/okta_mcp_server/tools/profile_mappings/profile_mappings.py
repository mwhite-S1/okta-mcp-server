# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Any, Dict, Optional

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.validation import validate_ids


@mcp.tool()
async def list_profile_mappings(
    ctx: Context,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    source_id: Optional[str] = None,
    target_id: Optional[str] = None,
) -> dict:
    """List all profile mappings in the Okta organization.

    Profile mappings define how attributes are transformed and propagated between
    Okta and connected applications or identity providers.

    Parameters:
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max number of results per page.
        source_id (str, optional): Filter mappings by source application or IdP ID.
        target_id (str, optional): Filter mappings by target application or IdP ID.

    Returns:
        Dict with items (list of ProfileMapping objects) and total_fetched.
    """
    logger.info("Listing profile mappings")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if after is not None:
            kwargs["after"] = after
        if limit is not None:
            kwargs["limit"] = limit
        if source_id is not None:
            kwargs["sourceId"] = source_id
        if target_id is not None:
            kwargs["targetId"] = target_id

        mappings, _, err = await client.list_profile_mappings(**kwargs)

        if err:
            logger.error(f"Error listing profile mappings: {err}")
            return {"error": str(err)}

        items = [m.to_dict() if hasattr(m, "to_dict") else m for m in (mappings or [])]
        logger.info(f"Retrieved {len(items)} profile mapping(s)")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing profile mappings: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("mapping_id", error_return_type="dict")
async def get_profile_mapping(
    ctx: Context,
    mapping_id: str,
) -> dict:
    """Retrieve a specific profile mapping by ID.

    Returns the full mapping definition including all attribute mappings between
    source and target.

    Parameters:
        mapping_id (str, required): The ID of the profile mapping.

    Returns:
        Dict containing the ProfileMapping details including source, target,
        and properties (attribute-level mappings).
    """
    logger.info(f"Getting profile mapping {mapping_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        mapping, _, err = await client.get_profile_mapping(mapping_id)

        if err:
            logger.error(f"Error getting profile mapping {mapping_id}: {err}")
            return {"error": str(err)}

        return mapping.to_dict() if hasattr(mapping, "to_dict") else mapping

    except Exception as e:
        logger.error(f"Exception getting profile mapping {mapping_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("mapping_id", error_return_type="dict")
async def update_profile_mapping(
    ctx: Context,
    mapping_id: str,
    properties: Dict[str, Any],
) -> dict:
    """Update a profile mapping's attribute-level mappings.

    Modifies how individual attributes are mapped between source and target.
    Only the properties included in the request are updated; others remain unchanged.

    Parameters:
        mapping_id (str, required): The ID of the profile mapping to update.
        properties (dict, required): Attribute mapping updates. Each key is an
            attribute name, and the value is a mapping expression object:
            {
                "attributeName": {
                    "expression": "<okta-expression>",
                    "pushStatus": "PUSH" | "DONT_PUSH"
                }
            }
            To remove an attribute mapping, set its value to null.

    Returns:
        Dict containing the updated ProfileMapping.
    """
    logger.info(f"Updating profile mapping {mapping_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body = {"properties": properties}
        mapping, _, err = await client.update_profile_mapping(mapping_id, body)

        if err:
            logger.error(f"Error updating profile mapping {mapping_id}: {err}")
            return {"error": str(err)}

        out = mapping.to_dict() if hasattr(mapping, "to_dict") else mapping
        logger.info(f"Updated profile mapping {mapping_id}")
        return out

    except Exception as e:
        logger.error(f"Exception updating profile mapping {mapping_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
