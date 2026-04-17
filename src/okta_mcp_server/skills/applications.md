════════════════════════════════════════
APPLICATIONS
════════════════════════════════════════

## Lookup

| Goal | Tool | Parameters |
|------|------|------------|
| Find by name (casual) | `list_applications` | `q="Salesforce"` |
| Active apps only | `list_applications` | `filter='status eq "ACTIVE"'` |
| Apps assigned to a specific user | `list_applications` | `filter='user.id eq "00u..."'` |
| Apps assigned to a specific group | `list_applications` | `filter='group.id eq "00g..."'` |
| Get app by ID | `get_application` | `app_id="0oa..."` |

## Assignments

| Goal | Tool | Parameters |
|------|------|------------|
| List users in an app | `list_application_users` | `app_id` |
| List groups in an app | `list_application_groups` | `app_id` |
| Assign a user | `assign_user_to_application` | `app_id, app_user={"id": "00u..."}` |
| Remove a user | `unassign_user_from_application` | `app_id, user_id` |
| Assign a group | `assign_group_to_application` | `app_id, group_id` |
| Remove a group | `unassign_group_from_application` | `app_id, group_id` |

## Application Lifecycle

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Create application | `create_application` | `app_data={...}` — full OIN/custom app schema |
| Update application settings | `update_application` | `app_id, app_data={...}` |
| Activate application | `activate_application` | `app_id` |
| Deactivate application | `deactivate_application` | `app_id` |
| Delete application (with elicitation) | `delete_application` | `app_id` |
| Confirm delete (no elicitation) | `confirm_delete_application` | `app_id, confirmation="DELETE"` |
| Assign sign-on policy | `assign_application_policy` | `app_id, policy_id` |
| Upload logo | `upload_application_logo` | `app_id, logo_file` |
| Preview SAML metadata | `preview_saml_metadata` | `app_id, key_id` |

## Application Users (Direct Assignments)

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Get a user's app profile | `get_application_user` | `app_id, user_id` |
| Update user's app profile | `update_application_user` | `app_id, user_id, profile={...}` |

## Application Groups (Direct Assignments)

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Get a group assignment | `get_application_group_assignment` | `app_id, group_id` |
| Update group assignment | `update_application_group_assignment` | `app_id, group_id, priority, profile` |

## Application Features (Provisioning)

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List features | `list_application_features` | `app_id` |
| Get feature | `get_application_feature` | `app_id, feature_name` |
| Update feature | `update_application_feature` | `app_id, feature_name, capabilities={...}` |

## Application Tokens (SSWS)

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List tokens | `list_application_tokens` | `app_id, expand="scope"` (optional) |
| Get token | `get_application_token` | `app_id, token_id` |
| Revoke one token | `revoke_application_token` | `app_id, token_id` |
| Revoke all tokens | `revoke_all_application_tokens` | `app_id` |

## OAuth Scope Consent Grants

> **⚠ These tools return 403** for user-delegated tokens (even Super Admin). Okta restricts `/api/v1/apps/{id}/grants` to SSWS/service tokens only.

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List scope grants | `list_scope_consent_grants` | `app_id, expand="scope"` — ⚠ 403 with delegated tokens |
| Get scope grant | `get_scope_consent_grant` | `app_id, grant_id` — ⚠ 403 |
| Grant scope consent | `grant_consent_to_scope` | `app_id, issuer, scope_id` — ⚠ 403 |
| Revoke scope grant | `revoke_scope_consent_grant` | `app_id, grant_id` — ⚠ 403 |

## Group Push Mappings

Push groups from Okta to an app. App must have `GROUP_PUSH` in its `features` list.

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List push mappings | `list_group_push_mappings` | `app_id` |
| Get mapping | `get_group_push_mapping` | `app_id`, `mapping_id` |
| Create mapping | `create_group_push_mapping` | `app_id`, `mapping={...}` — see `skill://detail/applications/group-push` for targetGroupName vs targetGroupId rules |
| Update mapping status | `update_group_push_mapping` | `app_id`, `mapping_id`, `update={"status": "ACTIVE"\|"INACTIVE"}` |
| Delete mapping | `delete_group_push_mapping` | `app_id`, `mapping_id`, `delete_target_group=false` — mapping must be INACTIVE first |

**Delete workflow**: deactivate (set INACTIVE) → delete. See `skill://detail/applications/group-push` for details.

## Provisioning Connections

Configure how Okta provisions users into the app (token or OAuth 2.0).

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Get current connection | `get_default_provisioning_connection` | `app_id` |
| Configure token-based | `update_default_provisioning_connection` | `app_id, connection={"authScheme":"TOKEN","token":"<t>"}` |
| Configure OAuth 2.0 | `update_default_provisioning_connection` | `app_id, connection={"authScheme":"OAUTH2","credentials":{...}}` |
| Activate connection | `activate_provisioning_connection` | `app_id` |
| Deactivate connection | `deactivate_provisioning_connection` | `app_id` |
| Get JWKS (for Org2Org target) | `get_provisioning_connection_jwks` | `app_id` |
| Complete OAuth consent | `verify_provisioning_connection` | `app_id, app_name, code, state` |

See `skill://detail/applications/provisioning` for setup flow and `app_name` enum values.
