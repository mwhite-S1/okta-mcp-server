# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""User admin role target tools.

Covers /api/v1/users/{userId}/roles/{roleAssignmentId}/targets/* — scoping
admin role assignments to specific applications or groups for least-privilege.

When an admin role is assigned to a user without targets, the role applies
org-wide. Adding targets restricts the role to only the specified apps or groups.
"""

import json as _json
from typing import Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.validation import validate_ids


async def _execute(client, method: str, path: str, body: dict = None):
    """Make a direct API call via the SDK request executor."""
    request_executor = client.get_request_executor()
    url = f"{client.get_base_url()}{path}"
    request, error = await request_executor.create_request(method, url, body or {})
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


# ---------------------------------------------------------------------------
# Application Targets
# ---------------------------------------------------------------------------

@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def list_user_app_role_targets(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all application targets for a user's admin role assignment.

    Returns the applications that the role assignment is scoped to. If no
    targets are configured, the role applies to all apps org-wide.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max results per page.

    Returns:
        Dict with items (list of CatalogApplication objects) and total_fetched.
        Each item includes: id, name, label, status, and optionally instances.
    """
    logger.info(f"Listing app role targets for user {user_id}, role {role_assignment_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        params = {}
        if after:
            params["after"] = after
        if limit is not None:
            params["limit"] = str(limit)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/targets/catalog/apps"
        if params:
            path += f"?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error listing app role targets for user {user_id}: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else []
        logger.info(f"Retrieved {len(items)} app target(s)")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing app role targets: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def assign_all_apps_as_user_role_target(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
) -> dict:
    """Assign all applications as targets for a user's admin role.

    Expands the role's scope to cover all applications in the org. This
    removes any previously set specific app targets and makes the role
    apply to all apps.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.

    Returns:
        Dict confirming the assignment.
    """
    logger.info(f"Assigning all apps as targets for user {user_id}, role {role_assignment_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/targets/catalog/apps"
        _, error = await _execute(client, "PUT", path)
        if error:
            logger.error(f"Error assigning all apps as targets: {error}")
            return {"error": str(error)}
        logger.info(f"Assigned all apps as targets for user {user_id}, role {role_assignment_id}")
        return {"message": f"All apps assigned as targets for role {role_assignment_id} on user {user_id}."}
    except Exception as e:
        logger.error(f"Exception assigning all apps as role targets: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def assign_app_target_to_user_role(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
    app_name: str,
) -> dict:
    """Assign a specific application type as a target for a user's admin role.

    Scopes the admin role to apply only to all instances of the specified
    application type (catalog app). To scope to a specific instance, use
    assign_app_instance_target_to_user_role instead.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.
        app_name (str, required): The catalog application name (app type key,
            e.g. "salesforce", "slack", "office365"). Use list_applications to
            find the app's name field.

    Returns:
        Dict confirming the assignment.
    """
    logger.info(f"Assigning app {app_name} as target for user {user_id}, role {role_assignment_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/targets/catalog/apps/{app_name}"
        _, error = await _execute(client, "PUT", path)
        if error:
            logger.error(f"Error assigning app {app_name} as target: {error}")
            return {"error": str(error)}
        logger.info(f"Assigned app {app_name} as target")
        return {"message": f"Application {app_name} assigned as target for role {role_assignment_id}."}
    except Exception as e:
        logger.error(f"Exception assigning app target to user role: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def unassign_app_target_from_user_role(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
    app_name: str,
) -> dict:
    """Remove an application type target from a user's admin role assignment.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.
        app_name (str, required): The catalog application name to remove.

    Returns:
        Dict confirming the removal.
    """
    logger.info(f"Removing app {app_name} target from user {user_id}, role {role_assignment_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/targets/catalog/apps/{app_name}"
        _, error = await _execute(client, "DELETE", path)
        if error:
            logger.error(f"Error removing app {app_name} target: {error}")
            return {"error": str(error)}
        logger.info(f"Removed app {app_name} target from role {role_assignment_id}")
        return {"message": f"Application {app_name} removed as target from role {role_assignment_id}."}
    except Exception as e:
        logger.error(f"Exception removing app target from user role: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "app_id", error_return_type="dict")
async def assign_app_instance_target_to_user_role(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
    app_name: str,
    app_id: str,
) -> dict:
    """Assign a specific application instance as a target for a user's admin role.

    Scopes the admin role to a single specific application instance (identified
    by both the app type name and instance ID). More granular than assigning
    all instances of an app type.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.
        app_name (str, required): The catalog application name (app type key).
        app_id (str, required): The specific application instance ID (0oa...).

    Returns:
        Dict confirming the assignment.
    """
    logger.info(f"Assigning app instance {app_id} ({app_name}) as target for user {user_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/targets/catalog/apps/{app_name}/{app_id}"
        _, error = await _execute(client, "PUT", path)
        if error:
            logger.error(f"Error assigning app instance {app_id} as target: {error}")
            return {"error": str(error)}
        logger.info(f"Assigned app instance {app_id} as target")
        return {"message": f"Application instance {app_id} assigned as target for role {role_assignment_id}."}
    except Exception as e:
        logger.error(f"Exception assigning app instance target: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "app_id", error_return_type="dict")
async def unassign_app_instance_target_from_user_role(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
    app_name: str,
    app_id: str,
) -> dict:
    """Remove a specific application instance target from a user's admin role.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.
        app_name (str, required): The catalog application name (app type key).
        app_id (str, required): The specific application instance ID to remove.

    Returns:
        Dict confirming the removal.
    """
    logger.info(f"Removing app instance {app_id} target from user {user_id}, role {role_assignment_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/targets/catalog/apps/{app_name}/{app_id}"
        _, error = await _execute(client, "DELETE", path)
        if error:
            logger.error(f"Error removing app instance {app_id} target: {error}")
            return {"error": str(error)}
        logger.info(f"Removed app instance {app_id} target from role {role_assignment_id}")
        return {"message": f"Application instance {app_id} removed as target from role {role_assignment_id}."}
    except Exception as e:
        logger.error(f"Exception removing app instance target: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Group Targets
# ---------------------------------------------------------------------------

@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def list_user_group_role_targets(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all group targets for a user's admin role assignment.

    Returns the groups that the role assignment is scoped to. Commonly used
    with the USER_ADMIN or HELP_DESK_ADMIN roles to restrict admin scope
    to specific user populations.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max results per page.

    Returns:
        Dict with items (list of Group objects) and total_fetched.
    """
    logger.info(f"Listing group role targets for user {user_id}, role {role_assignment_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        params = {}
        if after:
            params["after"] = after
        if limit is not None:
            params["limit"] = str(limit)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/targets/groups"
        if params:
            path += f"?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error listing group role targets for user {user_id}: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else []
        logger.info(f"Retrieved {len(items)} group target(s)")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing group role targets: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "group_id", error_return_type="dict")
async def assign_group_target_to_user_role(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
    group_id: str,
) -> dict:
    """Assign a group as a target for a user's admin role assignment.

    Scopes the admin role to the specified group. Commonly used to give a
    help-desk admin or user admin authority over a specific subset of users
    without org-wide access.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.
        group_id (str, required): The ID of the group to add as a target.

    Returns:
        Dict confirming the group was added as a target.
    """
    logger.info(f"Assigning group {group_id} as target for user {user_id}, role {role_assignment_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/targets/groups/{group_id}"
        _, error = await _execute(client, "PUT", path)
        if error:
            logger.error(f"Error assigning group {group_id} as target: {error}")
            return {"error": str(error)}
        logger.info(f"Assigned group {group_id} as target for role {role_assignment_id}")
        return {"message": f"Group {group_id} assigned as target for role {role_assignment_id}."}
    except Exception as e:
        logger.error(f"Exception assigning group target to user role: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "group_id", error_return_type="dict")
async def unassign_group_target_from_user_role(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
    group_id: str,
) -> dict:
    """Remove a group target from a user's admin role assignment.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.
        group_id (str, required): The ID of the group to remove as a target.

    Returns:
        Dict confirming the group was removed as a target.
    """
    logger.info(f"Removing group {group_id} target from user {user_id}, role {role_assignment_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/targets/groups/{group_id}"
        _, error = await _execute(client, "DELETE", path)
        if error:
            logger.error(f"Error removing group {group_id} target: {error}")
            return {"error": str(error)}
        logger.info(f"Removed group {group_id} target from role {role_assignment_id}")
        return {"message": f"Group {group_id} removed as target from role {role_assignment_id}."}
    except Exception as e:
        logger.error(f"Exception removing group target from user role: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Combined role targets view
# ---------------------------------------------------------------------------

@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def get_user_role_targets(
    ctx: Context,
    user_id: str,
    role_id: str,
) -> dict:
    """Retrieve all targets for a role assignment by role type or encoded role ID.

    Returns all app and group targets combined for the given role. Useful as a
    single call to see the complete scope of a role assignment.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_id (str, required): The role type key (e.g. "USER_ADMIN",
            "APP_ADMIN", "HELP_DESK_ADMIN") or an encoded role assignment ID.

    Returns:
        Dict containing the role targets (apps and/or groups).
    """
    logger.info(f"Getting role targets for user {user_id}, role {role_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/users/{user_id}/roles/{role_id}/targets")
        if error:
            logger.error(f"Error getting role targets for user {user_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception getting user role targets: {type(e).__name__}: {e}")
        return {"error": str(e)}
