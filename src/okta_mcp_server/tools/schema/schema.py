# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Dict, Optional

from loguru import logger
from mcp.server.fastmcp import Context

from okta_mcp_server.server import mcp
from okta_mcp_server.utils.client import get_okta_client
from okta_mcp_server.utils.validation import validate_ids


@mcp.tool()
async def get_user_schema(
    ctx: Context,
) -> dict:
    """Retrieve the default Okta user schema.

    Returns the full user profile schema including all base and custom attributes,
    their types, constraints, and mutability settings. Useful for understanding
    what profile fields exist and how they are configured.

    Returns:
        Dict containing the UserSchema with all defined attributes.
    """
    logger.info("Getting default user schema")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        schema, _, err = await client.get_user_schema("default")

        if err:
            logger.error(f"Error getting user schema: {err}")
            return {"error": str(err)}

        return schema.to_dict() if hasattr(schema, "to_dict") else schema

    except Exception as e:
        logger.error(f"Exception getting user schema: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_user_profile(
    ctx: Context,
    properties: Dict,
) -> dict:
    """Add or update custom properties in the default user profile schema.

    Use this to define new custom attributes or modify existing ones on the
    Okta user profile. Only the 'definitions.custom.properties' portion is
    updated — base properties cannot be modified.

    Parameters:
        properties (dict, required): Map of property names to their schema
            definitions. Each property definition can include:
            - title (str): Display label
            - type (str): Data type ("string", "boolean", "integer", "number", "array")
            - description (str, optional): Description of the attribute
            - required (bool, optional): Whether the field is required
            - permissions (list, optional): [{principal: "SELF", action: "READ_WRITE"}]

            Example:
            {
                "department": {
                    "title": "Department",
                    "type": "string",
                    "description": "User's department",
                    "permissions": [{"principal": "SELF", "action": "READ_ONLY"}]
                }
            }

    Returns:
        Dict containing the updated UserSchema.
    """
    logger.info(f"Updating user profile schema with {len(properties)} property definition(s)")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body = {
            "definitions": {
                "custom": {
                    "id": "#custom",
                    "type": "object",
                    "properties": properties,
                    "required": [],
                }
            }
        }

        schema, _, err = await client.update_user_profile("default", body)

        if err:
            logger.error(f"Error updating user profile schema: {err}")
            return {"error": str(err)}

        result = schema.to_dict() if hasattr(schema, "to_dict") else schema
        logger.info("Updated user profile schema")
        return result

    except Exception as e:
        logger.error(f"Exception updating user profile schema: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_group_schema(
    ctx: Context,
) -> dict:
    """Retrieve the Okta group profile schema.

    Returns all group profile attributes including base and custom properties,
    their types, constraints, and mutability.

    Returns:
        Dict containing the GroupSchema with all defined attributes.
    """
    logger.info("Getting group schema")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        schema, _, err = await client.get_group_schema()

        if err:
            logger.error(f"Error getting group schema: {err}")
            return {"error": str(err)}

        return schema.to_dict() if hasattr(schema, "to_dict") else schema

    except Exception as e:
        logger.error(f"Exception getting group schema: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_group_schema(
    ctx: Context,
    properties: Dict,
) -> dict:
    """Add or update custom properties in the group profile schema.

    Parameters:
        properties (dict, required): Map of property names to their schema
            definitions. Same structure as user profile properties.

    Returns:
        Dict containing the updated GroupSchema.
    """
    logger.info(f"Updating group schema with {len(properties)} property definition(s)")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body = {
            "definitions": {
                "custom": {
                    "id": "#custom",
                    "type": "object",
                    "properties": properties,
                    "required": [],
                }
            }
        }

        schema, _, err = await client.update_group_schema(body)

        if err:
            logger.error(f"Error updating group schema: {err}")
            return {"error": str(err)}

        result = schema.to_dict() if hasattr(schema, "to_dict") else schema
        logger.info("Updated group schema")
        return result

    except Exception as e:
        logger.error(f"Exception updating group schema: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def get_application_user_schema(
    ctx: Context,
    app_id: str,
) -> dict:
    """Retrieve the user schema for a specific application.

    Application user schemas define what profile attributes are available
    on application user objects (separate from the base Okta user schema).
    These attributes are typically mapped from the Okta user profile.

    Parameters:
        app_id (str, required): The ID of the application.

    Returns:
        Dict containing the application UserSchema.
    """
    logger.info(f"Getting application user schema for app {app_id}")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        schema, _, err = await client.get_application_user_schema(app_id)

        if err:
            logger.error(f"Error getting application user schema for {app_id}: {err}")
            return {"error": str(err)}

        return schema.to_dict() if hasattr(schema, "to_dict") else schema

    except Exception as e:
        logger.error(f"Exception getting application user schema for {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}


@mcp.tool()
@validate_ids("app_id", error_return_type="dict")
async def update_application_user_profile(
    ctx: Context,
    app_id: str,
    properties: Dict,
) -> dict:
    """Add or update custom properties in an application's user profile schema.

    Parameters:
        app_id (str, required): The ID of the application.
        properties (dict, required): Map of property names to their schema
            definitions. Same structure as user profile properties.

    Returns:
        Dict containing the updated application UserSchema.
    """
    logger.info(f"Updating application user profile schema for app {app_id} with {len(properties)} property definition(s)")

    manager = ctx.request_context.lifespan_context.okta_auth_manager

    try:
        client = await get_okta_client(manager)
        body = {
            "definitions": {
                "custom": {
                    "id": "#custom",
                    "type": "object",
                    "properties": properties,
                    "required": [],
                }
            }
        }

        schema, _, err = await client.update_application_user_profile(app_id, body)

        if err:
            logger.error(f"Error updating application user profile schema for {app_id}: {err}")
            return {"error": str(err)}

        result = schema.to_dict() if hasattr(schema, "to_dict") else schema
        logger.info(f"Updated application user profile schema for app {app_id}")
        return result

    except Exception as e:
        logger.error(f"Exception updating application user profile schema for {app_id}: {type(e).__name__}: {e}")
        return {"error": str(e)}
