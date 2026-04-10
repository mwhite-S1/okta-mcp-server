# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Access certification tools: campaigns, reviews, security access reviews."""

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
    return response_body if response_body else None, None


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_certification_campaigns(
    ctx: Context,
    filter: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    order_by: Optional[str] = None,
) -> dict:
    """List access certification campaigns in the Okta organization.

    Access certification campaigns allow reviewers to periodically certify
    whether users should retain access to resources. Okta then applies
    decisions to grant or revoke access. Results are sorted by created date
    by default.

    Parameters:
        filter (str, optional): SCIM filter expression. Supported fields:
            - name: eq               (e.g. 'name eq "Sales Review"')
            - status: eq             (SCHEDULED, LAUNCHING, ACTIVE, COMPLETED, DELETED, ERROR)
            - scheduleType: eq       (ONE_OFF, RECURRING)
            - reviewerType: eq       (USER, REVIEWER_EXPRESSION, GROUP, RESOURCE_OWNER, MULTI_LEVEL)
            - startDate: gt/ge/lt/le (ISO 8601 datetime)
            - endDate: gt/ge/lt/le
            - recurringCampaignId: eq
            Multiple conditions: 'status eq "COMPLETED" OR status eq "SCHEDULED"'
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum records per page (1-200, default 20).
        order_by (str, optional): Sort order for results. Supported fields with
            asc/desc suffix: name, created, startDate, endDate, status.
            Example: "created desc" or "name asc". Default: "created asc".

    Returns:
        Dictionary with a "data" array of campaign objects and pagination links.
    """
    logger.info("Listing access certification campaigns")
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
        if order_by:
            params["orderBy"] = order_by

        path = "/governance/api/v1/campaigns"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing campaigns: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved certification campaigns")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing campaigns: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_certification_campaign(ctx: Context, campaign: dict) -> dict:
    """Create an access certification campaign.

    Campaigns allow reviewers to periodically certify whether users should
    retain their current access to resources. Okta applies reviewer decisions
    to grant or revoke access when the campaign ends.

    Parameters:
        campaign (dict, required): Campaign configuration. Required fields:

            name (str): Campaign name (1-255 chars).
            scheduleSettings (dict): When the campaign runs:
                - type (str): "ONE_OFF" or "RECURRING"
                - startDate (str): ISO 8601 datetime (e.g. "2025-06-01T00:00:00.000Z")
                - durationInDays (int): How many days the campaign is active (>= 1)
                - timeZone (str): IANA timezone (e.g. "America/New_York" or "UTC")
                - recurrence (dict, optional): Only for RECURRING; requires "interval"
                  (ISO 8601 duration e.g. "P3M") and optionally "repeatOnType" and "ends"
            resourceSettings (dict): Which resources to certify:
                - targetTypes (list): Resource types — "GROUP", "APPLICATION",
                  "OKTA_SERVICE_ACCOUNT", "APP_SERVICE_ACCOUNT", "COLLECTION"
                - targetResources (list): Specific resources to include. Each item:
                    {"resourceId": "<id>", "resourceType": "<GROUP|APPLICATION|...>"}
            principalScopeSettings (dict): Which users are in scope:
                - type (str): Must be "USERS"
                - userScopeExpression (str, optional): Okta EL expression to filter users
                - userIds (list, optional): Specific user IDs (max 100)
                - groupIds (list, optional): Specific group IDs (max 5)
                - includeOnlyActiveUsers (bool, optional): Only active users
            reviewerSettings (dict): Who reviews access:
                - type (str): "USER", "REVIEWER_EXPRESSION", "GROUP",
                  "RESOURCE_OWNER", or "MULTI_LEVEL"
                - reviewerId (str): Required when type is USER — Okta user ID
                - reviewerScopeExpression (str): Required when type is REVIEWER_EXPRESSION
                - reviewerGroupId (str): Required when type is GROUP
                - fallBackReviewerId (str): Required when type is REVIEWER_EXPRESSION
                  or RESOURCE_OWNER — Okta user ID used if reviewer can't be determined
                - selfReviewDisabled (bool, optional): Prevent self-review
                - justificationRequired (bool, optional): Require justification text
            remediationSettings (dict): What happens after review:
                - accessApproved (str): Action on approval — only "NO_ACTION"
                - accessRevoked (str): Action on revocation — "NO_ACTION" or "DENY"
                - noResponse (str): Action if reviewer doesn't respond — "NO_ACTION" or "DENY"

            Optional top-level fields:
            - campaignType (str): "RESOURCE" (default) or "USER"
            - description (str): Campaign description (max 1000 chars)
            - notificationSettings (dict): Email notification options
            - reportingSettings (dict): {"createReportingPackageEnabled": bool}

        Example (minimal RESOURCE campaign):
            {
                "name": "Q1 App Access Review",
                "campaignType": "RESOURCE",
                "scheduleSettings": {
                    "type": "ONE_OFF",
                    "startDate": "2025-07-01T00:00:00.000Z",
                    "durationInDays": 14,
                    "timeZone": "UTC"
                },
                "resourceSettings": {
                    "targetTypes": ["APPLICATION"],
                    "targetResources": [
                        {"resourceId": "0oaABC123", "resourceType": "APPLICATION"}
                    ]
                },
                "principalScopeSettings": {"type": "USERS"},
                "reviewerSettings": {
                    "type": "RESOURCE_OWNER",
                    "fallBackReviewerId": "00u1234567890"
                },
                "remediationSettings": {
                    "accessApproved": "NO_ACTION",
                    "accessRevoked": "DENY",
                    "noResponse": "NO_ACTION"
                }
            }

    Returns:
        Dictionary containing the created campaign (status: SCHEDULED) or error info.
    """
    logger.info("Creating access certification campaign")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", "/governance/api/v1/campaigns", campaign)
        if error:
            logger.error(f"Okta API error creating campaign: {error}")
            return {"error": str(error)}

        logger.info("Successfully created certification campaign")
        return body

    except Exception as e:
        logger.error(f"Exception creating campaign: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_certification_campaign(ctx: Context, campaign_id: str) -> dict:
    """Get an access certification campaign by ID.

    Parameters:
        campaign_id (str, required): The ID of the campaign to retrieve.

    Returns:
        Dictionary containing the campaign details or error information.
    """
    logger.info(f"Getting certification campaign: {campaign_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/governance/api/v1/campaigns/{campaign_id}")
        if error:
            logger.error(f"Okta API error getting campaign {campaign_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved campaign: {campaign_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting campaign {campaign_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_certification_campaign(ctx: Context, campaign_id: str) -> dict:
    """Delete an access certification campaign.

    Only campaigns with a status of SCHEDULED or ERROR can be deleted.
    Attempting to delete a campaign in any other state (ACTIVE, COMPLETED, etc.)
    returns a 409 Conflict. If the campaign has a RECURRING schedule, deleting
    it also cancels all future occurrences.

    Parameters:
        campaign_id (str, required): The ID of the campaign to delete.

    Returns:
        Dictionary containing the result or error information.
    """
    logger.warning(f"Deleting certification campaign: {campaign_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "DELETE", f"/governance/api/v1/campaigns/{campaign_id}")
        if error:
            logger.error(f"Okta API error deleting campaign {campaign_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted campaign: {campaign_id}")
        return {"message": f"Certification campaign {campaign_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception deleting campaign {campaign_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def launch_certification_campaign(ctx: Context, campaign_id: str) -> dict:
    """Launch an access certification campaign.

    Transitions the campaign from SCHEDULED or PENDING to ACTIVE state,
    generating reviewer assignments and notifying reviewers.

    Parameters:
        campaign_id (str, required): The ID of the campaign to launch.

    Returns:
        Dictionary containing the updated campaign or error information.
    """
    logger.info(f"Launching certification campaign: {campaign_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", f"/governance/api/v1/campaigns/{campaign_id}/launch")
        if error:
            logger.error(f"Okta API error launching campaign {campaign_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully launched campaign: {campaign_id}")
        return body or {"message": f"Certification campaign {campaign_id} launched"}

    except Exception as e:
        logger.error(f"Exception launching campaign {campaign_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def end_certification_campaign(
    ctx: Context,
    campaign_id: str,
    skip_remediation: Optional[bool] = None,
) -> dict:
    """End an active access certification campaign before its scheduled end date.

    Closes any open reviews and prevents further review activity. Reviews are
    remediated according to the campaign's remediationSettings unless
    skip_remediation is set to True. Only ACTIVE campaigns can be ended;
    campaigns in other states return 409 Conflict.

    Parameters:
        campaign_id (str, required): The ID of the active campaign to end.
        skip_remediation (bool, optional): If True, skips remediation for cases
            where remediationSettings.noResponse is DENY. Default: False.

    Returns:
        Dictionary containing the result or error information.
    """
    logger.info(f"Ending certification campaign: {campaign_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        payload: dict = {}
        if skip_remediation is not None:
            payload["skipRemediation"] = skip_remediation
        body, error = await _execute(client, "POST", f"/governance/api/v1/campaigns/{campaign_id}/end", payload or None)
        if error:
            logger.error(f"Okta API error ending campaign {campaign_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully ended campaign: {campaign_id}")
        return body or {"message": f"Certification campaign {campaign_id} ended"}

    except Exception as e:
        logger.error(f"Exception ending campaign {campaign_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_certification_reviews(
    ctx: Context,
    filter: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    order_by: Optional[str] = None,
) -> dict:
    """List access certification reviews in the Okta organization.

    Reviews are individual reviewer assignments within a campaign. Reviews only
    exist for campaigns with status ACTIVE or COMPLETED. Okta recommends always
    filtering by campaignId for performance — listing without a filter on orgs
    with many campaigns may time out.

    Parameters:
        filter (str, optional): SCIM filter expression using the eq operator.
            Supported filter fields:
            - campaignId         (e.g. 'campaignId eq "icitABC123"')
            - principalId        (the user whose access is under review)
            - reviewerId         (the user assigned to do the review)
            - decision           (UNREVIEWED, APPROVE, REVOKE)
            - resourceId         (group ID or app ID being reviewed)
            - reviewerType       (USER, GROUP, RESOURCE_OWNER)
            - reviewerLevel      (FIRST, SECOND — for multi-level campaigns)
            - entitlementValueId (filter by entitlement value)
            - entitlementBundleId (filter by entitlement bundle)
            Examples:
              'campaignId eq "icitABC123"'
              'decision eq "UNREVIEWED"'
              'reviewerId eq "00u123..."'
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum records per page (1-200, default 20).
        order_by (str, optional): Sort order. Supported fields with asc/desc suffix:
            decided, decision, remediationStatus, created.
            Default: "created asc".

    Returns:
        Dictionary with a "data" array of review objects and pagination links.
    """
    logger.info("Listing certification reviews")
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
        if order_by:
            params["orderBy"] = order_by

        path = "/governance/api/v1/reviews"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing reviews: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved certification reviews")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing reviews: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_certification_review(ctx: Context, review_id: str) -> dict:
    """Get a specific access certification review by ID.

    Parameters:
        review_id (str, required): The ID of the review to retrieve.

    Returns:
        Dictionary containing the review details or error information.
    """
    logger.info(f"Getting certification review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/governance/api/v1/reviews/{review_id}")
        if error:
            logger.error(f"Okta API error getting review {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved review: {review_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting review {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def reassign_certification_review(
    ctx: Context,
    campaign_id: str,
    review_ids: list,
    reviewer_id: str,
    note: str,
    reviewer_level: Optional[str] = None,
) -> dict:
    """Reassign one or more access certification reviews to a different reviewer.

    Only reviews belonging to ACTIVE campaigns with a decision of UNREVIEWED can
    be reassigned. When reassigned, the reviewerType changes to USER and the
    reassignment is appended to the review's history.

    Parameters:
        campaign_id (str, required): The ID of the campaign containing the reviews.
        review_ids (list, required): List of review IDs to reassign (1-50 items).
            Example: ["icrhdk4Lwhd2bBRQe0g2", "icrhew4DFTxygUUgE0g2"]
        reviewer_id (str, required): Okta user ID of the new reviewer.
        note (str, required): Justification for the reassignment (1-300 chars).
        reviewer_level (str, optional): Reviewer level to reassign at — only
            applicable for multi-level campaigns. Values: "FIRST" or "SECOND".

    Returns:
        Dictionary with a "data" array of the reassigned review objects.
    """
    logger.info(f"Reassigning {len(review_ids)} review(s) in campaign {campaign_id} to {reviewer_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        payload: dict = {"reviewerId": reviewer_id, "reviewIds": review_ids, "note": note}
        if reviewer_level:
            payload["reviewerLevel"] = reviewer_level
        body, error = await _execute(
            client, "POST",
            f"/governance/api/v1/campaigns/{campaign_id}/reviews/reassign",
            payload,
        )
        if error:
            logger.error(f"Okta API error reassigning reviews in campaign {campaign_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully reassigned reviews in campaign: {campaign_id}")
        return body or {"message": f"Reviews reassigned to {reviewer_id} in campaign {campaign_id}"}

    except Exception as e:
        logger.error(f"Exception reassigning reviews in campaign {campaign_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Security Access Reviews
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_security_access_reviews(
    ctx: Context,
    filter: Optional[str] = None,
    order_by: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List security access reviews in the Okta organization.

    Security access reviews are triggered following a security event and target
    a specific user's access. Reviewers assess whether the user should retain
    their current access.

    Parameters:
        filter (str, optional): SCIM filter expression. Supported operators:
            eq and co for string fields; gt and lt for date fields.
            Supported fields:
            - name eq/co          (e.g. 'name co "Git"')
            - status eq           (e.g. 'status eq "ACTIVE"')
            - reviewer.name eq/co (e.g. 'reviewer.name co "Smith"')
            Example: 'status eq "ACTIVE"'
        order_by (str, optional): Sort order. Field name optionally followed by
            "asc" or "desc". Example: "created desc".
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of reviews to return per page (1-200).

    Returns:
        Dictionary containing security access review objects and pagination info.
    """
    logger.info("Listing security access reviews")
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

        path = "/governance/api/v2/security-access-reviews"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing security access reviews: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved security access reviews")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing security access reviews: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_security_access_review(
    ctx: Context,
    principal_id: str,
    name: str,
    reviewer_user_ids: list,
    end_time: Optional[str] = None,
) -> dict:
    """Create a security access review for a specific user.

    Launches a targeted access review for a user following a security event.
    Assigned reviewers assess whether the user should retain their current access.

    Parameters:
        principal_id (str, required): The Okta user ID (20 chars) of the user
            whose access is under review.
        name (str, required): A descriptive name for this security access review
            (1-255 chars).
        reviewer_user_ids (list, required): List of Okta user IDs for the
            security analysts who will conduct the review (1-10 items).
        end_time (str, optional): ISO 8601 datetime when the review closes.
            Defaults to 7 days after creation. Must be at least 1 day and
            less than 6 months after creation.
            Example: "2025-07-15T00:00:00.000Z"

    Returns:
        Dictionary containing the created review or error information.
    """
    logger.info(f"Creating security access review for principal: {principal_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        payload = {
            "principalId": principal_id,
            "name": name,
            "reviewerSettings": {
                "type": "USER",
                "userSettings": {
                    "includedUserIds": reviewer_user_ids,
                },
            },
        }
        if end_time:
            payload["endTime"] = end_time
        body, error = await _execute(client, "POST", "/governance/api/v2/security-access-reviews", payload)
        if error:
            logger.error(f"Okta API error creating security access review: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully created security access review for: {principal_id}")
        return body

    except Exception as e:
        logger.error(f"Exception creating security access review: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_security_access_review_stats(ctx: Context) -> dict:
    """Get aggregate statistics for security access reviews.

    Returns counts of reviews by status (pending, active, completed, etc.)
    across the entire organization.

    Returns:
        Dictionary containing review statistics or error information.
    """
    logger.info("Getting security access review stats")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", "/governance/api/v2/security-access-reviews/stats")
        if error:
            logger.error(f"Okta API error getting SAR stats: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved security access review stats")
        return body

    except Exception as e:
        logger.error(f"Exception getting SAR stats: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_security_access_review(ctx: Context, review_id: str) -> dict:
    """Get a specific security access review by ID.

    Parameters:
        review_id (str, required): The ID of the security access review.

    Returns:
        Dictionary containing the review details or error information.
    """
    logger.info(f"Getting security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET", f"/governance/api/v2/security-access-reviews/{review_id}"
        )
        if error:
            logger.error(f"Okta API error getting SAR {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved security access review: {review_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting SAR {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_security_access_review(
    ctx: Context,
    review_id: str,
    end_time: Optional[str] = None,
    reviewer_settings: Optional[dict] = None,
) -> dict:
    """Update a security access review (PATCH).

    Updates the end time and/or reviewer settings of an existing security
    access review.

    Parameters:
        review_id (str, required): The ID of the security access review to update.
        end_time (str, optional): New ISO 8601 datetime when the review closes.
            Example: "2025-07-30T00:00:00.000Z"
        reviewer_settings (dict, optional): Updated reviewer settings. Structure:
            {
                "type": "USER",
                "userSettings": {
                    "includedUserIds": ["00u123...", "00u456..."]
                }
            }

    Returns:
        Dictionary containing the updated review or error information.
    """
    logger.info(f"Updating security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        payload: dict = {}
        if end_time is not None:
            payload["endTime"] = end_time
        if reviewer_settings is not None:
            payload["reviewerSettings"] = reviewer_settings
        body, error = await _execute(
            client, "PATCH",
            f"/governance/api/v2/security-access-reviews/{review_id}",
            payload,
        )
        if error:
            logger.error(f"Okta API error updating SAR {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated security access review: {review_id}")
        return body or {"message": f"Security access review {review_id} updated"}

    except Exception as e:
        logger.error(f"Exception updating SAR {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_security_access_review_summary(ctx: Context, review_id: str) -> dict:
    """Generate a summary for a completed security access review.

    Produces an aggregated summary of reviewer decisions for the specified
    security access review.

    Parameters:
        review_id (str, required): The ID of the security access review.

    Returns:
        Dictionary containing the summary or error information.
    """
    logger.info(f"Creating summary for security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/governance/api/v2/security-access-reviews/{review_id}/summary",
        )
        if error:
            logger.error(f"Okta API error creating SAR summary {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully created SAR summary: {review_id}")
        return body or {"message": f"Summary created for security access review {review_id}"}

    except Exception as e:
        logger.error(f"Exception creating SAR summary {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_security_access_review_actions(
    ctx: Context,
    review_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List the actions available or taken for a security access review.

    Actions represent the decisions reviewers can make (approve, revoke, etc.)
    for each resource in the security access review.

    Parameters:
        review_id (str, required): The ID of the security access review.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of actions to return.

    Returns:
        Dictionary containing action objects and pagination info.
    """
    logger.info(f"Listing actions for security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v2/security-access-reviews/{review_id}/actions"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing SAR actions {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved SAR actions: {review_id}")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing SAR actions {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def submit_security_access_review_action(
    ctx: Context,
    review_id: str,
    action_type: str,
) -> dict:
    """Submit a review-level action for a security access review.

    Records an admin action on the entire security access review (not a
    per-resource action). Use this to close the review or restore all access.

    Parameters:
        review_id (str, required): The ID of the security access review.
        action_type (str, required): The action to submit. One of:
            - "CLOSE_REVIEW": Close the security access review.
            - "RESTORE_ALL_ACCESS": Restore all access for the principal.

    Returns:
        Dictionary containing the result or error information.
    """
    logger.info(f"Submitting action '{action_type}' for security access review: {review_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/governance/api/v2/security-access-reviews/{review_id}/actions",
            {"actionType": action_type},
        )
        if error:
            logger.error(f"Okta API error submitting SAR action {review_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully submitted SAR action '{action_type}': {review_id}")
        return body or {"message": f"Action '{action_type}' submitted for security access review {review_id}"}

    except Exception as e:
        logger.error(f"Exception submitting SAR action {review_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
