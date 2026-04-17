# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Application credential tools: SSO signing keys, CSRs, OAuth JWKs, and OAuth client secrets.

Covers /api/v1/apps/{appId}/credentials/* endpoints for key rotation,
certificate management, and OAuth 2.0 client credential lifecycle.
"""

import json as _json
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.elicitation import DeleteConfirmation, elicit_or_fallback
from okta_mcp_server.utils.messages import (
    DELETE_APPLICATION_JWK,
    DELETE_OAUTH2_CLIENT_SECRET,
    REVOKE_APPLICATION_CSR,
)
from okta_mcp_server.utils.validation import validate_ids


async def _execute(client, method: str, path: str, body: dict = None):
    """Make a direct API call via the SDK request executor."""
    request_executor = client.get_request_executor()
    url = f"{client.get_base_url()}{path}"
    # SDK only sets Content-Type when body is truthy; for bodyless POST/PUT
    # we must inject it explicitly or Okta returns E0000021.
    extra_headers: dict = {}
    if method.upper() in ("POST", "PUT") and not body:
        extra_headers["Content-Type"] = "application/json"
    request, error = await request_executor.create_request(method, url, body, headers=extra_headers)
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
# SSO Signing Keys (X.509 certs for SAML / WS-Fed apps)
# ---------------------------------------------------------------------------

@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def list_application_keys(
    ctx: Context,
    app_id: str,
) -> dict:
    """List all X.509 signing key credentials for an application.

    SSO signing keys are X.509 certificates used to sign SAML assertions or
    WS-Fed tokens. Most apps have a single active key; key rotation creates
    a new key and updates the app to use it.

    Parameters:
        app_id (str, required): The ID of the application.

    Returns:
        Dict with items (list of JsonWebKey / X.509 credential objects) and total_fetched.
        Each key includes: kid, kty, x5c (certificate chain), expiresAt, status.
    """
    logger.info(f"Listing signing keys for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/apps/{app_id}/credentials/keys")
        if error:
            logger.error(f"Error listing keys for app {app_id}: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else []
        logger.info(f"Retrieved {len(items)} key(s) for app {app_id}")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing keys for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def generate_application_key(
    ctx: Context,
    app_id: str,
    validity_years: Optional[int] = None,
) -> dict:
    """Generate a new X.509 signing key credential for an application.

    Generates a new key but does NOT automatically activate it — the app
    continues using its current key until you update the app's credentials
    to reference the new kid. Use clone_application_key to copy the key to
    another app before switching.

    Parameters:
        app_id (str, required): The ID of the application.
        validity_years (int, optional): Certificate validity in years (1–10).
            Default: 2.

    Returns:
        Dict containing the new JsonWebKey with kid, kty, x5c, and expiresAt.
    """
    logger.info(f"Generating signing key for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/apps/{app_id}/credentials/keys/generate"
        if validity_years is not None:
            path += f"?validityYears={validity_years}"
        body, error = await _execute(client, "POST", path)
        if error:
            logger.error(f"Error generating key for app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Generated key for app {app_id}: {(body or {}).get('kid', 'unknown')}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception generating key for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def get_application_key(
    ctx: Context,
    app_id: str,
    key_id: str,
) -> dict:
    """Retrieve a specific X.509 signing key credential for an application.

    Parameters:
        app_id (str, required): The ID of the application.
        key_id (str, required): The kid (key ID) of the signing key.

    Returns:
        Dict containing the JsonWebKey with kid, kty, x5c chain, and expiresAt.
    """
    logger.info(f"Getting key {key_id} for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/apps/{app_id}/credentials/keys/{key_id}")
        if error:
            logger.error(f"Error getting key {key_id} for app {app_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception getting key for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def clone_application_key(
    ctx: Context,
    app_id: str,
    key_id: str,
    target_app_id: str,
) -> dict:
    """Clone an X.509 signing key credential from one application to another.

    Copies the key to a target application so both can use the same signing
    certificate. Useful when sharing SAML metadata across multiple app instances
    or during SAML key rotation to keep the old and new IdP metadata in sync.

    Parameters:
        app_id (str, required): The source application ID.
        key_id (str, required): The kid of the key to clone.
        target_app_id (str, required): The target application ID to clone the key into.

    Returns:
        Dict containing the cloned JsonWebKey in the target application.
    """
    logger.info(f"Cloning key {key_id} from app {app_id} to app {target_app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/apps/{app_id}/credentials/keys/{key_id}/clone?targetAid={target_app_id}"
        body, error = await _execute(client, "POST", path)
        if error:
            logger.error(f"Error cloning key {key_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Cloned key {key_id} to app {target_app_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception cloning key: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Certificate Signing Requests (CSRs)
# ---------------------------------------------------------------------------

@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def list_application_csrs(
    ctx: Context,
    app_id: str,
) -> dict:
    """List all certificate signing requests (CSRs) for an application.

    CSRs are pending certificate requests that must be signed by your CA and
    then published back to Okta. Once published, the resulting certificate
    replaces the app's current signing key.

    Parameters:
        app_id (str, required): The ID of the application.

    Returns:
        Dict with items (list of Csr objects) and total_fetched.
        Each CSR includes: id, created, expiresAt, csrValue (PEM), kty, subject.
    """
    logger.info(f"Listing CSRs for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/apps/{app_id}/credentials/csrs")
        if error:
            logger.error(f"Error listing CSRs for app {app_id}: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else []
        logger.info(f"Retrieved {len(items)} CSR(s) for app {app_id}")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing CSRs for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def generate_application_csr(
    ctx: Context,
    app_id: str,
    subject: Dict[str, Any],
    subject_alt_names: Optional[Dict[str, Any]] = None,
) -> dict:
    """Generate a new certificate signing request (CSR) for an application.

    Generates a CSR for the app's signing credential. After signing the CSR
    with your CA, publish the signed certificate back with publish_application_csr.

    Parameters:
        app_id (str, required): The ID of the application.
        subject (dict, required): Certificate subject fields:
            - countryName (str): Two-letter country code (e.g. "US").
            - stateOrProvinceName (str): State or province.
            - localityName (str): City.
            - organizationName (str): Organization.
            - organizationalUnitName (str): Department.
            - commonName (str): Common name (usually the app or domain name).
        subject_alt_names (dict, optional): Subject alternative names:
            - dns (list[str]): DNS names.
            - email (list[str]): Email addresses.

    Returns:
        Dict containing the Csr with id, csrValue (PEM-encoded), and kty.
    """
    logger.info(f"Generating CSR for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        payload: Dict[str, Any] = {"subject": subject}
        if subject_alt_names:
            payload["subjectAltNames"] = subject_alt_names
        body, error = await _execute(client, "POST", f"/api/v1/apps/{app_id}/credentials/csrs", payload)
        if error:
            logger.error(f"Error generating CSR for app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Generated CSR for app {app_id}: {(body or {}).get('id', 'unknown')}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception generating CSR for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def get_application_csr(
    ctx: Context,
    app_id: str,
    csr_id: str,
) -> dict:
    """Retrieve a specific certificate signing request (CSR) for an application.

    Parameters:
        app_id (str, required): The ID of the application.
        csr_id (str, required): The ID of the CSR.

    Returns:
        Dict containing the Csr with id, csrValue (PEM), kty, and expiresAt.
    """
    logger.info(f"Getting CSR {csr_id} for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/apps/{app_id}/credentials/csrs/{csr_id}")
        if error:
            logger.error(f"Error getting CSR {csr_id} for app {app_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception getting CSR for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def revoke_application_csr(
    ctx: Context,
    app_id: str,
    csr_id: str,
) -> dict:
    """Revoke (delete) a certificate signing request for an application.

    Cancels a pending CSR. The CSR cannot be published after revocation.
    Use this when the CSR was generated in error or will not be signed.

    Parameters:
        app_id (str, required): The ID of the application.
        csr_id (str, required): The ID of the CSR to revoke.

    Returns:
        Dict confirming the CSR was revoked.
    """
    logger.warning(f"Revocation requested for CSR {csr_id} on app {app_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _app_obj, _ = await _execute(_client_tmp, "GET", f"/api/v1/apps/{app_id}")
        _app_name = _app_obj.get("label", "") if isinstance(_app_obj, dict) else ""
    except Exception:
        _app_name = ""
    _app_resource = f"'{_app_name}' ({app_id})" if _app_name else app_id
    _csr_resource = csr_id

    outcome = await elicit_or_fallback(
        ctx,
        message=REVOKE_APPLICATION_CSR.format(resource=_csr_resource, app_resource=_app_resource),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": (
                f"To confirm revoking CSR {csr_id} for application {_app_resource}, please confirm. "
                "The CSR cannot be published after revocation."
            ),
            "csr_id": csr_id,
            "app_id": app_id,
        },
    )

    if not outcome.used_elicitation:
        return outcome.fallback_response

    if not outcome.confirmed:
        return {"message": "CSR revocation cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "DELETE", f"/api/v1/apps/{app_id}/credentials/csrs/{csr_id}")
        if error:
            logger.error(f"Error revoking CSR {csr_id} for app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Revoked CSR {csr_id} for app {app_id}")
        return {"message": f"CSR {csr_id} revoked for application {app_id}."}
    except Exception as e:
        logger.error(f"Exception revoking CSR for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def publish_application_csr(
    ctx: Context,
    app_id: str,
    csr_id: str,
    signed_certificate: str,
) -> dict:
    """Publish a signed certificate to fulfill a CSR for an application.

    After your CA signs the CSR, submit the resulting certificate here.
    Okta activates the new certificate as the app's signing key.

    Parameters:
        app_id (str, required): The ID of the application.
        csr_id (str, required): The ID of the CSR being fulfilled.
        signed_certificate (str, required): The signed certificate in PEM or
            DER (base64) format. PEM example:
            "-----BEGIN CERTIFICATE-----\\nMIIB...\\n-----END CERTIFICATE-----"

    Returns:
        Dict containing the new JsonWebKey activated for the application.
    """
    logger.info(f"Publishing signed certificate for CSR {csr_id} on app {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        path = f"/api/v1/apps/{app_id}/credentials/csrs/{csr_id}/lifecycle/publish"
        body, error = await _execute(client, "POST", path, {"certificate": signed_certificate})
        if error:
            logger.error(f"Error publishing certificate for CSR {csr_id} on app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Published certificate for CSR {csr_id} on app {app_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception publishing CSR certificate for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# OAuth 2.0 Client JSON Web Keys (JWKs)
# ---------------------------------------------------------------------------

@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def list_application_jwks(
    ctx: Context,
    app_id: str,
) -> dict:
    """List all OAuth 2.0 client JSON Web Keys (JWKs) for an application.

    JWKs are public keys used for private_key_jwt client authentication.
    They are separate from the SSO signing keys used for SAML.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.

    Returns:
        Dict with items (list of JsonWebKey objects) and total_fetched.
        Each key includes: kid, kty, status, use, and the public key material.
    """
    logger.info(f"Listing OAuth2 JWKs for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/apps/{app_id}/credentials/jwks")
        if error:
            logger.error(f"Error listing JWKs for app {app_id}: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else ((body or {}).get("keys") or [])
        logger.info(f"Retrieved {len(items)} JWK(s) for app {app_id}")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing JWKs for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def add_application_jwk(
    ctx: Context,
    app_id: str,
    key_data: Dict[str, Any],
) -> dict:
    """Add an OAuth 2.0 client JSON Web Key (JWK) to an application.

    Adds an existing public key (e.g. from your internal PKI) for use with
    private_key_jwt client authentication. The key must be an RSA or EC public key
    in JWK format.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.
        key_data (dict, required): JWK object. Required fields:
            - kty (str): Key type — "RSA" or "EC".
            - use (str): Key use — typically "sig".
            - kid (str, optional): Key ID. Auto-generated if omitted.
            For RSA keys: n (modulus), e (exponent) in base64url encoding.
            For EC keys: crv ("P-256", "P-384"), x, y in base64url encoding.

    Returns:
        Dict containing the added JsonWebKey.
    """
    logger.info(f"Adding OAuth2 JWK to application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", f"/api/v1/apps/{app_id}/credentials/jwks", key_data)
        if error:
            logger.error(f"Error adding JWK to app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Added JWK to app {app_id}: {(body or {}).get('kid', 'unknown')}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception adding JWK to app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def get_application_jwk(
    ctx: Context,
    app_id: str,
    key_id: str,
) -> dict:
    """Retrieve a specific OAuth 2.0 client JSON Web Key (JWK) for an application.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.
        key_id (str, required): The kid (key ID) of the JWK.

    Returns:
        Dict containing the JsonWebKey with kid, kty, status, use, and key material.
    """
    logger.info(f"Getting OAuth2 JWK {key_id} for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/apps/{app_id}/credentials/jwks/{key_id}")
        if error:
            logger.error(f"Error getting JWK {key_id} for app {app_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception getting JWK for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def delete_application_jwk(
    ctx: Context,
    app_id: str,
    key_id: str,
) -> dict:
    """Delete an OAuth 2.0 client JSON Web Key (JWK) from an application.

    Removes the key permanently. Any OAuth clients using private_key_jwt
    authentication with this key will immediately start failing. Ensure no
    active clients depend on this key before deleting.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.
        key_id (str, required): The kid of the JWK to delete.

    Returns:
        Dict confirming the JWK was deleted.
    """
    logger.warning(f"Deletion requested for JWK {key_id} on app {app_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _app_obj, _ = await _execute(_client_tmp, "GET", f"/api/v1/apps/{app_id}")
        _app_name = _app_obj.get("label", "") if isinstance(_app_obj, dict) else ""
    except Exception:
        _app_name = ""
    _app_resource = f"'{_app_name}' ({app_id})" if _app_name else app_id
    _key_resource = key_id

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_APPLICATION_JWK.format(resource=_key_resource, app_resource=_app_resource),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": (
                f"To confirm deleting JWK {key_id} from application {_app_resource}, please confirm. "
                "OAuth clients using this key for authentication will immediately fail."
            ),
            "key_id": key_id,
            "app_id": app_id,
        },
    )

    if not outcome.used_elicitation:
        return outcome.fallback_response

    if not outcome.confirmed:
        return {"message": "JWK deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "DELETE", f"/api/v1/apps/{app_id}/credentials/jwks/{key_id}")
        if error:
            logger.error(f"Error deleting JWK {key_id} for app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Deleted JWK {key_id} from app {app_id}")
        return {"message": f"JWK {key_id} deleted from application {app_id}."}
    except Exception as e:
        logger.error(f"Exception deleting JWK from app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def activate_application_jwk(
    ctx: Context,
    app_id: str,
    key_id: str,
) -> dict:
    """Activate an OAuth 2.0 client JSON Web Key (JWK) for an application.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.
        key_id (str, required): The kid of the JWK to activate.

    Returns:
        Dict containing the updated JsonWebKey with status ACTIVE.
    """
    logger.info(f"Activating JWK {key_id} for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/apps/{app_id}/credentials/jwks/{key_id}/lifecycle/activate",
        )
        if error:
            logger.error(f"Error activating JWK {key_id} for app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Activated JWK {key_id} for app {app_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception activating JWK for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def deactivate_application_jwk(
    ctx: Context,
    app_id: str,
    key_id: str,
) -> dict:
    """Deactivate an OAuth 2.0 client JSON Web Key (JWK) for an application.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.
        key_id (str, required): The kid of the JWK to deactivate.

    Returns:
        Dict containing the updated JsonWebKey with status INACTIVE.
    """
    logger.info(f"Deactivating JWK {key_id} for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/apps/{app_id}/credentials/jwks/{key_id}/lifecycle/deactivate",
        )
        if error:
            logger.error(f"Error deactivating JWK {key_id} for app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Deactivated JWK {key_id} for app {app_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception deactivating JWK for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# OAuth 2.0 Client Secrets
# ---------------------------------------------------------------------------

@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def list_oauth2_client_secrets(
    ctx: Context,
    app_id: str,
) -> dict:
    """List all OAuth 2.0 client secrets for an application.

    Returns all client secrets for the application. Secret values are masked
    after creation — only the hash and metadata are returned. Multiple active
    secrets allow zero-downtime rotation.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.

    Returns:
        Dict with items (list of ClientSecret objects) and total_fetched.
        Each secret includes: id, status, created, lastUpdated, secretHash.
        The actual secret value is only returned on creation.
    """
    logger.info(f"Listing OAuth2 client secrets for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/apps/{app_id}/credentials/secrets")
        if error:
            logger.error(f"Error listing client secrets for app {app_id}: {error}")
            return {"error": str(error)}
        items = body if isinstance(body, list) else []
        logger.info(f"Retrieved {len(items)} client secret(s) for app {app_id}")
        return {"items": items, "total_fetched": len(items)}
    except Exception as e:
        logger.error(f"Exception listing client secrets for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def create_oauth2_client_secret(
    ctx: Context,
    app_id: str,
) -> dict:
    """Create a new OAuth 2.0 client secret for an application.

    Generates a new client secret. The secret value is returned ONLY in this
    response — it cannot be retrieved later. Save it immediately. Multiple
    secrets can coexist to support zero-downtime rotation.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.

    Returns:
        Dict containing the new ClientSecret with id, client_secret (the actual
        value — save this now), status, and secretHash.
    """
    logger.info(f"Creating OAuth2 client secret for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "POST", f"/api/v1/apps/{app_id}/credentials/secrets")
        if error:
            logger.error(f"Error creating client secret for app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Created client secret for app {app_id}: {(body or {}).get('id', 'unknown')}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception creating client secret for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def get_oauth2_client_secret(
    ctx: Context,
    app_id: str,
    secret_id: str,
) -> dict:
    """Retrieve metadata for a specific OAuth 2.0 client secret.

    Note: The actual secret value is not returned — only metadata like status,
    creation date, and the hash. The secret value is only available at creation.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.
        secret_id (str, required): The ID of the client secret.

    Returns:
        Dict containing the ClientSecret metadata (id, status, created, secretHash).
    """
    logger.info(f"Getting client secret {secret_id} for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(client, "GET", f"/api/v1/apps/{app_id}/credentials/secrets/{secret_id}")
        if error:
            logger.error(f"Error getting client secret {secret_id} for app {app_id}: {error}")
            return {"error": str(error)}
        return body or {}
    except Exception as e:
        logger.error(f"Exception getting client secret for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def delete_oauth2_client_secret(
    ctx: Context,
    app_id: str,
    secret_id: str,
) -> dict:
    """Delete an OAuth 2.0 client secret from an application.

    Permanently removes the secret. Any clients using this secret will
    immediately be unable to authenticate. Ensure the application has rotated
    to a new secret before deleting the old one.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.
        secret_id (str, required): The ID of the client secret to delete.

    Returns:
        Dict confirming the secret was deleted.
    """
    logger.warning(f"Deletion requested for client secret {secret_id} on app {app_id}")

    try:
        _client_tmp = await get_okta_client(ctx.request_context.lifespan_context.okta_auth_manager)
        _app_obj, _ = await _execute(_client_tmp, "GET", f"/api/v1/apps/{app_id}")
        _app_name = _app_obj.get("label", "") if isinstance(_app_obj, dict) else ""
    except Exception:
        _app_name = ""
    _app_resource = f"'{_app_name}' ({app_id})" if _app_name else app_id
    _secret_resource = secret_id

    outcome = await elicit_or_fallback(
        ctx,
        message=DELETE_OAUTH2_CLIENT_SECRET.format(resource=_secret_resource, app_resource=_app_resource),
        schema=DeleteConfirmation,
        fallback_payload={
            "confirmation_required": True,
            "message": (
                f"To confirm deleting client secret {secret_id} from application {_app_resource}, "
                "please confirm. Clients using this secret will immediately fail to authenticate."
            ),
            "secret_id": secret_id,
            "app_id": app_id,
        },
    )

    if not outcome.used_elicitation:
        return outcome.fallback_response

    if not outcome.confirmed:
        return {"message": "Client secret deletion cancelled by user."}

    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        _, error = await _execute(client, "DELETE", f"/api/v1/apps/{app_id}/credentials/secrets/{secret_id}")
        if error:
            logger.error(f"Error deleting client secret {secret_id} for app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Deleted client secret {secret_id} from app {app_id}")
        return {"message": f"Client secret {secret_id} deleted from application {app_id}."}
    except Exception as e:
        logger.error(f"Exception deleting client secret from app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def activate_oauth2_client_secret(
    ctx: Context,
    app_id: str,
    secret_id: str,
) -> dict:
    """Activate an OAuth 2.0 client secret for an application.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.
        secret_id (str, required): The ID of the client secret to activate.

    Returns:
        Dict containing the updated ClientSecret with status ACTIVE.
    """
    logger.info(f"Activating client secret {secret_id} for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/apps/{app_id}/credentials/secrets/{secret_id}/lifecycle/activate",
        )
        if error:
            logger.error(f"Error activating client secret {secret_id} for app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Activated client secret {secret_id} for app {app_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception activating client secret for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def deactivate_oauth2_client_secret(
    ctx: Context,
    app_id: str,
    secret_id: str,
) -> dict:
    """Deactivate an OAuth 2.0 client secret for an application.

    Deactivating a secret prevents it from being used for new token requests
    without permanently deleting it. Useful as an intermediate step before
    deletion during key rotation.

    Parameters:
        app_id (str, required): The ID of the OAuth 2.0 application.
        secret_id (str, required): The ID of the client secret to deactivate.

    Returns:
        Dict containing the updated ClientSecret with status INACTIVE.
    """
    logger.info(f"Deactivating client secret {secret_id} for application {app_id}")
    manager = ctx.request_context.lifespan_context.okta_auth_manager
    try:
        client = await get_okta_client(manager)
        body, error = await _execute(
            client, "POST",
            f"/api/v1/apps/{app_id}/credentials/secrets/{secret_id}/lifecycle/deactivate",
        )
        if error:
            logger.error(f"Error deactivating client secret {secret_id} for app {app_id}: {error}")
            return {"error": str(error)}
        logger.info(f"Deactivated client secret {secret_id} for app {app_id}")
        return body or {}
    except Exception as e:
        logger.error(f"Exception deactivating client secret for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
