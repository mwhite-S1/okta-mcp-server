════════════════════════════════════════
GROUPS
════════════════════════════════════════

## Lookup

| Goal | Tool | Parameters |
|------|------|------------|
| Find by exact name | `list_groups` | `search='profile.name eq "Okta.Admins"'` |
| Name starts with | `list_groups` | `search='profile.name sw "Engineering"'` |
| Names with dots / hyphens / underscores | `list_groups` | `search='profile.name eq "Okta.App.IAM_AI.Admins"'` — never use `q` for these |
| By type | `list_groups` | `search='type eq "OKTA_GROUP"'` |
| Combined filter | `list_groups` | `search='type eq "OKTA_GROUP" and profile.name sw "Sales"'` |
| Casual prefix browse (simple names only) | `list_groups` | `q="Engineering"` — avoid for names with dots or special characters |
| By ID | `get_group` | `group_id="00g..."` |

## Membership

| Goal | Tool | Parameters |
|------|------|------------|
| List members | `list_group_users` | `group_id` — paginated by default; add `fetch_all=True` only if user explicitly asks for all members |
| Add a member | `add_user_to_group` | `group_id, user_id` |
| Remove a member | `remove_user_from_group` | `group_id, user_id` |

## CRUD

| Goal | Tool | Parameters |
|------|------|------------|
| Create group | `create_group` | `profile={"name": "GroupName", "description": "..."}` |
| Update group | `update_group` | `group_id, profile={"name": "NewName", "description": "..."}` |

## Dynamic group rules

Rules auto-assign users to a group when their profile matches a condition expression. New rules are always created INACTIVE — activate after creating.

| Goal | Tool | Parameters |
|------|------|------------|
| List rules | `list_group_rules` | `search="keyword"` (optional) |
| Get rule detail | `get_group_rule` | `group_rule_id` |
| Create rule (INACTIVE) | `create_group_rule` | `rule_data={...}` — see `skill://detail/groups/rules` for full structure |
| Activate rule | `activate_group_rule` | `group_rule_id` |
| Deactivate rule | `deactivate_group_rule` | `group_rule_id` |
| Delete rule | `delete_group_rule` | `group_rule_id` — must be INACTIVE first |

## Delete

Deletion requires a two-step confirmation when elicitation is unavailable.

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Delete group (with elicitation) | `delete_group` | `group_id` — prompts for confirmation |
| Confirm deletion (no elicitation) | `confirm_delete_group` | `group_id, confirmation="DELETE"` — only call after user types DELETE |

## Owners

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List group owners | `list_group_owners` | `group_id` |
| Assign an owner | `assign_group_owner` | `group_id, user_id, type="USER"` |
| Remove an owner | `delete_group_owner` | `group_id, owner_id` |

## Applications assigned to group

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List apps assigned to a group | `list_group_apps` | `group_id` |
