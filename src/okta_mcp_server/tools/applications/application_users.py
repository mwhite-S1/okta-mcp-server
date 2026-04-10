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
async def list_application_users(
    ctx: Context,
    app_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    q: Optional[str] = None,
    expand: Optional[str] = None,
) -> dict:
    """List all users assigned to an application.

    Parameters:
        app_id (str, required): The ID of the application.
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max number of results per page.
        q (str, optional): Filters users by login, firstName, lastName, or email.
        expand (str, optional): Set to "user" to include the full user object.

    Returns:
        Dict with items (list of AppUser objects) and total_fetched.
    """
    logger.info(f"Listing users assigned to application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if after:
            kwargs["after"] = after
        if limit:
            kwargs["limit"] = limit
        if q:
            kwargs["q"] = q
        if expand:
            kwargs["expand"] = expand

        users, _, err = await client.list_application_users(app_id, **kwargs)

        if err:
            logger.error(f"Error listing users for app {app_id}: {err}")
            return {"error": str(err)}

        items = [u.to_dict() if hasattr(u, "to_dict") else u for u in (users or [])]
        logger.info(f"Retrieved {len(items)} users for app {app_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing users for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def assign_user_to_application(
    ctx: Context,
    app_id: str,
    app_user: Dict[str, Any],
) -> dict:
    """Assign a user to an application.

    For SSO-only apps, the body typically just needs the user ID. For provisioning
    apps, include credentials and an app-specific profile.

    Parameters:
        app_id (str, required): The ID of the application.
        app_user (dict, required): AppUser assignment object, must include:
            - id (str): The Okta user ID to assign.
            - credentials (dict, optional): App-specific credentials.
            - profile (dict, optional): App-specific profile attributes.

    Returns:
        Dict containing the created AppUser assignment.
    """
    logger.info(f"Assigning user to application {app_id}: user_id={app_user.get('id')}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        user, _, err = await client.assign_user_to_application(app_id, app_user)

        if err:
            logger.error(f"Error assigning user to app {app_id}: {err}")
            return {"error": str(err)}

        result = user.to_dict() if hasattr(user, "to_dict") else user
        logger.info(f"Assigned user to app {app_id}")
        return result

    except Exception as e:
        logger.error(f"Exception assigning user to app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "user_id", error_return_type="dict")
async def get_application_user(
    ctx: Context,
    app_id: str,
    user_id: str,
    expand: Optional[str] = None,
) -> dict:
    """Retrieve a specific user assignment for an application.

    Parameters:
        app_id (str, required): The ID of the application.
        user_id (str, required): The ID of the user assignment to retrieve.
        expand (str, optional): Set to "user" to include the full user object.

    Returns:
        Dict containing the AppUser assignment details.
    """
    logger.info(f"Getting user {user_id} from application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if expand:
            kwargs["expand"] = expand

        user, _, err = await client.get_application_user(app_id, user_id, **kwargs)

        if err:
            logger.error(f"Error getting user {user_id} from app {app_id}: {err}")
            return {"error": str(err)}

        return user.to_dict() if hasattr(user, "to_dict") else user

    except Exception as e:
        logger.error(f"Exception getting user {user_id} from app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "user_id", error_return_type="dict")
async def update_application_user(
    ctx: Context,
    app_id: str,
    user_id: str,
    app_user: Dict[str, Any],
) -> dict:
    """Update the profile or credentials of a user assigned to an application.

    Parameters:
        app_id (str, required): The ID of the application.
        user_id (str, required): The ID of the user assignment to update.
        app_user (dict, required): Updated AppUser object with:
            - credentials (dict, optional): Updated app-specific credentials.
            - profile (dict, optional): Updated app-specific profile attributes.

    Returns:
        Dict containing the updated AppUser assignment.
    """
    logger.info(f"Updating user {user_id} in application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        user, _, err = await client.update_application_user(app_id, user_id, app_user)

        if err:
            logger.error(f"Error updating user {user_id} in app {app_id}: {err}")
            return {"error": str(err)}

        result = user.to_dict() if hasattr(user, "to_dict") else user
        logger.info(f"Updated user {user_id} in app {app_id}")
        return result

    except Exception as e:
        logger.error(f"Exception updating user {user_id} in app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "user_id", error_return_type="dict")
async def unassign_user_from_application(
    ctx: Context,
    app_id: str,
    user_id: str,
    send_email: bool = False,
) -> dict:
    """Unassign a user from an application.

    If the app is provisioning-enabled and configured to deactivate users, the user
    will also be deactivated in the target app. This operation cannot be undone —
    the user's app profile is permanently removed.

    Parameters:
        app_id (str, required): The ID of the application.
        user_id (str, required): The ID of the user assignment to remove.
        send_email (bool, optional): Send a deactivation email to the admin. Default: False.

    Returns:
        Dict confirming the unassignment.
    """
    logger.warning(f"Unassigning user {user_id} from application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.unassign_user_from_application(app_id, user_id, send_email=send_email)

        if err:
            logger.error(f"Error unassigning user {user_id} from app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Unassigned user {user_id} from app {app_id}")
        return {"message": f"User {user_id} unassigned from application {app_id}."}

    except Exception as e:
        logger.error(f"Exception unassigning user {user_id} from app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
