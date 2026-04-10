# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Access requests tools: catalog, requests, conditions, sequences, settings."""

from typing import Any, Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils import messages


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
# Catalogs
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_access_catalog_entries(
    ctx: Context,
    filter: str,
    match: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List entries in the access request catalog.

    The catalog contains all requestable resources (apps, groups, entitlement
    bundles) that users can request access to through the access request workflow.

    The ``filter`` parameter is required and must use the ``parent`` property:

    - Top-level (parent) entries: ``not(parent pr)``
    - Children of a specific parent: ``parent eq "cen385AlcdqGaY8HE0g2"``

    Parameters:
        filter (str, required): SCIM filter expression using the ``parent`` property.
            Use ``not(parent pr)`` for top-level entries or
            ``parent eq "<parentId>"`` for child entries.
        match (str, optional): Fuzzy substring match against entry name/description
            (minimum 3 characters).
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of entries to return (1–200).

    Returns:
        Dictionary with ``data`` array of catalog entries and ``_links`` for pagination.
    """
    logger.info("Listing access catalog entries")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict[str, Any] = {"filter": filter}
        if match:
            params["match"] = match
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v2/catalogs/default/entries?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing catalog entries: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved access catalog entries")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing catalog entries: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_access_catalog_entry(ctx: Context, entry_id: str) -> dict:
    """Get a specific entry from the access request catalog.

    Parameters:
        entry_id (str, required): The ID of the catalog entry to retrieve.

    Returns:
        Dictionary containing the catalog entry details or error information.
    """
    logger.info(f"Getting access catalog entry: {entry_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET", f"/governance/api/v2/catalogs/default/entries/{entry_id}"
        )
        if error:
            logger.error(f"Okta API error getting catalog entry {entry_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved catalog entry: {entry_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting catalog entry {entry_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_catalog_entry_request_fields(
    ctx: Context,
    entry_id: str,
    user_id: str,
) -> dict:
    """Retrieve the request fields a user would see when submitting an access request.

    Evaluates the catalog entry's request conditions for the given requester and
    returns the fields from the highest-priority matching approval sequence.
    Also returns a risk assessment (``metadata.riskAssessment``) if the request
    could trigger separation-of-duty conflicts.

    Parameters:
        entry_id (str, required): The ID of the catalog entry.
        user_id (str, required): The Okta user ID of the requester.

    Returns:
        Dictionary with ``data`` array of request fields and optional ``metadata``
        containing a risk assessment.
    """
    logger.info(f"Getting request fields for entry {entry_id} and user {user_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "GET",
            f"/governance/api/v2/catalogs/default/entries/{entry_id}/users/{user_id}/request-fields",
        )
        if error:
            logger.error(f"Okta API error getting request fields for entry {entry_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved request fields for entry {entry_id}")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception getting request fields for entry {entry_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_user_catalog_entries(
    ctx: Context,
    user_id: str,
    filter: str,
    match: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List catalog entries available to a specific user.

    Returns the subset of the access catalog that a specific user is eligible
    to request, based on their profile and configured request policies.

    The ``filter`` parameter is required and must use the ``parent`` property:

    - Top-level (parent) entries: ``not(parent pr)``
    - Children of a specific parent: ``parent eq "cen385AlcdqGaY8HE0g2"``

    Parameters:
        user_id (str, required): The Okta user ID to list eligible catalog entries for.
        filter (str, required): SCIM filter expression using the ``parent`` property.
            Use ``not(parent pr)`` for top-level entries or
            ``parent eq "<parentId>"`` for child entries.
        match (str, optional): Fuzzy substring match against entry name/description
            (minimum 3 characters).
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of entries to return (1–200).

    Returns:
        Dictionary with ``data`` array of catalog entries and ``_links`` for pagination.
    """
    logger.info(f"Listing catalog entries for user: {user_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict[str, Any] = {"filter": filter}
        if match:
            params["match"] = match
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v2/catalogs/default/user/{user_id}/entries?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing catalog entries for user {user_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved catalog entries for user: {user_id}")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing catalog entries for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_access_requests(
    ctx: Context,
    filter: Optional[str] = None,
    order_by: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List access requests in the Okta organization.

    Access requests are submitted by users who want access to resources in the
    catalog. Requests flow through an approval workflow before access is granted.

    Parameters:
        filter (str, optional): Filter expression to narrow results. Supports
            various request properties. Query parameter percent encoding required.
            Examples:
              'requesterId eq "00u123..."'
              'status eq "PENDING"'
              'catalogEntryId eq "cen123..."'
        order_by (str, optional): Order results by a request property name
            followed by "asc" or "desc". Query parameter percent encoding required.
            Example: "created desc"
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of requests to return per page.

    Returns:
        Dictionary containing access request objects and pagination info.
    """
    logger.info("Listing access requests")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if filter:
            params["filter"] = filter
        if order_by:
            params["orderBy"] = order_by
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = "/governance/api/v2/requests"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing access requests: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved access requests")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing access requests: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_access_request(ctx: Context, request_id: str) -> dict:
    """Get a specific access request by ID.

    Parameters:
        request_id (str, required): The ID of the access request to retrieve.

    Returns:
        Dictionary containing the access request details or error information.
    """
    logger.info(f"Getting access request: {request_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET", f"/governance/api/v2/requests/{request_id}"
        )
        if error:
            logger.error(f"Okta API error getting access request {request_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved access request: {request_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting access request {request_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_access_request(
    ctx: Context,
    catalog_entry_id: str,
    requester_id: str,
    justification: Optional[str] = None,
) -> dict:
    """Submit a new access request for a catalog entry.

    Creates an access request that flows through the approval workflow
    defined by the resource's request condition.

    Parameters:
        catalog_entry_id (str, required): The catalog entry ID for the resource being requested.
        requester_id (str, required): The Okta user ID of the person requesting access.
        justification (str, optional): Business justification for the request.

    Returns:
        Dictionary containing the created access request or error information.
    """
    logger.info(f"Creating access request for entry {catalog_entry_id} by {requester_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload: dict[str, Any] = {
            "catalogEntryId": catalog_entry_id,
            "requesterId": requester_id,
        }
        if justification:
            payload["justification"] = justification

        body, error = await _execute(client, "POST", "/governance/api/v2/requests", payload)
        if error:
            logger.error(f"Okta API error creating access request: {error}")
            return {"error": str(error)}

        logger.info("Successfully created access request")
        return body

    except Exception as e:
        logger.error(f"Exception creating access request: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def cancel_access_request(ctx: Context, request_id: str) -> dict:
    """Cancel an in-flight access request.

    This action cancels an access request that is currently pending approval.
    Requires user confirmation before cancelling.

    Parameters:
        request_id (str, required): The ID of the access request to cancel.

    Returns:
        Dictionary with confirmation message or error information.
    """
    logger.info(f"Cancelling access request: {request_id}")

    outcome = await elicit_or_fallback(
        ctx,
        message=messages.CANCEL_ACCESS_REQUEST.format(request_id=request_id),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": messages.CANCEL_ACCESS_REQUEST.format(request_id=request_id),
            "request_id": request_id,
        },
    )

    if not outcome.used_elicitation:
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Access request cancellation cancelled for {request_id}")
        return {"message": f"Cancellation of access request {request_id} was cancelled."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "PATCH",
            f"/governance/api/v2/requests/{request_id}",
            {"status": "CANCELED"},
        )
        if error:
            logger.error(f"Okta API error cancelling access request {request_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully cancelled access request: {request_id}")
        return body or {"message": f"Access request {request_id} was cancelled successfully."}

    except Exception as e:
        logger.error(f"Exception cancelling access request {request_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def add_request_message(
    ctx: Context,
    request_id: str,
    message_body: str,
    sender_id: Optional[str] = None,
) -> dict:
    """Add a message to an access request.

    Used to communicate between requester and approvers during the request
    review process, or to add notes for audit purposes.

    Parameters:
        request_id (str, required): The ID of the access request.
        message_body (str, required): The message text to add to the request.
        sender_id (str, optional): The Okta user ID of the message sender.

    Returns:
        Dictionary containing the created message or error information.
    """
    logger.info(f"Adding message to access request: {request_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload: dict[str, Any] = {"body": message_body}
        if sender_id:
            payload["senderId"] = sender_id

        body, error = await _execute(
            client, "POST", f"/governance/api/v2/requests/{request_id}/messages", payload
        )
        if error:
            logger.error(f"Okta API error adding message to request {request_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully added message to request: {request_id}")
        return body or {"message": "Message added successfully."}

    except Exception as e:
        logger.error(f"Exception adding message to request {request_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Request Conditions  (resource-scoped)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_request_conditions(
    ctx: Context,
    resource_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List access request conditions for a specific resource.

    Request conditions define who can request access to a resource, what
    access levels are available, how long access is granted, and which
    approval sequence to use.

    Parameters:
        resource_id (str, required): The resource ID to list conditions for.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of conditions to return per page.

    Returns:
        Dictionary containing request condition objects and pagination info.
    """
    logger.info(f"Listing request conditions for resource: {resource_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v2/resources/{resource_id}/request-conditions"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing request conditions for resource {resource_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved request conditions for resource: {resource_id}")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing request conditions for resource {resource_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_request_condition(
    ctx: Context,
    resource_id: str,
    condition_id: str,
) -> dict:
    """Get a specific access request condition for a resource.

    Parameters:
        resource_id (str, required): The resource ID the condition belongs to.
        condition_id (str, required): The ID of the request condition to retrieve.

    Returns:
        Dictionary containing the request condition details or error information.
    """
    logger.info(f"Getting request condition {condition_id} for resource: {resource_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "GET",
            f"/governance/api/v2/resources/{resource_id}/request-conditions/{condition_id}",
        )
        if error:
            logger.error(f"Okta API error getting request condition {condition_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved request condition: {condition_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting request condition {condition_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_request_condition(
    ctx: Context,
    resource_id: str,
    condition_config: dict[str, Any],
) -> dict:
    """Create a new access request condition for a resource.

    Request conditions define auto-approval rules, escalation paths, and
    routing logic for access requests. Each condition must reference a request
    sequence that defines the approval steps.

    Parameters:
        resource_id (str, required): The resource ID. Accepts Okta instance ID
            (e.g. 0oa...) or ORN format.
        condition_config (dict, required): The condition configuration.
            Required fields:
              name (str, 1-255 chars): Unique display name for the condition.
              approvalSequenceId (str, 24 chars): ID of the approval sequence.
              requesterSettings (dict): Who may submit requests.
                type: "EVERYONE" | "GROUPS" | "TEAMS"
              accessScopeSettings (dict): What access level can be requested.
                type: "RESOURCE_DEFAULT" | "ENTITLEMENT_BUNDLES" | "GROUPS"
            Optional fields:
              description (str): Human-readable description (1-2000 chars).
              priority (int, >= 0): Lower number = higher priority. Default: lowest.
              accessDurationSettings (dict): Duration controls.
            Example:
              {
                "name": "App | Permanent | Everyone",
                "approvalSequenceId": "61eb0f06c462d20007f051ac",
                "requesterSettings": {"type": "EVERYONE"},
                "accessScopeSettings": {"type": "RESOURCE_DEFAULT"},
                "priority": 0
              }

    Returns:
        Dictionary containing the created condition (status starts as INACTIVE)
        or error information.
    """
    logger.info(f"Creating request condition for resource: {resource_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "POST",
            f"/governance/api/v2/resources/{resource_id}/request-conditions",
            condition_config,
        )
        if error:
            logger.error(f"Okta API error creating request condition for resource {resource_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully created request condition for resource: {resource_id}")
        return body

    except Exception as e:
        logger.error(f"Exception creating request condition for resource {resource_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_request_condition(
    ctx: Context,
    resource_id: str,
    condition_id: str,
    updates: dict[str, Any],
) -> dict:
    """Update an existing access request condition for a resource (PATCH).

    Conditions can be updated when status is ACTIVE, INACTIVE, or INVALID.
    A successful update always results in ACTIVE or INACTIVE status.
    Any requesterSettings or accessScopeSettings are validated against the
    resource's current request settings.

    Parameters:
        resource_id (str, required): The resource ID. Accepts instance ID or ORN.
        condition_id (str, required): The ID of the condition to update.
        updates (dict, required): Fields to update (all optional on patch):
            name (str): Unique display name (1-255 chars).
            description (str): Human-readable description.
            approvalSequenceId (str): ID of the approval sequence (24 chars).
            requesterSettings (dict):
              type: "EVERYONE" | "GROUPS" | "TEAMS"
            accessScopeSettings (dict):
              type: "RESOURCE_DEFAULT" | "ENTITLEMENT_BUNDLES" | "GROUPS"
            priority (int, >= 0): Lower number = higher priority.
            accessDurationSettings (dict or null).

    Returns:
        Dictionary containing the updated condition or error information.
    """
    logger.info(f"Updating request condition {condition_id} for resource: {resource_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "PATCH",
            f"/governance/api/v2/resources/{resource_id}/request-conditions/{condition_id}",
            updates,
        )
        if error:
            logger.error(f"Okta API error updating request condition {condition_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated request condition: {condition_id}")
        return body or {"message": f"Request condition {condition_id} updated successfully."}

    except Exception as e:
        logger.error(f"Exception updating request condition {condition_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_request_condition(
    ctx: Context,
    resource_id: str,
    condition_id: str,
) -> dict:
    """Delete an access request condition from a resource.

    Permanently removes the request condition. Requires user confirmation
    before deleting.

    Parameters:
        resource_id (str, required): The resource ID the condition belongs to.
        condition_id (str, required): The ID of the request condition to delete.

    Returns:
        Dictionary with confirmation message or error information.
    """
    logger.info(f"Deleting request condition {condition_id} from resource: {resource_id}")

    outcome = await elicit_or_fallback(
        ctx,
        message=messages.DELETE_REQUEST_CONDITION.format(
            condition_id=condition_id, resource_id=resource_id
        ),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": messages.DELETE_REQUEST_CONDITION.format(
                condition_id=condition_id, resource_id=resource_id
            ),
            "condition_id": condition_id,
            "resource_id": resource_id,
        },
    )

    if not outcome.used_elicitation:
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Request condition deletion cancelled for {condition_id}")
        return {"message": f"Deletion of request condition {condition_id} was cancelled."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, error = await _execute(
            client,
            "DELETE",
            f"/governance/api/v2/resources/{resource_id}/request-conditions/{condition_id}",
        )
        if error:
            logger.error(f"Okta API error deleting request condition {condition_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted request condition: {condition_id}")
        return {"message": f"Request condition {condition_id} deleted successfully."}

    except Exception as e:
        logger.error(f"Exception deleting request condition {condition_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def activate_request_condition(
    ctx: Context,
    resource_id: str,
    condition_id: str,
) -> dict:
    """Activate a request condition for a resource.

    Makes an inactive request condition active so that it can match access
    requests and route them through its approval sequence.

    Parameters:
        resource_id (str, required): The resource ID the condition belongs to.
        condition_id (str, required): The ID of the request condition to activate.

    Returns:
        Dictionary with the result or error information.
    """
    logger.info(f"Activating request condition {condition_id} for resource: {resource_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "POST",
            f"/governance/api/v2/resources/{resource_id}/request-conditions/{condition_id}/activate",
        )
        if error:
            logger.error(f"Okta API error activating request condition {condition_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully activated request condition: {condition_id}")
        return body or {"message": f"Request condition {condition_id} activated successfully."}

    except Exception as e:
        logger.error(f"Exception activating request condition {condition_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def deactivate_request_condition(
    ctx: Context,
    resource_id: str,
    condition_id: str,
) -> dict:
    """Deactivate a request condition for a resource.

    Makes an active request condition inactive. Deactivated conditions no longer
    match access requests until re-activated.

    Parameters:
        resource_id (str, required): The resource ID the condition belongs to.
        condition_id (str, required): The ID of the request condition to deactivate.

    Returns:
        Dictionary with the result or error information.
    """
    logger.info(f"Deactivating request condition {condition_id} for resource: {resource_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "POST",
            f"/governance/api/v2/resources/{resource_id}/request-conditions/{condition_id}/deactivate",
        )
        if error:
            logger.error(f"Okta API error deactivating request condition {condition_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deactivated request condition: {condition_id}")
        return body or {"message": f"Request condition {condition_id} deactivated successfully."}

    except Exception as e:
        logger.error(f"Exception deactivating request condition {condition_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Request Sequences  (resource-scoped)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_request_sequences(
    ctx: Context,
    resource_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List request sequences available for a resource.

    Request sequences define the series of approval steps (questions, approval
    tasks, custom tasks) that must be completed for a requester to gain access.
    Sequences are created in the Okta Access Requests app and referenced by
    request conditions.

    Parameters:
        resource_id (str, required): The resource ID to list sequences for.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of sequences to return per page.

    Returns:
        Dictionary containing request sequence objects and pagination info.
    """
    logger.info(f"Listing request sequences for resource: {resource_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v2/resources/{resource_id}/request-sequences"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing request sequences for resource {resource_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved request sequences for resource: {resource_id}")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing request sequences for resource {resource_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_request_sequence(
    ctx: Context,
    resource_id: str,
    sequence_id: str,
) -> dict:
    """Get a specific request sequence for a resource.

    Parameters:
        resource_id (str, required): The resource ID the sequence is associated with.
        sequence_id (str, required): The ID of the request sequence to retrieve.

    Returns:
        Dictionary containing the request sequence details or error information.
    """
    logger.info(f"Getting request sequence {sequence_id} for resource: {resource_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "GET",
            f"/governance/api/v2/resources/{resource_id}/request-sequences/{sequence_id}",
        )
        if error:
            logger.error(f"Okta API error getting request sequence {sequence_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved request sequence: {sequence_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting request sequence {sequence_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_request_sequence(ctx: Context, sequence_id: str) -> dict:
    """Delete a request sequence.

    Permanently removes a request sequence. The sequence must not be referenced
    by any active request conditions before it can be deleted.

    Parameters:
        sequence_id (str, required): The ID of the request sequence to delete.

    Returns:
        Dictionary with confirmation message or error information.
    """
    logger.info(f"Deleting request sequence: {sequence_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, error = await _execute(
            client, "DELETE", f"/governance/api/v2/request-sequences/{sequence_id}"
        )
        if error:
            logger.error(f"Okta API error deleting request sequence {sequence_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted request sequence: {sequence_id}")
        return {"message": f"Request sequence {sequence_id} deleted successfully."}

    except Exception as e:
        logger.error(f"Exception deleting request sequence {sequence_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Request Settings  (org-level and resource-level)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_request_settings(ctx: Context) -> dict:
    """Get the access request settings for the Okta organization.

    Returns the org-level configuration for access requests, including
    approval workflows, escalation settings, and notification preferences.

    Returns:
        Dictionary containing the access request settings or error information.
    """
    logger.info("Getting org-level access request settings")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", "/governance/api/v2/request-settings")
        if error:
            logger.error(f"Okta API error getting request settings: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved org-level request settings")
        return body

    except Exception as e:
        logger.error(f"Exception getting request settings: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_request_settings(ctx: Context, settings: dict[str, Any]) -> dict:
    """Update the access request settings for the Okta organization.

    Modifies org-level configuration for access requests such as approval
    timeouts, escalation settings, and notification preferences.

    Parameters:
        settings (dict, required): Settings fields to update. Common fields:
            - ``approvalTimeout`` (int): Days before a pending request expires.
            - ``escalationEnabled`` (bool): Whether escalation is enabled.

    Returns:
        Dictionary containing the updated settings or error information.
    """
    logger.info("Updating org-level access request settings")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "PATCH", "/governance/api/v2/request-settings", settings
        )
        if error:
            logger.error(f"Okta API error updating request settings: {error}")
            return {"error": str(error)}

        logger.info("Successfully updated org-level request settings")
        return body or {"message": "Access request settings updated successfully."}

    except Exception as e:
        logger.error(f"Exception updating request settings: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_resource_request_settings(ctx: Context, resource_id: str) -> dict:
    """Get access request settings for a specific resource.

    Resource-level settings may override org-level defaults and indicate
    whether creating a request condition is valid for this resource.

    Parameters:
        resource_id (str, required): The resource ID to retrieve settings for.

    Returns:
        Dictionary containing the resource request settings or error information.
    """
    logger.info(f"Getting request settings for resource: {resource_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET", f"/governance/api/v2/resources/{resource_id}/request-settings"
        )
        if error:
            logger.error(f"Okta API error getting request settings for resource {resource_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved request settings for resource: {resource_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting request settings for resource {resource_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_resource_request_settings(
    ctx: Context,
    resource_id: str,
    settings: dict[str, Any],
) -> dict:
    """Update access request settings for a specific resource.

    Modifies resource-level configuration that controls how access requests
    behave for this resource, potentially overriding org-level defaults.

    Parameters:
        resource_id (str, required): The resource ID to update settings for.
        settings (dict, required): Settings fields to update.

    Returns:
        Dictionary containing the updated settings or error information.
    """
    logger.info(f"Updating request settings for resource: {resource_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client,
            "PATCH",
            f"/governance/api/v2/resources/{resource_id}/request-settings",
            settings,
        )
        if error:
            logger.error(f"Okta API error updating request settings for resource {resource_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated request settings for resource: {resource_id}")
        return body or {"message": f"Request settings for resource {resource_id} updated successfully."}

    except Exception as e:
        logger.error(f"Exception updating request settings for resource {resource_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
