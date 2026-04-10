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
        kwargs = {}
        if after:
            kwargs["after"] = after
        if limit:
            kwargs["limit"] = limit
        if last_updated:
            kwargs["last_updated"] = last_updated
        if source_group_id:
            kwargs["source_group_id"] = source_group_id
        if status:
            kwargs["status"] = status

        mappings, _, err = await client.list_group_push_mappings(app_id, **kwargs)

        if err:
            logger.error(f"Error listing push mappings for app {app_id}: {err}")
            return {"error": str(err)}

        items = [m.to_dict() if hasattr(m, "to_dict") else m for m in (mappings or [])]
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
        result, _, err = await client.create_group_push_mapping(app_id, mapping)

        if err:
            logger.error(f"Error creating push mapping for app {app_id}: {err}")
            return {"error": str(err)}

        out = result.to_dict() if hasattr(result, "to_dict") else result
        logger.info(f"Created push mapping for app {app_id}: {out.get('mappingId', 'unknown')}")
        return out

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
        mapping, _, err = await client.get_group_push_mapping(app_id, mapping_id)

        if err:
            logger.error(f"Error getting push mapping {mapping_id} for app {app_id}: {err}")
            return {"error": str(err)}

        return mapping.to_dict() if hasattr(mapping, "to_dict") else mapping

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
        result, _, err = await client.update_group_push_mapping(app_id, mapping_id, update)

        if err:
            logger.error(f"Error updating push mapping {mapping_id} for app {app_id}: {err}")
            return {"error": str(err)}

        out = result.to_dict() if hasattr(result, "to_dict") else result
        logger.info(f"Updated push mapping {mapping_id} for app {app_id}")
        return out

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
        _, _, err = await client.delete_group_push_mapping(app_id, mapping_id, delete_target_group=delete_target_group)

        if err:
            logger.error(f"Error deleting push mapping {mapping_id} from app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Deleted push mapping {mapping_id} from app {app_id}")
        return {"message": f"Group push mapping {mapping_id} deleted from application {app_id}."}

    except Exception as e:
        logger.error(f"Exception deleting push mapping {mapping_id} from app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
