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
async def list_application_features(
    ctx: Context,
    app_id: str,
) -> dict:
    """List all features for an application.

    Returns features that configure provisioning capabilities (e.g. PUSH_NEW_USERS,
    PUSH_PROFILE_UPDATES, PUSH_GROUPS). Requires provisioning to be enabled.

    Parameters:
        app_id (str, required): The ID of the application.

    Returns:
        Dict with items (list of ApplicationFeature objects) and total_fetched.
    """
    logger.info(f"Listing features for application: {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        features, _, err = await client.list_features_for_application(app_id)

        if err:
            logger.error(f"Error listing features for app {app_id}: {err}")
            return {"error": str(err)}

        items = [f.to_dict() if hasattr(f, "to_dict") else f for f in (features or [])]
        logger.info(f"Retrieved {len(items)} features for app {app_id}")
        return {"items": items, "total_fetched": len(items)}

    except Exception as e:
        logger.error(f"Exception listing features for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def get_application_feature(
    ctx: Context,
    app_id: str,
    feature_name: str,
) -> dict:
    """Retrieve a specific feature for an application.

    Parameters:
        app_id (str, required): The ID of the application.
        feature_name (str, required): The feature name (e.g. "PUSH_NEW_USERS",
            "PUSH_PROFILE_UPDATES", "PUSH_GROUPS", "IMPORT_NEW_USERS").

    Returns:
        Dict containing the ApplicationFeature details.
    """
    logger.info(f"Getting feature {feature_name} for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        feature, _, err = await client.get_feature_for_application(app_id, feature_name)

        if err:
            logger.error(f"Error getting feature {feature_name} for app {app_id}: {err}")
            return {"error": str(err)}

        return feature.to_dict() if hasattr(feature, "to_dict") else feature

    except Exception as e:
        logger.error(f"Exception getting feature {feature_name} for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def update_application_feature(
    ctx: Context,
    app_id: str,
    feature_name: str,
    capabilities: Dict[str, Any],
) -> dict:
    """Update a feature for an application.

    Enables or disables provisioning capabilities and configures their behaviour.

    Parameters:
        app_id (str, required): The ID of the application.
        feature_name (str, required): The feature name (e.g. "PUSH_NEW_USERS",
            "PUSH_PROFILE_UPDATES", "PUSH_GROUPS", "IMPORT_NEW_USERS").
        capabilities (dict, required): Feature capabilities configuration, e.g.:
            For PUSH_NEW_USERS: {"create": {"lifecycleCreate": {"status": "ACTIVE"}}}
            For PUSH_PROFILE_UPDATES: {"update": {"profile": {"action": "AUTOMATIC"}}}

    Returns:
        Dict containing the updated ApplicationFeature.
    """
    logger.info(f"Updating feature {feature_name} for application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        feature, _, err = await client.update_feature_for_application(app_id, feature_name, capabilities)

        if err:
            logger.error(f"Error updating feature {feature_name} for app {app_id}: {err}")
            return {"error": str(err)}

        out = feature.to_dict() if hasattr(feature, "to_dict") else feature
        logger.info(f"Updated feature {feature_name} for app {app_id}")
        return out

    except Exception as e:
        logger.error(f"Exception updating feature {feature_name} for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def upload_application_logo(
    ctx: Context,
    app_id: str,
    file_path: str,
) -> dict:
    """Upload a logo for an application.

    Uploads a logo image for the app. If the app already has a logo, it is replaced.
    The logo appears in the Admin Console and (for single-link apps) the End-User Dashboard.

    Parameters:
        app_id (str, required): The ID of the application.
        file_path (str, required): Absolute path to the logo image file.
            Must be PNG, JPG, SVG, or GIF format, less than 1 MB.
            Recommended: transparent background, 200×200 px square.

    Returns:
        Dict confirming the upload.
    """
    logger.info(f"Uploading logo for application {app_id} from: {file_path}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    except OSError as e:
        return {"error": f"Cannot read file '{file_path}': {e}"}

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.upload_application_logo(app_id, file_bytes)

        if err:
            logger.error(f"Error uploading logo for app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Uploaded logo for app {app_id}")
        return {"message": f"Logo uploaded successfully for application {app_id}."}

    except Exception as e:
        logger.error(f"Exception uploading logo for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", "policy_id", error_return_type="dict")
async def assign_application_policy(
    ctx: Context,
    app_id: str,
    policy_id: str,
) -> dict:
    """Assign a sign-on policy to an application.

    Assigns an app sign-in policy to the application. If the app was previously
    assigned to another policy, that assignment is replaced.

    Parameters:
        app_id (str, required): The ID of the application.
        policy_id (str, required): The ID of the sign-on policy to assign.

    Returns:
        Dict confirming the policy assignment.
    """
    logger.info(f"Assigning policy {policy_id} to application {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        _, _, err = await client.assign_application_policy(app_id, policy_id)

        if err:
            logger.error(f"Error assigning policy {policy_id} to app {app_id}: {err}")
            return {"error": str(err)}

        logger.info(f"Assigned policy {policy_id} to app {app_id}")
        return {"message": f"Policy {policy_id} assigned to application {app_id}."}

    except Exception as e:
        logger.error(f"Exception assigning policy {policy_id} to app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def preview_saml_metadata(
    ctx: Context,
    app_id: str,
    kid: str,
) -> dict:
    """Preview the SAML metadata for an application.

    Returns the SSO SAML metadata XML for the specified application and signing key.

    Parameters:
        app_id (str, required): The ID of the SAML application.
        kid (str, required): The ID of the signing key to use in the metadata.

    Returns:
        Dict with a "metadata" field containing the SAML XML string.
    """
    logger.info(f"Previewing SAML metadata for application {app_id}, kid={kid}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        xml, _, err = await client.preview_sam_lmetadata_for_application(app_id, kid)

        if err:
            logger.error(f"Error previewing SAML metadata for app {app_id}: {err}")
            return {"error": str(err)}

        return {"metadata": xml}

    except Exception as e:
        logger.error(f"Exception previewing SAML metadata for app {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
