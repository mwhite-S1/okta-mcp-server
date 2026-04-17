# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2025-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from loguru import logger
from mcp.server.fastmcp import FastMCP

from okta_mcp_server.utils.auth.auth_manager import OktaAuthManager
from okta_mcp_server.utils.auth.middleware import _user_token_var

LOG_FILE = os.environ.get("OKTA_LOG_FILE")

# Comma-separated list of Okta group names that are allowed to use this MCP server.
# If empty, no group restriction is enforced.
_ALLOWED_GROUPS: list[str] = [
    g.strip()
    for g in os.environ.get("OKTA_ALLOWED_GROUPS", "").split(",")
    if g.strip()
]


@dataclass
class OktaAppContext:
    okta_auth_manager: OktaAuthManager


@asynccontextmanager
async def okta_authorisation_flow(server: FastMCP) -> AsyncIterator[OktaAppContext]:
    """Per-connection lifecycle: authenticate the caller and yield context for tools.

    When the API Gateway forwards the user's Okta access token via the
    Authorization header on the SSE connection, that token is extracted by
    TokenExtractionMiddleware and stored in _user_token_var. We use it here
    so every Okta API call runs under the caller's identity.

    Falls back to the service account flows (browserless / device) when no
    delegated token is present — useful for local development without the gateway.
    """
    token = _user_token_var.get()
    manager = OktaAuthManager()

    if token:
        logger.info("Using user-delegated token for this MCP session")
        try:
            await manager.set_delegated_token(token)
        except ValueError as exc:
            logger.error(f"Delegated token rejected: {exc}")
            raise RuntimeError(f"Invalid or expired authorization token: {exc}") from exc
    else:
        logger.info("No delegated token — initiating interactive device authorization flow")
        try:
            await manager.authenticate()
        except RuntimeError as exc:
            logger.error(f"Authentication failed: {exc}")
            raise

    # Group membership check — runs for both delegated and device flow tokens.
    # Rejects the session immediately if the user is not in an allowed group.
    if _ALLOWED_GROUPS:
        try:
            await manager.check_group_membership(_ALLOWED_GROUPS)
        except PermissionError as exc:
            logger.error(f"Access denied: {exc}")
            raise RuntimeError(str(exc)) from exc

    logger.info("Okta authentication completed successfully")

    try:
        yield OktaAppContext(okta_auth_manager=manager)
    finally:
        logger.debug("Clearing Okta tokens")
        manager.clear_tokens()


mcp = FastMCP("Okta IDaaS MCP Server", lifespan=okta_authorisation_flow)


def main():
    """Run the Okta MCP server."""
    logger.remove()

    if LOG_FILE:
        logger.add(
            LOG_FILE,
            mode="w",
            level=os.environ.get("OKTA_LOG_LEVEL", "INFO"),
            retention="5 days",
            enqueue=True,
            serialize=True,
        )

    logger.add(
        sys.stderr, level=os.environ.get("OKTA_LOG_LEVEL", "INFO"), format="{time} {level} {message}", serialize=True
    )

    logger.info("Starting Okta MCP Server")
    from okta_mcp_server.tools.applications import applications  # noqa: F401
    from okta_mcp_server.tools.applications import application_users  # noqa: F401
    from okta_mcp_server.tools.applications import application_groups  # noqa: F401
    from okta_mcp_server.tools.applications import application_grants  # noqa: F401
    from okta_mcp_server.tools.applications import application_tokens  # noqa: F401
    from okta_mcp_server.tools.applications import application_connections  # noqa: F401
    from okta_mcp_server.tools.applications import application_features  # noqa: F401
    from okta_mcp_server.tools.applications import application_push  # noqa: F401
    from okta_mcp_server.tools.devices import devices  # noqa: F401
    from okta_mcp_server.tools.governance import access_requests  # noqa: F401
    from okta_mcp_server.tools.governance import certifications  # noqa: F401
    from okta_mcp_server.tools.governance import collections  # noqa: F401
    from okta_mcp_server.tools.governance import delegates  # noqa: F401
    from okta_mcp_server.tools.governance import entitlements  # noqa: F401
    from okta_mcp_server.tools.governance import labels  # noqa: F401
    from okta_mcp_server.tools.governance import operations  # noqa: F401
    from okta_mcp_server.tools.governance import resource_owners  # noqa: F401
    from okta_mcp_server.tools.governance import risk_rules  # noqa: F401
    from okta_mcp_server.tools.governance import settings  # noqa: F401
    from okta_mcp_server.tools.governance import enduser  # noqa: F401
    from okta_mcp_server.tools.governance import iam_bundles  # noqa: F401
    from okta_mcp_server.tools.governance import request_types  # noqa: F401
    from okta_mcp_server.tools.groups import group_rules  # noqa: F401
    from okta_mcp_server.tools.groups import group_owners  # noqa: F401
    from okta_mcp_server.tools.groups import groups  # noqa: F401
    from okta_mcp_server.tools.policies import policies  # noqa: F401
    from okta_mcp_server.tools.system_logs import system_logs  # noqa: F401
    from okta_mcp_server.tools.users import users  # noqa: F401
    from okta_mcp_server.tools.users import user_lifecycle  # noqa: F401
    from okta_mcp_server.tools.users import user_credentials  # noqa: F401
    from okta_mcp_server.tools.users import user_sessions  # noqa: F401
    from okta_mcp_server.tools.users import user_factors  # noqa: F401
    from okta_mcp_server.tools.users import user_oauth  # noqa: F401
    from okta_mcp_server.tools.profile_mappings import profile_mappings  # noqa: F401
    from okta_mcp_server.tools.network_zones import network_zones  # noqa: F401
    from okta_mcp_server.tools.trusted_origins import trusted_origins  # noqa: F401
    from okta_mcp_server.tools.schema import schema  # noqa: F401
    from okta_mcp_server.tools.authenticators import authenticators  # noqa: F401
    from okta_mcp_server.tools.applications import application_credentials  # noqa: F401
    from okta_mcp_server.tools.agent_pools import agent_pools  # noqa: F401
    from okta_mcp_server.tools.users import user_role_targets  # noqa: F401
    from okta_mcp_server import resources  # noqa: F401

    mcp.run()
