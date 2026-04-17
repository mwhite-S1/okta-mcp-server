════════════════════════════════════════
GOVERNANCE
════════════════════════════════════════

> **ORN format used in this org:**
> Apps: `orn:oktapreview:idp:00o1e0scx8qAmdRrp1d7:apps:saasure:{appId}`
> Users: `orn:okta:directory:00o1e0scx8qAmdRrp1d7:users:{userId}`
> Entitlements: `orn:okta:governance:00o1e0scx8qAmdRrp1d7:entitlements:{entId}`
> Entitlement values: `orn:okta:governance:00o1e0scx8qAmdRrp1d7:entitlement-values:{valId}`
> Governance-enrolled Okta Admin Console app ID: `0oa1e0scxcfZCJlXB1d7`
> Org ID: `00o1e0scx8qAmdRrp1d7`

## Access requests

| Goal | Tool | Parameters |
|------|------|------------|
| List all requests | `list_access_requests` | (no params) |
| Pending only | `list_access_requests` | `filter='status eq "PENDING"'` |
| By requester ID | `list_access_requests` | `filter='requesterId eq "00u..."'` |
| Sorted newest first | `list_access_requests` | `order_by="created desc"` |
| Get request detail | `get_access_request` | `request_id` |
| Create request | `create_access_request` | `catalog_entry_id`, `requester_id` (must be session user for self-request; on-behalf requires resource setting), `justification` |
| Cancel request | `cancel_access_request` | ⚠ **Always fails 405** — Okta governance v2 API has no cancel endpoint. Cancellation is performed by the approval workflow service only. |

> **⚠ `create_access_request` caveats:**
> - Use **child** catalog entry IDs (from `list_access_catalog_entries` with `filter='parent eq "{parentEntryId}"'`). Parent/top-level entries have `requestable: false`.
> - `requester_id` must match the session user's Okta ID for self-requests. Requesting on behalf of another user requires the resource's `validRequestOnBehalfOfSettings` to be non-empty.
> - Requests may be auto-rejected immediately by external approval sequences.

End-user self-service (own requests):

| Goal | Tool | Parameters |
|------|------|------------|
| List my requests | `list_access_requests` | (no params) |
| Submit my request | `create_my_access_request` | `request_data={...}` |
| Get my request | `get_my_access_request` | `request_id` |
| Cancel my request | `cancel_my_access_request` | `request_id` |
| Browse access catalog | `list_my_catalog_entries` | `filter='not(parent pr)'` for top-level entries |
| Get catalog entry | `get_my_catalog_entry` | `entry_id` |

## Entitlements

Permissions or roles within an application or resource. Only governance-enrolled apps have entitlements.

> **⚠ Entitlement caveats** — see `skill://detail/governance/entitlements` for filter requirements, bundle creation rules, and PUT field requirements.

| Goal | Tool | Parameters |
|------|------|------------|
| List by app (**filter required**) | `list_entitlements` | `filter='parent.externalId eq "0oa..." AND parent.type eq "APPLICATION"'` |
| Filter by name | `list_entitlements` | `filter='parent.externalId eq "0oa..." AND name co "admin"'` |
| Get entitlement detail | `get_entitlement` | `entitlement_id` |
| List entitlement values | `list_entitlement_values` | `entitlement_id` |
| List entitlement bundles | `list_entitlement_bundles` | (no params) |
| Get bundle | `get_entitlement_bundle` | `bundle_id`, optionally `include="full_entitlements"` |
| Create bundle | `create_entitlement_bundle` | `bundle={"name":"...","target":{"externalId":"0oa...","type":"APPLICATION"},"entitlements":[{"id":"esp...","values":[{"id":"ent..."}]}]}` |
| Update bundle (replace) | `update_entitlement_bundle` | `bundle_id, bundle` — must include `id`, `targetResourceOrn`, `target`, and `status` |

## Governance labels

Tag resources for use in certification campaigns and policies.

