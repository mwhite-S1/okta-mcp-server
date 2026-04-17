# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Governance operations tools: async operation status polling."""

import json as _json
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


@mcp.tool()
async def get_governance_operation(ctx: Context, operation_id: str) -> dict:
    """Retrieve the status and result of an asynchronous governance operation.

    The operation ID is returned in the `_links` response of governance APIs
    that initiate async operations (such as campaign launches and bulk actions).
    Use this to poll for completion and retrieve results.

    Parameters:
        operation_id (str, required): The ID of the governance operation to retrieve.

    Returns:
        Dictionary containing the operation status and result, or error information.
    """
    logger.info(f"Getting governance operation: {operation_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/governance/api/v1/operations/{operation_id}")
        if error:
            logger.error(f"Okta API error getting operation {operation_id}: {error}")
            return {"error": str(error)}

        logger.info(f"Successfully retrieved governance operation: {operation_id}")
        return body

    except Exception as e:
        logger.error(f"Exception getting governance operation {operation_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
