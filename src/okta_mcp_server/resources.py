# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""MCP resources exposing skill content in three tiers:
- Tier 0: skill://core — always-injected core rules
- Tier 1: skill://domain/{name} — domain overview + tool tables
- Tier 2: skill://detail/{domain}/{subtopic} — complex structures / caveats
"""

from pathlib import Path

from okta_mcp_server.server import mcp

_SKILLS_DIR = Path(__file__).parent / "skills"


def _read(rel: str) -> str:
    return (_SKILLS_DIR / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tier 0 — Core rules (always injected)
# ---------------------------------------------------------------------------


@mcp.resource("skill://core")
def resource_core() -> str:
    return _read("core.md")


# ---------------------------------------------------------------------------
# Tier 1 — Domain overviews
# ---------------------------------------------------------------------------


@mcp.resource("skill://domain/users")
def resource_users() -> str:
    return _read("users.md")


@mcp.resource("skill://domain/groups")
def resource_groups() -> str:
    return _read("groups.md")


@mcp.resource("skill://domain/applications")
def resource_applications() -> str:
    return _read("applications.md")


@mcp.resource("skill://domain/devices")
def resource_devices() -> str:
    return _read("devices.md")


@mcp.resource("skill://domain/policies")
def resource_policies() -> str:
    return _read("policies.md")


@mcp.resource("skill://domain/network-zones")
def resource_network_zones() -> str:
    return _read("network-zones.md")


@mcp.resource("skill://domain/trusted-origins")
def resource_trusted_origins() -> str:
    return _read("trusted-origins.md")


@mcp.resource("skill://domain/system-logs")
def resource_system_logs() -> str:
    return _read("system-logs.md")


@mcp.resource("skill://domain/governance")
def resource_governance() -> str:
    return _read("governance.md")


@mcp.resource("skill://domain/profile-mappings")
def resource_profile_mappings() -> str:
    return _read("profile-mappings.md")


@mcp.resource("skill://domain/authenticators")
def resource_authenticators() -> str:
    return _read("authenticators.md")


@mcp.resource("skill://domain/application-credentials")
def resource_application_credentials() -> str:
    return _read("application-credentials.md")


@mcp.resource("skill://domain/agent-pools")
def resource_agent_pools() -> str:
    return _read("agent-pools.md")


@mcp.resource("skill://domain/user-role-targets")
def resource_user_role_targets() -> str:
    return _read("user-role-targets.md")


@mcp.resource("skill://domain/workflows")
def resource_workflows() -> str:
    return _read("workflows.md")


# ---------------------------------------------------------------------------
# Tier 2 — Detail subtopics (complex structures / caveats)
# ---------------------------------------------------------------------------


@mcp.resource("skill://detail/governance/risk-rules")
def resource_detail_governance_risk_rules() -> str:
    return _read("detail/governance-risk-rules.md")


@mcp.resource("skill://detail/governance/grants")
def resource_detail_governance_grants() -> str:
    return _read("detail/governance-grants.md")


@mcp.resource("skill://detail/governance/entitlements")
def resource_detail_governance_entitlements() -> str:
    return _read("detail/governance-entitlements.md")


@mcp.resource("skill://detail/applications/provisioning")
def resource_detail_applications_provisioning() -> str:
    return _read("detail/applications-provisioning.md")


@mcp.resource("skill://detail/applications/group-push")
def resource_detail_applications_group_push() -> str:
    return _read("detail/applications-group-push.md")


@mcp.resource("skill://detail/groups/rules")
def resource_detail_groups_rules() -> str:
    return _read("detail/groups-rules.md")


@mcp.resource("skill://detail/policies/simulation")
def resource_detail_policies_simulation() -> str:
    return _read("detail/policies-simulation.md")


@mcp.resource("skill://detail/authenticators/aaguids")
def resource_detail_authenticators_aaguids() -> str:
    return _read("detail/authenticators-aaguids.md")


@mcp.resource("skill://detail/system-logs/scenarios")
def resource_detail_system_logs_scenarios() -> str:
    return _read("detail/logs-scenarios.md")
