# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Any, Dict, Optional

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.validation import validate_ids


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

        grants, _, err = await client.list_scope_consent_grants(app_id, **kwargs)

        if err:
            logger.error(f"Error listing grants for app {app_id}: {err}")
            return {"error": str(err)}

        items = [g.to_dict() if hasattr(g, "to_dict") else g for g in (grants or [])]
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
        result, _, err = await client.grant_consent_to_scope(app_id, grant)

        if err:
            logger.error(f"Error granting scope consent to app {app_id}: {err}")
            return {"error": str(err)}

        out = result.to_dict() if hasattr(result, "to_dict") else result
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
