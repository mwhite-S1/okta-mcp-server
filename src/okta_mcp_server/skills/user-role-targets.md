════════════════════════════════════════
USER ADMIN ROLE TARGETS
════════════════════════════════════════

By default, admin roles assigned to a user apply org-wide. Adding targets
scopes the role to specific apps or groups — essential for least-privilege.

**Common use case**: Assign USER_ADMIN or HELP_DESK_ADMIN scoped to a specific group
so a team lead can only manage their own department's users.

## View Targets

| Goal | Tool | Parameters |
|------|------|------------|
| Get all targets for a role | `get_user_role_targets` | `user_id, role_id` — role key (e.g. "USER_ADMIN") or assignment ID |
| List app targets | `list_user_app_role_targets` | `user_id, role_assignment_id` |
| List group targets | `list_user_group_role_targets` | `user_id, role_assignment_id` |

## Application Targets

| Goal | Tool | Parameters |
|------|------|------------|
| Scope to all apps | `assign_all_apps_as_user_role_target` | `user_id, role_assignment_id` — clears specific targets |
| Scope to an app type | `assign_app_target_to_user_role` | `user_id, role_assignment_id, app_name="salesforce"` |
| Remove app type target | `unassign_app_target_from_user_role` | `user_id, role_assignment_id, app_name` |
| Scope to specific instance | `assign_app_instance_target_to_user_role` | `user_id, role_assignment_id, app_name, app_id` |
| Remove instance target | `unassign_app_instance_target_from_user_role` | `user_id, role_assignment_id, app_name, app_id` |

## Group Targets

| Goal | Tool | Parameters |
|------|------|------------|
| Scope to a group | `assign_group_target_to_user_role` | `user_id, role_assignment_id, group_id` |
| Remove group target | `unassign_group_target_from_user_role` | `user_id, role_assignment_id, group_id` |

**Note**: Role assignment IDs are returned by the users API when listing a user's assigned roles.
To get the role assignment ID: call `get_user` or list the user's roles via the Okta API first.
