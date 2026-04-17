# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Governance delegates tools: org settings, delegate listings, principal settings."""

import json as _json
from typing import Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client


async def _execute(client, method: str, path: str, body: dict = None, keep_empty_params: bool = False):
    """Make a direct API call via the SDK request executor."""
    request_executor = client.get_request_executor()
    url = f"{client.get_base_url()}{path}"
    request, error = await request_executor.create_request(method, url, body or {}, keep_empty_params=keep_empty_params)
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


@mcp.tool()
async def get_governance_delegate_settings(ctx: Context) -> dict:
    """Get the org-level governance delegate settings.

    Returns the org-wide configuration for governance delegation, including
    whether end users can appoint delegates and any restrictions on delegate types.

    Returns:
        Dictionary containing the org delegate settings or error information.
    """
    logger.info("Getting governance delegate settings")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", "/governance/api/v1/settings")
        if error:
            logger.error(f"Okta API error getting delegate settings: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved delegate settings")
        return body

    except Exception as e:
        logger.error(f"Exception getting delegate settings: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_governance_delegates(
    ctx: Context,
    principal_id: Optional[str] = None,
    delegate_id: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List governance delegate appointments in the Okta organization.

    Delegates act on behalf of principals during access certification reviews
    and access request approvals.

    Parameters:
        principal_id (str, optional): Filter delegates appointed by a specific user.
        delegate_id (str, optional): Filter appointments for a specific delegate user.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of delegate records to return.

    Returns:
        Dictionary containing delegate appointment objects and pagination info.
    """
    logger.info("Listing governance delegates")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if principal_id:
            params["principalId"] = principal_id
        if delegate_id:
            params["delegateId"] = delegate_id
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = "/governance/api/v1/delegates"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing delegates: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved governance delegates")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing delegates: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_principal_governance_settings(ctx: Context, principal_id: str) -> dict:
    """Get the governance settings for a specific user (principal).

    Returns the delegate appointments currently configured for the specified user,
    including who is authorized to act on their behalf during certification reviews
    and access requests.

    Parameters:
        principal_id (str, required): The Okta user ID to retrieve settings for.

    Returns:
        Dictionary containing the principal's governance settings or error information.
    """
    logger.info(f"Getting governance settings for principal: {principal_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        # Okta's governance API does not support GET on /principal-settings/{id}.
        # The admin-readable equivalent is the delegates endpoint filtered by principalId.
        path = f"/governance/api/v1/delegates?{urlencode({'principalId': principal_id})}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error getting settings for {principal_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved governance settings for: {principal_id}")
        return body or {"delegateAppointments": []}

    except Exception as e:
        logger.error(f"Exception getting settings for {principal_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_principal_governance_settings(
    ctx: Context,
    principal_id: str,
    delegate_appointments: list,
) -> dict:
    """Update the governance delegate settings for a specific user (principal).

    Assigns delegates who can act on behalf of the specified user during access
    certification reviews and access request approvals. Pass an empty list to
    remove all delegate appointments.

    Parameters:
        principal_id (str, required): The Okta user ID to update settings for.
        delegate_appointments (list, required): List of delegate appointment objects.
            Each appointment must include:
              - delegate (dict, required): The delegate identity object:
                  - type (str): Must be "OKTA_USER"
                  - externalId (str): Okta user ID of the delegate
              - note (str, optional): A description of the delegation
              - startTime (str, optional): ISO 8601 start time
              - endTime (str, optional): ISO 8601 end time

    Example (add delegate):
        delegate_appointments=[
            {
                "delegate": {"type": "OKTA_USER", "externalId": "00u1234567890abcdef"},
                "note": "Covering during leave",
                "endTime": "2026-12-31T00:00:00.000Z"
            }
        ]

    Example (clear all delegates):
        delegate_appointments=[]

    Returns:
        Dictionary containing the updated settings or error information.
    """
    logger.info(f"Updating governance settings for principal: {principal_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        payload = {"delegates": {"appointments": delegate_appointments}}
        body, error = await _execute(
            client, "PATCH", f"/governance/api/v1/principal-settings/{principal_id}", payload,
            keep_empty_params=True
        )
        if error:
            logger.error(f"Okta API error updating settings for {principal_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated governance settings for: {principal_id}")
        return body or {"message": f"Governance settings updated for principal {principal_id}"}

    except Exception as e:
        logger.error(f"Exception updating settings for {principal_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
