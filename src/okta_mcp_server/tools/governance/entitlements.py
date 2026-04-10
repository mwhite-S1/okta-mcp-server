# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Governance entitlements tools: entitlements, bundles, grants, principal entitlements, principal access."""

from typing import Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import REVOKE_PRINCIPAL_ACCESS


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
# Entitlements
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_entitlements(
    ctx: Context,
    filter: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    order_by: Optional[str] = None,
) -> dict:
    """List governance entitlements in the Okta organization.

    An entitlement is a permission that allows users to take specific actions
    within a resource, such as a role within an application.

    Parameters:
        filter (str, required): SCIM filter expression (required by the API).
            Supported filter fields:
            - parent.externalId: eq  (Okta app ID, e.g. '0oaABC123')
            - parent.type: eq        (e.g. 'APPLICATION')
            - parentResourceOrn: eq  (full resource ORN)
            - name: sw, co          (starts-with, contains)
            - created: gt, ge, lt, le (ISO 8601 timestamp)
            Example: 'parent.externalId eq "0oaABC123" AND parent.type eq "APPLICATION"'
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of entitlements to return per page.
        order_by (str, optional): Sort order. Supported fields: name, created.
            Example: "name asc" or "created desc".

    Returns:
        Dictionary containing entitlement objects and pagination info.
    """
    logger.info("Listing governance entitlements")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {"filter": filter}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit
        if order_by:
            params["orderBy"] = order_by

        path = f"/governance/api/v1/entitlements?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing entitlements: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved entitlements")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing entitlements: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_entitlement(ctx: Context, entitlement: dict) -> dict:
    """Create a governance entitlement.

    An entitlement is a permission that allows users to take specific actions
    within a resource. The app must have entitlement management enabled.

    Parameters:
        entitlement (dict, required): Entitlement configuration. Required fields:
            - name (str): Entitlement name.
            - externalValue (str): The entitlement's external identifier in the source system.
            - parent (dict): The application this entitlement belongs to:
                - externalId (str): The Okta app instance ID (e.g. "0oaABC123...").
                - type (str): Must be "APPLICATION".
            - multiValue (bool): Whether multiple values can be assigned simultaneously.
            - dataType (str): "string" or "array".
            - values (list): Entitlement value definitions. Each item:
                - name (str): Display name for the value.
                - externalValue (str): Value identifier in the source system.
                - description (str, optional): Value description.

        Example:
            {
                "name": "Salesforce Role",
                "externalValue": "sf_role",
                "parent": {"externalId": "0oaABC123", "type": "APPLICATION"},
                "multiValue": false,
                "dataType": "string",
                "values": [
                    {"name": "Admin", "externalValue": "admin"},
                    {"name": "Read Only", "externalValue": "read_only"}
                ]
            }

    Returns:
        Dictionary containing the created entitlement or error information.
    """
    logger.info("Creating governance entitlement")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", "/governance/api/v1/entitlements", entitlement)
        if error:
            logger.error(f"Okta API error creating entitlement: {error}")
            return {"error": str(error)}

        logger.info("Successfully created entitlement")
        return body

    except Exception as e:
        logger.error(f"Exception creating entitlement: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_entitlement(ctx: Context, entitlement_id: str) -> dict:
    """Get a governance entitlement by ID.

    Parameters:
        entitlement_id (str, required): The ID of the entitlement to retrieve.

    Returns:
        Dictionary containing the entitlement details or error information.
    """
    logger.info(f"Getting entitlement: {entitlement_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/governance/api/v1/entitlements/{entitlement_id}")
        if error:
            logger.error(f"Okta API error getting entitlement {entitlement_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved entitlement: {entitlement_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting entitlement {entitlement_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_entitlement(ctx: Context, entitlement_id: str, entitlement: dict) -> dict:
    """Replace a governance entitlement (full update via PUT).

    Performs a full replacement of the entitlement. All required fields must be
    included; omitted fields will be cleared.

    Parameters:
        entitlement_id (str, required): The ID of the entitlement to replace.
        entitlement (dict, required): The full replacement entitlement object.
            Required fields:
            - id (str): Must match entitlement_id.
            - name (str): Entitlement display name.
            - externalValue (str): The entitlement identifier in the source system.
            - multiValue (bool): Whether multiple values can be assigned simultaneously.
            - dataType (str): "string" or "array".
            - parent (dict): {"externalId": "<app_id>", "type": "APPLICATION"}
            - parentResourceOrn (str): Full ORN of the parent resource.
            - values (list): Entitlement values. Each item should include "id" for
                existing values, plus "name", "externalValue" for updates.

    Returns:
        Dictionary containing the updated entitlement or error information.
    """
    logger.info(f"Updating entitlement: {entitlement_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "PUT", f"/governance/api/v1/entitlements/{entitlement_id}", entitlement
        )
        if error:
            logger.error(f"Okta API error updating entitlement {entitlement_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated entitlement: {entitlement_id}")
        return body

    except Exception as e:
        logger.error(f"Exception updating entitlement {entitlement_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def patch_entitlement(ctx: Context, entitlement_id: str, operations: list) -> dict:
    """Partially update a governance entitlement using patch operations (PATCH).

    Supports updating entitlement values (add, replace, remove) and entitlement
    properties (name, description). Each operation object uses a refType discriminator
    to distinguish between value operations and property operations.

    Parameters:
        entitlement_id (str, required): The ID of the entitlement to patch.
        operations (list, required): List of 1-100 patch operation objects.
            Each operation must include: op, path, refType.

            For entitlement value operations (refType: "ENTITLEMENT-VALUE"):
            - op: "ADD", "REPLACE", or "REMOVE"
            - path: "/values/-" for ADD, "/values/{valueId}" for REPLACE or REMOVE
            - value (dict, for ADD/REPLACE): {"name": "...", "externalValue": "..."}
            - refType: "ENTITLEMENT-VALUE"

            For entitlement property operations (refType: "ENTITLEMENT"):
            - op: "REPLACE"
            - path: "/name" or "/description"
            - value (str): New value for the property
            - refType: "ENTITLEMENT"

            Example (add a new value):
            [
                {
                    "op": "ADD",
                    "path": "/values/-",
                    "value": {"name": "Editor", "externalValue": "editor"},
                    "refType": "ENTITLEMENT-VALUE"
                }
            ]

    Returns:
        Dictionary containing the updated entitlement or error information.
    """
    logger.info(f"Patching entitlement: {entitlement_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "PATCH", f"/governance/api/v1/entitlements/{entitlement_id}", operations
        )
        if error:
            logger.error(f"Okta API error patching entitlement {entitlement_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully patched entitlement: {entitlement_id}")
        return body

    except Exception as e:
        logger.error(f"Exception patching entitlement {entitlement_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_entitlement(ctx: Context, entitlement_id: str) -> dict:
    """Delete a governance entitlement.

    Parameters:
        entitlement_id (str, required): The ID of the entitlement to delete.

    Returns:
        Dictionary containing the result or error information.
    """
    logger.warning(f"Deleting entitlement: {entitlement_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "DELETE", f"/governance/api/v1/entitlements/{entitlement_id}")
        if error:
            logger.error(f"Okta API error deleting entitlement {entitlement_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted entitlement: {entitlement_id}")
        return {"message": f"Entitlement {entitlement_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception deleting entitlement {entitlement_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_entitlement_values(
    ctx: Context,
    entitlement_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List values for a specific governance entitlement.

    Entitlement values represent the specific instances of an entitlement,
    such as individual roles within an application.

    Parameters:
        entitlement_id (str, required): The ID of the entitlement whose values to list.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of values to return per page.

    Returns:
        Dictionary containing entitlement value objects and pagination info.
    """
    logger.info(f"Listing values for entitlement: {entitlement_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v1/entitlements/{entitlement_id}/values"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing entitlement values: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved entitlement values")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing entitlement values: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_entitlement_value(ctx: Context, entitlement_id: str, value_id: str) -> dict:
    """Get a specific value of a governance entitlement.

    Parameters:
        entitlement_id (str, required): The ID of the entitlement.
        value_id (str, required): The ID of the entitlement value to retrieve.

    Returns:
        Dictionary containing the entitlement value details or error information.
    """
    logger.info(f"Getting value {value_id} for entitlement {entitlement_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET",
            f"/governance/api/v1/entitlements/{entitlement_id}/values/{value_id}",
        )
        if error:
            logger.error(f"Okta API error getting entitlement value: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved entitlement value: {value_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting entitlement value: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Entitlement Bundles
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_entitlement_bundles(
    ctx: Context,
    filter: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    order_by: Optional[str] = None,
    include: Optional[str] = None,
) -> dict:
    """List entitlement bundles in the Okta organization.

    Entitlement bundles group related entitlements together so they can be
    requested or certified as a unit.

    Parameters:
        filter (str, optional): SCIM filter expression. Supported fields:
            - id: eq
            - lastUpdated: gt, ge, lt, le
            - targetResourceOrn: eq
            - target.externalId: eq  (Okta app ID, e.g. "0oa...")
            - target.type: eq        (e.g. "APPLICATION")
            - status: eq             (e.g. "ACTIVE")
            - name: eq, sw, co
            Example: 'target.externalId eq "0oaABC123"'
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of bundles to return per page.
        order_by (str, optional): Sort order. Example: "name asc" or "lastUpdated desc".
        include (str, optional): Extra fields. Use "full_entitlements" to include
            complete entitlement objects instead of just references.

    Returns:
        Dictionary containing entitlement bundle objects and pagination info.
    """
    logger.info("Listing entitlement bundles")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {}
        if filter:
            params["filter"] = filter
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit
        if order_by:
            params["orderBy"] = order_by
        if include:
            params["include"] = include

        path = "/governance/api/v1/entitlement-bundles"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing entitlement bundles: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved entitlement bundles")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing entitlement bundles: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_entitlement_bundle(ctx: Context, bundle: dict) -> dict:
    """Create an entitlement bundle.

    Entitlement bundles group multiple entitlements so they can be
    requested or certified together as a unit. The target application
    must have entitlement management enabled in Okta.

    Parameters:
        bundle (dict, required): Bundle configuration. Required fields:
            - name (str): Bundle name.
            - target (dict): The application this bundle belongs to:
                - externalId (str): The Okta app instance ID (e.g. "0oaABC123...").
                - type (str): Must be "APPLICATION".
            - entitlements (list): Entitlement references to include in the bundle.
                Each item: {"id": "<entitlement_id>", "values": [{"id": "<value_id>"}]}.
                Can be an empty list if no specific entitlements are pre-selected.
            Optional fields:
            - description (str): Bundle description.

        Example:
            {
                "name": "Salesforce Admin Bundle",
                "description": "Admin-level Salesforce access",
                "target": {"externalId": "0oaABC123", "type": "APPLICATION"},
                "entitlements": []
            }

    Returns:
        Dictionary containing the created bundle or error information.
    """
    logger.info("Creating entitlement bundle")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", "/governance/api/v1/entitlement-bundles", bundle)
        if error:
            logger.error(f"Okta API error creating entitlement bundle: {error}")
            return {"error": str(error)}

        logger.info("Successfully created entitlement bundle")
        return body

    except Exception as e:
        logger.error(f"Exception creating entitlement bundle: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_entitlement_bundle(ctx: Context, bundle_id: str, include: Optional[str] = None) -> dict:
    """Get an entitlement bundle by ID.

    Parameters:
        bundle_id (str, required): The ID of the entitlement bundle to retrieve.
        include (str, optional): Extra fields to include. Use "full_entitlements" to
            return complete entitlement objects instead of just references.

    Returns:
        Dictionary containing the bundle details or error information.
    """
    logger.info(f"Getting entitlement bundle: {bundle_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        path = f"/governance/api/v1/entitlement-bundles/{bundle_id}"
        if include:
            path += f"?{urlencode({'include': include})}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error getting bundle {bundle_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved bundle: {bundle_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting bundle {bundle_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_entitlement_bundle(ctx: Context, bundle_id: str, bundle: dict) -> dict:
    """Replace an entitlement bundle (full update via PUT).

    Performs a full replacement of the entitlement bundle. All required fields
    must be included; omitted fields will be cleared.

    Parameters:
        bundle_id (str, required): The ID of the entitlement bundle to replace.
        bundle (dict, required): The full replacement bundle object. Required fields:
            - id (str): Must match bundle_id.
            - name (str): Bundle name.
            - targetResourceOrn (str): ORN of the target resource.
            - target (dict): Application reference:
                - externalId (str): Okta app ID (e.g. "0oaABC123...").
                - type (str): Must be "APPLICATION".
            - entitlements (list): Entitlement references (can be empty list).
            Optional fields:
            - description (str): Bundle description.

    Returns:
        Dictionary containing the updated bundle or error information.
    """
    logger.info(f"Updating entitlement bundle: {bundle_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "PUT", f"/governance/api/v1/entitlement-bundles/{bundle_id}", bundle
        )
        if error:
            logger.error(f"Okta API error updating bundle {bundle_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated bundle: {bundle_id}")
        return body

    except Exception as e:
        logger.error(f"Exception updating bundle {bundle_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_entitlement_bundle(ctx: Context, bundle_id: str) -> dict:
    """Delete an entitlement bundle.

    Parameters:
        bundle_id (str, required): The ID of the entitlement bundle to delete.

    Returns:
        Dictionary containing the result or error information.
    """
    logger.warning(f"Deleting entitlement bundle: {bundle_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, error = await _execute(
            client, "DELETE", f"/governance/api/v1/entitlement-bundles/{bundle_id}"
        )
        if error:
            logger.error(f"Okta API error deleting bundle {bundle_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted bundle: {bundle_id}")
        return {"message": f"Entitlement bundle {bundle_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception deleting bundle {bundle_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Grants
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_grants(
    ctx: Context,
    filter: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List governance grants in the Okta organization.

    Grants represent assignments of entitlements or entitlement bundles to a
    principal (user or group). The filter must reference a specific resource.

    Parameters:
        filter (str, required): SCIM filter expression (required by the API).
            Must reference a resource. Example: 'resourceId eq "abc123"'.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of grants to return per page.

    Returns:
        Dictionary containing grant objects and pagination info.
    """
    logger.info("Listing governance grants")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {"filter": filter}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v1/grants?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing grants: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved grants")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing grants: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_grant(ctx: Context, grant: dict) -> dict:
    """Create a governance grant to assign entitlements to a principal.

    Grants assign entitlements or entitlement bundles to a user or group.

    Parameters:
        grant (dict, required): Grant configuration. Key fields:
            - principalId (str): The user or group ID receiving the grant.
            - resourceId (str): The resource the grant applies to.
            - entitlementId (str) or bundleId (str): What is being granted.
            - type (str): Grant type (e.g. "DIRECT").

    Returns:
        Dictionary containing the created grant or error information.
    """
    logger.info("Creating governance grant")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", "/governance/api/v1/grants", grant)
        if error:
            logger.error(f"Okta API error creating grant: {error}")
            return {"error": str(error)}

        logger.info("Successfully created grant")
        return body

    except Exception as e:
        logger.error(f"Exception creating grant: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_grant(ctx: Context, grant_id: str) -> dict:
    """Get a governance grant by ID.

    Parameters:
        grant_id (str, required): The ID of the grant to retrieve.

    Returns:
        Dictionary containing the grant details or error information.
    """
    logger.info(f"Getting grant: {grant_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/governance/api/v1/grants/{grant_id}")
        if error:
            logger.error(f"Okta API error getting grant {grant_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved grant: {grant_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting grant {grant_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_grant(ctx: Context, grant_id: str, grant: dict) -> dict:
    """Replace a governance grant (full update via PUT).

    Parameters:
        grant_id (str, required): The ID of the grant to replace.
        grant (dict, required): The full replacement grant object.

    Returns:
        Dictionary containing the updated grant or error information.
    """
    logger.info(f"Updating grant: {grant_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "PUT", f"/governance/api/v1/grants/{grant_id}", grant)
        if error:
            logger.error(f"Okta API error updating grant {grant_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated grant: {grant_id}")
        return body

    except Exception as e:
        logger.error(f"Exception updating grant {grant_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def patch_grant(ctx: Context, grant_id: str, operations: list) -> dict:
    """Partially update a governance grant using patch operations.

    Parameters:
        grant_id (str, required): The ID of the grant to patch.
        operations (list, required): List of patch operation objects.

    Returns:
        Dictionary containing the updated grant or error information.
    """
    logger.info(f"Patching grant: {grant_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "PATCH", f"/governance/api/v1/grants/{grant_id}", operations
        )
        if error:
            logger.error(f"Okta API error patching grant {grant_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully patched grant: {grant_id}")
        return body

    except Exception as e:
        logger.error(f"Exception patching grant {grant_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Principal Entitlements
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_principal_entitlements(
    ctx: Context,
    filter: str,
    after: Optional[str] = None,
) -> dict:
    """List the effective entitlements for a principal (user or group).

    Principal entitlements represent the net effective access after evaluating
    all grants, policies, and group memberships.

    Parameters:
        filter (str, required): SCIM filter expression (required by the API).
            Example: 'principalId eq "00u123..."'.
        after (str, optional): Pagination cursor for the next page of results.

    Returns:
        Dictionary containing principal entitlement objects and pagination info.
    """
    logger.info("Listing principal entitlements")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {"filter": filter}
        if after:
            params["after"] = after

        path = f"/governance/api/v1/principal-entitlements?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing principal entitlements: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved principal entitlements")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception listing principal entitlements: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_principal_entitlement_history(
    ctx: Context,
    filter: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """Get the entitlement change history for a principal.

    Returns a log of all entitlement grants and revocations for a user or group,
    useful for auditing access changes over time.

    Parameters:
        filter (str, required): SCIM filter expression (required by the API).
            Example: 'principalId eq "00u123..."'.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of history entries to return.

    Returns:
        Dictionary containing entitlement history entries and pagination info.
    """
    logger.info("Getting principal entitlement history")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {"filter": filter}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v1/principal-entitlements/history?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error getting entitlement history: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved entitlement history")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception getting entitlement history: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_principal_entitlements_change(ctx: Context, change_id: str) -> dict:
    """Get the details of a principal entitlements change operation.

    Returns information about a specific entitlement change event for a principal,
    including what changed, when, and why.

    Parameters:
        change_id (str, required): The ID of the principal entitlements change.

    Returns:
        Dictionary containing the change details or error information.
    """
    logger.info(f"Getting principal entitlements change: {change_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET",
            f"/governance/api/v1/principal-entitlements-changes/{change_id}",
        )
        if error:
            logger.error(f"Okta API error getting change {change_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved entitlements change: {change_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting change {change_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Principal Access
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_principal_access(
    ctx: Context,
    filter: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """Get a summary of a principal's access to resources.

    Returns the effective access summary for a user across resources,
    including which entitlements they hold on each resource.

    Parameters:
        filter (str, required): SCIM filter expression.
            Example: 'principalId eq "00u123..."'.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of results to return.

    Returns:
        Dictionary containing principal access summary and pagination info.
    """
    logger.info("Getting principal access summary")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {"filter": filter}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v1/principal-access?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error getting principal access: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved principal access")
        return body or {"items": []}

    except Exception as e:
        logger.error(f"Exception getting principal access: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def revoke_principal_access(ctx: Context, resource_id: str, principal_id: str) -> dict:
    """Revoke a principal's access to a resource.

    Removes the entitlement grant for a user or group on a specific resource.
    The user will be asked for confirmation before the revocation proceeds.

    Parameters:
        resource_id (str, required): The ID of the resource to revoke access to.
        principal_id (str, required): The ID of the user or group whose access
            will be revoked.

    Returns:
        Dictionary containing the result of the revocation or error information.
    """
    logger.warning(f"Revoke access requested: principal={principal_id}, resource={resource_id}")

    outcome = await elicit_or_fallback(
        ctx,
        message=REVOKE_PRINCIPAL_ACCESS.format(principal_id=principal_id, resource_id=resource_id),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": (
                f"Confirm revocation of access for principal {principal_id} "
                f"on resource {resource_id}. This action cannot be undone."
            ),
            "principal_id": principal_id,
            "resource_id": resource_id,
        },
    )

    if not outcome.used_elicitation:
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Access revocation cancelled for principal {principal_id}")
        return {"message": "Access revocation cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            "/governance/api/v2/revoke-principal-access",
            {"principalId": principal_id, "resourceId": resource_id},
        )
        if error:
            logger.error(f"Okta API error revoking access: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully revoked access: principal={principal_id}, resource={resource_id}")
        return body or {"message": f"Access revoked for principal {principal_id} on resource {resource_id}"}

    except Exception as e:
        logger.error(f"Exception revoking access: {type(e).__name__}: {e}")
        return {"error": str(e)}
