# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Governance v1 request-types tools: create, list, publish, and manage request types."""

from typing import Any, Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client


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
    return response_body if response_body else None, None


# ---------------------------------------------------------------------------
# Teams (needed to get ownerId for request types)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_governance_teams(
    ctx: Context,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List governance teams in the Okta organization.

    Teams are used as the owner/administrator of v1 request types. The team ID
    (ownerId) is required when creating a request type.

    Parameters:
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of teams to return per page.

    Returns:
        Dictionary containing team objects and pagination info.
    """
    logger.info("Listing governance teams")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = "/governance/api/v1/teams"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing governance teams: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved governance teams")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing governance teams: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Request Types (v1)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_request_types(
    ctx: Context,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all v1 request types in the Okta organization.

    Request types define who can request access to which resources and what
    approval workflow is used. This is the v1 governance API for access
    request configuration.

    Parameters:
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of request types per page.

    Returns:
        Dictionary containing request type objects and pagination info.
    """
    logger.info("Listing v1 request types")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = "/governance/api/v1/request-types"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing request types: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved request types")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing request types: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_request_type(ctx: Context, request_type_id: str) -> dict:
    """Retrieve a specific v1 request type by ID.

    Parameters:
        request_type_id (str, required): The ID of the request type to retrieve.

    Returns:
        Dictionary containing the request type details or error information.
    """
    logger.info(f"Getting request type: {request_type_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET", f"/governance/api/v1/request-types/{request_type_id}"
        )
        if error:
            logger.error(f"Okta API error getting request type {request_type_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved request type: {request_type_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting request type {request_type_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_request_type(
    ctx: Context,
    name: str,
    owner_id: str,
    resource_settings: dict[str, Any],
    approval_settings: dict[str, Any],
    request_settings: Optional[dict[str, Any]] = None,
    description: Optional[str] = None,
    access_duration: Optional[str] = None,
) -> dict:
    """Create a new v1 access request type.

    Request types define which resources can be requested, who can request them,
    and what approval workflow is required. Created request types start as DRAFT
    and must be published to become active.

    Parameters:
        name (str, required): Unique name for this request type (1-50 chars).
        owner_id (str, required): ID of the governance team that administers this
            request type (24-char hex ID). Use list_governance_teams to find it.
        resource_settings (dict, required): Which resource(s) are requestable.
            For groups:
              {"type": "GROUPS", "targetResources": [{"resourceId": "00gXXX..."}]}
            For apps:
              {"type": "APPS", "targetResources": [{"resourceId": "0oaXXX..."}]}
        approval_settings (dict, required): Approval workflow configuration.
            For a specific user approver:
              {"type": "SERIAL", "approvals": [{"approverType": "USER",
               "approverUserId": "00uXXX...", "approverFields": []}]}
            For no approval:
              {"type": "NONE"}
        request_settings (dict, optional): Who can submit requests.
            All users: {"type": "EVERYONE", "requesterFields": []}
            Group members only: {"type": "MEMBER_OF",
              "requesterMemberOf": ["00gXXX..."], "requesterFields": []}
            Defaults to EVERYONE if omitted.
        description (str, optional): Human-readable description (1-2000 chars).
        access_duration (str, optional): ISO 8601 duration for how long access
            is granted after approval. E.g. "P30D" (30 days), "PT8H" (8 hours).
            Null means permanent.

    Returns:
        Dictionary containing the created request type (status: DRAFT) or error info.
    """
    logger.info(f"Creating v1 request type: {name!r}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload: dict[str, Any] = {
            "name": name,
            "ownerId": owner_id,
            "resourceSettings": resource_settings,
            "approvalSettings": approval_settings,
        }
        if request_settings is not None:
            payload["requestSettings"] = request_settings
        if description:
            payload["description"] = description
        if access_duration:
            payload["accessDuration"] = access_duration

        body, error = await _execute(client, "POST", "/governance/api/v1/request-types", payload)
        if error:
            logger.error(f"Okta API error creating request type {name!r}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully created request type: {name!r}")
        return body

    except Exception as e:
        logger.error(f"Exception creating request type {name!r}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def publish_request_type(ctx: Context, request_type_id: str) -> dict:
    """Publish a v1 request type, making it ACTIVE and visible to requesters.

    Request types are created in DRAFT status and must be published before
    users can submit requests against them.

    Parameters:
        request_type_id (str, required): The ID of the request type to publish.

    Returns:
        Dictionary with the result or error information.
    """
    logger.info(f"Publishing request type: {request_type_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "POST",
            f"/governance/api/v1/request-types/{request_type_id}/publish",
        )
        if error:
            logger.error(f"Okta API error publishing request type {request_type_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully published request type: {request_type_id}")
        return body or {"message": f"Request type {request_type_id} published successfully."}

    except Exception as e:
        logger.error(f"Exception publishing request type {request_type_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def unpublish_request_type(ctx: Context, request_type_id: str) -> dict:
    """Unpublish (deactivate) a v1 request type.

    Transitions an ACTIVE request type back to DISABLED status, preventing
    new requests from being submitted against it.

    Parameters:
        request_type_id (str, required): The ID of the request type to unpublish.

    Returns:
        Dictionary with the result or error information.
    """
    logger.info(f"Unpublishing request type: {request_type_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "POST",
            f"/governance/api/v1/request-types/{request_type_id}/un-publish",
        )
        if error:
            logger.error(f"Okta API error unpublishing request type {request_type_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully unpublished request type: {request_type_id}")
        return body or {"message": f"Request type {request_type_id} unpublished successfully."}

    except Exception as e:
        logger.error(f"Exception unpublishing request type {request_type_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_request_type(ctx: Context, request_type_id: str) -> dict:
    """Delete a v1 request type.

    Permanently removes a request type. Only DRAFT or DISABLED request types
    can be deleted.

    Parameters:
        request_type_id (str, required): The ID of the request type to delete.

    Returns:
        Dictionary with the result or error information.
    """
    logger.info(f"Deleting request type: {request_type_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "DELETE",
            f"/governance/api/v1/request-types/{request_type_id}",
        )
        if error:
            logger.error(f"Okta API error deleting request type {request_type_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted request type: {request_type_id}")
        return {"message": f"Request type {request_type_id} deleted successfully."}

    except Exception as e:
        logger.error(f"Exception deleting request type {request_type_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
