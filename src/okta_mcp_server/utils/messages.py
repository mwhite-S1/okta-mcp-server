# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""Centralised user-facing confirmation messages for elicitation prompts.

All messages are string templates using ``str.format()`` placeholders so
they can be rendered with resource-specific identifiers at call time.

{resource} should be formatted as "'Display Name' (okta-id)" when a name
is available, or just the bare ID when it is not.

Keeping them in one place makes future localisation straightforward —
swap this module for a locale-aware loader without touching tool code.
"""


def _fmt(name: str | None, okta_id: str) -> str:
    """Return 'Name' (id) when name is known, otherwise just the id."""
    if name and name != okta_id:
        return f"'{name}' ({okta_id})"
    return okta_id


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------

DELETE_GROUP = (
    "Are you sure you want to delete group {resource}? "
    "This action cannot be undone."
)

DELETE_GROUP_RULE = (
    "Are you sure you want to delete group rule {resource}? "
    "This will permanently remove the rule and stop automatic group membership assignments. "
    "This action cannot be undone."
)

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

DELETE_APPLICATION = (
    "Are you sure you want to delete application {resource}? "
    "This action cannot be undone."
)

DEACTIVATE_APPLICATION = (
    "Are you sure you want to deactivate application {resource}? "
    "The application will become unavailable to all assigned users."
)

# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

DEACTIVATE_USER = (
    "Are you sure you want to deactivate user {resource}? "
    "The user will lose access to all applications."
)

DELETE_USER = (
    "Are you sure you want to permanently delete user {resource}? "
    "This action cannot be undone."
)

# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------

DELETE_POLICY = (
    "Are you sure you want to delete policy {resource}? "
    "This action cannot be undone."
)

DEACTIVATE_POLICY = (
    "Are you sure you want to deactivate policy {resource}?"
)

DELETE_POLICY_RULE = (
    "Are you sure you want to delete rule {resource} from policy {policy_resource}? "
    "This action cannot be undone."
)

DEACTIVATE_POLICY_RULE = (
    "Are you sure you want to deactivate rule {resource} "
    "in policy {policy_resource}?"
)

# ---------------------------------------------------------------------------
# Devices
# ---------------------------------------------------------------------------

DEACTIVATE_DEVICE = (
    "Are you sure you want to deactivate device {resource}? "
    "Users will lose access via this device."
)

SUSPEND_DEVICE = (
    "Are you sure you want to suspend device {resource}? "
    "The device will be blocked from accessing Okta resources."
)

DELETE_DEVICE = (
    "Are you sure you want to permanently delete device {resource}? "
    "The device must already be deactivated. This action cannot be undone."
)

# ---------------------------------------------------------------------------
# Governance
# ---------------------------------------------------------------------------

DELETE_GOVERNANCE_LABEL = (
    "Are you sure you want to delete governance label {resource}? "
    "The label must have no values assigned to any resources. This action cannot be undone."
)

REVOKE_PRINCIPAL_ACCESS = (
    "Are you sure you want to revoke access for principal {resource} "
    "on resource {resource_id}? This action cannot be undone."
)

CANCEL_ACCESS_REQUEST = (
    "Are you sure you want to cancel access request {resource}? "
    "This action cannot be undone."
)

DELETE_REQUEST_CONDITION = (
    "Are you sure you want to delete request condition {resource} "
    "from resource {resource_id}? This action cannot be undone."
)

DELETE_IAM_GOVERNANCE_BUNDLE = (
    "Are you sure you want to delete IAM governance bundle {resource}? "
    "This will remove the bundle and all its entitlement assignments. This action cannot be undone."
)

OPT_OUT_IAM_GOVERNANCE = (
    "Are you sure you want to opt out the Admin Console from entitlement management? "
    "This will disable entitlement management for the entire organization. This action cannot be undone."
)

# ---------------------------------------------------------------------------
# User credentials / sessions / factors
# ---------------------------------------------------------------------------

REVOKE_USER_SESSIONS = (
    "Are you sure you want to revoke all active sessions for user {resource}? "
    "This will immediately sign the user out of all devices and browsers."
)

UNENROLL_FACTOR = (
    "Are you sure you want to unenroll factor {resource} from user {user_resource}? "
    "The user will need to re-enroll this factor. This action cannot be undone."
)

REVOKE_TOKENS_FOR_CLIENT = (
    "Are you sure you want to revoke all refresh tokens for client {resource} "
    "belonging to user {user_resource}? All active sessions with this app will be terminated."
)

# ---------------------------------------------------------------------------
# Network Zones
# ---------------------------------------------------------------------------

DELETE_NETWORK_ZONE = (
    "Are you sure you want to delete network zone {resource}? "
    "Any policies referencing this zone will be affected. This action cannot be undone."
)

# ---------------------------------------------------------------------------
# Trusted Origins
# ---------------------------------------------------------------------------

DELETE_TRUSTED_ORIGIN = (
    "Are you sure you want to delete trusted origin {resource}? "
    "This may break CORS or iFrame embedding for the affected origin. This action cannot be undone."
)

# ---------------------------------------------------------------------------
# Authenticators
# ---------------------------------------------------------------------------

DELETE_CUSTOM_AAGUID = (
    "Are you sure you want to remove AAGUID {resource} from authenticator {authenticator_id}? "
    "New enrollments of that hardware key model will be blocked. This action cannot be undone."
)

# ---------------------------------------------------------------------------
# Application Credentials
# ---------------------------------------------------------------------------

REVOKE_APPLICATION_CSR = (
    "Are you sure you want to revoke CSR {resource} for application {app_resource}? "
    "The CSR cannot be published after revocation. This action cannot be undone."
)

DELETE_APPLICATION_JWK = (
    "Are you sure you want to delete JWK {resource} from application {app_resource}? "
    "OAuth clients using this key for authentication will immediately fail. This action cannot be undone."
)

DELETE_OAUTH2_CLIENT_SECRET = (
    "Are you sure you want to delete client secret {resource} from application {app_resource}? "
    "Clients using this secret will immediately be unable to authenticate. This action cannot be undone."
)
