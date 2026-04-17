# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import json as _json
from typing import Any, Dict, Optional

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.validation import validate_ids


async def _execute(client, method: str, path: str, body: dict = None):
    request_executor = client.get_request_executor()
    url = f"{client.get_base_url()}{path}"
    request, error = await request_executor.create_request(method, url, body or {})
    if error:
        return None, None, error
    response, response_body, error = await request_executor.execute(request)
    if error:
        return None, None, error
    if not response_body:
        return response, None, None
    if isinstance(response_body, str):
        try:
            response_body = _json.loads(response_body)
        except Exception:
            pass
    return response, response_body, None


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def list_scope_consent_grants(
    ctx: Context,
    app_id: str,
    expand: Optional[str] = None,
) -> dict:
    """List all scope consent grants for an application.

    Returns all OAuth 2.0 scope consent grants that the app has been granted.

    Parameters:
        app_id (str, required): The ID of the application.
        expand (str, optional): Set to "scope" to include scope details.

    Returns:
        Dict with items (list of OAuth2ScopeConsentGrant objects) and total_fetched.
    """
    logger.info(f"Listing scope consent grants for application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if expand:
            kwargs["expand"] = expand

        path = f"/api/v1/apps/{app_id}/grants"
        if expand:
            path += f"?expand={expand}"
        _, body, err = await _execute(client, "GET", path)

        if err:
            logger.error(f"Error listing grants for app {app_id}: {err}")
            return {"error": str(err)}

        items = body if isinstance(body, list) else []
        logger.info(f"Retrieved {len(items)} grants for app {app_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing grants for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def grant_consent_to_scope(
    ctx: Context,
    app_id: str,
    grant: Dict[str, Any],
) -> dict:
    """Grant consent for an application to request an OAuth 2.0 scope.

    Parameters:
        app_id (str, required): The ID of the application.
        grant (dict, required): Scope consent grant object containing:
            - issuer (str, required): The issuer of the OAuth 2.0 scope.
            - scopeId (str, required): The OAuth 2.0 scope to grant.

    Returns:
        Dict containing the created OAuth2ScopeConsentGrant.
    """
    logger.info(f"Granting scope consent to application {app_id}: scope={grant.get('scopeId')}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, result, err = await _execute(client, "POST", f"/api/v1/apps/{app_id}/grants", grant)

        if err:
            logger.error(f"Error granting scope consent to app {app_id}: {err}")
            return {"error": str(err)}

        out = result if isinstance(result, dict) else {}
        logger.info(f"Granted scope consent to app {app_id}")
        return out

    except Exception as e:
        logger.error(f"Exception granting scope consent to app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "grant_id", error_return_type="dict")
async def get_scope_consent_grant(
    ctx: Context,
    app_id: str,
    grant_id: str,
    expand: Optional[str] = None,
) -> dict:
    """Retrieve a single scope consent grant for an application.

    Parameters:
        app_id (str, required): The ID of the application.
        grant_id (str, required): The ID of the scope consent grant to retrieve.
        expand (str, optional): Set to "scope" to include scope details.

    Returns:
        Dict containing the OAuth2ScopeConsentGrant details.
    """
    logger.info(f"Getting grant {grant_id} for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if expand:
            kwargs["expand"] = expand

        grant, _, err = await client.get_scope_consent_grant(app_id, grant_id, **kwargs)

        if err:
            logger.error(f"Error getting grant {grant_id} for app {app_id}: {err}")
            return {"error": str(err)}

        return grant.to_dict() if hasattr(grant, "to_dict") else grant

    except Exception as e:
        logger.error(f"Exception getting grant {grant_id} for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "grant_id", error_return_type="dict")
async def revoke_scope_consent_grant(
    ctx: Context,
    app_id: str,
    grant_id: str,
) -> dict:
    """Revoke a scope consent grant from an application.

    Revokes permission for the app to request the given OAuth 2.0 scope.

    Parameters:
        app_id (str, required): The ID of the application.
        grant_id (str, required): The ID of the scope consent grant to revoke.

    Returns:
        Dict confirming the revocation.
    """
    logger.warning(f"Revoking grant {grant_id} from application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.revoke_scope_consent_grant(app_id, grant_id)

        if err:
            logger.error(f"Error revoking grant {grant_id} from app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Revoked grant {grant_id} from app {app_id}")
        return {"message": f"Scope consent grant {grant_id} revoked from application {app_id}."}

    except Exception as e:
        logger.error(f"Exception revoking grant {grant_id} from app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
