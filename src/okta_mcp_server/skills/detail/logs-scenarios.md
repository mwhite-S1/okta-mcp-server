════════════════════════════════════════
SYSTEM LOGS — SCENARIO REFERENCE
════════════════════════════════════════

When a user describes a scenario rather than a raw event type, map it to the filter below and call `get_logs` immediately with that filter + a `since` value.

## Authentication & Sessions

| User asks about… | filter |
|---|---|
| Who signed in | `eventType eq "user.session.start"` |
| Who signed out | `eventType eq "user.session.end"` |
| Failed login attempts | `eventType eq "user.session.start" and outcome.result eq "FAILURE"` |
| MFA challenges | `eventType eq "user.authentication.auth_via_mfa"` |
| SSO to an application | `eventType eq "user.authentication.sso"` |
| Sign-on policy evaluated | `eventType eq "policy.evaluate_sign_on"` |
| Passwordless / device assurance | `eventType eq "user.authentication.auth_via_device_assurance"` |

## Account Lockout & Recovery

| User asks about… | filter |
|---|---|
| Accounts locked out | `eventType eq "user.account.lock"` |
| Admin unlocked account | `eventType eq "user.account.unlock_by_admin"` |
| Self-service unlock | `eventType eq "user.account.unlock_by_self_service"` |
| Password reset initiated | `eventType eq "user.account.reset_password"` |
| Password changed by user | `eventType eq "user.account.update_password"` |
| Password expired | `eventType eq "user.account.expire_password"` |

## User Lifecycle

| User asks about… | filter |
|---|---|
| Users created | `eventType eq "user.lifecycle.create"` |
| Users activated | `eventType eq "user.lifecycle.activate"` |
| Users deactivated | `eventType eq "user.lifecycle.deactivate"` |
| Users suspended | `eventType eq "user.lifecycle.suspend"` |
| Users unsuspended | `eventType eq "user.lifecycle.unsuspend"` |
| Users deleted | `eventType eq "user.lifecycle.delete"` |
| Profile fields changed | `eventType eq "user.account.update_profile"` |

## Group Membership

| User asks about… | filter |
|---|---|
| Any group membership change | `eventType eq "group.user_membership.add" or eventType eq "group.user_membership.remove"` |
| Users added to groups | `eventType eq "group.user_membership.add"` |
| Users removed from groups | `eventType eq "group.user_membership.remove"` |
| Groups created | `eventType eq "group.lifecycle.create"` |
| Groups deleted | `eventType eq "group.lifecycle.delete"` |
| Group rule activated | `eventType eq "group.rule.activate"` |
| Group rule deactivated | `eventType eq "group.rule.deactivate"` |

## Application Access

| User asks about… | filter |
|---|---|
| Any app assignment change | `eventType eq "application.user_membership.add" or eventType eq "application.user_membership.remove"` |
| User assigned to app | `eventType eq "application.user_membership.add"` |
| User removed from app | `eventType eq "application.user_membership.remove"` |
| App created | `eventType eq "application.lifecycle.create"` |
| App activated | `eventType eq "application.lifecycle.activate"` |
| App deactivated | `eventType eq "application.lifecycle.deactivate"` |
| App deleted | `eventType eq "application.lifecycle.delete"` |

## MFA / Factors

| User asks about… | filter |
|---|---|
| Factor enrolled | `eventType eq "user.mfa.factor.activate"` |
| Factor removed | `eventType eq "user.mfa.factor.deactivate"` |
| All factors reset by admin | `eventType eq "user.mfa.factor.reset_all"` |
| Push notification sent | `eventType eq "user.mfa.okta_verify.push_sent"` |
| Push accepted | `eventType eq "user.mfa.okta_verify.push_accepted"` |
| Push denied / rejected | `eventType eq "user.mfa.okta_verify.push_denied"` |

## OAuth & Tokens

| User asks about… | filter |
|---|---|
| OAuth token granted | `eventType eq "app.oauth2.token.grant"` |
| OAuth token revoked | `eventType eq "app.oauth2.token.revoke"` |
| Refresh token revoked | `eventType eq "app.oauth2.as.token.refresh_token_revoked"` |

## Admin & Privilege Changes

| User asks about… | filter |
|---|---|
| Admin role granted | `eventType eq "user.account.privilege.grant"` |
| Admin role revoked | `eventType eq "user.account.privilege.revoke"` |
| Policy created | `eventType eq "policy.lifecycle.create"` |
| Policy updated | `eventType eq "policy.lifecycle.update"` |
| Policy deleted | `eventType eq "policy.lifecycle.delete"` |
| Policy rule created | `eventType eq "policy.rule.create"` |
| Policy rule deleted | `eventType eq "policy.rule.delete"` |

## Security & Threats

| User asks about… | filter |
|---|---|
| Threat / anomaly detected | `eventType eq "security.threat.detected"` |
| Rate limit warning | `eventType eq "system.org.rate_limit.warning"` |
| Rate limit violation | `eventType eq "system.org.rate_limit.violation"` |

## Combining filters

To scope any of the above to a specific user, add:
`and actor.alternateId eq "jane.doe@example.com"`

To scope to a specific app or group by ID, add:
`and target.id eq "0oa..."`

Example — failed logins for a specific user:
`filter='eventType eq "user.session.start" and outcome.result eq "FAILURE" and actor.alternateId eq "jane.doe@example.com"'`
