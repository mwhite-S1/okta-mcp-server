# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Governance resource owners tools: list, configure, update, and catalog lookup."""

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


@mcp.tool()
async def list_resource_owners(
    ctx: Context,
    filter: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    include: Optional[str] = None,
) -> dict:
    """List resources with assigned owners in the Okta organization.

    Returns all resources (such as entitlements or entitlement bundles) for an app
    that have owners assigned. A filter is required by the API.

    Parameters:
        filter (str, required): SCIM filter expression. Supported fields and operators:
            - parentResourceOrn: eq  (required for app/group/entitlement/bundle resources)
            - resource.orn: eq       (for collections, use instead of parentResourceOrn)
            - resource.type: eq
            - resource.profile.name: sw, co  (requires parentResourceOrn + resource.type)
            Examples:
              'parentResourceOrn eq "orn:okta:idp:{orgId}:apps:salesforce:{appId}"'
              'parentResourceOrn eq "orn:..." AND resource.type eq "entitlement-bundles"'
              'resource.orn eq "orn:okta:governance:{orgId}:collections:{colId}"'
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum records per page (1-200, default 20).
        include (str, optional): Extra fields to add to the response.
            Use "parent_resource_owner" to include parent resource owners.

    Returns:
        Dictionary with a "data" array of resource-owner objects and pagination links.
    """
    logger.info("Listing resource owners")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {"filter": filter}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit
        if include:
            params["include"] = include

        path = f"/governance/api/v1/resource-owners?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing resource owners: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved resource owners")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing resource owners: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_resource_owner(
    ctx: Context,
    resource_orns: list,
    principal_orns: list,
) -> dict:
    """Assign or update owners for one or more resources.

    Configures the owners for the specified resources. If no principal ORNs are
    provided (empty list), all current owners are removed from those resources.
    Resource owners are automatically assigned as reviewers for access
    certification campaigns or access requests scoped to their resources.

    Parameters:
        resource_orns (list, required): ORNs of the resources to assign owners to
            (1-10 items). Supported resource types:
              orn:okta:idp:{orgId}:apps:{protocol}:{appId}
              orn:okta:directory:{orgId}:groups:{groupId}
              orn:okta:governance:{orgId}:entitlement-bundles:{bundleId}
              orn:okta:governance:{orgId}:collections:{colId}
              orn:okta:governance:{orgId}:entitlement-values:{valueId}
        principal_orns (list, required): ORNs of the users or groups to assign as
            owners (0-5 items). Pass an empty list to remove all current owners.
            User ORN format:  orn:okta:directory:{orgId}:users:{userId}
            Group ORN format: orn:okta:directory:{orgId}:groups:{groupId}

    Returns:
        Dictionary with a "data" array of resource-owner records.
    """
    logger.info(f"Configuring resource owners for {len(resource_orns)} resource(s)")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        payload = {"resourceOrns": resource_orns, "principalOrns": principal_orns}
        body, error = await _execute(client, "POST", "/governance/api/v1/resource-owners", payload)
        if error:
            logger.error(f"Okta API error configuring resource owners: {error}")
            return {"error": str(error)}

        logger.info("Successfully configured resource owners")
        return body or {}

    except Exception as e:
        logger.error(f"Exception configuring resource owners: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_resource_owners(
    ctx: Context,
    resource_orn: str,
    operations: list,
) -> dict:
    """Apply patch operations to the owner list of a specific resource.

    Supports removing individual principal owners from a resource using
    REMOVE operations. Each operation specifies a single principal ORN to remove.

    Parameters:
        resource_orn (str, required): ORN of the resource whose owners should be
            updated. Supported types: app, entitlement value, entitlement bundle,
            or collection.
            Example: 'orn:okta:governance:{orgId}:entitlement-bundles:{bundleId}'
        operations (list, required): List of patch operation objects (1-5 items).
            Each object must have:
              op   (str): The operation type. Only "REMOVE" is supported.
              path (str): The property to update. Only "/principalOrn" is supported.
              value (str): The principal ORN to remove.
            Example:
              [{"op": "REMOVE", "path": "/principalOrn",
                "value": "orn:okta:directory:{orgId}:users:{userId}"}]

    Returns:
        Empty response body on success (HTTP 204).
    """
    logger.info(f"Updating resource owners for resource: {resource_orn}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        payload = {"resourceOrn": resource_orn, "data": operations}
        body, error = await _execute(client, "PATCH", "/governance/api/v1/resource-owners", payload)
        if error:
            logger.error(f"Okta API error updating resource owners for '{resource_orn}': {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated owners for resource: {resource_orn}")
        return body or {}

    except Exception as e:
        logger.error(f"Exception updating resource owners for '{resource_orn}': {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_resource_owners_catalog(
    ctx: Context,
    filter: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List resources that do NOT yet have owners assigned.

    Returns all resources for an app (the parent resource) that do not have owners
    assigned. Use this to identify resources that still need owner configuration.
    A filter with parentResourceOrn is required by the API.

    Parameters:
        filter (str, required): SCIM filter expression. Supported fields and operators:
            - parentResourceOrn: eq  (required)
            - resource.type: eq
            - resource.profile.name: sw, co  (requires parentResourceOrn + resource.type)
            - resource.profile.parent.id: eq  (for entitlement-values)
            Examples:
              'parentResourceOrn eq "orn:okta:idp:{orgId}:apps:salesforce:{appId}"'
              'parentResourceOrn eq "orn:..." AND resource.type eq "entitlement-bundles"'
              'parentResourceOrn eq "orn:..." AND resource.type eq "entitlement-bundles"
               AND resource.profile.name sw "License"'
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum records per page (1-200, default 20).

    Returns:
        Dictionary with parentResourceOrn, a "data" array of unowned resources,
        and pagination links.
    """
    logger.info("Listing unowned resources from resource owners catalog")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {"filter": filter}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v1/resource-owners/catalog/resources?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing resource owners catalog: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved resource owners catalog")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing resource owners catalog: {type(e).__name__}: {e}")
        return {"error": str(e)}