| Goal | Tool | Parameters |
|------|------|------------|
| All labels | `list_governance_labels` | (no params — do NOT pass `limit`, API returns 400) |
| Name starts with | `list_governance_labels` | `filter='name sw "team"'` |
| Name contains | `list_governance_labels` | `filter='name co "finance"'` |
| Get label detail | `get_governance_label` | `label_id` |
| Create label | `create_governance_label` | `name`, `values=[{"name":"...", "metadata":{"backgroundColor":"red"}}]`. Colors: red/orange/yellow/green/blue/purple/teal/beige/gray |
| Update label | `update_governance_label` | `label_id`, `operations=[{"op":"REPLACE","path":"/name","value":"...","refType":"LABEL-CATEGORY"}]` |
| Delete label | `delete_governance_label` | `label_id` (elicitation confirmation required; label must have no assigned values) |
| Assign labels to resources | `assign_governance_labels` | `resource_orns=["orn:oktapreview:idp:{orgId}:apps:saasure:{appId}"]`, `label_value_ids=["lbl..."]` |
| Remove labels from resources | `unassign_governance_labels` | same params as assign |
| Resources with a label | `list_labeled_resources` | `filter='labelValueId eq "lbl..."'` or `filter='resourceType eq "apps"'` |

## Certification campaigns

| Goal | Tool | Parameters |
|------|------|------------|
| List campaigns | `list_certification_campaigns` | `filter, order_by` (e.g. `order_by="created desc"`) |
| Get campaign detail | `get_certification_campaign` | `campaign_id` |
| Create campaign | `create_certification_campaign` | `campaign_data={...}` |
| Launch campaign | `launch_certification_campaign` | `campaign_id` |
| End campaign | `end_certification_campaign` | `campaign_id` |
| Delete campaign | `delete_certification_campaign` | `campaign_id` |
| List reviews in campaign | `list_certification_reviews` | `campaign_id` |
| Get review detail | `get_certification_review` | `campaign_id`, `review_id` |
| Reassign review | `reassign_certification_review` | `campaign_id`, `review_id`, `assignee_id` |
| Get cert settings | `get_certification_settings` | (no params) ⚠ 403 even with governance scopes — needs dedicated certification admin role |
| Update cert settings | `update_certification_settings` | `settings={"integrations":{"settings":[...]}}` — merge-patch object (only `integrations` field), NOT JSON Patch list |

## IAM governance bundles

| Goal | Tool | Parameters |
|------|------|------------|
| Opt-in status | `get_iam_governance_opt_in_status` | (no params) |
| List bundles | `list_iam_governance_bundles` | (no params) |
| Get bundle | `get_iam_governance_bundle` | `bundle_id` |
| Create bundle | `create_iam_governance_bundle` | `bundle_data={...}` |
| Replace bundle | `replace_iam_governance_bundle` | `bundle_id, bundle_data={...}` |
| Delete bundle | `delete_iam_governance_bundle` | `bundle_id` |
| List bundle entitlements | `list_iam_bundle_entitlements` | `bundle_id` |
| List bundle entitlement values | `list_iam_bundle_entitlement_values` | `bundle_id`, `entitlement_id` |

## Request types

| Goal | Tool | Parameters |
|------|------|------------|
| List request types | `list_request_types` | optional `filter='status eq "ACTIVE"'`, `order_by="name%20asc"`, `after`, `limit` |
| Get request type | `get_request_type` | `request_type_id` |
| Create request type | `create_request_type` | `type_data={...}` |
| Publish request type | `publish_request_type` | `request_type_id` |
| Unpublish request type | `unpublish_request_type` | `request_type_id` |
| Delete request type | `delete_request_type` | `request_type_id` |

## Request Conditions & Sequences

Request conditions define approval logic for access request types.

