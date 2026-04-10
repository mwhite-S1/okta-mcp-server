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
@validate_ids("user_id", error_return_type="dict")
async def reset_password(
    ctx: Context,
    user_id: str,
    send_email: bool = True,
    revoke_sessions: bool = False,
) -> dict:
    """Reset a user's password.

    When send_email=True (default), Okta sends the user a password-reset email.
    When send_email=False, the response contains a resetPasswordUrl that an
    admin can share directly with the user.

    Parameters:
        user_id (str, required): The ID of the user.
        send_email (bool, optional): If True, Okta emails the reset link to the user.
            If False, returns the reset URL in the response. Default: True.
        revoke_sessions (bool, optional): If True, revokes the user's current sessions
            after the password is reset. Default: False.

    Returns:
        Dict. If send_email=False, contains resetPasswordUrl. Otherwise a confirmation.
    """
    logger.info(f"Resetting password for user {user_id} (send_email={send_email})")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {"sendEmail": send_email}
        if revoke_sessions:
            kwargs["revokeSessions"] = revoke_sessions

        token, _, err = await client.reset_password(user_id, **kwargs)

        if err:
            logger.error(f"Error resetting password for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Reset password for user {user_id}")
        if token and hasattr(token, "to_dict"):
            return token.to_dict()
        return {"message": f"Password reset email sent to user {user_id}."}

    except Exception as e:
        logger.error(f"Exception resetting password for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def expire_password(
    ctx: Context,
    user_id: str,
) -> dict:
    """Expire a user's current password.

    Forces the user to change their password at their next login attempt.
    The user's status changes to PASSWORD_EXPIRED.

    Parameters:
        user_id (str, required): The ID of the user.

    Returns:
        Dict containing the updated user object.
    """
    logger.info(f"Expiring password for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        user, _, err = await client.expire_password(user_id)

        if err:
            logger.error(f"Error expiring password for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Expired password for user {user_id}")
        return user.to_dict() if hasattr(user, "to_dict") else {"message": f"Password expired for user {user_id}."}

    except Exception as e:
        logger.error(f"Exception expiring password for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def expire_password_with_temp_password(
    ctx: Context,
    user_id: str,
    revoke_sessions: bool = False,
) -> dict:
    """Expire a user's password and return a temporary password.

    Sets the user's status to PASSWORD_EXPIRED and returns a one-time
    temporary password that an admin can give to the user. The user must
    change this temporary password on their next login.

    Parameters:
        user_id (str, required): The ID of the user.
        revoke_sessions (bool, optional): If True, revoke current sessions. Default: False.

    Returns:
        Dict containing the tempPassword field.
    """
    logger.info(f"Expiring password with temp for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if revoke_sessions:
            kwargs["revokeSessions"] = revoke_sessions

        temp, _, err = await client.expire_password_and_get_temporary_password(user_id, **kwargs)

        if err:
            logger.error(f"Error expiring password with temp for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Expired password and generated temp password for user {user_id}")
        return temp.to_dict() if hasattr(temp, "to_dict") else {"message": f"Temp password generated for user {user_id}."}

    except Exception as e:
        logger.error(f"Exception expiring password with temp for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def change_password(
    ctx: Context,
    user_id: str,
    old_password: str,
    new_password: str,
    strict: bool = False,
) -> dict:
    """Change a user's password (requires current password).

    Updates the password using the user's existing credentials. For an admin
    reset without requiring the old password, use reset_password instead.

    Parameters:
        user_id (str, required): The ID of the user.
        old_password (str, required): The user's current password.
        new_password (str, required): The new password to set.
        strict (bool, optional): If True, enforces password policy strictly. Default: False.

    Returns:
        Dict containing the updated UserCredentials.
    """
    logger.info(f"Changing password for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body = {
            "oldPassword": {"value": old_password},
            "newPassword": {"value": new_password},
        }
        kwargs = {}
        if strict:
            kwargs["strict"] = strict

        creds, _, err = await client.change_password(user_id, body, **kwargs)

        if err:
            logger.error(f"Error changing password for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Changed password for user {user_id}")
        return creds.to_dict() if hasattr(creds, "to_dict") else {"message": f"Password changed for user {user_id}."}

    except Exception as e:
        logger.error(f"Exception changing password for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def forgot_password(
    ctx: Context,
    user_id: str,
    send_email: Optional[bool] = None,
) -> dict:
    """Initiate the forgot-password flow for a user.

    Sends a password-reset email to the user's registered email address, or
    returns a recovery URL if send_email=False (for programmatic flows).

    Parameters:
        user_id (str, required): The ID of the user.
        send_email (bool, optional): If True, send email. If False, return recovery URL.
            If omitted, uses the org's default behaviour.

    Returns:
        Dict. If send_email=False, contains a recovery URL. Otherwise a confirmation.
    """
    logger.info(f"Starting forgot-password flow for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if send_email is not None:
            kwargs["sendEmail"] = send_email

        result, _, err = await client.forgot_password(user_id, **kwargs)

        if err:
            logger.error(f"Error in forgot-password for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Initiated forgot-password for user {user_id}")
        if result and hasattr(result, "to_dict"):
            return result.to_dict()
        return {"message": f"Forgot-password flow initiated for user {user_id}."}

    except Exception as e:
        logger.error(f"Exception in forgot-password for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def change_recovery_question(
    ctx: Context,
    user_id: str,
    password: str,
    recovery_question: str,
    recovery_answer: str,
) -> dict:
    """Update a user's recovery question and answer.

    Requires the user's current password for verification.

    Parameters:
        user_id (str, required): The ID of the user.
        password (str, required): The user's current password for verification.
        recovery_question (str, required): The new security question.
        recovery_answer (str, required): The answer to the new security question.

    Returns:
        Dict containing the updated UserCredentials.
    """
    logger.info(f"Changing recovery question for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body = {
            "password": {"value": password},
            "recovery_question": {
                "question": recovery_question,
                "answer": recovery_answer,
            },
        }

        creds, _, err = await client.change_recovery_question(user_id, body)

        if err:
            logger.error(f"Error changing recovery question for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Changed recovery question for user {user_id}")
        return creds.to_dict() if hasattr(creds, "to_dict") else {"message": f"Recovery question updated for user {user_id}."}

    except Exception as e:
        logger.error(f"Exception changing recovery question for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
