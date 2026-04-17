════════════════════════════════════════
USERS
════════════════════════════════════════

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