> **⚠ resource_id is the app ID** (e.g. `0oa...`), NOT the catalog entry ID. Use the app ID from `list_applications`.

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List conditions | `list_request_conditions` | `resource_id` = app ID |
| Get condition | `get_request_condition` | `resource_id` = app ID, `request_condition_id` |
| Create condition | `create_request_condition` | `resource_id` = app ID, `condition_data={...}` |
| Update condition | `update_request_condition` | `resource_id`, `request_condition_id`, `condition_data` |
| Delete condition | `delete_request_condition` | `resource_id`, `request_condition_id` |
| Activate condition | `activate_request_condition` | `resource_id`, `request_condition_id` |
| Deactivate condition | `deactivate_request_condition` | `resource_id`, `request_condition_id` |
| List sequences | `list_request_sequences` | `resource_id` = app ID |
| Get sequence | `get_request_sequence` | `resource_id` = app ID, `request_sequence_id` |
| Delete sequence | `delete_request_sequence` | `resource_id`, `request_sequence_id` |
| List settings | `list_request_settings` | (no params) |
| Update settings | `update_request_settings` | `settings={"subprocessorsAcknowledged": true}` — valid fields: `subprocessorsAcknowledged` (bool), `integrations` (dict, beta: `{"settings":[{"type":"SLACK",...}]}`) |

## Resource owners

| Goal | Tool | Parameters |
|------|------|------------|
| List resource owners | `list_resource_owners` | `filter='parentResourceOrn eq "orn:oktapreview:idp:{orgId}:apps:saasure:{appId}"'` |
| List resource owners catalog | `list_resource_owners_catalog` | `filter='parentResourceOrn eq "orn:okta:idp:{orgId}:apps:{appType}:{appId}" AND resource.type eq "entitlement-bundles"'` — both fields required; `orn:okta:idp:` prefix works |
| Create resource owner | `create_resource_owner` | `resource_id`, `owner_data={...}` |
| Update resource owners | `update_resource_owners` | `resource_id`, `owners=[...]` |

## Risk rules

> **⚠ `conflict_criteria` structure is complex** — see `skill://detail/governance/risk-rules` for the full JSON structure and field requirements.

| Goal | Tool | Parameters |
|------|------|------------|
| List rules | `list_risk_rules` | (no params); optional `filter='resourceOrn eq "orn:..." AND name eq "..."'` |
| Get rule | `get_risk_rule` | `rule_id` |
| Create rule | `create_risk_rule` | `name`, `resources=[{"resourceOrn":"orn:..."}]`, `conflict_criteria={...}` (see detail resource) |
| Update rule | `update_risk_rule` | `rule_id`, `name`, `description`, `notes`, `conflict_criteria` — `type` and `resources` cannot be updated |
| Delete rule | `delete_risk_rule` | `rule_id` |
| Assess principal | `assess_risk_rules` | `principal_orn="orn:okta:directory:{orgId}:users:{userId}"` (always `orn:okta:` prefix), `resource_orns` **required** — use bundle ORNs: `"orn:okta:governance:{orgId}:entitlement-bundles:{id}"` (get from `list_entitlement_bundles`); returns empty when no rules configured |

## Collections

> **⚠ `list_collections` returns 403** despite governance scopes — likely requires org-level admin permission beyond `okta.governance.*` scopes.

| Goal | Tool | Parameters |
|------|------|------------|
| List collections | `list_collections` | (no params) — ⚠ 403 |
| Get collection | `get_collection` | `collection_id` |
| Create collection | `create_collection` | `collection_data={...}` |
| Update collection | `update_collection` | `collection_id, collection_data={...}` |
| Delete collection | `delete_collection` | `collection_id` |
| List collection resources | `list_collection_resources` | `collection_id` |
| Add resource to collection | `add_collection_resources` | `collection_id`, `resource_orns=[...]` |
| Remove resource from collection | `remove_collection_resource` | `collection_id`, `resource_id` |

## Principal entitlements

> **⚠ Known issues:** `get_principal_access` and `list_principal_entitlements` return 400 "filter condition is invalid" — the correct filter field name is unknown (neither `principalId eq "..."` nor `principal.id eq "..."` works). `get_principal_entitlement_history` returns 404 "Not found: Principal" for users without governance activity history. These tools are blocked pending Okta support clarification.

