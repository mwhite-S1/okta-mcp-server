# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Authenticator management tools.

Covers /api/v1/authenticators — list, create, replace, activate/deactivate
authenticators and their methods, and manage custom WebAuthn AAGUIDs.
"""

import json as _json
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import DELETE_CUSTOM_AAGUID


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


# ---------------------------------------------------------------------------
# Authenticators — core CRUD
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_authenticators(
    ctx: Context,
) -> dict:
    """List all authenticators configured in the organization.

    Returns all authenticators regardless of status. Authenticators represent
    the individual factors available for use in sign-on and enrollment policies
    (e.g. password, email, Okta Verify TOTP/push, WebAuthn, phone SMS/voice,
    security question, YubiKey).

    Returns:
        Dict with items (list of Authenticator objects) and total_fetched.
    """
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", "/api/v1/authenticators")
        if error:
            logger.error(f"Error listing authenticators: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else (body or {}).get("value", [body] if body else [])
        logger.info(f"Retrieved {len(items)} authenticator(s)")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing authenticators: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_authenticator(
    ctx: Context,
    authenticator_data: Dict[str, Any],
    activate: Optional[bool] = None,
) -> dict:
    """Create a new authenticator in the organization.

    Creates an authenticator that can then be added to enrollment or sign-on
    policies. The authenticator starts in INACTIVE status unless activate=True.

    Parameters:
        authenticator_data (dict, required): Authenticator configuration object.
            Required fields:
            - key (str): Authenticator type key, one of:
                "okta_email", "okta_password", "okta_verify", "onprem_mfa",
                "phone_number", "security_question", "webauthn", "yubikey_token",
                "custom_otp", "google_otp", "smart_card_idp", "duo", "external_idp"
            - name (str): Display name for the authenticator.
            Optional fields:
            - settings (dict): Type-specific settings (e.g. algorithm, passCode length).
            - provider (dict): Provider configuration (required for some types).
            Example for email OTP:
                {"key": "okta_email", "name": "Email", "settings": {"allowedFor": "any"}}
        activate (bool, optional): Immediately activate after creation. Default: False.

    Returns:
        Dict containing the created Authenticator object.
    """
    logger.info(f"Creating authenticator: {authenticator_data.get('name', 'unknown')}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = "/api/v1/authenticators"
        if activate is not None:
            path += f"?activate={str(activate).lower()}"
        body, error = await _execute(client, "POST", path, authenticator_data)
        if error:
            logger.error(f"Error creating authenticator: {error}")
            return {"error": str(error)}
        logger.info(f"Created authenticator: {(body or {}).get('id', 'unknown')}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception creating authenticator: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_authenticator(
    ctx: Context,
    authenticator_id: str,
) -> dict:
    """Retrieve an authenticator by ID.

    Parameters:
        authenticator_id (str, required): The ID of the authenticator.

    Returns:
        Dict containing the Authenticator object with id, key, name, status,
        type, settings, provider, and _links.
    """
    logger.info(f"Getting authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/authenticators/{authenticator_id}")
        if error:
            logger.error(f"Error getting authenticator {authenticator_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception getting authenticator {authenticator_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def replace_authenticator(
    ctx: Context,
    authenticator_id: str,
    authenticator_data: Dict[str, Any],
) -> dict:
    """Replace (full update) an authenticator's configuration.

    Replaces all writable fields of the authenticator. The key and type fields
    cannot be changed after creation.

    Parameters:
        authenticator_id (str, required): The ID of the authenticator to update.
        authenticator_data (dict, required): Full authenticator configuration.
            Required: name (str).
            Optional: settings (dict), provider (dict).

    Returns:
        Dict containing the updated Authenticator object.
    """
    logger.info(f"Replacing authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "PUT", f"/api/v1/authenticators/{authenticator_id}", authenticator_data)
        if error:
            logger.error(f"Error replacing authenticator {authenticator_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Replaced authenticator {authenticator_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception replacing authenticator {authenticator_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def activate_authenticator(
    ctx: Context,
    authenticator_id: str,
) -> dict:
    """Activate an authenticator.

    Makes the authenticator available to be added to enrollment and sign-on policies.
    The authenticator must be in INACTIVE status.

    Parameters:
        authenticator_id (str, required): The ID of the authenticator to activate.

    Returns:
        Dict containing the updated Authenticator with status ACTIVE.
    """
    logger.info(f"Activating authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", f"/api/v1/authenticators/{authenticator_id}/lifecycle/activate")
        if error:
            logger.error(f"Error activating authenticator {authenticator_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Activated authenticator {authenticator_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception activating authenticator {authenticator_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def deactivate_authenticator(
    ctx: Context,
    authenticator_id: str,
) -> dict:
    """Deactivate an authenticator.

    Removes the authenticator from all enrollment and sign-on policies it is used in.
    Only authenticators that are not the sole active factor in a required policy
    can be deactivated.

    Parameters:
        authenticator_id (str, required): The ID of the authenticator to deactivate.

    Returns:
        Dict containing the updated Authenticator with status INACTIVE.
    """
    logger.info(f"Deactivating authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", f"/api/v1/authenticators/{authenticator_id}/lifecycle/deactivate")
        if error:
            logger.error(f"Error deactivating authenticator {authenticator_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Deactivated authenticator {authenticator_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception deactivating authenticator {authenticator_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Authenticator Methods
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_authenticator_methods(
    ctx: Context,
    authenticator_id: str,
) -> dict:
    """List all methods for an authenticator.

    Methods define how an authenticator verifies the user (e.g. the Okta Verify
    authenticator has push, totp, and signed_nonce methods).

    Parameters:
        authenticator_id (str, required): The ID of the authenticator.

    Returns:
        Dict with items (list of AuthenticatorMethod objects) and total_fetched.
        Each method has: type, status, settings (algorithm, timeIntervalInSeconds, etc.).
    """
    logger.info(f"Listing methods for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/authenticators/{authenticator_id}/methods")
        if error:
            logger.error(f"Error listing methods for authenticator {authenticator_id}: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else (body or {}).get("value", [body] if body else [])
        logger.info(f"Retrieved {len(items)} method(s) for authenticator {authenticator_id}")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing authenticator methods: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_authenticator_method(
    ctx: Context,
    authenticator_id: str,
    method_type: str,
) -> dict:
    """Retrieve a specific method for an authenticator.

    Parameters:
        authenticator_id (str, required): The ID of the authenticator.
        method_type (str, required): The method type, one of:
            "cert", "duo", "email", "idp", "password", "push", "signed_nonce",
            "security_question", "sms", "totp", "token", "voice", "webauthn"

    Returns:
        Dict containing the AuthenticatorMethod with type, status, and settings.
    """
    logger.info(f"Getting method {method_type} for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/authenticators/{authenticator_id}/methods/{method_type}")
        if error:
            logger.error(f"Error getting method {method_type} for authenticator {authenticator_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception getting authenticator method: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def replace_authenticator_method(
    ctx: Context,
    authenticator_id: str,
    method_type: str,
    method_data: Dict[str, Any],
) -> dict:
    """Replace (full update) a method's configuration for an authenticator.

    Updates method-level settings such as TOTP algorithm, time step, or
    FIDO2 allowed user verification modes.

    Parameters:
        authenticator_id (str, required): The ID of the authenticator.
        method_type (str, required): The method type (e.g. "totp", "push", "webauthn").
        method_data (dict, required): Method configuration. Key fields vary by type:
            For totp: {"settings": {"algorithm": "HMacSHA256", "timeIntervalInSeconds": 30}}
            For webauthn: {"settings": {"userVerification": "PREFERRED"}}

    Returns:
        Dict containing the updated AuthenticatorMethod.
    """
    logger.info(f"Replacing method {method_type} for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "PUT",
            f"/api/v1/authenticators/{authenticator_id}/methods/{method_type}",
            method_data,
        )
        if error:
            logger.error(f"Error replacing method {method_type} for authenticator {authenticator_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Replaced method {method_type} for authenticator {authenticator_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception replacing authenticator method: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def activate_authenticator_method(
    ctx: Context,
    authenticator_id: str,
    method_type: str,
) -> dict:
    """Activate a method for an authenticator.

    Parameters:
        authenticator_id (str, required): The ID of the authenticator.
        method_type (str, required): The method type to activate (e.g. "push", "totp").

    Returns:
        Dict containing the updated AuthenticatorMethod with status ACTIVE.
    """
    logger.info(f"Activating method {method_type} for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/authenticators/{authenticator_id}/methods/{method_type}/lifecycle/activate",
        )
        if error:
            logger.error(f"Error activating method {method_type}: {error}")
            return {"error": str(error)}
        logger.info(f"Activated method {method_type} for authenticator {authenticator_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception activating authenticator method: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def deactivate_authenticator_method(
    ctx: Context,
    authenticator_id: str,
    method_type: str,
) -> dict:
    """Deactivate a method for an authenticator.

    Parameters:
        authenticator_id (str, required): The ID of the authenticator.
        method_type (str, required): The method type to deactivate (e.g. "push", "totp").

    Returns:
        Dict containing the updated AuthenticatorMethod with status INACTIVE.
    """
    logger.info(f"Deactivating method {method_type} for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/authenticators/{authenticator_id}/methods/{method_type}/lifecycle/deactivate",
        )
        if error:
            logger.error(f"Error deactivating method {method_type}: {error}")
            return {"error": str(error)}
        logger.info(f"Deactivated method {method_type} for authenticator {authenticator_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception deactivating authenticator method: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def verify_rp_id_domain(
    ctx: Context,
    authenticator_id: str,
    web_authn_method_type: str,
    rp_id: str,
) -> dict:
    """Verify a Relying Party (RP) ID domain for a WebAuthn authenticator method.

    Verifies that the given RP ID domain is valid and resolvable for the WebAuthn
    authenticator. Used to validate custom RP IDs before configuring them.

    Parameters:
        authenticator_id (str, required): The ID of the WebAuthn authenticator.
        web_authn_method_type (str, required): The WebAuthn method type (e.g. "webauthn").
        rp_id (str, required): The Relying Party ID domain to verify (e.g. "example.com").

    Returns:
        Dict with verification result.
    """
    logger.info(f"Verifying RP ID domain '{rp_id}' for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = (
            f"/api/v1/authenticators/{authenticator_id}"
            f"/methods/{web_authn_method_type}/verify-rp-id-domain"
        )
        body, error = await _execute(client, "POST", path, {"rpId": rp_id})
        if error:
            logger.error(f"Error verifying RP ID domain: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception verifying RP ID domain: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Custom AAGUIDs (WebAuthn hardware key allowlisting)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_custom_aaguids(
    ctx: Context,
    authenticator_id: str,
    after: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """List all custom AAGUIDs for a WebAuthn authenticator.

    AAGUIDs (Authenticator Attestation Globally Unique Identifiers) identify
    specific hardware security key models (e.g. YubiKey 5 NFC). Configuring
    custom AAGUIDs restricts WebAuthn enrollment to specific hardware key models.

    Parameters:
        authenticator_id (str, required): The ID of the WebAuthn authenticator.
        after (str, optional): Pagination cursor for the next page.
        limit (int, optional): Max results per page.

    Returns:
        Dict with items (list of AAGUID objects) and total_fetched.
    """
    logger.info(f"Listing custom AAGUIDs for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        params = {}
        if after:
            params["after"] = after
        if limit is not None:
            params["limit"] = str(limit)
        path = f"/api/v1/authenticators/{authenticator_id}/aaguids"
        if params:
            path += f"?{urlencode(params)}"
        body, error = await _execute(client, "GET", path)
        if error:
            logger.error(f"Error listing custom AAGUIDs: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else (body or {}).get("value", [])
        logger.info(f"Retrieved {len(items)} custom AAGUID(s)")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing custom AAGUIDs: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def create_custom_aaguid(
    ctx: Context,
    authenticator_id: str,
    aaguid: str,
    name: str,
) -> dict:
    """Add a custom AAGUID to a WebAuthn authenticator's allowlist.

    Allows a specific hardware security key model to be enrolled with this
    WebAuthn authenticator. The AAGUID is a UUID that identifies the key model.

    Parameters:
        authenticator_id (str, required): The ID of the WebAuthn authenticator.
        aaguid (str, required): The AAGUID UUID identifying the hardware key model
            (e.g. "2fc0579f-8113-47ea-b116-bb5a8db9202a" for YubiKey 5 NFC).
        name (str, required): Display name for this AAGUID entry.

    Returns:
        Dict containing the created AAGUID entry.
    """
    logger.info(f"Creating custom AAGUID {aaguid} for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/authenticators/{authenticator_id}/aaguids",
            {"aaguid": aaguid, "name": name},
        )
        if error:
            logger.error(f"Error creating custom AAGUID {aaguid}: {error}")
            return {"error": str(error)}
        logger.info(f"Created custom AAGUID {aaguid} for authenticator {authenticator_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception creating custom AAGUID: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_custom_aaguid(
    ctx: Context,
    authenticator_id: str,
    aaguid: str,
) -> dict:
    """Retrieve a specific custom AAGUID entry from a WebAuthn authenticator.

    Parameters:
        authenticator_id (str, required): The ID of the WebAuthn authenticator.
        aaguid (str, required): The AAGUID UUID to retrieve.

    Returns:
        Dict containing the AAGUID entry with aaguid, name, and _links.
    """
    logger.info(f"Getting custom AAGUID {aaguid} for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "GET",
            f"/api/v1/authenticators/{authenticator_id}/aaguids/{aaguid}",
        )
        if error:
            logger.error(f"Error getting custom AAGUID {aaguid}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception getting custom AAGUID: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def replace_custom_aaguid(
    ctx: Context,
    authenticator_id: str,
    aaguid: str,
    name: str,
) -> dict:
    """Replace (full update) a custom AAGUID entry for a WebAuthn authenticator.

    Parameters:
        authenticator_id (str, required): The ID of the WebAuthn authenticator.
        aaguid (str, required): The AAGUID UUID to update.
        name (str, required): New display name for the AAGUID entry.

    Returns:
        Dict containing the updated AAGUID entry.
    """
    logger.info(f"Replacing custom AAGUID {aaguid} for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "PUT",
            f"/api/v1/authenticators/{authenticator_id}/aaguids/{aaguid}",
            {"aaguid": aaguid, "name": name},
        )
        if error:
            logger.error(f"Error replacing custom AAGUID {aaguid}: {error}")
            return {"error": str(error)}
        logger.info(f"Replaced custom AAGUID {aaguid}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception replacing custom AAGUID: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_custom_aaguid(
    ctx: Context,
    authenticator_id: str,
    aaguid: str,
    name: str,
) -> dict:
    """Partially update a custom AAGUID entry for a WebAuthn authenticator.

    Parameters:
        authenticator_id (str, required): The ID of the WebAuthn authenticator.
        aaguid (str, required): The AAGUID UUID to update.
        name (str, required): New display name for the AAGUID entry.

    Returns:
        Dict containing the updated AAGUID entry.
    """
    logger.info(f"Updating custom AAGUID {aaguid} for authenticator {authenticator_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "PATCH",
            f"/api/v1/authenticators/{authenticator_id}/aaguids/{aaguid}",
            {"name": name},
        )
        if error:
            logger.error(f"Error updating custom AAGUID {aaguid}: {error}")
            return {"error": str(error)}
        logger.info(f"Updated custom AAGUID {aaguid}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception updating custom AAGUID: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def delete_custom_aaguid(
    ctx: Context,
    authenticator_id: str,
    aaguid: str,
) -> dict:
    """Delete a custom AAGUID from a WebAuthn authenticator's allowlist.

    Removes the specified hardware key model from the allowlist. Existing
    enrolled keys with this AAGUID are not affected — only future enrollments
    of that model will be blocked.

    Parameters:
        authenticator_id (str, required): The ID of the WebAuthn authenticator.
        aaguid (str, required): The AAGUID UUID to remove.

    Returns:
        Dict confirming the deletion.
    """
    logger.warning(f"Deletion requested for custom AAGUID {aaguid} on authenticator {authenticator_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _aaguid_obj, _ = await _execute(_client_tmp, "GET", f"/api/v1/authenticators/{authenticator_id}/aaguids/{aaguid}")
        _aaguid_name = _aaguid_obj.get("name", "") if isinstance(_aaguid_obj, dict) else ""
    except Exception:
        _aaguid_name = ""
    _aaguid_resource = f"'{_aaguid_name}' ({aaguid})" if _aaguid_name else aaguid

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_CUSTOM_AAGUID.format(resource=_aaguid_resource, authenticator_id=authenticator_id),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": (
                f"To confirm removing AAGUID {_aaguid_resource} from authenticator {authenticator_id}, "
                "please confirm. New enrollments of that hardware key model will be blocked."
            ),
            "aaguid": aaguid,
            "authenticator_id": authenticator_id,
        },
    )

    if not outcome.used_elicitation:
        return outcome.fallback_response

    if not outcome.confirmed:
        logger.info(f"Custom AAGUID deletion cancelled for {aaguid}")
        return {"message": "Custom AAGUID deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        _, error = await _execute(
            client, "DELETE",
            f"/api/v1/authenticators/{authenticator_id}/aaguids/{aaguid}",
        )
        if error:
            logger.error(f"Error deleting custom AAGUID {aaguid}: {error}")
            return {"error": str(error)}
        logger.info(f"Deleted custom AAGUID {aaguid} from authenticator {authenticator_id}")
        return {"message": f"Custom AAGUID {aaguid} deleted from authenticator {authenticator_id}."}
    except Exception as e:
        logger.error(f"Exception deleting custom AAGUID: {type(e).__name__}: {e}")
        return {"error": str(e)}
