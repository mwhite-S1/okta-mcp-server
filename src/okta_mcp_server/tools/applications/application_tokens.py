# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Optional

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.validation import validate_ids


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def list_application_tokens(
    ctx: Context,
    app_id: str,
    expand: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all OAuth 2.0 refresh tokens for an application.

    Parameters:
        app_id (str, required): The ID of the application.
        expand (str, optional): Set to "scope" to include scope details.
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max number of results per page.

    Returns:
        Dict with items (list of OAuth2RefreshToken objects) and total_fetched.
    """
    logger.info(f"Listing OAuth2 tokens for application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if expand:
            kwargs["expand"] = expand
        if after:
            kwargs["after"] = after
        if limit:
            kwargs["limit"] = limit

        tokens, _, err = await client.list_o_auth2_tokens_for_application(app_id, **kwargs)

        if err:
            logger.error(f"Error listing tokens for app {app_id}: {err}")
            return {"error": str(err)}

        items = [t.to_dict() if hasattr(t, "to_dict") else t for t in (tokens or [])]
        logger.info(f"Retrieved {len(items)} tokens for app {app_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing tokens for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "token_id", error_return_type="dict")
async def get_application_token(
    ctx: Context,
    app_id: str,
    token_id: str,
    expand: Optional[str] = None,
) -> dict:
    """Retrieve a specific OAuth 2.0 refresh token for an application.

    Parameters:
        app_id (str, required): The ID of the application.
        token_id (str, required): The ID of the refresh token to retrieve.
        expand (str, optional): Set to "scope" to include scope details.

    Returns:
        Dict containing the OAuth2RefreshToken details.
    """
    logger.info(f"Getting token {token_id} for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if expand:
            kwargs["expand"] = expand

        token, _, err = await client.get_o_auth2_token_for_application(app_id, token_id, **kwargs)

        if err:
            logger.error(f"Error getting token {token_id} for app {app_id}: {err}")
            return {"error": str(err)}

        return token.to_dict() if hasattr(token, "to_dict") else token

    except Exception as e:
        logger.error(f"Exception getting token {token_id} for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "token_id", error_return_type="dict")
async def revoke_application_token(
    ctx: Context,
    app_id: str,
    token_id: str,
) -> dict:
    """Revoke a specific OAuth 2.0 refresh token for an application.

    Any access tokens issued with this refresh token are also revoked.

    Parameters:
        app_id (str, required): The ID of the application.
        token_id (str, required): The ID of the refresh token to revoke.

    Returns:
        Dict confirming the revocation.
    """
    logger.warning(f"Revoking token {token_id} from application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.revoke_o_auth2_token_for_application(app_id, token_id)

        if err:
            logger.error(f"Error revoking token {token_id} from app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Revoked token {token_id} from app {app_id}")
        return {"message": f"Token {token_id} revoked from application {app_id}."}

    except Exception as e:
        logger.error(f"Exception revoking token {token_id} from app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def revoke_all_application_tokens(
    ctx: Context,
    app_id: str,
) -> dict:
    """Revoke all OAuth 2.0 refresh tokens for an application.

    Revokes all refresh tokens for the specified app. Any access tokens issued
    with these refresh tokens are also revoked. Access tokens issued without a
    refresh token are not affected.

    Parameters:
        app_id (str, required): The ID of the application.

    Returns:
        Dict confirming all tokens were revoked.
    """
    logger.warning(f"Revoking all OAuth2 tokens for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.revoke_o_auth2_tokens_for_application(app_id)

        if err:
            logger.error(f"Error revoking all tokens for app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Revoked all tokens for app {app_id}")
        return {"message": f"All OAuth 2.0 refresh tokens revoked for application {app_id}."}

    except Exception as e:
        logger.error(f"Exception revoking all tokens for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