| Goal | Tool | Parameters |
|------|------|------------|
| List entitlements for a principal | `list_principal_entitlements` | `filter` — ⚠ correct field unknown |
| Get principal access summary | `get_principal_access` | `filter` — ⚠ correct field unknown |
| Revoke principal access | `revoke_principal_access` | `principal_id, access_id` |
| Entitlement history | `get_principal_entitlement_history` | `principal_id` — ⚠ 404 if not a governance principal |
| Entitlement changes | `get_principal_entitlements_change` | `principal_id, change_id` |
| Principal governance settings | `get_principal_governance_settings` | `principal_id` — uses `/delegates?principalId={id}` internally |
| Update principal settings | `update_principal_governance_settings` | `principal_id`, `delegate_appointments=[{"delegate":{"type":"OKTA_USER","externalId":"00u..."},"note":"..."}]`; use `[]` to clear all |

## Resource settings

> **⚠ `resource_id` must be a full ORN** (e.g. `orn:oktapreview:idp:{orgId}:apps:saasure:{appId}`), not a bare app ID.

| Goal | Tool | Parameters |
|------|------|------------|
| Get resource entitlement settings | `get_resource_entitlement_settings` | `resource_id` = full app ORN |
| Update resource entitlement settings | `update_resource_entitlement_settings` | `resource_id` = full app ORN, `settings={"status":"OPTED_IN"}` — status values: `"OPTED_IN"` or `"OPTED_OUT"` |
| Get resource request settings | `get_resource_request_settings` | `resource_id` = full app ORN |
| Update resource request settings | `update_resource_request_settings` | `resource_id` = full app ORN, `settings_data` |

## Security Access Reviews (Admin)

Access reviews let admins create periodic reviews of who has access to what.

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List reviews | `list_security_access_reviews` | `filter, after, limit, order_by` |
| Create review | `create_security_access_review` | `review_data={...}` |
| Get review | `get_security_access_review` | `security_access_review_id` |
| Update review | `update_security_access_review` | `security_access_review_id, review_data={...}` |
| Get stats | `get_security_access_review_stats` | `security_access_review_id` |
| List review actions | `list_security_access_review_actions` | `security_access_review_id` |
| Submit action | `submit_security_access_review_action` | `security_access_review_id, action_id, decision` |
| Create summary | `create_security_access_review_summary` | `security_access_review_id` |

## Security Access Reviews (My / Enduser)

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List my reviews | `list_my_security_access_reviews` | `filter, after, limit` |
| Get my review | `get_my_security_access_review` | `security_access_review_id` |
| My review stats | `get_my_security_access_review_stats` | `security_access_review_id` |
| My review history | `get_my_security_access_review_history` | `security_access_review_id` |
| Get a principal in my review | `get_my_security_access_review_principal` | `security_access_review_id, principal_id` |
| Access anomalies | `get_my_security_access_review_access_anomalies` | `security_access_review_id, access_id` |
| List accesses for review | `list_my_security_access_review_accesses` | `security_access_review_id` |
| List sub-accesses | `list_my_security_access_review_sub_accesses` | `security_access_review_id, access_id` |
| List my actions | `list_my_security_access_review_actions` | `security_access_review_id` |
| Submit my action | `submit_my_security_access_review_action` | `security_access_review_id, action_id, decision` |
| Submit access action | `submit_my_security_access_review_access_action` | `security_access_review_id, access_id, action_id, decision` |
| Add comment | `add_my_security_access_review_comment` | `security_access_review_id, comment` |
| Create summary | `create_my_security_access_review_summary` | `security_access_review_id` |
| Create access summary | `create_my_security_access_review_access_summary` | `security_access_review_id, access_id` |

## Grants

