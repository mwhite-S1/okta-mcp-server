# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import json as _json
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
    request, error = await request_executor.create_request(method, url, body if body is not None else {})
    if error:
        return None, error
    response, response_body, error = await request_executor.execute(request)
    if error:
        return None, error
    if not response_body:
        return None, None
    if isinstance(response_body, str):
        try:
            response_body = _json.loads(response_body)
        except Exception:
            pass
    return response_body, None


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def list_group_push_mappings(
    ctx: Context,
    app_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    last_updated: Optional[str] = None,
    source_group_id: Optional[str] = None,
    status: Optional[str] = None,
) -> dict:
    """List all group push mappings for an application.

    Group push mappings define how Okta groups are pushed to a target app (e.g. AD, LDAP).

    Parameters:
        app_id (str, required): The ID of the application.
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max results per page (1–1000, default 100).
        last_updated (str, optional): Filter by last updated date (ISO 8601, e.g. "2025-01-01T00:00:00Z").
        source_group_id (str, optional): Filter by source Okta group ID.
        status (str, optional): Filter by status ("ACTIVE" or "INACTIVE").

    Returns:
        Dict with items (list of GroupPushMapping objects) and total_fetched.
    """
    logger.info(f"Listing group push mappings for application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit
        if last_updated:
            params["lastUpdated"] = last_updated
        if source_group_id:
            params["sourceGroupId"] = source_group_id
        if status:
            params["status"] = status

        path = f"/api/v1/apps/{app_id}/group-push/mappings"
        if params:
            path += f"?{urlencode(params)}"

        body, err = await _execute(client, "GET", path)

        if err:
            logger.error(f"Error listing push mappings for app {app_id}: {err}")
            return {"error": str(err)}

        items = body if isinstance(body, list) else []
        logger.info(f"Retrieved {len(items)} push mappings for app {app_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing push mappings for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def create_group_push_mapping(
    ctx: Context,
    app_id: str,
    mapping: Dict[str, Any],
) -> dict:
    """Create a group push mapping for an application.

    Creates or links a group push mapping. Either targetGroupId (link to an
    existing target group) or targetGroupName (create a new target group) must
    be provided, but not both.

    Parameters:
        app_id (str, required): The ID of the application.
        mapping (dict, required): GroupPushMapping configuration:
            - sourceGroupId (str, required): The Okta source group ID to push.
            - targetGroupId (str, optional): Existing target group ID to link to.
            - targetGroupName (str, optional): Name for a new target group to create.
            - userNameTemplate (dict, optional): Username template for pushed users.

    Returns:
        Dict containing the created GroupPushMapping.
    """
    logger.info(f"Creating group push mapping for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, err = await _execute(client, "POST", f"/api/v1/apps/{app_id}/group-push/mappings", mapping)

        if err:
            logger.error(f"Error creating push mapping for app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Created push mapping for app {app_id}")
        return body or {"message": f"Group push mapping created for app {app_id}"}

    except Exception as e:
        logger.error(f"Exception creating push mapping for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def get_group_push_mapping(
    ctx: Context,
    app_id: str,
    mapping_id: str,
) -> dict:
    """Retrieve a specific group push mapping by ID.

    Parameters:
        app_id (str, required): The ID of the application.
        mapping_id (str, required): The ID of the group push mapping to retrieve.

    Returns:
        Dict containing the GroupPushMapping details.
    """
    logger.info(f"Getting push mapping {mapping_id} for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, err = await _execute(client, "GET", f"/api/v1/apps/{app_id}/group-push/mappings/{mapping_id}")

        if err:
            logger.error(f"Error getting push mapping {mapping_id} for app {app_id}: {err}")
            return {"error": str(err)}

        return body or {}

    except Exception as e:
        logger.error(f"Exception getting push mapping {mapping_id} for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def update_group_push_mapping(
    ctx: Context,
    app_id: str,
    mapping_id: str,
    update: Dict[str, Any],
) -> dict:
    """Update the status of a group push mapping.

    Parameters:
        app_id (str, required): The ID of the application.
        mapping_id (str, required): The ID of the group push mapping to update.
        update (dict, required): Update configuration, typically:
            - status (str): "ACTIVE" or "INACTIVE"

    Returns:
        Dict containing the updated GroupPushMapping.
    """
    logger.info(f"Updating push mapping {mapping_id} for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, err = await _execute(client, "PATCH", f"/api/v1/apps/{app_id}/group-push/mappings/{mapping_id}", update)

        if err:
            logger.error(f"Error updating push mapping {mapping_id} for app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Updated push mapping {mapping_id} for app {app_id}")
        return body or {"message": f"Push mapping {mapping_id} updated"}

    except Exception as e:
        logger.error(f"Exception updating push mapping {mapping_id} for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def delete_group_push_mapping(
    ctx: Context,
    app_id: str,
    mapping_id: str,
    delete_target_group: bool = False,
) -> dict:
    """Delete a group push mapping.

    The mapping must be in an INACTIVE state before deletion.

    Parameters:
        app_id (str, required): The ID of the application.
        mapping_id (str, required): The ID of the group push mapping to delete.
        delete_target_group (bool, required): If True, the target group in the
            connected app is also deleted. Default: False.

    Returns:
        Dict confirming the deletion.
    """
    logger.warning(f"Deleting push mapping {mapping_id} from application {app_id}, delete_target_group={delete_target_group}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/apps/{app_id}/group-push/mappings/{mapping_id}?deleteTargetGroup={str(delete_target_group).lower()}"
        _, err = await _execute(client, "DELETE", path)

        if err:
            logger.error(f"Error deleting push mapping {mapping_id} from app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Deleted push mapping {mapping_id} from app {app_id}")
        return {"message": f"Group push mapping {mapping_id} deleted from application {app_id}."}

    except Exception as e:
        logger.error(f"Exception deleting push mapping {mapping_id} from app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
