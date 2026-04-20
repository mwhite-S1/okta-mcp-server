════════════════════════════════════════
USERS
════════════════════════════════════════

## Lookup

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Find by email / login | `list_users` | `search='profile.login eq "jane.doe@example.com"'` — always use `search`, never `q`, for emails |
| Find by exact first+last name | `list_users` | `search='profile.firstName eq "Jane" and profile.lastName eq "Doe"'` |
| Display name contains | `list_users` | `search='profile.displayName co "Jane"'` |
| Find by department | `list_users` | `search='profile.department eq "Engineering"'` |
| Find by status | `list_users` | `search='status eq "ACTIVE"'` — valid values: ACTIVE, DEPROVISIONED, LOCKED_OUT, PASSWORD_EXPIRED, PROVISIONED, RECOVERY, STAGED, SUSPENDED |
| Prefix browse (simple names, no dots) | `list_users` | `q="jane"` — only for simple strings; breaks on dots, @, hyphens |
| Get one user by ID | `get_user` | `user_id="00u..."` |
| Get one user by login | `get_user` | `user_id="jane.doe@example.com"` — login works as the ID |
| List members of a group | `list_group_users` | `group_id="00g..."` — **use this, not `list_users`, when listing members of a specific group** |
| List all users (paginated) | `list_users` | no filter — returns first page only |

⚠ **Search parameter rules:**
- Use `search` (SCIM 2.0) whenever the value contains a dot, @, hyphen, or space — it is indexed and reliable.
- Use `q` only for casual prefix browsing with plain single-word values.
- Never use `q` for email addresses or logins — the dot breaks matching and returns empty results.

## Lifecycle

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Create user (staged) | `create_user` | `profile={...}, activate=False` |
| Create and activate | `create_user` | `profile={...}, activate=True` |
| Activate a staged user | `activate_user` | `user_id, send_email=True` |
| Deactivate | `deactivate_user` | `user_id` |
| Suspend | `suspend_user` | `user_id` |
| Unsuspend | `unsuspend_user` | `user_id` |
| Unlock | `unlock_user` | `user_id` |
| Reactivate deprovisioned | `reactivate_user` | `user_id` |
| Delete (must be deactivated first) | `delete_deactivated_user` | `user_id` |
| Update profile fields | `update_user_profile` | `user_id, profile={field: value}` |
| Replace full user object | `replace_user` | `user_id, user={...}` |

## Credentials

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Send password reset email | `reset_password` | `user_id, send_email=True` |
| Get reset URL (no email) | `reset_password` | `user_id, send_email=False` → returns `resetPasswordUrl` |
| Expire password (force change at next login) | `expire_password` | `user_id` |
| Expire + get temp password | `expire_password_with_temp_password` | `user_id, revoke_sessions=False` |
| Initiate self-service forgot-password | `forgot_password` | `user_id, send_email=True` |
| Change password (knows current) | `change_password` | `user_id, old_password, new_password, strict=False` |
| Change recovery question | `change_recovery_question` | `user_id, password, recovery_question, recovery_answer` |

## Factors (MFA)

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List enrolled factors | `list_factors` | `user_id` |
| Get factor detail | `get_factor` | `user_id, factor_id` |
| List factor types the user can enroll | `list_supported_factors` | `user_id` |
| List available security questions | `list_supported_security_questions` | `user_id` |
| Enroll a factor | `enroll_factor` | `user_id, factor_type, provider, ...` |
| Activate enrolled factor | `activate_factor` | `user_id, factor_id, activation_token` |
| Re-send activation (email/SMS) | `resend_enroll_factor` | `user_id, factor_id` |
| Verify / challenge a factor | `verify_factor` | `user_id, factor_id, pass_code` |
| Check async verification status | `get_factor_transaction_status` | `user_id, factor_id, transaction_id` |
| Unenroll one factor | `unenroll_factor` | `user_id, factor_id` |
| Wipe all factors (re-enroll at next login) | `reset_factors` | `user_id` |

## Sessions & Token Management

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Revoke all active sessions | `revoke_user_sessions` | `user_id, oauth_tokens=False` |
| List OAuth refresh tokens for a client | `list_refresh_tokens_for_user_and_client` | `user_id, client_id` |
| Get a specific refresh token | `get_refresh_token_for_user_and_client` | `user_id, client_id, token_id` |
| Revoke one refresh token | `revoke_token_for_user_and_client` | `user_id, client_id, token_id` |
| Revoke all refresh tokens for a client | `revoke_tokens_for_user_and_client` | `user_id, client_id` |

**`list_user_blocks`** — returns why a user is blocked from signing in (rate limits, lockout, etc.).