Governance grants represent a principal's authorized access to a resource. `create_grant` uses a **discriminated union** on `grantType` — see `skill://detail/governance/grants` for the full type table and examples.

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List grants | `list_grants` | `filter='target.externalId eq "0oa..." AND target.type eq "APPLICATION"'` |
| Create grant (bundle) | `create_grant` | `grant={"grantType":"ENTITLEMENT-BUNDLE","entitlementBundleId":"gbun...","targetPrincipal":{"externalId":"00u...","type":"OKTA_USER"}}` |
| Create grant (entitlement) | `create_grant` | See `skill://detail/governance/grants` for full structure |
| Get grant | `get_grant` | `grant_id` |
| Update grant (replace) | `update_grant` | `grant_id, grant` — **must include all system fields** (`id`, `_links`, `created`, `createdBy`, `lastUpdated`, `lastUpdatedBy`, `status`) |
| Patch grant (expiry only) | `patch_grant` | `grant_id, patch_data={"id":"gra...","scheduleSettings":{"expirationDate":"2027-01-01T00:00:00Z"}}` |

> **⚠ `list_grants` filter:** Use `target.externalId` + `target.type`, not `resourceId`.
> **⚠ `update_grant` (PUT):** Include all fields from the GET response, not just writable fields.
> **⚠ `patch_grant`:** Only supports updating `scheduleSettings.expirationDate`. Not a JSON Patch operations endpoint.

## Access Catalog

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List catalog entries (admin) | `list_access_catalog_entries` | `filter, after, limit` |
| Get catalog entry (admin) | `get_access_catalog_entry` | `entry_id` |
| Get request fields for entry | `get_catalog_entry_request_fields` | `entry_id` |
| List user catalog entries | `list_user_catalog_entries` | `user_id` |
| List enduser catalog entries | `list_my_catalog_entries` | `filter='not(parent pr)'` for top-level |
| Get enduser catalog entry | `get_my_catalog_entry` | `entry_id` |
| Get enduser request fields | `get_my_catalog_entry_request_fields` | `entry_id` |
| Get per-user request fields | `get_my_catalog_entry_user_request_fields` | `entry_id, user_id` ⚠ 409 if resource doesn't allow "on behalf of" |
| List users for catalog entry | `list_my_catalog_entry_users` | `entry_id` ⚠ 409 same restriction |

## Governance Settings

| Goal | Tool | Key Parameters |
|------|------|----------------|
| IAM governance opt-in status | `get_iam_governance_opt_in_status` | (no params) |
| Opt in | `opt_in_iam_governance` | (no params) |
| Opt out | `opt_out_iam_governance` | (no params) |
| My governance settings | `get_my_governance_settings` | (no params) |
| Update my settings | `update_my_governance_settings` | `settings_data={...}` |
| Update org settings | `update_org_governance_settings` | `settings={"governanceAI":{"securityAccessReview":{"enabled":true}}}` or `{"delegates":{"enduser":{"permissions":["READ","WRITE"]}}}` — merge-patch object, NOT JSON Patch list |
| List governance integrations | `list_governance_integrations` | (no params) |
| Create governance integration | `create_governance_integration` | `integration_data={...}` |
| Delete governance integration | `delete_governance_integration` | `integration_id` |

## Principal & Delegate Access

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List all delegates | `list_governance_delegates` | optional `principal_id`, `delegate_id` |
| Org-level delegate settings | `get_governance_delegate_settings` | (no params) |
| My delegate users | `list_my_delegate_users` | `filter` **required** (e.g. `filter='firstName sw "a"'`); 400 without it |
| Principal governance settings | `get_principal_governance_settings` | `principal_id` |
| Update principal settings | `update_principal_governance_settings` | `principal_id`, `delegate_appointments=[{"delegate":{"type":"OKTA_USER","externalId":"00u..."},"note":"..."}]`; use `[]` to clear |

## Misc

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Get governance operation (async) | `get_governance_operation` | `operation_id` |
| List governance teams | `list_governance_teams` | optional `filter='name eq "..."'`, `after`, `limit` |
| Add message to request | `add_request_message` | `request_id, message` |
