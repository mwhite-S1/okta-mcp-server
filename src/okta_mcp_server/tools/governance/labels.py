# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Governance labels tools: list, create, update, delete, assign."""

import json as _json
from typing import Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import DELETE_GOVERNANCE_LABEL


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


@mcp.tool()
async def list_governance_labels(
    ctx: Context,
    filter: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List governance labels in the Okta organization.

    Governance labels categorize resources (apps, groups, entitlements) to
    control access certification campaigns and access request policies.

    Parameters:
        filter (str, optional): Filter expression. Supported fields and operators:
            - name: sw (starts with), co (contains), eq (equal)
            Example: 'name sw "team"'
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of labels to return per page.

    Returns:
        Dictionary containing a list of label objects and pagination info.
    """
    logger.info("Listing governance labels")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if filter:
            params["filter"] = filter
        if after:
            params["after"] = after
        # NOTE: /governance/api/v1/labels does not accept a 'limit' parameter
        # (returns 400 if passed). Silently drop it.

        path = "/governance/api/v1/labels"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing governance labels: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved governance labels")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing governance labels: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_governance_label(ctx: Context, label_id: str) -> dict:
    """Get a governance label by ID.

    Parameters:
        label_id (str, required): The ID of the label to retrieve.

    Returns:
        Dictionary containing the label details or error information.
    """
    logger.info(f"Getting governance label: {label_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/governance/api/v1/labels/{label_id}")
        if error:
            logger.error(f"Okta API error getting label {label_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved label: {label_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting label {label_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_governance_label(ctx: Context, name: str, values: list) -> dict:
    """Create a governance label in the Okta organization.

    Labels are used to categorize resources for governance workflows such as
    access certification campaigns and access request policies.

    Parameters:
        name (str, required): The label key name (e.g. "sensitivity", "team").
        values (list, required): List of value objects, each with a "name" field
            and optional "metadata" with a "backgroundColor" field.
            Allowed colors: red, orange, yellow, green, blue, purple, teal, beige, gray.

    Example:
        name="sensitivity"
        values=[
            {"name": "High", "metadata": {"backgroundColor": "red"}},
            {"name": "Medium", "metadata": {"backgroundColor": "yellow"}},
            {"name": "Low", "metadata": {"backgroundColor": "green"}}
        ]

    Returns:
        Dictionary containing the created label or error information.
    """
    logger.info(f"Creating governance label: {name}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        payload = {"name": name, "values": values}
        body, error = await _execute(client, "POST", "/governance/api/v1/labels", payload)
        if error:
            logger.error(f"Okta API error creating label '{name}': {error}")
            return {"error": str(error)}

        logger.info(f"Successfully created governance label: {name}")
        return body

    except Exception as e:
        logger.error(f"Exception creating label '{name}': {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_governance_label(ctx: Context, label_id: str, operations: list) -> dict:
    """Update a governance label using Okta patch operations.

    Supports updating the label key name, adding/removing/updating label values,
    and modifying background colors.

    Parameters:
        label_id (str, required): The ID of the label to update.
        operations (list, required): List of Okta patch operation objects.
            Each operation has "op" (must be "REPLACE"), "path", "value",
            and "refType" ("LABEL-CATEGORY" for name, "LABEL-VALUE" for values).

    Example — rename label:
        operations=[
            {"op": "REPLACE", "path": "/name", "value": "data-sensitivity", "refType": "LABEL-CATEGORY"}
        ]

    Returns:
        Dictionary containing the updated label or error information.
    """
    logger.info(f"Updating governance label: {label_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "PATCH", f"/governance/api/v1/labels/{label_id}", operations)
        if error:
            logger.error(f"Okta API error updating label {label_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated label: {label_id}")
        return body

    except Exception as e:
        logger.error(f"Exception updating label {label_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_governance_label(ctx: Context, label_id: str) -> dict:
    """Delete a governance label from the Okta organization.

    A label can only be deleted if none of its values are currently assigned
    to any resources. The user will be asked for confirmation before deletion.

    Parameters:
        label_id (str, required): The ID of the label to delete.

    Returns:
        Dictionary containing the result of the deletion or error information.
    """
    logger.warning(f"Deletion requested for governance label: {label_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _label_obj, _ = await _execute(_client_tmp, "GET", f"/governance/api/v1/labels/{label_id}")
        _label_name = _label_obj.get("name", "") if isinstance(_label_obj, dict) else ""
    except Exception:
        _label_name = ""
    _label_resource = f"'{_label_name}' ({label_id})" if _label_name else label_id

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_GOVERNANCE_LABEL.format(resource=_label_resource),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": (
                f"To confirm deletion of governance label {_label_resource}, please confirm. "
                "The label must have no values assigned to any resources."
            ),
            "label_id": label_id,
        },
    )

    if not outcome.used_elicitation:
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Label deletion cancelled for {label_id}")
        return {"message": "Label deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "DELETE", f"/governance/api/v1/labels/{label_id}")
        if error:
            logger.error(f"Okta API error deleting label {label_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted label: {label_id}")
        return {"message": f"Governance label {label_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception deleting label {label_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_labeled_resources(
    ctx: Context,
    filter: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List resources that have governance labels assigned.

    Parameters:
        filter (str, required): SCIM filter expression. Supported fields:
            - orn eq "orn:okta:..."  — specific resource by ORN
            - labelValueId eq "lblXXX"  — resources with a specific label value
            - resourceType eq "apps"  — filter by resource type
            (values: apps, groups, entitlement-values, collections)
            Operators can be combined with AND/OR.

            Examples:
              'labelValueId eq "lblo3v6xlwdtEX2il1d6" AND resourceType eq "apps"'
              'orn eq "orn:okta:idp:00o11ed...:apps:oidc:0oafxq..."'

        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max records per page (1–200, default 20).

    Returns:
        Dictionary containing labeled resources and pagination info.
    """
    logger.info("Listing labeled resources")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params: dict = {"filter": filter}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v1/resource-labels?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing labeled resources: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved labeled resources")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing labeled resources: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def assign_governance_labels(
    ctx: Context,
    resource_orns: list,
    label_value_ids: list,
) -> dict:
    """Assign governance label values to one or more resources.

    Resources are identified by their ORN (Okta Resource Name), e.g.:
      orn:okta:apps:{orgId}:apps:{appId}
      orn:okta:directory:{orgId}:groups:{groupId}

    Parameters:
        resource_orns (list, required): List of ORN strings identifying the
            resources to label.
        label_value_ids (list, required): List of label value IDs to assign
            to the specified resources.

    Returns:
        Dictionary containing the result of the assignment or error information.
    """
    logger.info(f"Assigning labels to {len(resource_orns)} resource(s)")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        payload = {"resourceOrns": resource_orns, "labelValueIds": label_value_ids}
        body, error = await _execute(client, "POST", "/governance/api/v1/resource-labels/assign", payload)
        if error:
            logger.error(f"Okta API error assigning labels: {error}")
            return {"error": str(error)}

        logger.info("Successfully assigned governance labels")
        return body or {"message": "Labels assigned successfully"}

    except Exception as e:
        logger.error(f"Exception assigning labels: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def unassign_governance_labels(
    ctx: Context,
    resource_orns: list,
    label_value_ids: list,
) -> dict:
    """Remove governance label values from one or more resources.

    Parameters:
        resource_orns (list, required): List of ORN strings identifying the
            resources to remove labels from (1–10 items).
        label_value_ids (list, required): List of label value IDs to remove
            from the specified resources (1–10 items).

    Returns:
        Dictionary containing the result or error information.
    """
    logger.info(f"Unassigning labels from {len(resource_orns)} resource(s)")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        payload = {"resourceOrns": resource_orns, "labelValueIds": label_value_ids}
        _, error = await _execute(client, "POST", "/governance/api/v1/resource-labels/unassign", payload)
        if error:
            logger.error(f"Okta API error unassigning labels: {error}")
            return {"error": str(error)}

        logger.info("Successfully unassigned governance labels")
        return {"message": "Labels unassigned successfully"}

    except Exception as e:
        logger.error(f"Exception unassigning labels: {type(e).__name__}: {e}")
        return {"error": str(e)}
