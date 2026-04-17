════════════════════════════════════════
PROFILE MAPPINGS & SCHEMAS
════════════════════════════════════════

## Profile mappings

Profile mappings define how attributes flow between sources (Okta, apps, directories) and targets.

| Goal | Tool | Parameters |
|------|------|------------|
| List all mappings | `list_profile_mappings` | (no params) |
| Mappings for a specific source | `list_profile_mappings` | `source_id="0oa..."` |
| Mappings for a specific target | `list_profile_mappings` | `target_id="0oa..."` |
| Get mapping detail (all attribute rules) | `get_profile_mapping` | `mapping_id` |
| Update attribute mapping rules | `update_profile_mapping` | `mapping_id, mappings={attributeName: {expression, pushStatus}}` |

## Schemas

| Goal | Tool | Parameters |
|------|------|------------|
| Get Okta user schema | `get_user_schema` | (no params) — shows all profile attributes including custom ones |
| Get group schema | `get_group_schema` | (no params) |
| Get app user schema | `get_application_user_schema` | `app_id` — shows app-specific profile attributes |
| Update group schema | `update_group_schema` | `schema_data={...}` |

## User Profile Schema (Write)

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Update Okta user profile schema | `update_user_profile` | `schema_id="default", schema_data={...}` |
| Update app user profile schema | `update_application_user_profile` | `app_id, schema_data={...}` |

These tools modify the schema definition (add/remove/update custom attributes), not individual user profiles.
