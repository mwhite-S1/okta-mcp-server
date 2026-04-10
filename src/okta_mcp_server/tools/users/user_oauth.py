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
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import REVOKE_TOKENS_FOR_CLIENT
from okta_mcp_server.utils.validation import validate_ids


@mcp.tool()
@validate_ids("user_id", "client_id", error_return_type="dict")
async def list_refresh_tokens_for_user_and_client(
    ctx: Context,
    user_id: str,
    client_id: str,
    expand: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all refresh tokens a user has for a specific OAuth 2.0 client app.

    Shows the active refresh tokens (and associated scopes) that a user has
    granted to a specific application.

    Parameters:
        user_id (str, required): The ID of the user.
        client_id (str, required): The OAuth 2.0 client ID of the application.
        expand (str, optional): Set to "scope" to include scope details in the response.
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max results per page.

    Returns:
        Dict with items (list of OAuth2RefreshToken objects) and total_fetched.
    """
    logger.info(f"Listing refresh tokens for user {user_id} and client {client_id}")

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

        tokens, _, err = await client.list_refresh_tokens_for_user_and_client(user_id, client_id, **kwargs)

        if err:
            logger.error(f"Error listing tokens for user {user_id} client {client_id}: {err}")
            return {"error": str(err)}

        items = [t.to_dict() if hasattr(t, "to_dict") else t for t in (tokens or [])]
        logger.info(f"Retrieved {len(items)} refresh token(s) for user {user_id} client {client_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing tokens for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "client_id", "token_id", error_return_type="dict")
async def get_refresh_token_for_user_and_client(
    ctx: Context,
    user_id: str,
    client_id: str,
    token_id: str,
    expand: Optional[str] = None,
) -> dict:
    """Retrieve a specific refresh token for a user and client.

    Parameters:
        user_id (str, required): The ID of the user.
        client_id (str, required): The OAuth 2.0 client ID of the application.
        token_id (str, required): The ID of the refresh token.
        expand (str, optional): Set to "scope" to include scope details.

    Returns:
        Dict containing the OAuth2RefreshToken details.
    """
    logger.info(f"Getting token {token_id} for user {user_id} client {client_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if expand:
            kwargs["expand"] = expand

        token, _, err = await client.get_refresh_token_for_user_and_client(user_id, client_id, token_id, **kwargs)

        if err:
            logger.error(f"Error getting token {token_id} for user {user_id}: {err}")
            return {"error": str(err)}

        return token.to_dict() if hasattr(token, "to_dict") else token

    except Exception as e:
        logger.error(f"Exception getting token {token_id} for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "client_id", error_return_type="dict")
async def revoke_tokens_for_user_and_client(
    ctx: Context,
    user_id: str,
    client_id: str,
) -> dict:
    """Revoke all refresh tokens a user has for a specific OAuth 2.0 client.

    The user will be prompted for confirmation before proceeding.
    This terminates all active sessions between this user and the app.

    Parameters:
        user_id (str, required): The ID of the user.
        client_id (str, required): The OAuth 2.0 client ID of the application.

    Returns:
        Dict confirming all tokens were revoked.
    """
    logger.warning(f"Revocation requested for all tokens of user {user_id} for client {client_id}")

    fallback_payload = {
        "confirmation_required": True,
        "message": (
            f"To confirm revoking all refresh tokens for client {client_id} "
            f"belonging to user {user_id}, please explicitly confirm."
        ),
        "user_id": user_id,
        "client_id": client_id,
    }

    outcome = await elicit_or_fallback(
        ctx,
        message=REVOKE_TOKENS_FOR_CLIENT.format(client_id=client_id, user_id=user_id),
        schema=DeleteConfirmation,
        fallback_payload=fallback_payload,
    )

    if not outcome.used_elicitation:
        logger.info("Elicitation unavailable for token revocation — returning fallback")
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Token revocation cancelled for user {user_id} client {client_id}")
        return {"message": "Token revocation cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.revoke_tokens_for_user_and_client(user_id, client_id)

        if err:
            logger.error(f"Error revoking tokens for user {user_id} client {client_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Revoked all tokens for user {user_id} client {client_id}")
        return {"message": f"All refresh tokens for client {client_id} revoked for user {user_id}."}

    except Exception as e:
        logger.error(f"Exception revoking tokens for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "client_id", "token_id", error_return_type="dict")
async def revoke_token_for_user_and_client(
    ctx: Context,
    user_id: str,
    client_id: str,
    token_id: str,
) -> dict:
    """Revoke a specific refresh token for a user and OAuth 2.0 client.

    Parameters:
        user_id (str, required): The ID of the user.
        client_id (str, required): The OAuth 2.0 client ID of the application.
        token_id (str, required): The ID of the refresh token to revoke.

    Returns:
        Dict confirming the token was revoked.
    """
    logger.info(f"Revoking token {token_id} for user {user_id} client {client_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.revoke_token_for_user_and_client(user_id, client_id, token_id)

        if err:
            logger.error(f"Error revoking token {token_id} for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Revoked token {token_id} for user {user_id} client {client_id}")
        return {"message": f"Token {token_id} revoked for user {user_id} client {client_id}."}

    except Exception as e:
        logger.error(f"Exception revoking token {token_id} for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
