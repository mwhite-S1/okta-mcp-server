#!/usr/bin/env python3
"""
Run the Okta MCP Server with SSE/HTTP transport for Docker deployment.

This replaces the default stdio transport with an HTTP/SSE server so the
API Gateway can call Okta MCP tools over the network inside Docker.
"""

import os
import sys

from loguru import logger

LOG_FILE = os.environ.get("OKTA_LOG_FILE")

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
    sys.stderr,
    level=os.environ.get("OKTA_LOG_LEVEL", "INFO"),
    format="{time} {level} {message}",
    serialize=True,
)

logger.info("Starting Okta MCP Server (SSE/HTTP transport mode)")

# Register all tool modules in the same order as server.main()
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

# Import the mcp instance AFTER all tools are registered
from okta_mcp_server.server import mcp  # noqa: E402

if __name__ == "__main__":
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8001"))
    transport = os.environ.get("MCP_TRANSPORT", "sse")

    logger.info(f"Listening on {host}:{port} with transport={transport}")

    # FastMCP configures host/port via settings, not run() kwargs
    if hasattr(mcp, "settings"):
        mcp.settings.host = host
        mcp.settings.port = port

        # Disable DNS-rebinding protection: this server only listens on the
        # internal Docker app-mcp network and is never reachable from outside
        # the compose stack, so the host-header allowlist is unnecessary friction.
        try:
            from mcp.server.transport_security import TransportSecuritySettings
            mcp.settings.transport_security = TransportSecuritySettings(
                enable_dns_rebinding_protection=False
            )
        except ImportError:
            pass  # older SDK version without this setting

    mcp.run(transport=transport)
