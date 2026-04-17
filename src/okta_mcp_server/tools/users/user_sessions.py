# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import REVOKE_USER_SESSIONS
from okta_mcp_server.utils.validation import validate_ids


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def revoke_user_sessions(
    ctx: Context,
    user_id: str,
    oauth_tokens: bool = False,
    forget_devices: bool = False,
) -> dict:
    """Revoke all active sessions for a user (force logout from all devices).

    The user will be asked for confirmation before the operation proceeds.
    This immediately signs the user out of all active browser sessions.

    Parameters:
        user_id (str, required): The ID of the user whose sessions to revoke.
        oauth_tokens (bool, optional): If True, also revoke the user's active
            OAuth 2.0 access and refresh tokens. Default: False.
        forget_devices (bool, optional): If True, also clear the user's
            "remember this device" state. Default: False.

    Returns:
        Dict confirming sessions were revoked.
    """
    logger.warning(f"Session revocation requested for user {user_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _user_obj, _, _ = await _client_tmp.get_user(user_id)
        _user_login = (
            _user_obj.profile.login
            if hasattr(_user_obj, "profile") and hasattr(_user_obj.profile, "login")
            else (_user_obj.get("profile", {}) or {}).get("login", "") if isinstance(_user_obj, dict) else ""
        )
    except Exception:
        _user_login = ""
    _user_resource = f"'{_user_login}' ({user_id})" if _user_login else user_id

    fallback_payload = {
        "confirmation_required": True,
        "message": (
            f"To confirm revoking all sessions for user {_user_resource}, please explicitly confirm. "
            f"oauth_tokens={oauth_tokens}, forget_devices={forget_devices}."
        ),
        "user_id": user_id,
    }

    outcome = await elicit_or_fallback(
        ctx,
        message=REVOKE_USER_SESSIONS.format(resource=_user_resource),
        schema=DeleteConfirmation,
        fallback_payload=fallback_payload,
    )

    if not outcome.used_elicitation:
        logger.info(f"Elicitation unavailable for session revocation of user {user_id} — returning fallback")
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Session revocation cancelled for user {user_id}")
        return {"message": "Session revocation cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if oauth_tokens:
            kwargs["oauthTokens"] = oauth_tokens
        if forget_devices:
            kwargs["forgetDevices"] = forget_devices

        _, _, err = await client.revoke_user_sessions(user_id, **kwargs)

        if err:
            logger.error(f"Error revoking sessions for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Revoked all sessions for user {user_id}")
        return {"message": f"All sessions revoked for user {user_id}."}

    except Exception as e:
        logger.error(f"Exception revoking sessions for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
