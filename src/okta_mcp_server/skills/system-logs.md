════════════════════════════════════════
SYSTEM LOGS
════════════════════════════════════════

Log event fields: `actor` (who), `target` (what), `eventType`, `outcome.result`, `severity`, `published` (when).

## Query patterns

| Goal | Tool | Parameters |
|------|------|------------|
| Events since a timestamp | `get_logs` | `since="2024-01-01T00:00:00.000Z"` |
| Bounded time window | `get_logs` | `since="...", until="..."` |
| By event type | `get_logs` | `filter='eventType eq "user.session.start"'` |
| By actor Okta ID | `get_logs` | `filter='actor.id eq "00u..."'` |
| By actor login / email | `get_logs` | `filter='actor.alternateId eq "john.doe@example.com"'` |
| Failed outcomes only | `get_logs` | `filter='outcome.result eq "FAILURE"'` |
| Failed login attempts | `get_logs` | `filter='eventType eq "user.session.start" and outcome.result eq "FAILURE"'` |
| By target resource ID | `get_logs` | `filter='target.id eq "0oa..."'` |
| Keyword search (less reliable) | `get_logs` | `q="password reset"` — prefer filter when you know the eventType |
| All pages (bulk) | `get_logs` | `fetch_all=True, since="...", filter="..."` |

## Common eventType values

| eventType | Meaning |
|-----------|---------|
| `user.session.start` / `user.session.end` | Sign in / sign out |
| `user.account.lock` | Account locked out |
| `user.account.unlock_by_admin` | Admin unlocked the account |
| `user.account.update_profile` | Profile field changed |
| `user.mfa.factor.activate` | MFA factor enrolled |
| `user.authentication.auth_via_mfa` | MFA challenge used |
| `user.lifecycle.activate` | User activated |
| `user.lifecycle.deactivate` | User deactivated |
| `user.lifecycle.suspend` | User suspended |
| `user.lifecycle.unsuspend` | User unsuspended |
| `application.user_membership.add` | User assigned to app |
| `application.user_membership.remove` | User removed from app |
| `group.user_membership.add` | User added to group |
| `group.user_membership.remove` | User removed from group |
| `policy.evaluate_sign_on` | Sign-on policy evaluated |
| `user.account.reset_password` | Password reset initiated |
| `user.account.update_password` | Password changed |
| `app.oauth2.token.grant` | OAuth token granted |
| `app.oauth2.token.revoke` | OAuth token revoked |
