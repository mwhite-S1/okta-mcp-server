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
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import UNENROLL_FACTOR
from okta_mcp_server.utils.validation import validate_ids


async def _execute(client, method: str, path: str, body: dict = None):
    """Make a direct API call bypassing SDK Pydantic deserialization."""
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
@validate_ids("user_id", error_return_type="dict")
async def list_factors(
    ctx: Context,
    user_id: str,
) -> dict:
    """List all enrolled MFA factors for a user.

    Returns all authenticator factors (TOTP, SMS, push, security key, etc.)
    that a user has enrolled, along with their status and metadata.

    Uses a direct API call to avoid SDK Pydantic deserialization errors on
    non-standard factor types (e.g. signed_nonce, webauthn).

    Parameters:
        user_id (str, required): The ID of the user.

    Returns:
        Dict with items (list of factor objects) and total_fetched.
    """
    logger.info(f"Listing factors for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body, err = await _execute(client, "GET", f"/api/v1/users/{user_id}/factors")

        if err:
            logger.error(f"Error listing factors for user {user_id}: {err}")
            return {"error": str(err)}

        items = body if isinstance(body, list) else []
        logger.info(f"Retrieved {len(items)} factor(s) for user {user_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing factors for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def list_supported_factors(
    ctx: Context,
    user_id: str,
) -> dict:
    """List all MFA factor types that a user is eligible to enroll.

    Returns the authenticator types available for enrollment based on the
    user's profile, group membership, and org policy.

    Parameters:
        user_id (str, required): The ID of the user.

    Returns:
        Dict with items (list of supported factor types) and total_fetched.
    """
    logger.info(f"Listing supported factors for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        factors, _, err = await client.list_supported_factors(user_id)

        if err:
            logger.error(f"Error listing supported factors for user {user_id}: {err}")
            return {"error": str(err)}

        items = [f.to_dict() if hasattr(f, "to_dict") else f for f in (factors or [])]
        logger.info(f"Retrieved {len(items)} supported factor(s) for user {user_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing supported factors for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def list_supported_security_questions(
    ctx: Context,
    user_id: str,
) -> dict:
    """List the security questions available for a user to enroll.

    Returns the list of predefined security questions the user can choose
    from when enrolling a security question factor.

    Parameters:
        user_id (str, required): The ID of the user.

    Returns:
        Dict with items (list of security question objects) and total_fetched.
    """
    logger.info(f"Listing supported security questions for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        questions, _, err = await client.list_supported_security_questions(user_id)

        if err:
            logger.error(f"Error listing security questions for user {user_id}: {err}")
            return {"error": str(err)}

        items = [q.to_dict() if hasattr(q, "to_dict") else q for q in (questions or [])]
        logger.info(f"Retrieved {len(items)} security question(s) for user {user_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing security questions for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "factor_id", error_return_type="dict")
async def get_factor(
    ctx: Context,
    user_id: str,
    factor_id: str,
) -> dict:
    """Retrieve a specific enrolled factor for a user.

    Parameters:
        user_id (str, required): The ID of the user.
        factor_id (str, required): The ID of the factor to retrieve.

    Returns:
        Dict containing the UserFactor details including factorType, provider, and status.
    """
    logger.info(f"Getting factor {factor_id} for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        factor, _, err = await client.get_factor(user_id, factor_id)

        if err:
            logger.error(f"Error getting factor {factor_id} for user {user_id}: {err}")
            return {"error": str(err)}

        return factor.to_dict() if hasattr(factor, "to_dict") else factor

    except Exception as e:
        logger.error(f"Exception getting factor {factor_id} for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", error_return_type="dict")
async def enroll_factor(
    ctx: Context,
    user_id: str,
    factor: Dict[str, Any],
    activate: bool = False,
    update_phone: bool = False,
    template_id: Optional[str] = None,
) -> dict:
    """Enroll a user in an MFA factor.

    Initiates factor enrollment for a user. Some factors (e.g. TOTP) require
    an additional activation step after enrollment.

    Parameters:
        user_id (str, required): The ID of the user.
        factor (dict, required): Factor configuration. Common shapes:
            TOTP:    {"factorType": "token:software:totp", "provider": "GOOGLE"}
            SMS:     {"factorType": "sms", "provider": "OKTA", "profile": {"phoneNumber": "+15551234567"}}
            Email:   {"factorType": "email", "provider": "OKTA", "profile": {"email": "user@example.com"}}
            Call:    {"factorType": "call", "provider": "OKTA", "profile": {"phoneNumber": "+15551234567"}}
            Push:    {"factorType": "push", "provider": "OKTA"}
            Question: {"factorType": "question", "provider": "OKTA",
                       "profile": {"question": "disliked_food", "answer": "anchovies"}}
        activate (bool, optional): If True, automatically activate the factor if possible. Default: False.
        update_phone (bool, optional): If True, update the user's phone if it changed. Default: False.
        template_id (str, optional): SMS template ID for custom SMS messages.

    Returns:
        Dict containing the enrolled factor with activation details if applicable.
    """
    logger.info(f"Enrolling factor for user {user_id}: {factor.get('factorType', 'unknown')}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if activate:
            kwargs["activate"] = activate
        if update_phone:
            kwargs["updatePhone"] = update_phone
        if template_id:
            kwargs["templateId"] = template_id

        enrolled, _, err = await client.enroll_factor(user_id, factor, **kwargs)

        if err:
            logger.error(f"Error enrolling factor for user {user_id}: {err}")
            return {"error": str(err)}

        out = enrolled.to_dict() if hasattr(enrolled, "to_dict") else enrolled
        logger.info(f"Enrolled factor {out.get('id', 'unknown')} for user {user_id}")
        return out

    except Exception as e:
        logger.error(f"Exception enrolling factor for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "factor_id", error_return_type="dict")
async def activate_factor(
    ctx: Context,
    user_id: str,
    factor_id: str,
    activation: Dict[str, Any],
) -> dict:
    """Activate a factor after enrollment.

    Completes the factor enrollment for factors that require a verification
    step (e.g. TOTP requires entering the first OTP code, email requires
    clicking a link or entering a code).

    Parameters:
        user_id (str, required): The ID of the user.
        factor_id (str, required): The ID of the factor to activate.
        activation (dict, required): Activation payload. Shape depends on factor type:
            TOTP:  {"passCode": "123456"}
            Email: {"passCode": "123456"}
            SMS:   {"passCode": "123456"}

    Returns:
        Dict containing the activated factor.
    """
    logger.info(f"Activating factor {factor_id} for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        # Use direct API call — SDK's UserFactorActivateRequest model only has
        # useNumberMatchingChallenge (push factors) and strips passCode for TOTP.
        body, err = await _execute(
            client, "POST",
            f"/api/v1/users/{user_id}/factors/{factor_id}/lifecycle/activate",
            activation
        )

        if err:
            logger.error(f"Error activating factor {factor_id} for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Activated factor {factor_id} for user {user_id}")
        return body or {"message": f"Factor {factor_id} activated successfully"}

    except Exception as e:
        logger.error(f"Exception activating factor {factor_id} for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "factor_id", error_return_type="dict")
async def unenroll_factor(
    ctx: Context,
    user_id: str,
    factor_id: str,
    remove_recovery_enrollment: bool = False,
) -> dict:
    """Unenroll (delete) a specific MFA factor from a user.

    The user will be prompted for confirmation before the factor is removed.

    Parameters:
        user_id (str, required): The ID of the user.
        factor_id (str, required): The ID of the factor to unenroll.
        remove_recovery_enrollment (bool, optional): If True, also remove the
            factor if it is used as a recovery authenticator. Default: False.

    Returns:
        Dict confirming the factor was unenrolled.
    """
    logger.warning(f"Unenroll requested for factor {factor_id} from user {user_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _factor_obj, _, _ = await _client_tmp.get_factor(user_id, factor_id)
        _factor_type = (
            _factor_obj.factorType
            if hasattr(_factor_obj, "factorType")
            else (_factor_obj.get("factorType", "") if isinstance(_factor_obj, dict) else "")
        )
    except Exception:
        _factor_type = ""
    try:
        _user_obj, _, _ = await _client_tmp.get_user(user_id)
        _user_login = (
            _user_obj.profile.login
            if hasattr(_user_obj, "profile") and hasattr(_user_obj.profile, "login")
            else (_user_obj.get("profile", {}) or {}).get("login", "") if isinstance(_user_obj, dict) else ""
        )
    except Exception:
        _user_login = ""
    _factor_resource = f"'{_factor_type}' ({factor_id})" if _factor_type else factor_id
    _user_resource = f"'{_user_login}' ({user_id})" if _user_login else user_id

    fallback_payload = {
        "confirmation_required": True,
        "message": (
            f"To confirm unenrolling factor {_factor_resource} from user {_user_resource}, "
            "please explicitly confirm."
        ),
        "user_id": user_id,
        "factor_id": factor_id,
    }

    outcome = await elicit_or_fallback(
        ctx,
        message=UNENROLL_FACTOR.format(resource=_factor_resource, user_resource=_user_resource),
        schema=DeleteConfirmation,
        fallback_payload=fallback_payload,
    )

    if not outcome.used_elicitation:
        logger.info(f"Elicitation unavailable for factor unenroll — returning fallback")
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Factor unenroll cancelled for factor {factor_id} from user {user_id}")
        return {"message": "Factor unenroll cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if remove_recovery_enrollment:
            kwargs["removeRecoveryEnrollment"] = remove_recovery_enrollment

        _, _, err = await client.unenroll_factor(user_id, factor_id, **kwargs)

        if err:
            logger.error(f"Error unenrolling factor {factor_id} from user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Unenrolled factor {factor_id} from user {user_id}")
        return {"message": f"Factor {factor_id} unenrolled from user {user_id}."}

    except Exception as e:
        logger.error(f"Exception unenrolling factor {factor_id} from user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "factor_id", error_return_type="dict")
async def verify_factor(
    ctx: Context,
    user_id: str,
    factor_id: str,
    verification: Optional[Dict[str, Any]] = None,
) -> dict:
    """Verify a user's enrolled factor (admin-initiated challenge).

    Triggers a factor verification challenge or validates a provided passcode.
    Useful for testing that a factor is working correctly.

    Parameters:
        user_id (str, required): The ID of the user.
        factor_id (str, required): The ID of the factor to verify.
        verification (dict, optional): Verification payload:
            For passcode-based: {"passCode": "123456"}
            For push: {} (triggers push notification)

    Returns:
        Dict containing the verification result and transaction status.
    """
    logger.info(f"Verifying factor {factor_id} for user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        # Use direct API call — SDK's UserFactorVerifyRequest model only has
        # useNumberMatchingChallenge (push factors) and strips passCode for TOTP.
        body, err = await _execute(
            client, "POST",
            f"/api/v1/users/{user_id}/factors/{factor_id}/verify",
            verification or {}
        )

        if err:
            logger.error(f"Error verifying factor {factor_id} for user {user_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Verified factor {factor_id} for user {user_id}")
        return body or {"message": f"Factor {factor_id} verification initiated for user {user_id}."}

    except Exception as e:
        logger.error(f"Exception verifying factor {factor_id} for user {user_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "factor_id", error_return_type="dict")
async def resend_enroll_factor(
    ctx: Context,
    user_id: str,
    factor_id: str,
    factor: Dict[str, Any],
    template_id: Optional[str] = None,
) -> dict:
    """Resend the enrollment challenge for a pending factor.

    Used when a user didn't receive the enrollment SMS/email. Triggers
    a new delivery of the enrollment passcode.

    Parameters:
        user_id (str, required): The ID of the user.
        factor_id (str, required): The ID of the pending factor.
        factor (dict, required): The factor object (same shape as enroll_factor).
        template_id (str, optional): SMS template ID for custom SMS messages.

    Returns:
        Dict containing the factor with updated enrollment details.
    """
    logger.info(f"Resending enrollment for factor {factor_id} of user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if template_id:
            kwargs["templateId"] = template_id

        result, _, err = await client.resend_enroll_factor(user_id, factor_id, factor, **kwargs)

        if err:
            logger.error(f"Error resending enrollment for factor {factor_id}: {err}")
            return {"error": str(err)}

        out = result.to_dict() if hasattr(result, "to_dict") else result
        logger.info(f"Resent enrollment challenge for factor {factor_id} of user {user_id}")
        return out

    except Exception as e:
        logger.error(f"Exception resending enrollment for factor {factor_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("user_id", "factor_id", "transaction_id", error_return_type="dict")
async def get_factor_transaction_status(
    ctx: Context,
    user_id: str,
    factor_id: str,
    transaction_id: str,
) -> dict:
    """Get the status of an async factor transaction (e.g. push notification).

    After triggering a push factor verification, poll this endpoint to check
    whether the user approved or rejected the push.

    Parameters:
        user_id (str, required): The ID of the user.
        factor_id (str, required): The ID of the factor.
        transaction_id (str, required): The transaction ID from the verify_factor response.

    Returns:
        Dict containing the transaction status (WAITING, SUCCESS, REJECTED, TIMEOUT).
    """
    logger.info(f"Getting transaction {transaction_id} status for factor {factor_id} of user {user_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        result, _, err = await client.get_factor_transaction_status(user_id, factor_id, transaction_id)

        if err:
            logger.error(f"Error getting transaction status {transaction_id}: {err}")
            return {"error": str(err)}

        return result.to_dict() if hasattr(result, "to_dict") else result

    except Exception as e:
        logger.error(f"Exception getting transaction status {transaction_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
