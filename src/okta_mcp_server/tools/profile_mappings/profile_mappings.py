# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import json as _json
import re
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.validation import validate_ids


async def _execute(client, method: str, path: str, body=None):
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
        params = {}
        if after is not None:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit
        if source_id is not None:
            params["sourceId"] = source_id
        if target_id is not None:
            params["targetId"] = target_id

        path = f"/api/v1/mappings?{urlencode(params)}" if params else "/api/v1/mappings"
        _, mappings, err = await _execute(client, "GET", path)

        if err:
            logger.error(f"Error listing profile mappings: {err}")
            return {"error": str(err)}

        items = mappings if isinstance(mappings, list) else ([mappings] if mappings else [])
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
        _, mapping, err = await _execute(client, "GET", f"/api/v1/mappings/{mapping_id}")

        if err:
            logger.error(f"Error getting profile mapping {mapping_id}: {err}")
            return {"error": str(err)}

        return mapping if isinstance(mapping, dict) else {}

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
        _, updated, err = await _execute(client, "POST", f"/api/v1/mappings/{mapping_id}", body=body)

        if err:
            logger.error(f"Error updating profile mapping {mapping_id}: {err}")
            return {"error": str(err)}

        out = updated if isinstance(updated, dict) else {}
        logger.info(f"Updated profile mapping {mapping_id}")
        return out

    except Exception as e:
        logger.error(f"Exception updating profile mapping {mapping_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
