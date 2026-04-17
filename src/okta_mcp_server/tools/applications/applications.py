# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import json as _json
import re
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeactivateConfirmation, DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import DEACTIVATE_APPLICATION, DELETE_APPLICATION
from okta_mcp_server.utils.serialize import to_dict
from okta_mcp_server.utils.validation import validate_ids


async def _execute(client, method: str, path: str, body: dict = None, keep_empty_params: bool = False):
    """Make a direct API call bypassing SDK Pydantic deserialization.

    Returns (response, body, error). response carries HTTP headers (e.g. Link
    for pagination cursors); body is the parsed JSON dict or list.
    """
    request_executor = client.get_request_executor()
    url = f"{client.get_base_url()}{path}"
    request, error = await request_executor.create_request(method, url, body or {}, keep_empty_params=keep_empty_params)
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
async def list_applications(
    ctx: Context,
    q: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    filter: Optional[str] = None,
    expand: Optional[str] = None,
    include_non_deleted: Optional[bool] = None,
) -> dict:
    """List all applications from the Okta organization.

    PARAMETER SELECTION GUIDE — pick one search parameter, do not combine:
        filter (PREFERRED for status/id queries): Okta filter expression. Use for exact
            status filtering or lookups by user/group assignment. Reliable and indexed.
              by status:     filter='status eq "ACTIVE"'
              by user:       filter='user.id eq "00u1234abcd"'
              by group:      filter='group.id eq "00g1234abcd"'

        q: Prefix text search on the application label. Unreliable for labels containing
            special characters (dots, hyphens, slashes). Only use for casual browsing
            when an inexact match is acceptable.
              example: q="Salesforce"

    Parameters:
        q (str, optional): Prefix text search on app label (avoid for special-character names).
        filter (str, optional): Okta filter expression for status, user.id, or group.id (preferred).
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Results per page (min 20, max 100).
        expand (str, optional): Embed related resources inline (e.g. "user/groups").
        include_non_deleted (bool, optional): Include non-deleted applications in results.

    Examples:
        List all active applications:
            list_applications(filter='status eq "ACTIVE"')
        Find apps assigned to a specific group:
            list_applications(filter='group.id eq "00g1234abcd"')
        Browse apps by name prefix:
            list_applications(q="Okta")

    Returns:
        Dict containing:
        - items: List of application objects
        - total_fetched: Number of applications returned
        - has_more: Boolean indicating if more results are available
        - next_cursor: Cursor value to pass as 'after' for the next page
    """
    logger.info("Listing applications from Okta organization")
    logger.debug(f"Query parameters: q='{q}', filter='{filter}', limit={limit}")

    # Validate limit parameter range
    if limit is not None:
        if limit < 20:
            logger.warning(f"Limit {limit} is below minimum (20), setting to 20")
            limit = 20
        elif limit > 100:
            logger.warning(f"Limit {limit} exceeds maximum (100), setting to 100")
            limit = 100

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        params: Dict[str, Any] = {}
        if q:
            params["q"] = q
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit
        if filter:
            params["filter"] = filter
        if expand:
            params["expand"] = expand
        if include_non_deleted is not None:
            params["includeNonDeleted"] = str(include_non_deleted).lower()

        path = f"/api/v1/apps?{urlencode(params)}" if params else "/api/v1/apps"
        logger.debug(f"Calling Okta API to list applications: {path}")
        response, apps, err = await _execute(client, "GET", path)

        if err:
            logger.error(f"Okta API error while listing applications: {err}")
            return {"error": str(err)}

        if not apps:
            logger.info("No applications found")
            return {"items": [], "total_fetched": 0, "has_more": False, "next_cursor": None}

        items = apps if isinstance(apps, list) else [apps]
        next_cursor = _parse_next_cursor(response)
        logger.info(f"Successfully retrieved {len(items)} applications (has_more={next_cursor is not None})")
        return {
            "items": items,
            "total_fetched": len(items),
            "has_more": next_cursor is not None,
            "next_cursor": next_cursor,
        }
    except Exception as e:
        logger.error(f"Exception while listing applications: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def get_application(ctx: Context, app_id: str, expand: Optional[str] = None) -> Any:
    """Get an application by ID from the Okta organization.

    Parameters:
        app_id (str, required): The ID of the application to retrieve
        expand (str, optional): Expands the app user object to include the user's profile or expand the
        app group object

    Returns:
        Dictionary containing the application details or error information.
    """
    logger.info(f"Getting application with ID: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        params: Dict[str, Any] = {}
        if expand:
            params["expand"] = expand
        path = f"/api/v1/apps/{app_id}?{urlencode(params)}" if params else f"/api/v1/apps/{app_id}"
        _, app, err = await _execute(client, "GET", path)

        if err:
            logger.error(f"Okta API error while getting application {app_id}: {err}")
            return {"error": str(err)}

        if not app:
            return None

        logger.info(f"Successfully retrieved application: {app_id}")
        return [app] if isinstance(app, dict) else [to_dict(app)]
    except Exception as e:
        logger.error(f"Exception while getting application {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_application(ctx: Context, app_config: Dict[str, Any], activate: bool = True) -> Any:
    """Create a new application in the Okta organization.

    Parameters:
        app_config (dict, required): The application configuration including name, label, signOnMode, settings, etc.
        activate (bool, optional): Execute activation lifecycle operation after creation. Defaults to True.

    Returns:
        Dictionary containing the created application details or error information.
    """
    logger.info("Creating new application in Okta organization")
    logger.debug(f"Application label: {app_config.get('label', 'N/A')}, name: {app_config.get('name', 'N/A')}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        activate_str = "true" if activate else "false"
        path = f"/api/v1/apps?activate={activate_str}"

        logger.debug("Calling Okta API to create application")
        _, app, err = await _execute(client, "POST", path, app_config, keep_empty_params=True)

        if err:
            logger.error(f"Okta API error while creating application: {err}")
            return {"error": str(err)}

        logger.info(f"Successfully created application")
        return app if isinstance(app, dict) else to_dict(app)
    except Exception as e:
        logger.error(f"Exception while creating application: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def update_application(ctx: Context, app_id: str, app_config: Dict[str, Any]) -> Any:
    """Update an application by ID in the Okta organization.

    Parameters:
        app_id (str, required): The ID of the application to update
        app_config (dict, required): The updated application configuration

    Returns:
        Dictionary containing the updated application details or error information.
    """
    logger.info(f"Updating application with ID: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        logger.debug(f"Calling Okta API to update application {app_id}")
        _, app, err = await _execute(client, "PUT", f"/api/v1/apps/{app_id}", app_config, keep_empty_params=True)

        if err:
            logger.error(f"Okta API error while updating application {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Successfully updated application: {app_id}")
        return app if isinstance(app, dict) else to_dict(app)
    except Exception as e:
        logger.error(f"Exception while updating application {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id")
async def delete_application(ctx: Context, app_id: str) -> list:
    """Delete an application by ID from the Okta organization.

    This tool deletes an application by its ID from the Okta organization.
    The user will be asked for confirmation before the deletion proceeds.

    Parameters:
        app_id (str, required): The ID of the application to delete

    Returns:
        List containing the result of the deletion operation.
    """
    logger.warning(f"Deletion requested for application {app_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _, _app_obj, _ = await _execute(_client_tmp, "GET", f"/api/v1/apps/{app_id}")
        _app_name = _app_obj.get("label", "") if isinstance(_app_obj, dict) else ""
    except Exception:
        _app_name = ""
    _app_resource = f"'{_app_name}' ({app_id})" if _app_name else app_id

    fallback_payload = {
        "confirmation_required": True,
        "message": (
            f"To confirm deletion of application {_app_resource}, please call the "
            f"'confirm_delete_application' tool with app_id='{app_id}' and "
            f"confirmation='DELETE'."
        ),
        "app_id": app_id,
        "tool_to_use": "confirm_delete_application",
    }

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_APPLICATION.format(resource=_app_resource),
        schema=DeleteConfirmation,
        fallback_payload=fallback_payload,
    )

    if not outcome.used_elicitation:
        logger.info(f"Elicitation unavailable for application {app_id} — returning fallback confirmation prompt")
        return [outcome.fallback_response]

    if not outcome.confirmed:
        logger.info(f"Application deletion cancelled for {app_id}")
        return [{"message": "Application deletion cancelled by user."}]

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        logger.debug(f"Calling Okta API to delete application {app_id}")

        _, _, err = await client.delete_application(app_id)

        if err:
            logger.error(f"Okta API error while deleting application {app_id}: {err}")
            return [{"error": f"Error: {err}"}]

        logger.info(f"Successfully deleted application: {app_id}")
        return [{"message": f"Application {app_id} deleted successfully"}]
    except Exception as e:
        logger.error(f"Exception while deleting application {app_id}: {type(e).__name__}: {e}")
        return [{"error": f"Exception: {e}"}]


@mcp.tool()
@validate_ids("app_id")
async def confirm_delete_application(ctx: Context, app_id: str, confirmation: str) -> list:
    """Confirm and execute application deletion after receiving confirmation.

    .. deprecated::
        This tool exists for backward compatibility with clients that do not
        support MCP elicitation.  New clients should rely on the built-in
        elicitation prompt in ``delete_application`` instead.

    This function MUST ONLY be called after the human user has explicitly typed 'DELETE' as confirmation.
    NEVER call this function automatically after delete_application.

    Parameters:
        app_id (str, required): The ID of the application to delete
        confirmation (str, required): Must be 'DELETE' to confirm deletion

    Returns:
        List containing the result of the deletion operation.
    """
    logger.info(f"Processing deletion confirmation for application {app_id} (deprecated flow)")

    if confirmation != "DELETE":
        logger.warning(f"Application deletion cancelled for {app_id} - incorrect confirmation")
        return ["Error: Deletion cancelled. Confirmation 'DELETE' was not provided correctly."]

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        logger.debug(f"Calling Okta API to delete application {app_id}")

        _, _, err = await client.delete_application(app_id)

        if err:
            logger.error(f"Okta API error while deleting application {app_id}: {err}")
            return [f"Error: {err}"]

        logger.info(f"Successfully deleted application: {app_id}")
        return [f"Application {app_id} deleted successfully"]
    except Exception as e:
        logger.error(f"Exception while deleting application {app_id}: {type(e).__name__}: {e}")
        return [f"Exception: {e}"]


@mcp.tool()
@validate_ids("app_id")
async def activate_application(ctx: Context, app_id: str) -> list:
    """Activate an application in the Okta organization.

    Parameters:
        app_id (str, required): The ID of the application to activate

    Returns:
        List containing the result of the activation operation.
    """
    logger.info(f"Activating application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        logger.debug(f"Calling Okta API to activate application {app_id}")

        _, _, err = await client.activate_application(app_id)

        if err:
            logger.error(f"Okta API error while activating application {app_id}: {err}")
            return [f"Error: {err}"]

        logger.info(f"Successfully activated application: {app_id}")
        return [f"Application {app_id} activated successfully"]
    except Exception as e:
        logger.error(f"Exception while activating application {app_id}: {type(e).__name__}: {e}")
        return [f"Exception: {e}"]


@mcp.tool()
@validate_ids("app_id")
async def deactivate_application(ctx: Context, app_id: str) -> list:
    """Deactivate an application in the Okta organization.

    Parameters:
        app_id (str, required): The ID of the application to deactivate

    Returns:
        List containing the result of the deactivation operation.
    """
    logger.info(f"Deactivation requested for application: {app_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _, _app_obj, _ = await _execute(_client_tmp, "GET", f"/api/v1/apps/{app_id}")
        _app_name = _app_obj.get("label", "") if isinstance(_app_obj, dict) else ""
    except Exception:
        _app_name = ""
    _app_resource = f"'{_app_name}' ({app_id})" if _app_name else app_id

    outcome = await elicit_or_fallback(
        ctx,
        message=DEACTIVATE_APPLICATION.format(resource=_app_resource),
        schema=DeactivateConfirmation,
        auto_confirm_on_fallback=True,
    )

    if not outcome.confirmed:
        logger.info(f"Application deactivation cancelled for {app_id}")
        return [{"message": "Application deactivation cancelled by user."}]

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        logger.debug(f"Calling Okta API to deactivate application {app_id}")

        _, _, err = await client.deactivate_application(app_id)

        if err:
            logger.error(f"Okta API error while deactivating application {app_id}: {err}")
            return [f"Error: {err}"]

        logger.info(f"Successfully deactivated application: {app_id}")
        return [f"Application {app_id} deactivated successfully"]
    except Exception as e:
        logger.error(f"Exception while deactivating application {app_id}: {type(e).__name__}: {e}")
        return [f"Exception: {e}"]
