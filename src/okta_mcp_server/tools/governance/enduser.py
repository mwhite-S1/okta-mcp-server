# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""End-user governance tools: my catalog, my requests, my security access reviews, my settings.

These tools operate in the context of the authenticated user (the "me" perspective),
as opposed to the admin tools which operate on behalf of any user.
"""

import json as _json
from typing import Optional
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
    if not response_body:
        return None, None
    if isinstance(response_body, str):
        try:
            response_body = _json.loads(response_body)
        except Exception:
            pass
    return response_body, None


# ---------------------------------------------------------------------------
# My Catalogs
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_my_catalog_entries(
    ctx: Context,
    filter: str,
    match: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List access catalog entries available to the current authenticated user.

    Returns the subset of the access catalog that the current user is eligible
    to request, based on their profile and configured request policies.

    Parameters:
        filter (str, required): SCIM filter expression using the ``parent`` property.
            - Top-level entries: ``not(parent pr)``
            - Children of a specific parent: ``parent eq "<parentId>"``
        match (str, optional): Fuzzy substring match against entry name or
            description (minimum 3 characters).
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of entries to return (1-200).

    Returns:
        Dictionary with ``data`` array of catalog entries and ``_links`` for pagination.
    """
    logger.info("Listing my catalog entries")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {"filter": filter}
        if match:
            params["match"] = match
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v2/my/catalogs/default/entries?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing my catalog entries: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved my catalog entries")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing my catalog entries: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_my_catalog_entry(ctx: Context, entry_id: str) -> dict:
    """Get a specific catalog entry available to the current user.

    Parameters:
        entry_id (str, required): The ID of the catalog entry to retrieve.

    Returns:
        Dictionary containing the catalog entry details or error information.
    """
    logger.info(f"Getting my catalog entry: {entry_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET", f"/governance/api/v2/my/catalogs/default/entries/{entry_id}"
        )
        if error:
            logger.error(f"Okta API error getting my catalog entry {entry_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved my catalog entry: {entry_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting my catalog entry {entry_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_my_catalog_entry_request_fields(ctx: Context, entry_id: str) -> dict:
    """Get the request fields the current user would see when submitting an access request.

    Evaluates the catalog entry's request conditions for the current user and
    returns the fields from the highest-priority matching approval sequence.
    Also returns a risk assessment if the request could trigger SOD conflicts.

    Parameters:
        entry_id (str, required): The ID of the catalog entry.

    Returns:
        Dictionary with ``data`` array of request fields and optional ``metadata``
        containing a risk assessment.
    """
    logger.info(f"Getting my request fields for catalog entry: {entry_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET",
            f"/governance/api/v2/my/catalogs/default/entries/{entry_id}/request-fields",
        )
        if error:
            logger.error(f"Okta API error getting my request fields for entry {entry_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved my request fields for entry: {entry_id}")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception getting my request fields for entry {entry_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_my_catalog_entry_users(
    ctx: Context,
    entry_id: str,
    filter: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List users associated with a catalog entry (for requesting on behalf of).

    Returns the users that the current user can request access for when
    using a catalog entry.

    Parameters:
        entry_id (str, required): The ID of the catalog entry.
        filter (str, required): SCIM filter expression to narrow results.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of users to return.

    Returns:
        Dictionary containing a list of user objects and pagination info.
    """
    logger.info(f"Listing users for my catalog entry: {entry_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {"filter": filter}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v2/my/catalogs/default/entries/{entry_id}/users?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing users for entry {entry_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved users for entry: {entry_id}")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing users for entry {entry_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_my_catalog_entry_user_request_fields(
    ctx: Context,
    entry_id: str,
    user_id: str,
) -> dict:
    """Get the request fields for a specific user on a catalog entry.

    Returns the fields the current user would fill out when requesting access
    on behalf of a specific target user.

    Parameters:
        entry_id (str, required): The ID of the catalog entry.
        user_id (str, required): The Okta user ID of the target user.

    Returns:
        Dictionary with ``data`` array of request fields and optional ``metadata``.
    """
    logger.info(f"Getting request fields for user {user_id} on my catalog entry: {entry_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET",
            f"/governance/api/v2/my/catalogs/default/entries/{entry_id}/users/{user_id}/request-fields",
        )
        if error:
            logger.error(f"Okta API error getting request fields for user {user_id} on entry {entry_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved request fields for user {user_id} on entry: {entry_id}")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception getting request fields for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# My Requests
# ---------------------------------------------------------------------------

@mcp.tool()
async def create_my_access_request(
    ctx: Context,
    entry_id: str,
    requester_field_values: Optional[list] = None,
) -> dict:
    """Submit an access request for a catalog entry as the current user.

    Creates an access request for the current authenticated user for the
    specified catalog entry. The request flows through the approval workflow
    defined by the resource's request condition.

    Parameters:
        entry_id (str, required): The catalog entry ID for the resource to request.
        requester_field_values (list, optional): Required input fields for the
            approval sequence. Each item should match the field definitions returned
            by ``get_my_catalog_entry_request_fields``. Fields are determined by
            the approval system. Structure:
            [
                {"id": "<fieldId>", "value": "<user_provided_value>"}
            ]

    Returns:
        Dictionary containing the created access request or error information.
    """
    logger.info(f"Creating my access request for entry: {entry_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload: dict = {}
        if requester_field_values is not None:
            payload["requesterFieldValues"] = requester_field_values

        body, error = await _execute(
            client, "POST",
            f"/governance/api/v2/my/catalogs/default/entries/{entry_id}/requests",
            payload or None,
        )
        if error:
            logger.error(f"Okta API error creating my access request for entry {entry_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully created my access request for entry: {entry_id}")
        return body

    except Exception as e:
        logger.error(f"Exception creating my access request for entry {entry_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_my_access_request(ctx: Context, entry_id: str, request_id: str) -> dict:
    """Get a specific access request submitted by the current user.

    Parameters:
        entry_id (str, required): The catalog entry ID the request was for.
        request_id (str, required): The ID of the access request to retrieve.

    Returns:
        Dictionary containing the access request details or error information.
    """
    logger.info(f"Getting my access request {request_id} for entry: {entry_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET",
            f"/governance/api/v2/my/catalogs/default/entries/{entry_id}/requests/{request_id}",
        )
        if error:
            logger.error(f"Okta API error getting my access request {request_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved my access request: {request_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting my access request {request_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# My Security Access Reviews
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_my_security_access_reviews(
    ctx: Context,
    filter: Optional[str] = None,
    order_by: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List security access reviews assigned to the current user as reviewer.

    Returns SAR reviews where the current authenticated user is a designated
    reviewer.

    Parameters:
        filter (str, optional): SCIM filter expression. Supports eq and co for
            string fields; gt and lt for date fields.
            Example: 'status eq "ACTIVE"'
        order_by (str, optional): Sort order. Field name optionally followed by
            "asc" or "desc". Example: "created desc".
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of reviews to return (1-200).

    Returns:
        Dictionary containing security access review objects and pagination info.
    """
    logger.info("Listing my security access reviews")
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

        path = "/governance/api/v2/my/security-access-reviews"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing my security access reviews: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved my security access reviews")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing my security access reviews: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_my_security_access_review_stats(ctx: Context) -> dict:
    """Get aggregate statistics for security access reviews assigned to the current user.

    Returns counts of reviews by status (pending, active, completed, etc.)
    for the reviews where the current user is a reviewer.

    Returns:
        Dictionary containing review statistics or error information.
    """
    logger.info("Getting my security access review stats")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET", "/governance/api/v2/my/security-access-reviews/stats"
        )
        if error:
            logger.error(f"Okta API error getting my SAR stats: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved my security access review stats")
        return body

    except Exception as e:
        logger.error(f"Exception getting my SAR stats: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_my_security_access_review(ctx: Context, review_id: str) -> dict:
    """Get a specific security access review assigned to the current user.

    Parameters:
        review_id (str, required): The ID of the security access review.

    Returns:
        Dictionary containing the review details or error information.
    """
    logger.info(f"Getting my security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET",
            f"/governance/api/v2/my/security-access-reviews/{review_id}",
        )
        if error:
            logger.error(f"Okta API error getting my SAR {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved my security access review: {review_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting my SAR {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_my_security_access_review_accesses(
    ctx: Context,
    review_id: str,
    filter: Optional[str] = None,
    order_by: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List access items for a security access review assigned to the current user.

    Returns the individual access items (resources, entitlements) that are
    part of the specified security access review for the reviewer to evaluate.

    Parameters:
        review_id (str, required): The ID of the security access review.
        filter (str, optional): SCIM filter expression to narrow results.
        order_by (str, optional): Sort order. Example: "created desc".
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of accesses to return (1-200).

    Returns:
        Dictionary containing access item objects and pagination info.
    """
    logger.info(f"Listing accesses for my security access review: {review_id}")
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

        path = f"/governance/api/v2/my/security-access-reviews/{review_id}/accesses"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing accesses for my SAR {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved accesses for my SAR: {review_id}")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing accesses for my SAR {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_my_security_access_review_sub_accesses(
    ctx: Context,
    review_id: str,
    access_id: str,
    filter: Optional[str] = None,
    order_by: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List sub-accesses for a specific access item in a security access review.

    Returns granular entitlement-level access details within a specific
    resource access item in a security access review.

    Parameters:
        review_id (str, required): The ID of the security access review.
        access_id (str, required): The ID of the access item.
        filter (str, optional): SCIM filter expression to narrow results.
        order_by (str, optional): Sort order. Example: "created desc".
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of sub-accesses to return (1-200).

    Returns:
        Dictionary containing sub-access objects and pagination info.
    """
    logger.info(f"Listing sub-accesses for access {access_id} in my SAR: {review_id}")
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

        path = f"/governance/api/v2/my/security-access-reviews/{review_id}/accesses/{access_id}/sub-accesses"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing sub-accesses for access {access_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved sub-accesses for access: {access_id}")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing sub-accesses for access {access_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def submit_my_security_access_review_access_action(
    ctx: Context,
    review_id: str,
    target_id: str,
    action_type: str,
) -> dict:
    """Submit a reviewer decision for a specific access item in a security access review.

    Records the reviewer's decision for a resource or entitlement in the
    security access review. Use this to approve, revoke, or flag access.

    Parameters:
        review_id (str, required): The ID of the security access review.
        target_id (str, required): The ID of the access target to act on.
        action_type (str, required): The reviewer decision. One of:
            - "REVOKE_ACCESS": Revoke the user's access to this resource.
            - "RESTORE_ACCESS": Restore/approve the user's access.
            - "FLAG_FOR_MANUAL_REMEDIATION": Mark for manual access revocation.
            - "FLAG_FOR_MANUAL_RESTORATION": Mark for manual access restoration.

    Returns:
        Dictionary containing the result or error information.
    """
    logger.info(f"Submitting access action '{action_type}' for target {target_id} in SAR: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/governance/api/v2/my/security-access-reviews/{review_id}/accesses/{target_id}/actions",
            {"type": action_type},
        )
        if error:
            logger.error(f"Okta API error submitting access action for target {target_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully submitted access action '{action_type}' for target: {target_id}")
        return body or {"message": f"Action '{action_type}' submitted for target {target_id}"}

    except Exception as e:
        logger.error(f"Exception submitting access action for target {target_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_my_security_access_review_access_anomalies(
    ctx: Context,
    review_id: str,
    target_id: str,
) -> dict:
    """Get anomalies detected for a specific access item in a security access review.

    Returns risk signals and anomaly information for the principal's access
    to a specific resource, helping reviewers make informed decisions.

    Parameters:
        review_id (str, required): The ID of the security access review.
        target_id (str, required): The ID of the access target.

    Returns:
        Dictionary containing anomaly objects or error information.
    """
    logger.info(f"Getting anomalies for target {target_id} in my SAR: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET",
            f"/governance/api/v2/my/security-access-reviews/{review_id}/accesses/{target_id}/anomalies",
        )
        if error:
            logger.error(f"Okta API error getting anomalies for target {target_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved anomalies for target: {target_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting anomalies for target {target_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_my_security_access_review_access_summary(
    ctx: Context,
    review_id: str,
    target_id: str,
) -> dict:
    """Generate a summary for a specific access item in a security access review.

    Produces an aggregated summary for the reviewer's decisions on a specific
    resource target within the security access review.

    Parameters:
        review_id (str, required): The ID of the security access review.
        target_id (str, required): The ID of the access target.

    Returns:
        Dictionary containing the summary or error information.
    """
    logger.info(f"Creating access summary for target {target_id} in my SAR: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/governance/api/v2/my/security-access-reviews/{review_id}/accesses/{target_id}/summary",
        )
        if error:
            logger.error(f"Okta API error creating access summary for target {target_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully created access summary for target: {target_id}")
        return body or {"message": f"Access summary created for target {target_id}"}

    except Exception as e:
        logger.error(f"Exception creating access summary for target {target_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_my_security_access_review_actions(
    ctx: Context,
    review_id: str,
) -> dict:
    """List the actions available for a security access review assigned to the current user.

    Returns the review-level actions the reviewer can take (e.g. close review,
    restore all access).

    Parameters:
        review_id (str, required): The ID of the security access review.

    Returns:
        Dictionary containing available action objects or error information.
    """
    logger.info(f"Listing actions for my security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET",
            f"/governance/api/v2/my/security-access-reviews/{review_id}/actions",
        )
        if error:
            logger.error(f"Okta API error listing actions for my SAR {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved actions for my SAR: {review_id}")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing actions for my SAR {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def submit_my_security_access_review_action(
    ctx: Context,
    review_id: str,
    action_type: str,
) -> dict:
    """Submit a review-level action for a security access review assigned to the current user.

    Records a reviewer action on the entire security access review (not a
    per-resource action). Use this to close the review or restore all access.

    Parameters:
        review_id (str, required): The ID of the security access review.
        action_type (str, required): The action to submit. One of:
            - "CLOSE_REVIEW": Close the security access review.
            - "RESTORE_ALL_ACCESS": Restore all access for the principal.

    Returns:
        Dictionary containing the result or error information.
    """
    logger.info(f"Submitting action '{action_type}' for my security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/governance/api/v2/my/security-access-reviews/{review_id}/actions",
            {"actionType": action_type},
        )
        if error:
            logger.error(f"Okta API error submitting action for my SAR {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully submitted action '{action_type}' for my SAR: {review_id}")
        return body or {"message": f"Action '{action_type}' submitted for review {review_id}"}

    except Exception as e:
        logger.error(f"Exception submitting action for my SAR {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def add_my_security_access_review_comment(
    ctx: Context,
    review_id: str,
    comment: str,
) -> dict:
    """Add a comment to a security access review assigned to the current user.

    Allows the reviewer to add notes or context to the security access review
    for audit and communication purposes.

    Parameters:
        review_id (str, required): The ID of the security access review.
        comment (str, required): The comment text to add (1-1000 chars).

    Returns:
        Dictionary containing the result or error information.
    """
    logger.info(f"Adding comment to my security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/governance/api/v2/my/security-access-reviews/{review_id}/comment",
            {"comment": comment},
        )
        if error:
            logger.error(f"Okta API error adding comment to my SAR {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully added comment to my SAR: {review_id}")
        return body or {"message": "Comment added successfully"}

    except Exception as e:
        logger.error(f"Exception adding comment to my SAR {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_my_security_access_review_history(
    ctx: Context,
    review_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """Get the history of actions and events for a security access review assigned to the current user.

    Returns a chronological log of reviewer actions, status changes, and
    other events for the specified security access review.

    Parameters:
        review_id (str, required): The ID of the security access review.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of history entries to return.

    Returns:
        Dictionary containing history objects and pagination info.
    """
    logger.info(f"Getting history for my security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v2/my/security-access-reviews/{review_id}/history"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error getting history for my SAR {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved history for my SAR: {review_id}")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception getting history for my SAR {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_my_security_access_review_principal(ctx: Context, review_id: str) -> dict:
    """Get the principal (target user) details for a security access review assigned to the current user.

    Returns information about the user whose access is under review in the
    specified security access review.

    Parameters:
        review_id (str, required): The ID of the security access review.

    Returns:
        Dictionary containing the principal details or error information.
    """
    logger.info(f"Getting principal for my security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET",
            f"/governance/api/v2/my/security-access-reviews/{review_id}/principal",
        )
        if error:
            logger.error(f"Okta API error getting principal for my SAR {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved principal for my SAR: {review_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting principal for my SAR {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_my_security_access_review_summary(ctx: Context, review_id: str) -> dict:
    """Generate a summary for a security access review assigned to the current user.

    Produces an aggregated summary of all reviewer decisions for the specified
    security access review.

    Parameters:
        review_id (str, required): The ID of the security access review.

    Returns:
        Dictionary containing the summary or error information.
    """
    logger.info(f"Creating summary for my security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/governance/api/v2/my/security-access-reviews/{review_id}/summary",
        )
        if error:
            logger.error(f"Okta API error creating summary for my SAR {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully created summary for my SAR: {review_id}")
        return body or {"message": f"Summary created for security access review {review_id}"}

    except Exception as e:
        logger.error(f"Exception creating summary for my SAR {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# My Access Certification Reviews
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_my_agent_managed_connections(
    ctx: Context,
    campaign_id: str,
    review_id: str,
    agent_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """Get agent-managed connections for a certification review assigned to the current user.

    Returns the agent-managed resource connections associated with a specific
    access certification review, used for agent-based remediation workflows.

    Parameters:
        campaign_id (str, required): The ID of the certification campaign.
        review_id (str, required): The ID of the review within the campaign.
        agent_id (str, required): The ID of the agent managing the connections.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of connections to return.

    Returns:
        Dictionary containing agent-managed connection objects and pagination info.
    """
    logger.info(f"Getting agent-managed connections for review {review_id} in campaign {campaign_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v1/my/campaigns/{campaign_id}/reviews/{review_id}/agent-managed-connections/{agent_id}"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error getting agent-managed connections: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved agent-managed connections")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception getting agent-managed connections: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# My Settings
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_my_governance_settings(ctx: Context) -> dict:
    """Get the governance settings for the current authenticated user.

    Returns the current user's governance configuration, including delegate
    appointments for governance reviews.

    Returns:
        Dictionary containing the user's governance settings or error information.
    """
    logger.info("Getting my governance settings")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", "/governance/api/v1/my/settings")
        if error:
            logger.error(f"Okta API error getting my governance settings: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved my governance settings")
        return body

    except Exception as e:
        logger.error(f"Exception getting my governance settings: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_my_governance_settings(
    ctx: Context,
    delegates: Optional[dict] = None,
) -> dict:
    """Update the governance settings for the current authenticated user.

    Allows end users to manage their own delegate appointments for governance
    reviews such as access certification campaigns.

    Parameters:
        delegates (dict, optional): Delegate configuration. Structure:
            {
                "appointments": [
                    {
                        "delegateId": "<user_id>",
                        "startDate": "2025-07-01T00:00:00.000Z",
                        "endDate": "2025-08-01T00:00:00.000Z"
                    }
                ]
            }
            Maximum 1 appointment. Set ``appointments`` to an empty list or
            null to remove all delegates.

    Returns:
        Dictionary containing the updated settings or error information.
    """
    logger.info("Updating my governance settings")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload: dict = {}
        if delegates is not None:
            payload["delegates"] = delegates

        body, error = await _execute(client, "PATCH", "/governance/api/v1/my/settings", payload)
        if error:
            logger.error(f"Okta API error updating my governance settings: {error}")
            return {"error": str(error)}

        logger.info("Successfully updated my governance settings")
        return body or {"message": "My governance settings updated successfully"}

    except Exception as e:
        logger.error(f"Exception updating my governance settings: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_my_delegate_users(
    ctx: Context,
    filter: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List users available to be appointed as governance delegates for the current user.

    Returns the list of users that the current user can appoint as a delegate
    for governance tasks such as access certification reviews.

    Parameters:
        filter (str, optional): Filter expression. Supports ``sw`` operator on
            ``firstName`` or ``lastName``. When omitted, returns all eligible users.
            Example: 'firstName sw "John"'
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of users to return (1-200).

    Returns:
        Dictionary containing user objects and pagination info.
    """
    logger.info("Listing my delegate users")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if filter:
            params["filter"] = filter
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = "/governance/api/v1/my/settings/delegate/users"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing my delegate users: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved my delegate users")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing my delegate users: {type(e).__name__}: {e}")
        return {"error": str(e)}
