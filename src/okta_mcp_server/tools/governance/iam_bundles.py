# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Admin IAM governance tools: bundles, entitlements, opt-in/out, and user role governance sources.

Covers the Admin Management API (/api/v1/iam/governance/* and
/api/v1/users/{userId}/roles/{roleAssignmentId}/governance/*) — distinct from
the IGA Governance Service API (/governance/api/v1/).
"""

from typing import Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import DELETE_IAM_GOVERNANCE_BUNDLE, OPT_OUT_IAM_GOVERNANCE


async def _execute(client, method: str, path: str, body: dict = None):
    """Make a direct API call via the SDK request executor."""
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


# ---------------------------------------------------------------------------
# IAM Governance Bundles
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_iam_governance_bundles(
    ctx: Context,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all IAM governance bundles for the Admin Console in the organization.

    Governance bundles group Admin Console entitlements (roles + resource sets)
    so they can be assigned to users as a unit via IGA.

    Parameters:
        after (str, optional): Pagination cursor from a previous response Link header.
        limit (int, optional): Number of results to return (1–200, default 20).

    Returns:
        Dictionary containing a list of governance bundles and pagination links.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        params = {}
        if after:
            params["after"] = after
        if limit is not None:
            params["limit"] = str(limit)
        path = "/api/v1/iam/governance/bundles"
        if params:
            path += f"?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error listing IAM governance bundles: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception listing IAM governance bundles: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_iam_governance_bundle(
    ctx: Context,
    name: str,
    description: Optional[str] = None,
    entitlements: Optional[list] = None,
) -> dict:
    """Create a new IAM governance bundle for the Admin Console.

    A governance bundle groups Admin Console entitlements (role + optional
    resource sets/targets) that can be assigned to users through IGA workflows.

    Parameters:
        name (str, required): Name of the governance bundle.
        description (str, optional): Description of the governance bundle.
        entitlements (list, optional): List of entitlement objects to include.
            Each entitlement object may contain:
            - role (str): The role key (e.g. "SUPER_ADMIN").
            - resourceSets (list[str]): Resource set IDs for custom roles.
            - targets (list[str]): Target resource IDs (app or group IDs) to scope the role.

    Returns:
        Dictionary containing the created governance bundle.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        payload: dict = {"name": name}
        if description is not None:
            payload["description"] = description
        if entitlements is not None:
            payload["entitlements"] = entitlements
        body, error = await _execute(client, "POST", "/api/v1/iam/governance/bundles", payload)
        if error:
            logger.error(f"Error creating IAM governance bundle: {error}")
            return {"error": str(error)}
        logger.info(f"Created IAM governance bundle: {(body or {}).get('id', '')}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception creating IAM governance bundle: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_iam_governance_bundle(ctx: Context, bundle_id: str) -> dict:
    """Retrieve a single IAM governance bundle by ID.

    Parameters:
        bundle_id (str, required): The ID of the governance bundle.

    Returns:
        Dictionary containing the governance bundle details.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/iam/governance/bundles/{bundle_id}")
        if error:
            logger.error(f"Error retrieving IAM governance bundle {bundle_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception retrieving IAM governance bundle {bundle_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def replace_iam_governance_bundle(
    ctx: Context,
    bundle_id: str,
    name: str,
    description: Optional[str] = None,
    entitlements: Optional[list] = None,
) -> dict:
    """Replace (full update) an IAM governance bundle.

    All writable fields are replaced. Omitting optional fields clears them.

    Parameters:
        bundle_id (str, required): The ID of the governance bundle to replace.
        name (str, required): New name for the governance bundle.
        description (str, optional): New description. Omit to clear the existing description.
        entitlements (list, optional): Replacement list of entitlement objects.
            Each entitlement object may contain:
            - role (str): The role key.
            - resourceSets (list[str]): Resource set IDs for custom roles.
            - targets (list[str]): Target resource IDs (app or group IDs).

    Returns:
        Dictionary containing the updated governance bundle.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        payload: dict = {"name": name}
        if description is not None:
            payload["description"] = description
        if entitlements is not None:
            payload["entitlements"] = entitlements
        body, error = await _execute(client, "PUT", f"/api/v1/iam/governance/bundles/{bundle_id}", payload)
        if error:
            logger.error(f"Error replacing IAM governance bundle {bundle_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Replaced IAM governance bundle: {bundle_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception replacing IAM governance bundle {bundle_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_iam_governance_bundle(ctx: Context, bundle_id: str) -> dict:
    """Delete an IAM governance bundle from the Admin Console.

    The user will be asked for confirmation before deletion proceeds.

    Parameters:
        bundle_id (str, required): The ID of the governance bundle to delete.

    Returns:
        Dictionary containing the result of the deletion.
    """
    logger.warning(f"Deletion requested for IAM governance bundle: {bundle_id}")

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_IAM_GOVERNANCE_BUNDLE.format(bundle_id=bundle_id),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": (
                f"To confirm deletion of IAM governance bundle {bundle_id}, please confirm. "
                "This will remove the bundle and all its entitlement assignments."
            ),
            "bundle_id": bundle_id,
        },
    )

    if not outcome.used_elicitation:
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"IAM governance bundle deletion cancelled for {bundle_id}")
        return {"message": "IAM governance bundle deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "DELETE", f"/api/v1/iam/governance/bundles/{bundle_id}")
        if error:
            logger.error(f"Error deleting IAM governance bundle {bundle_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Successfully deleted IAM governance bundle: {bundle_id}")
        return {"message": f"IAM governance bundle {bundle_id} deleted successfully."}
    except Exception as e:
        logger.error(f"Exception deleting IAM governance bundle {bundle_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_iam_bundle_entitlements(
    ctx: Context,
    bundle_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all entitlements for a specific IAM governance bundle.

    Parameters:
        bundle_id (str, required): The ID of the governance bundle.
        after (str, optional): Pagination cursor from a previous response Link header.
        limit (int, optional): Number of results to return (1–200, default 20).

    Returns:
        Dictionary containing the list of bundle entitlements and pagination links.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        params = {}
        if after:
            params["after"] = after
        if limit is not None:
            params["limit"] = str(limit)
        path = f"/api/v1/iam/governance/bundles/{bundle_id}/entitlements"
        if params:
            path += f"?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error listing entitlements for bundle {bundle_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception listing entitlements for bundle {bundle_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_iam_bundle_entitlement_values(
    ctx: Context,
    bundle_id: str,
    entitlement_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all values for a specific entitlement within an IAM governance bundle.

    Entitlement values represent the concrete resources (groups, apps, resource sets)
    that the entitlement grants access to.

    Parameters:
        bundle_id (str, required): The ID of the governance bundle.
        entitlement_id (str, required): The ID of the bundle entitlement.
        after (str, optional): Pagination cursor from a previous response Link header.
        limit (int, optional): Number of results to return (1–200, default 20).

    Returns:
        Dictionary containing the list of entitlement values and pagination links.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        params = {}
        if after:
            params["after"] = after
        if limit is not None:
            params["limit"] = str(limit)
        path = f"/api/v1/iam/governance/bundles/{bundle_id}/entitlements/{entitlement_id}/values"
        if params:
            path += f"?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error listing values for entitlement {entitlement_id} in bundle {bundle_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception listing values for entitlement {entitlement_id} in bundle {bundle_id}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# IAM Governance Opt-in / Opt-out
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_iam_governance_opt_in_status(ctx: Context) -> dict:
    """Retrieve the entitlement management opt-in status for the Admin Console.

    The status will be one of: OPTING_IN, OPTED_IN, OPTING_OUT, OPTED_OUT.

    Returns:
        Dictionary containing the optInStatus and related links.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", "/api/v1/iam/governance/optIn")
        if error:
            logger.error(f"Error retrieving IAM governance opt-in status: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception retrieving IAM governance opt-in status: {e}")
        return {"error": str(e)}


@mcp.tool()
async def opt_in_iam_governance(ctx: Context) -> dict:
    """Opt the Admin Console in to entitlement management.

    Enables IGA entitlement management for the Admin Console, allowing governance
    bundles to be assigned to users through access request workflows.

    Returns:
        Dictionary containing the updated opt-in status.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", "/api/v1/iam/governance/optIn")
        if error:
            logger.error(f"Error opting in to IAM governance: {error}")
            return {"error": str(error)}
        logger.info("Successfully opted in to IAM governance entitlement management")
        return body or {}
    except Exception as e:
        logger.error(f"Exception opting in to IAM governance: {e}")
        return {"error": str(e)}


@mcp.tool()
async def opt_out_iam_governance(ctx: Context) -> dict:
    """Opt the Admin Console out of entitlement management.

    Disables IGA entitlement management for the Admin Console organization-wide.
    The user will be asked for confirmation before this proceeds.

    Returns:
        Dictionary containing the updated opt-in status.
    """
    logger.warning("Opt-out from IAM governance entitlement management requested")

    outcome = await elicit_or_fallback(
        ctx,
        message=OPT_OUT_IAM_GOVERNANCE,
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": (
                "Opting out will disable entitlement management for the Admin Console "
                "organization-wide. Please confirm this action."
            ),
        },
    )

    if not outcome.used_elicitation:
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info("IAM governance opt-out cancelled by user")
        return {"message": "IAM governance opt-out cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", "/api/v1/iam/governance/optOut")
        if error:
            logger.error(f"Error opting out of IAM governance: {error}")
            return {"error": str(error)}
        logger.info("Successfully opted out of IAM governance entitlement management")
        return body or {}
    except Exception as e:
        logger.error(f"Exception opting out of IAM governance: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# User Role Governance Sources
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_user_role_governance_sources(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
) -> dict:
    """Retrieve all governance sources for a role assigned to a user.

    Returns the governance grants (entitlement bundle assignments or custom grants)
    that are the source of this role assignment for the given user.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.

    Returns:
        Dictionary containing the list of governance grants and links.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/governance"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error retrieving governance sources for user {user_id} role {role_assignment_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception retrieving governance sources for user {user_id} role {role_assignment_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_user_role_governance_grant(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
    grant_id: str,
) -> dict:
    """Retrieve a single governance grant for a role assigned to a user.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.
        grant_id (str, required): The ID of the governance grant.

    Returns:
        Dictionary containing the governance grant details including type,
        bundleId, expirationDate, and links.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/governance/{grant_id}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error retrieving governance grant {grant_id} for user {user_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception retrieving governance grant {grant_id} for user {user_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_user_role_governance_grant_resources(
    ctx: Context,
    user_id: str,
    role_assignment_id: str,
    grant_id: str,
) -> dict:
    """Retrieve the resources associated with a governance grant for a user's role.

    Returns the concrete resources (apps, groups, resource sets) that the governance
    grant provides access to within the given role assignment.

    Parameters:
        user_id (str, required): The ID of the Okta user.
        role_assignment_id (str, required): The ID of the role assignment.
        grant_id (str, required): The ID of the governance grant.

    Returns:
        Dictionary containing the list of resources and pagination links.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/users/{user_id}/roles/{role_assignment_id}/governance/{grant_id}/resources"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error retrieving resources for governance grant {grant_id} user {user_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception retrieving resources for governance grant {grant_id} user {user_id}: {e}")
        return {"error": str(e)}
