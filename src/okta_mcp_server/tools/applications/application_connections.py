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
async def get_default_provisioning_connection(
    ctx: Context,
    app_id: str,
) -> dict:
    """Retrieve the default provisioning connection for an application.

    Parameters:
        app_id (str, required): The ID of the application.

    Returns:
        Dict containing the ProvisioningConnectionResponse with authScheme, status, and profile.
    """
    logger.info(f"Getting default provisioning connection for application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        conn, _, err = await client.get_default_provisioning_connection_for_application(app_id)

        if err:
            logger.error(f"Error getting provisioning connection for app {app_id}: {err}")
            return {"error": str(err)}

        return conn.to_dict() if hasattr(conn, "to_dict") else conn

    except Exception as e:
        logger.error(f"Exception getting provisioning connection for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def update_default_provisioning_connection(
    ctx: Context,
    app_id: str,
    connection: Dict[str, Any],
    activate: bool = False,
) -> dict:
    """Update the default provisioning connection for an application.

    Supports token-based and OAuth 2.0 provisioning connections.

    Parameters:
        app_id (str, required): The ID of the application.
        connection (dict, required): Provisioning connection configuration:
            For token-based: {"authScheme": "TOKEN", "token": "<token>"}
            For OAuth: {"authScheme": "OAUTH2", "credentials": {...}}
        activate (bool, optional): Activate the connection immediately. Default: False.

    Returns:
        Dict containing the updated ProvisioningConnectionResponse.
    """
    logger.info(f"Updating default provisioning connection for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        conn, _, err = await client.update_default_provisioning_connection_for_application(
            app_id, connection, activate=activate
        )

        if err:
            logger.error(f"Error updating provisioning connection for app {app_id}: {err}")
            return {"error": str(err)}

        out = conn.to_dict() if hasattr(conn, "to_dict") else conn
        logger.info(f"Updated provisioning connection for app {app_id}")
        return out

    except Exception as e:
        logger.error(f"Exception updating provisioning connection for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def get_provisioning_connection_jwks(
    ctx: Context,
    app_id: str,
) -> dict:
    """Retrieve the JSON Web Key Set (JWKS) for the default provisioning connection.

    The JWKS can be used by an OAuth 2.0 app's jwk_uri property in the target org
    to verify tokens issued by Okta for provisioning.

    Parameters:
        app_id (str, required): The ID of the application.

    Returns:
        Dict containing the JWKS with the public keys.
    """
    logger.info(f"Getting provisioning connection JWKS for application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        jwks, _, err = await client.get_user_provisioning_connection_jwks(app_id)

        if err:
            logger.error(f"Error getting JWKS for app {app_id}: {err}")
            return {"error": str(err)}

        return jwks.to_dict() if hasattr(jwks, "to_dict") else jwks

    except Exception as e:
        logger.error(f"Exception getting JWKS for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def activate_provisioning_connection(
    ctx: Context,
    app_id: str,
) -> dict:
    """Activate the default provisioning connection for an application.

    Parameters:
        app_id (str, required): The ID of the application.

    Returns:
        Dict confirming activation.
    """
    logger.info(f"Activating provisioning connection for application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.activate_default_provisioning_connection_for_application(app_id)

        if err:
            logger.error(f"Error activating provisioning connection for app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Activated provisioning connection for app {app_id}")
        return {"message": f"Provisioning connection activated for application {app_id}."}

    except Exception as e:
        logger.error(f"Exception activating provisioning connection for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def deactivate_provisioning_connection(
    ctx: Context,
    app_id: str,
) -> dict:
    """Deactivate the default provisioning connection for an application.

    Parameters:
        app_id (str, required): The ID of the application.

    Returns:
        Dict confirming deactivation.
    """
    logger.info(f"Deactivating provisioning connection for application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.deactivate_default_provisioning_connection_for_application(app_id)

        if err:
            logger.error(f"Error deactivating provisioning connection for app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Deactivated provisioning connection for app {app_id}")
        return {"message": f"Provisioning connection deactivated for application {app_id}."}

    except Exception as e:
        logger.error(f"Exception deactivating provisioning connection for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def verify_provisioning_connection(
    ctx: Context,
    app_id: str,
    app_name: str,
    code: Optional[str] = None,
    state: Optional[str] = None,
) -> dict:
    """Verify the OAuth 2.0 provisioning connection for an application.

    Completes the OAuth 2.0 consent flow as the final step of provisioning setup
    for OAuth-based connections. Only supports: office365, google, zoomus, slack.

    Parameters:
        app_id (str, required): The ID of the application.
        app_name (str, required): The app name identifier — one of:
            "office365", "google", "zoomus", "slack".
        code (str, optional): The authorization code from the OAuth redirect.
        state (str, optional): The state string from the OAuth redirect.

    Returns:
        Dict confirming verification.
    """
    logger.info(f"Verifying provisioning connection for app {app_id} (app_name={app_name})")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        kwargs = {}
        if code:
            kwargs["code"] = code
        if state:
            kwargs["state"] = state

        _, _, err = await client.verify_provisioning_connection_for_application(app_name, app_id, **kwargs)

        if err:
            logger.error(f"Error verifying provisioning connection for app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Verified provisioning connection for app {app_id}")
        return {"message": f"Provisioning connection verified for application {app_id}."}

    except Exception as e:
        logger.error(f"Exception verifying provisioning connection for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
