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
@validate_ids("user_id", error_return_type="dict")
async def activate_user(
    ctx: Context,
    user_id: str,
    send_email: bool = True,
) -> dict:
    """Activate a user in the Okta organization.

    Activates a user with STAGED or DEPROVISIONED status. When send_email=True,
    Okta sends the user an activation email. When send_email=False, the response
    contains an activationUrl and activationToken that can be used to complete
    activation programmatically.

    Parameters:
        user_id (str, required): The ID of the user to activate.
        send_email (bool, optional): If True, Okta sends an activation email.
            If False, the activation token is returned in the response. Default: True.

    Returns:
        Dict containing the activation result. If send_email=False, includes
        activationToken and activationUrl.
    """
    logger.info(f"Activating user {user_id} (send_email={send_email})")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        token, _, err = await client.activate_user(user_id, send_email=send_email)

        if err:
            logger.error(f"Error activating user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Activated user {user_id}")
        if token and hasattr(token, "to_dict"):
            return token.to_dict()
        return {"message": f"User {user_id} activated successfully."}

    except Exception as e:
        logger.error(f"Exception activating user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def reactivate_user(
    ctx: Context,
    user_id: str,
    send_email: bool = True,
) -> dict:
    """Reactivate a user with PROVISIONED status.

    Reactivates a user that has already been activated but is in PROVISIONED
    status (e.g., their activation email expired). A new activation email or
    token is generated.

    Parameters:
        user_id (str, required): The ID of the user to reactivate.
        send_email (bool, optional): If True, Okta sends a reactivation email.
            If False, the activation token is returned in the response. Default: True.

    Returns:
        Dict containing the reactivation result. If send_email=False, includes
        activationToken and activationUrl.
    """
    logger.info(f"Reactivating user {user_id} (send_email={send_email})")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        token, _, err = await client.reactivate_user(user_id, send_email=send_email)

        if err:
            logger.error(f"Error reactivating user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Reactivated user {user_id}")
        if token and hasattr(token, "to_dict"):
            return token.to_dict()
        return {"message": f"User {user_id} reactivated successfully."}

    except Exception as e:
        logger.error(f"Exception reactivating user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def reset_factors(
    ctx: Context,
    user_id: str,
) -> dict:
    """Reset all MFA factors for a user.

    Removes all enrolled authenticator factors from a user, requiring them to
    re-enroll at next sign-in. The user's status is not changed.

    Parameters:
        user_id (str, required): The ID of the user whose factors to reset.

    Returns:
        Dict confirming the factors were reset.
    """
    logger.info(f"Resetting factors for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.reset_factors(user_id)

        if err:
            logger.error(f"Error resetting factors for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Reset factors for user {user_id}")
        return {"message": f"All factors reset for user {user_id}."}

    except Exception as e:
        logger.error(f"Exception resetting factors for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def suspend_user(
    ctx: Context,
    user_id: str,
) -> dict:
    """Suspend an active user.

    Suspends a user so they cannot sign in. The user's status changes to
    SUSPENDED. Use unsuspend_user to restore access.

    Parameters:
        user_id (str, required): The ID of the user to suspend.

    Returns:
        Dict confirming the user was suspended.
    """
    logger.info(f"Suspending user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.suspend_user(user_id)

        if err:
            logger.error(f"Error suspending user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Suspended user {user_id}")
        return {"message": f"User {user_id} suspended successfully."}

    except Exception as e:
        logger.error(f"Exception suspending user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def unlock_user(
    ctx: Context,
    user_id: str,
) -> dict:
    """Unlock a user who has been locked out.

    Unlocks a user with LOCKED_OUT status due to too many failed sign-in
    attempts. The user's status returns to ACTIVE.

    Parameters:
        user_id (str, required): The ID of the user to unlock.

    Returns:
        Dict confirming the user was unlocked.
    """
    logger.info(f"Unlocking user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.unlock_user(user_id)

        if err:
            logger.error(f"Error unlocking user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Unlocked user {user_id}")
        return {"message": f"User {user_id} unlocked successfully."}

    except Exception as e:
        logger.error(f"Exception unlocking user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def unsuspend_user(
    ctx: Context,
    user_id: str,
) -> dict:
    """Unsuspend a suspended user.

    Restores a SUSPENDED user to ACTIVE status so they can sign in again.

    Parameters:
        user_id (str, required): The ID of the user to unsuspend.

    Returns:
        Dict confirming the user was unsuspended.
    """
    logger.info(f"Unsuspending user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.unsuspend_user(user_id)

        if err:
            logger.error(f"Error unsuspending user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Unsuspended user {user_id}")
        return {"message": f"User {user_id} unsuspended successfully."}

    except Exception as e:
        logger.error(f"Exception unsuspending user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
