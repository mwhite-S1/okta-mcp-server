# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Governance risk rules tools: list, create, get, update, delete, assess.

Risk rules define separation-of-duties (SOD) constraints used in Access
Certifications and Access Requests to detect and surface conflicts when a
principal already holds — or is requesting — entitlements that should not
be held concurrently.
"""

from typing import Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client


async def _execute(client, method: str, path: str, body: dict = None):
    request_executor = client.get_request_executor()
    url = f"{client.get_base_url()}{path}"
    request, error = await request_executor.create_request(method, url, body or {})
    if error:
        return None, error
    response, error = await request_executor.execute(request)
    if error:
        return None, error
    if response is None:
        return None, None
    body = response.get_body()
    return body if body else None, None


@mcp.tool()
async def list_risk_rules(
    ctx: Context,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List governance risk rules in the Okta organization.

    Risk rules define separation-of-duties (SOD) constraints. They are
    evaluated during Access Certification campaigns and Access Request
    workflows to surface conflicts when a principal holds entitlements
    that should not be held concurrently.

    Parameters:
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of risk rules to return per page.

    Returns:
        Dictionary containing a list of risk rule objects and pagination info.
    """
    logger.info("Listing governance risk rules")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = "/governance/api/v1/risk-rules"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing risk rules: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved governance risk rules")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing risk rules: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_risk_rule(
    ctx: Context,
    name: str,
    resources: list,
    conflict_criteria: dict,
    description: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Create a new governance risk rule in the Okta organization.

    Risk rules express separation-of-duties (SOD) policies by specifying
    entitlement combinations that a principal should not hold at the same
    time. Once created, rules are enforced in Access Certification campaigns
    and Access Request workflows.

    Parameters:
        name (str, required): Display name for the risk rule (1-255 chars).
        resources (list, required): List of resource ORNs the rule applies to
            (max 1 item). Each item: {"resourceOrn": "<orn_string>"}.
            Example: [{"resourceOrn": "orn:okta:..."}]
        conflict_criteria (dict, required): Defines the entitlement conflict.
            Structure:
            {
                "and": [
                    {
                        "name": "criteria_1_name",
                        "attribute": "principal.effective_grants",
                        ...
                    },
                    {
                        "name": "criteria_2_name",
                        "attribute": "principal.effective_grants",
                        ...
                    }
                ]
            }
            Exactly 2 criteria items are required in the "and" array.
        description (str, optional): Human-readable description (max 1000 chars)
            explaining the SOD conflict the rule prevents.
        notes (str, optional): Additional notes about the rule (max 1000 chars).

    Returns:
        Dictionary containing the created risk rule or error information.
    """
    logger.info(f"Creating governance risk rule: {name}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload: dict = {
            "name": name,
            "type": "SEPARATION_OF_DUTIES",
            "resources": resources,
            "conflictCriteria": conflict_criteria,
        }
        if description is not None:
            payload["description"] = description
        if notes is not None:
            payload["notes"] = notes

        body, error = await _execute(client, "POST", "/governance/api/v1/risk-rules", payload)
        if error:
            logger.error(f"Okta API error creating risk rule '{name}': {error}")
            return {"error": str(error)}

        logger.info(f"Successfully created governance risk rule: {name}")
        return body

    except Exception as e:
        logger.error(f"Exception creating risk rule '{name}': {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_risk_rule(ctx: Context, rule_id: str) -> dict:
    """Get a governance risk rule by ID.

    Retrieves the full definition of a single risk rule, including its
    name, description, and SOD condition configuration.

    Parameters:
        rule_id (str, required): The ID of the risk rule to retrieve.

    Returns:
        Dictionary containing the risk rule details or error information.
    """
    logger.info(f"Getting governance risk rule: {rule_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/governance/api/v1/risk-rules/{rule_id}")
        if error:
            logger.error(f"Okta API error getting risk rule {rule_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved risk rule: {rule_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting risk rule {rule_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_risk_rule(
    ctx: Context,
    rule_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    notes: Optional[str] = None,
    conflict_criteria: Optional[dict] = None,
) -> dict:
    """Update an existing governance risk rule (PUT).

    The `id` field in the request body must match rule_id. Only include
    the fields you want to update.

    Parameters:
        rule_id (str, required): The ID of the risk rule to update.
        name (str, optional): New display name (1-255 chars).
        description (str, optional): Updated description (max 1000 chars).
        notes (str, optional): Updated notes (max 1000 chars).
        conflict_criteria (dict, optional): Updated conflict criteria. Structure:
            {
                "and": [
                    {"name": "...", "attribute": "principal.effective_grants", ...},
                    {"name": "...", "attribute": "principal.effective_grants", ...}
                ]
            }

    Returns:
        Dictionary containing the updated risk rule or error information.
    """
    logger.info(f"Updating governance risk rule: {rule_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload: dict = {"id": rule_id}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if notes is not None:
            payload["notes"] = notes
        if conflict_criteria is not None:
            payload["conflictCriteria"] = conflict_criteria

        body, error = await _execute(client, "PUT", f"/governance/api/v1/risk-rules/{rule_id}", payload)
        if error:
            logger.error(f"Okta API error updating risk rule {rule_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated risk rule: {rule_id}")
        return body

    except Exception as e:
        logger.error(f"Exception updating risk rule {rule_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_risk_rule(ctx: Context, rule_id: str) -> dict:
    """Delete a governance risk rule from the Okta organization.

    Permanently removes the risk rule. Deleted rules are no longer evaluated
    during Access Certification campaigns or Access Request workflows.
    The API returns HTTP 204 (No Content) on success.

    Parameters:
        rule_id (str, required): The ID of the risk rule to delete.

    Returns:
        Dictionary with a success message or error information.
    """
    logger.warning(f"Deleting governance risk rule: {rule_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "DELETE", f"/governance/api/v1/risk-rules/{rule_id}")
        if error:
            logger.error(f"Okta API error deleting risk rule {rule_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted risk rule: {rule_id}")
        return {"message": f"Risk rule {rule_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception deleting risk rule {rule_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def assess_risk_rules(
    ctx: Context,
    principal_orn: str,
    resource_orns: Optional[list] = None,
) -> dict:
    """Evaluate risk rules against a principal (and optionally specific resources) to identify separation-of-duties conflicts.

    Runs the configured SOD risk rules against a principal's current
    entitlements and, if supplied, the candidate resources being requested
    or reviewed. Use this tool to proactively surface conflicts before
    approving access requests or during access certification reviews.

    Parameters:
        principal_orn (str, required): The Okta user ORN (Okta Resource Name)
            to evaluate risk rules against.
            Example: "orn:okta:directory:00o123:users:00u456"
        resource_orns (list, optional): List of resource ORNs to scope the
            assessment to. All items must be the same resource type. Limits:
            - Max 1 collection ORN
            - Max 1 bundle ORN
            - Max 20 entitlement ORNs
            When omitted, the assessment covers all resources the principal
            currently has access to.

    Returns:
        Dictionary containing the risk assessment results, including any
        SOD conflicts detected, or error information.
    """
    logger.info(f"Assessing risk rules for principal: {principal_orn}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload: dict = {"principalOrn": principal_orn}
        if resource_orns is not None:
            payload["resourceOrnList"] = resource_orns

        body, error = await _execute(client, "POST", "/governance/api/v1/risk-rule-assessments", payload)
        if error:
            logger.error(f"Okta API error assessing risk rules for principal {principal_orn}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully assessed risk rules for principal: {principal_orn}")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception assessing risk rules for principal {principal_orn}: {type(e).__name__}: {e}")
        return {"error": str(e)}
