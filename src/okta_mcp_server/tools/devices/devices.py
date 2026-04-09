# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Optional
from urllib.parse import urlencode

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
        (body, error) where body is the parsed JSON response (dict or list),
        or None on error.
    """
    request_executor = client.get_request_executor()
    url = f"{client.get_base_url()}{path}"

    request, error = await request_executor.create_request(method, url, body or {})
    if error:
        return None, error

    response, error = await request_executor.execute(request)
    if error:
        return None, error

    # 204 No Content responses have no body
    if response is None:
        return None, None
    body = response.get_body()
    return body if body else None, None


@mcp.tool()
async def list_devices(
    ctx: Context,
    search: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    expand: Optional[str] = None,
) -> list:
    """List devices in the Okta organization.

    Parameters:
        search (str, optional): SCIM filter expression for device attributes,
            e.g. 'status eq "ACTIVE"' or 'profile.displayName co "Mac"'.
            Searchable properties: id, status, lastUpdated, and all profile attributes.
        after (str, optional): Pagination cursor for the next page of results
        limit (int, optional): Number of results per page (max 200, default 200)
        expand (str, optional): Embed associated user details in the response.
            Use 'user' for full user details or 'userSummary' for summaries.

    Returns:
        List of device objects.
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

        body, error = await _execute(client, "GET", path)

        if error:
            logger.error(f"Okta API error while listing devices: {error}")
            return [{"error": str(error)}]

        if not body:
            logger.info("No devices found")
            return []

        logger.info(f"Successfully retrieved {len(body)} devices")
        return body

    except Exception as e:
        logger.error(f"Exception while listing devices: {type(e).__name__}: {e}")
        return [{"error": str(e)}]


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
        body, error = await _execute(client, "GET", f"/api/v1/devices/{device_id}")

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
        body, error = await _execute(client, "GET", f"/api/v1/devices/{device_id}/users")

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
        _, error = await _execute(client, "POST", f"/api/v1/devices/{device_id}/lifecycle/activate")

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

    outcome = await elicit_or_fallback(
        ctx,
        message=DEACTIVATE_DEVICE.format(device_id=device_id),
        schema=DeactivateConfirmation,
        auto_confirm_on_fallback=True,
    )

    if not outcome.confirmed:
        logger.info(f"Device deactivation cancelled for {device_id}")
        return {"message": "Device deactivation cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "POST", f"/api/v1/devices/{device_id}/lifecycle/deactivate")

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

    outcome = await elicit_or_fallback(
        ctx,
        message=SUSPEND_DEVICE.format(device_id=device_id),
        schema=DeactivateConfirmation,
        auto_confirm_on_fallback=True,
    )

    if not outcome.confirmed:
        logger.info(f"Device suspension cancelled for {device_id}")
        return {"message": "Device suspension cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "POST", f"/api/v1/devices/{device_id}/lifecycle/suspend")

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
        _, error = await _execute(client, "POST", f"/api/v1/devices/{device_id}/lifecycle/unsuspend")

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

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_DEVICE.format(device_id=device_id),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": (
                f"To confirm deletion of device {device_id}, please confirm. "
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
        _, error = await _execute(client, "DELETE", f"/api/v1/devices/{device_id}")

        if error:
            logger.error(f"Okta API error while deleting device {device_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted device: {device_id}")
        return {"message": f"Device {device_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception while deleting device {device_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
