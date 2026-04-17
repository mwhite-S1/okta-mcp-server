# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import re
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeactivateConfirmation, DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import DEACTIVATE_DEVICE, DELETE_DEVICE, SUSPEND_DEVICE
from okta_mcp_server.utils.validation import validate_ids


async def _execute(client, method: str, path: str, body: dict = None):
    """Make a direct API call via the SDK's request executor.

    Returns:
        (response, body, error) where response is the raw HTTP response object
        (useful for headers like Link), body is the parsed JSON response
        (dict or list), and error is any error encountered.
    """
    import json as _json

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
        next_url = match.group(1)
        params = parse_qs(urlparse(next_url).query)
        values = params.get("after", [])
        return values[0] if values else None
    except Exception:
        return None


@mcp.tool()
async def list_devices(
    ctx: Context,
    search: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    expand: Optional[str] = None,
) -> dict:
    """List devices in the Okta organization.

    Parameters:
        search (str, optional): SCIM filter expression for device attributes,
            e.g. 'status eq "ACTIVE"' or 'profile.displayName co "Mac"'.
            Searchable properties: id, status, lastUpdated, and all profile attributes.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Number of results per page (max 200, default 200).
        expand (str, optional): Embed associated user details in the response.
            Use 'user' for full user details or 'userSummary' for summaries.

    Returns:
        Dict containing:
        - items: List of device objects
        - total_fetched: Number of devices returned
        - has_more: Boolean indicating if more results are available
        - next_cursor: Cursor value to pass as 'after' for the next page
    """
    logger.info("Listing devices from Okta organization")

    if limit is not None and limit > 200:
        logger.warning(f"Limit {limit} exceeds maximum (200), setting to 200")
        limit = 200

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        query_params = {}
        if search:
            query_params["search"] = search
        if after:
            query_params["after"] = after
        if limit:
            query_params["limit"] = limit
        if expand:
            query_params["expand"] = expand

        path = "/api/v1/devices"
        if query_params:
            path += f"?{urlencode(query_params)}"

        response, body, error = await _execute(client, "GET", path)

        if error:
            logger.error(f"Okta API error while listing devices: {error}")
            return {"error": str(error)}

        items = body if isinstance(body, list) else ([] if not body else [body])
        next_cursor = _parse_next_cursor(response)

        logger.info(f"Successfully retrieved {len(items)} devices (has_more={next_cursor is not None})")
        return {
            "items": items,
            "total_fetched": len(items),
            "has_more": next_cursor is not None,
            "next_cursor": next_cursor,
        }

    except Exception as e:
        logger.error(f"Exception while listing devices: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("device_id")
async def get_device(ctx: Context, device_id: str) -> dict:
    """Get a device by ID from the Okta organization.

    Parameters:
        device_id (str, required): The ID of the device to retrieve

    Returns:
        Dictionary containing the device details or error information.
    """
    logger.info(f"Getting device with ID: {device_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, body, error = await _execute(client, "GET", f"/api/v1/devices/{device_id}")

        if error:
            logger.error(f"Okta API error while getting device {device_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved device: {device_id}")
        return body

    except Exception as e:
        logger.error(f"Exception while getting device {device_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("device_id")
async def list_device_users(ctx: Context, device_id: str) -> list:
    """List users associated with a device.

    Parameters:
        device_id (str, required): The ID of the device

    Returns:
        List of device user objects.
    """
    logger.info(f"Listing users for device: {device_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, body, error = await _execute(client, "GET", f"/api/v1/devices/{device_id}/users")

        if error:
            logger.error(f"Okta API error while listing device users for {device_id}: {error}")
            return [{"error": str(error)}]

        if not body:
            logger.info(f"No users found for device {device_id}")
            return []

        logger.info(f"Successfully retrieved {len(body)} users for device {device_id}")
        return body

    except Exception as e:
        logger.error(f"Exception while listing device users for {device_id}: {type(e).__name__}: {e}")
        return [{"error": str(e)}]


@mcp.tool()
@validate_ids("device_id")
async def activate_device(ctx: Context, device_id: str) -> dict:
    """Activate a device in the Okta organization.

    Transitions the device from CREATED or DEACTIVATED status to ACTIVE.

    Parameters:
        device_id (str, required): The ID of the device to activate

    Returns:
        Dictionary containing the result of the activation operation.
    """
    logger.info(f"Activating device: {device_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, error = await _execute(client, "POST", f"/api/v1/devices/{device_id}/lifecycle/activate")

        if error:
            logger.error(f"Okta API error while activating device {device_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully activated device: {device_id}")
        return {"message": f"Device {device_id} activated successfully"}

    except Exception as e:
        logger.error(f"Exception while activating device {device_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("device_id")
async def deactivate_device(ctx: Context, device_id: str) -> dict:
    """Deactivate a device in the Okta organization.

    Transitions the device to DEACTIVATED status. This is a prerequisite for deletion.
    The user will be asked for confirmation before the deactivation proceeds.

    Parameters:
        device_id (str, required): The ID of the device to deactivate

    Returns:
        Dictionary containing the result of the deactivation operation.
    """
    logger.info(f"Deactivation requested for device: {device_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _, _dev_obj, _ = await _execute(_client_tmp, "GET", f"/api/v1/devices/{device_id}")
        _dev_name = (_dev_obj.get("profile", {}) or {}).get("displayName", "") if isinstance(_dev_obj, dict) else ""
    except Exception:
        _dev_name = ""
    _dev_resource = f"'{_dev_name}' ({device_id})" if _dev_name else device_id

    outcome = await elicit_or_fallback(
        ctx,
        message=DEACTIVATE_DEVICE.format(resource=_dev_resource),
        schema=DeactivateConfirmation,
        auto_confirm_on_fallback=True,
    )

    if not outcome.confirmed:
        logger.info(f"Device deactivation cancelled for {device_id}")
        return {"message": "Device deactivation cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, error = await _execute(client, "POST", f"/api/v1/devices/{device_id}/lifecycle/deactivate")

        if error:
            logger.error(f"Okta API error while deactivating device {device_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deactivated device: {device_id}")
        return {"message": f"Device {device_id} deactivated successfully"}

    except Exception as e:
        logger.error(f"Exception while deactivating device {device_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("device_id")
async def suspend_device(ctx: Context, device_id: str) -> dict:
    """Suspend a device in the Okta organization.

    Transitions an ACTIVE device to SUSPENDED status, blocking user access.
    The user will be asked for confirmation before the suspension proceeds.

    Parameters:
        device_id (str, required): The ID of the device to suspend

    Returns:
        Dictionary containing the result of the suspension operation.
    """
    logger.info(f"Suspension requested for device: {device_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _, _dev_obj, _ = await _execute(_client_tmp, "GET", f"/api/v1/devices/{device_id}")
        _dev_name = (_dev_obj.get("profile", {}) or {}).get("displayName", "") if isinstance(_dev_obj, dict) else ""
    except Exception:
        _dev_name = ""
    _dev_resource = f"'{_dev_name}' ({device_id})" if _dev_name else device_id

    outcome = await elicit_or_fallback(
        ctx,
        message=SUSPEND_DEVICE.format(resource=_dev_resource),
        schema=DeactivateConfirmation,
        auto_confirm_on_fallback=True,
    )

    if not outcome.confirmed:
        logger.info(f"Device suspension cancelled for {device_id}")
        return {"message": "Device suspension cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, error = await _execute(client, "POST", f"/api/v1/devices/{device_id}/lifecycle/suspend")

        if error:
            logger.error(f"Okta API error while suspending device {device_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully suspended device: {device_id}")
        return {"message": f"Device {device_id} suspended successfully"}

    except Exception as e:
        logger.error(f"Exception while suspending device {device_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("device_id")
async def unsuspend_device(ctx: Context, device_id: str) -> dict:
    """Unsuspend a device in the Okta organization.

    Transitions a SUSPENDED device back to ACTIVE status.

    Parameters:
        device_id (str, required): The ID of the device to unsuspend

    Returns:
        Dictionary containing the result of the unsuspend operation.
    """
    logger.info(f"Unsuspending device: {device_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, error = await _execute(client, "POST", f"/api/v1/devices/{device_id}/lifecycle/unsuspend")

        if error:
            logger.error(f"Okta API error while unsuspending device {device_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully unsuspended device: {device_id}")
        return {"message": f"Device {device_id} unsuspended successfully"}

    except Exception as e:
        logger.error(f"Exception while unsuspending device {device_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("device_id")
async def delete_device(ctx: Context, device_id: str) -> dict:
    """Permanently delete a device from the Okta organization.

    The device must be in DEACTIVATED status before it can be deleted.
    The user will be asked for confirmation before the deletion proceeds.

    Parameters:
        device_id (str, required): The ID of the deactivated device to delete

    Returns:
        Dictionary containing the result of the deletion operation.
    """
    logger.warning(f"Deletion requested for device: {device_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _, _dev_obj, _ = await _execute(_client_tmp, "GET", f"/api/v1/devices/{device_id}")
        _dev_name = (_dev_obj.get("profile", {}) or {}).get("displayName", "") if isinstance(_dev_obj, dict) else ""
    except Exception:
        _dev_name = ""
    _dev_resource = f"'{_dev_name}' ({device_id})" if _dev_name else device_id

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_DEVICE.format(resource=_dev_resource),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": (
                f"To confirm deletion of device {_dev_resource}, please confirm. "
                "The device must already be deactivated. This action cannot be undone."
            ),
            "device_id": device_id,
        },
    )

    if not outcome.used_elicitation:
        logger.info(f"Elicitation unavailable for device {device_id} — returning fallback confirmation prompt")
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Device deletion cancelled for {device_id}")
        return {"message": "Device deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, error = await _execute(client, "DELETE", f"/api/v1/devices/{device_id}")

        if error:
            logger.error(f"Okta API error while deleting device {device_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted device: {device_id}")
        return {"message": f"Device {device_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception while deleting device {device_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
