# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Any, Dict, List, Optional

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.validation import validate_ids


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def list_application_group_assignments(
    ctx: Context,
    app_id: str,
    q: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    expand: Optional[str] = None,
) -> dict:
    """List all group assignments for an application.

    Parameters:
        app_id (str, required): The ID of the application.
        q (str, optional): Filters groups by name prefix (startsWith).
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max number of results per page.
        expand (str, optional): Set to "group" to include the full group profile.

    Returns:
        Dict with items (list of ApplicationGroupAssignment objects) and total_fetched.
    """
    logger.info(f"Listing group assignments for application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if q:
            kwargs["q"] = q
        if after:
            kwargs["after"] = after
        if limit:
            kwargs["limit"] = limit
        if expand:
            kwargs["expand"] = expand

        assignments, _, err = await client.list_application_group_assignments(app_id, **kwargs)

        if err:
            logger.error(f"Error listing group assignments for app {app_id}: {err}")
            return {"error": str(err)}

        items = [a.to_dict() if hasattr(a, "to_dict") else a for a in (assignments or [])]
        logger.info(f"Retrieved {len(items)} group assignments for app {app_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing group assignments for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "group_id", error_return_type="dict")
async def get_application_group_assignment(
    ctx: Context,
    app_id: str,
    group_id: str,
    expand: Optional[str] = None,
) -> dict:
    """Retrieve a specific group assignment for an application.

    Parameters:
        app_id (str, required): The ID of the application.
        group_id (str, required): The ID of the group assignment to retrieve.
        expand (str, optional): Set to "group" to include the full group profile.

    Returns:
        Dict containing the ApplicationGroupAssignment details.
    """
    logger.info(f"Getting group {group_id} assignment for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if expand:
            kwargs["expand"] = expand

        assignment, _, err = await client.get_application_group_assignment(app_id, group_id, **kwargs)

        if err:
            logger.error(f"Error getting group {group_id} for app {app_id}: {err}")
            return {"error": str(err)}

        return assignment.to_dict() if hasattr(assignment, "to_dict") else assignment

    except Exception as e:
        logger.error(f"Exception getting group {group_id} for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "group_id", error_return_type="dict")
async def assign_group_to_application(
    ctx: Context,
    app_id: str,
    group_id: str,
    assignment: Optional[Dict[str, Any]] = None,
) -> dict:
    """Assign a group to an application.

    Assigns a group to an app, which in turn gives each group member access to the app.
    The resulting AppUser scope is GROUP for users assigned via group membership.

    Parameters:
        app_id (str, required): The ID of the application.
        group_id (str, required): The ID of the group to assign.
        assignment (dict, optional): Optional assignment configuration:
            - priority (int, optional): Priority of the group assignment.
            - profile (dict, optional): App-specific profile for the group.

    Returns:
        Dict containing the created ApplicationGroupAssignment.
    """
    logger.info(f"Assigning group {group_id} to application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        result, _, err = await client.assign_group_to_application(app_id, group_id, assignment or {})

        if err:
            logger.error(f"Error assigning group {group_id} to app {app_id}: {err}")
            return {"error": str(err)}

        out = result.to_dict() if hasattr(result, "to_dict") else result
        logger.info(f"Assigned group {group_id} to app {app_id}")
        return out

    except Exception as e:
        logger.error(f"Exception assigning group {group_id} to app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "group_id", error_return_type="dict")
async def update_application_group_assignment(
    ctx: Context,
    app_id: str,
    group_id: str,
    patch_operations: List[Dict[str, Any]],
) -> dict:
    """Update a group assignment for an application using JSON Patch.

    Parameters:
        app_id (str, required): The ID of the application.
        group_id (str, required): The ID of the group assignment to update.
        patch_operations (list, required): List of JSON Patch operations, each with:
            - op (str): "add", "remove", or "replace"
            - path (str): JSON path to the field to patch (e.g. "/priority")
            - value: New value for the field.

    Returns:
        Dict containing the updated ApplicationGroupAssignment.
    """
    logger.info(f"Updating group {group_id} assignment for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        result, _, err = await client.update_group_assignment_to_application(app_id, group_id, patch_operations)

        if err:
            logger.error(f"Error updating group {group_id} for app {app_id}: {err}")
            return {"error": str(err)}

        out = result.to_dict() if hasattr(result, "to_dict") else result
        logger.info(f"Updated group {group_id} assignment for app {app_id}")
        return out

    except Exception as e:
        logger.error(f"Exception updating group {group_id} for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "group_id", error_return_type="dict")
async def unassign_group_from_application(
    ctx: Context,
    app_id: str,
    group_id: str,
) -> dict:
    """Unassign a group from an application.

    Removes the group assignment. Users that were assigned via this group will
    lose access to the app (unless they are directly assigned or part of another
    assigned group).

    Parameters:
        app_id (str, required): The ID of the application.
        group_id (str, required): The ID of the group to unassign.

    Returns:
        Dict confirming the unassignment.
    """
    logger.warning(f"Unassigning group {group_id} from application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.unassign_application_from_group(app_id, group_id)

        if err:
            logger.error(f"Error unassigning group {group_id} from app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Unassigned group {group_id} from app {app_id}")
        return {"message": f"Group {group_id} unassigned from application {app_id}."}

    except Exception as e:
        logger.error(f"Exception unassigning group {group_id} from app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
