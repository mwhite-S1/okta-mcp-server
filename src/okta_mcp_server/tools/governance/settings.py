# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Governance settings tools: org settings, integrations, certification settings, entitlement settings."""

from typing import Optional
from urllib.parse import quote, urlencode

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
    response, error = await request_executor.execute(request)
    if error:
        return None, error
    if response is None:
        return None, None
    body = response.get_body()
    return body if body else None, None


# ---------------------------------------------------------------------------
# Org Governance Settings
# ---------------------------------------------------------------------------


@mcp.tool()
async def update_org_governance_settings(ctx: Context, operations: list) -> dict:
    """Update the org-level governance settings using JSON Patch operations.

    Applies one or more patch operations to the org governance settings resource
    at /governance/api/v1/settings. Use this to enable or disable governance
    features, adjust org-wide defaults, and configure delegation rules.

    Parameters:
        operations (list, required): A list of JSON Patch operation objects.
            Each operation must include:
              - op (str): The operation type — "add", "remove", or "replace".
              - path (str): The JSON Pointer path to the field being patched.
              - value (any, optional): The new value for "add" or "replace" ops.

    Example:
        operations=[
            {"op": "replace", "path": "/delegationEnabled", "value": True}
        ]

    Returns:
        Dictionary containing the updated org governance settings or error info.
    """
    logger.info("Updating org governance settings")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "PATCH", "/governance/api/v1/settings", operations)
        if error:
            logger.error(f"Okta API error updating org governance settings: {error}")
            return {"error": str(error)}

        logger.info("Successfully updated org governance settings")
        return body or {"message": "Org governance settings updated successfully"}

    except Exception as e:
        logger.error(f"Exception updating org governance settings: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_governance_integrations(
    ctx: Context,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List governance integrations configured in the Okta organization.

    Governance integrations connect Okta to external systems (such as identity
    governance platforms) that participate in access certification and access
    request workflows.

    Parameters:
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of integrations to return per page.

    Returns:
        Dictionary containing integration objects and pagination info.
    """
    logger.info("Listing governance integrations")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = "/governance/api/v1/settings/integrations"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing governance integrations: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved governance integrations")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing governance integrations: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_governance_integration(ctx: Context, integration: dict) -> dict:
    """Create a new governance integration in the Okta organization.

    Registers an external governance system as an integration so it can
    participate in access certification campaigns and access request workflows.

    Parameters:
        integration (dict, required): The full integration configuration object.
            Typically includes fields such as:
              - name (str): A human-readable name for the integration.
              - type (str): The integration type (e.g. "IGA").
              - settings (dict): Integration-specific configuration.

    Returns:
        Dictionary containing the created integration object or error info.
    """
    logger.info("Creating governance integration")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", "/governance/api/v1/settings/integrations", integration)
        if error:
            logger.error(f"Okta API error creating governance integration: {error}")
            return {"error": str(error)}

        logger.info("Successfully created governance integration")
        return body

    except Exception as e:
        logger.error(f"Exception creating governance integration: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_governance_integration(ctx: Context, integration_id: str) -> dict:
    """Delete a governance integration by ID.

    Removes the specified external governance integration from the Okta
    organization. The integration will no longer participate in certification
    or access request workflows.

    Parameters:
        integration_id (str, required): The ID of the integration to delete.

    Returns:
        Dictionary with a success message on 204 No Content, or error info.
    """
    logger.info(f"Deleting governance integration: {integration_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, error = await _execute(
            client, "DELETE", f"/governance/api/v1/settings/integrations/{integration_id}"
        )
        if error:
            logger.error(f"Okta API error deleting integration {integration_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted governance integration: {integration_id}")
        return {"message": f"Governance integration {integration_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception deleting integration {integration_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Certification Settings
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_certification_settings(ctx: Context) -> dict:
    """Get the org-level access certification settings.

    Returns the configuration that governs how access certification campaigns
    behave across the organization, such as default reviewer fallback rules,
    self-certification settings, and completion behaviors.

    Returns:
        Dictionary containing the certification settings or error information.
    """
    logger.info("Getting certification settings")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", "/governance/api/v1/settings/certification")
        if error:
            logger.error(f"Okta API error getting certification settings: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved certification settings")
        return body

    except Exception as e:
        logger.error(f"Exception getting certification settings: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_certification_settings(ctx: Context, operations: list) -> dict:
    """Update the org-level access certification settings using JSON Patch operations.

    Applies one or more patch operations to the certification settings resource
    at /governance/api/v1/settings/certification. Use this to change reviewer
    fallback rules, self-certification policies, and other campaign defaults.

    Parameters:
        operations (list, required): A list of JSON Patch operation objects.
            Each operation must include:
              - op (str): The operation type — "add", "remove", or "replace".
              - path (str): The JSON Pointer path to the field being patched.
              - value (any, optional): The new value for "add" or "replace" ops.

    Example:
        operations=[
            {"op": "replace", "path": "/selfCertificationAllowed", "value": False}
        ]

    Returns:
        Dictionary containing the updated certification settings or error info.
    """
    logger.info("Updating certification settings")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "PATCH", "/governance/api/v1/settings/certification", operations
        )
        if error:
            logger.error(f"Okta API error updating certification settings: {error}")
            return {"error": str(error)}

        logger.info("Successfully updated certification settings")
        return body or {"message": "Certification settings updated successfully"}

    except Exception as e:
        logger.error(f"Exception updating certification settings: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Entitlement Settings (v2 resource-scoped)
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_resource_entitlement_settings(ctx: Context, resource_orn: str) -> dict:
    """Get the entitlement settings for a specific governance resource.

    Returns the entitlement configuration for the resource identified by its
    Okta Resource Name (ORN). Entitlement settings control how entitlements
    for this resource are discovered, surfaced in the access catalog, and
    governed.

    Parameters:
        resource_orn (str, required): The Okta Resource Name (ORN) of the resource.
            Example: "orn:okta:idp:org123:apps:0oa456..."

    Returns:
        Dictionary containing the resource entitlement settings or error info.
    """
    logger.info(f"Getting entitlement settings for resource: {resource_orn}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        encoded_orn = quote(resource_orn, safe="")
        path = f"/governance/api/v2/resources/{encoded_orn}/entitlement-settings"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error getting entitlement settings for {resource_orn}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved entitlement settings for: {resource_orn}")
        return body

    except Exception as e:
        logger.error(f"Exception getting entitlement settings for {resource_orn}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_resource_entitlement_settings(
    ctx: Context,
    resource_orn: str,
    operations: list,
) -> dict:
    """Update the entitlement settings for a specific governance resource using JSON Patch.

    Applies one or more patch operations to the entitlement settings for the
    resource identified by its Okta Resource Name (ORN). Use this to control
    entitlement discovery, catalog visibility, and governance behavior at the
    resource level.

    Parameters:
        resource_orn (str, required): The Okta Resource Name (ORN) of the resource.
            Example: "orn:okta:idp:org123:apps:0oa456..."
        operations (list, required): A list of JSON Patch operation objects.
            Each operation must include:
              - op (str): The operation type — "add", "remove", or "replace".
              - path (str): The JSON Pointer path to the field being patched.
              - value (any, optional): The new value for "add" or "replace" ops.

    Example:
        operations=[
            {"op": "replace", "path": "/entitlementDiscoveryEnabled", "value": True}
        ]

    Returns:
        Dictionary containing the updated entitlement settings or error info.
    """
    logger.info(f"Updating entitlement settings for resource: {resource_orn}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        encoded_orn = quote(resource_orn, safe="")
        path = f"/governance/api/v2/resources/{encoded_orn}/entitlement-settings"

        body, error = await _execute(client, "PATCH", path, operations)
        if error:
            logger.error(f"Okta API error updating entitlement settings for {resource_orn}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated entitlement settings for: {resource_orn}")
        return body or {"message": f"Entitlement settings updated for resource {resource_orn}"}

    except Exception as e:
        logger.error(f"Exception updating entitlement settings for {resource_orn}: {type(e).__name__}: {e}")
        return {"error": str(e)}
