════════════════════════════════════════
SYSTEM LOGS
════════════════════════════════════════

Log event fields: `actor` (who), `target` (what), `eventType`, `outcome.result`, `severity`, `published` (when).

⚠ **Default time window:** Always set `since` to at least 24 hours ago (7 days preferred) unless the user specifies a narrower range. Omitting `since` returns Okta's internal default window which may be very short and return empty results. Never call `get_logs` without a `since` parameter.

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
| All pages (bulk) | `get_logs` | `fetch_all=True, since="...", filter="..."` — ⚠ only use when user explicitly asks for ALL/complete/full/entire events; returns hundreds of thousands of characters |
| **Complete export** | `create_export` | `tool="get_logs", tool_params={fetch_all: true, since="...", filter="..."}` — **must include `fetch_all: true`** when user says "complete", "all", "full", "entire", or "everything"; without it only 100 entries are returned |

## Common scenario quick-reference

When a user describes a scenario, use these filters directly. For the full table see `skill://detail/system-logs/scenarios`.

| Scenario | filter |
|---|---|
| Who signed in | `eventType eq "user.session.start"` |
| Failed logins | `eventType eq "user.session.start" and outcome.result eq "FAILURE"` |
| Account lockouts | `eventType eq "user.account.lock"` |
| Password resets / changes | `eventType eq "user.account.reset_password"` or `eventType eq "user.account.update_password"` |
| Group membership changes | `eventType eq "group.user_membership.add" or eventType eq "group.user_membership.remove"` |
| App assignment changes | `eventType eq "application.user_membership.add" or eventType eq "application.user_membership.remove"` |
| MFA factor enrolled/removed | `eventType eq "user.mfa.factor.activate"` or `eventType eq "user.mfa.factor.deactivate"` |
| User lifecycle (create/activate/deactivate) | `eventType eq "user.lifecycle.create"` / `"user.lifecycle.activate"` / `"user.lifecycle.deactivate"` |

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
