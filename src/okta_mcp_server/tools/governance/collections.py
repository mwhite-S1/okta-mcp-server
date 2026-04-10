# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Governance collections tools: list, create, get, update, delete, and manage resources."""

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
async def list_collections(
    ctx: Context,
    filter: Optional[str] = None,
    include: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List governance collections in the Okta organization.

    Collections group resources (such as apps or groups) together so they can
    be managed, certified, or governed as a unit within Okta Governance workflows.

    Parameters:
        filter (str, optional): Filter expression. Supported operators:
            - name sw/co    (e.g. 'name sw "Sales"')
            - id eq         (e.g. 'id eq "col123"')
        include (str, optional): Extra fields to include. Use "counts" to
            include resource counts and assignment counts in the response.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of collections to return per page (1-200).

    Returns:
        Dictionary containing a list of collection objects and pagination info,
        or a dictionary with an "error" key on failure.
    """
    logger.info("Listing governance collections")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if filter:
            params["filter"] = filter
        if include:
            params["include"] = include
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = "/governance/api/v1/collections"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing collections: {error}")
            return {"error": str(error)}

        logger.info("Successfully retrieved governance collections")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing collections: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_collection(
    ctx: Context,
    name: str,
    description: Optional[str] = None,
) -> dict:
    """Create a governance collection in the Okta organization.

    A collection is a named grouping of resources used in governance workflows
    such as access certification campaigns and access request policies.

    Parameters:
        name (str, required): The display name for the new collection.
        description (str, optional): A human-readable description of the collection's
            purpose or membership criteria.

    Returns:
        Dictionary containing the created collection object, or a dictionary with
        an "error" key on failure.
    """
    logger.info(f"Creating governance collection: {name}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload: dict = {"name": name}
        if description is not None:
            payload["description"] = description

        body, error = await _execute(client, "POST", "/governance/api/v1/collections", payload)
        if error:
            logger.error(f"Okta API error creating collection '{name}': {error}")
            return {"error": str(error)}

        logger.info(f"Successfully created governance collection: {name}")
        return body

    except Exception as e:
        logger.error(f"Exception creating collection '{name}': {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_collection(ctx: Context, collection_id: str) -> dict:
    """Get a governance collection by ID.

    Parameters:
        collection_id (str, required): The unique ID of the collection to retrieve.

    Returns:
        Dictionary containing the collection details, or a dictionary with an
        "error" key on failure.
    """
    logger.info(f"Getting governance collection: {collection_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        body, error = await _execute(client, "GET", f"/governance/api/v1/collections/{collection_id}")
        if error:
            logger.error(f"Okta API error getting collection {collection_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved collection: {collection_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting collection {collection_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_collection(
    ctx: Context,
    collection_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """Update a governance collection by ID.

    Performs a full replacement (PUT) of the collection. Only fields provided
    will be included in the request body; omitted optional fields are not sent.

    Parameters:
        collection_id (str, required): The unique ID of the collection to update.
        name (str, optional): New display name for the collection.
        description (str, optional): New description for the collection.

    Returns:
        Dictionary containing the updated collection object, or a dictionary with
        an "error" key on failure.
    """
    logger.info(f"Updating governance collection: {collection_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description

        body, error = await _execute(
            client, "PUT", f"/governance/api/v1/collections/{collection_id}", payload
        )
        if error:
            logger.error(f"Okta API error updating collection {collection_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully updated collection: {collection_id}")
        return body

    except Exception as e:
        logger.error(f"Exception updating collection {collection_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_collection(ctx: Context, collection_id: str) -> dict:
    """Delete a governance collection by ID.

    Permanently removes the collection. The API returns 204 No Content on
    success. Any resources that were members of the collection are not deleted;
    only the collection grouping itself is removed.

    Parameters:
        collection_id (str, required): The unique ID of the collection to delete.

    Returns:
        Dictionary with a "message" key confirming deletion, or a dictionary
        with an "error" key on failure.
    """
    logger.warning(f"Deleting governance collection: {collection_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        _, error = await _execute(client, "DELETE", f"/governance/api/v1/collections/{collection_id}")
        if error:
            logger.error(f"Okta API error deleting collection {collection_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully deleted collection: {collection_id}")
        return {"message": f"Collection {collection_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Exception deleting collection {collection_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_collection_resources(
    ctx: Context,
    collection_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List the resources that belong to a governance collection.

    Resources are identified by their ORN (Okta Resource Name) and may
    represent apps, groups, entitlement values, or other governed objects.

    Parameters:
        collection_id (str, required): The unique ID of the collection whose
            resources should be listed.
        after (str, optional): Pagination cursor for the next page of results.
        limit (int, optional): Maximum number of resources to return per page.

    Returns:
        Dictionary containing a list of resource objects and pagination info,
        or a dictionary with an "error" key on failure.
    """
    logger.info(f"Listing resources for collection: {collection_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        params = {}
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit

        path = f"/governance/api/v1/collections/{collection_id}/resources"
        if params:
            path += f"?{urlencode(params)}"

        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Okta API error listing resources for collection {collection_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved resources for collection: {collection_id}")
        return body or {"data": []}

    except Exception as e:
        logger.error(f"Exception listing resources for collection {collection_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def add_collection_resources(
    ctx: Context,
    collection_id: str,
    resource_orns: list,
) -> dict:
    """Add resources to a governance collection.

    Resources are specified by their ORN (Okta Resource Name), for example:
      orn:okta:idp:{orgId}:apps:oidc:{appId}
      orn:okta:directory:{orgId}:groups:{groupId}

    Parameters:
        collection_id (str, required): The unique ID of the collection to add
            resources to.
        resource_orns (list, required): List of ORN strings identifying the
            resources to add to the collection.

    Returns:
        Dictionary containing the result of the addition, or a dictionary with
        an "error" key on failure.
    """
    logger.info(f"Adding {len(resource_orns)} resource(s) to collection: {collection_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        payload = {"resourceOrns": resource_orns}
        body, error = await _execute(
            client, "POST", f"/governance/api/v1/collections/{collection_id}/resources", payload
        )
        if error:
            logger.error(f"Okta API error adding resources to collection {collection_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully added resources to collection: {collection_id}")
        return body or {"message": f"Resources added to collection {collection_id} successfully"}

    except Exception as e:
        logger.error(f"Exception adding resources to collection {collection_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def remove_collection_resource(
    ctx: Context,
    collection_id: str,
    resource_id: str,
) -> dict:
    """Remove a resource from a governance collection.

    Removes the specified resource from the collection. The resource itself is
    not deleted from Okta; only its membership in the collection is removed.
    The API returns 204 No Content on success.

    Parameters:
        collection_id (str, required): The unique ID of the collection from which
            the resource should be removed.
        resource_id (str, required): The ID of the resource to remove from the
            collection.

    Returns:
        Dictionary with a "message" key confirming removal, or a dictionary with
        an "error" key on failure.
    """
    logger.warning(f"Removing resource {resource_id} from collection {collection_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)

        _, error = await _execute(
            client,
            "DELETE",
            f"/governance/api/v1/collections/{collection_id}/resources/{resource_id}",
        )
        if error:
            logger.error(
                f"Okta API error removing resource {resource_id} from collection {collection_id}: {error}"
            )
            return {"error": str(error)}

        logger.info(f"Successfully removed resource {resource_id} from collection {collection_id}")
        return {"message": f"Resource {resource_id} removed from collection {collection_id} successfully"}

    except Exception as e:
        logger.error(
            f"Exception removing resource {resource_id} from collection {collection_id}: {type(e).__name__}: {e}"
        )
        return {"error": str(e)}
