# Runbook: Users

Covers `users.py`, `user_lifecycle.py`, `user_credentials.py`, `user_factors.py`,
`user_oauth.py`, `user_role_targets.py`, `user_sessions.py` — 46 tools total.

---

## Prerequisites

Resolve once at the start and hold for the session:

| Variable | How to resolve |
|----------|---------------|
| `$FIRST_ACTIVE_USER_ID` | `list_users(filter='status eq "ACTIVE"', limit=1)` → first `id` |
| `$FIRST_APP_ID` | `list_applications(limit=1)` → first `id` |
| `$FIRST_GROUP_ID` | `list_groups(limit=1)` → first `id` |
| `$TEST_USER_ID` | Created in T-4; used throughout and deleted in T-9 |

---

## Section 1 — Users (Core)

### T-1: list_users

**Call:** `list_users(limit=5)`  
**Expect:** `{"items": [...], ...}` — list, each item has `id`, `status`, `profile`

---

### T-2: list_users with filter

**Call:** `list_users(filter='status eq "ACTIVE"', limit=3)`  
**Expect:** all returned items have `status == "ACTIVE"`

---

### T-3: get_user_profile_attributes

**Call:** `get_user_profile_attributes()`  
**Expect:** dict describing profile schema attributes (no `error`)

---

### T-4: get_user

**Call:** `get_user(user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** `result["id"] == $FIRST_ACTIVE_USER_ID`

---

### T-5: list_user_blocks

**Call:** `list_user_blocks(user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** list (may be empty); no `error`

---

### T-6: invalid user returns error

**Call:** `get_user(user_id="invalid-user-000")`  
**Expect:** `"error"` in result

---

### T-7: 🔁 create_user → update_user → replace_user → deactivate → delete

⚠️ This cycle creates a real user. Cleanup is in T-9.

**CREATE:**  
```
create_user(profile={
  "firstName": "Runbook",
  "lastName": "TestUser",
  "email": "runbook-testuser@example.com",
  "login": "runbook-testuser@example.com"
}, activate=False)
```
**Expect:** `result["id"]` is present → set `$TEST_USER_ID`; `result["status"] == "STAGED"`

---

### T-8: update_user

**Call:** `update_user(user_id=$TEST_USER_ID, profile={"nickName": "Runbook"})`  
**Expect:** no `error`; `result["profile"]["nickName"] == "Runbook"`

---

### T-9: replace_user

**Call:** `replace_user(user_id=$TEST_USER_ID, profile={"firstName":"Runbook","lastName":"TestUser","email":"runbook-testuser@example.com","login":"runbook-testuser@example.com","nickName":"RunbookReplaced"})`  
**Expect:** no `error`; `result["profile"]["nickName"] == "RunbookReplaced"`

---

## Section 2 — User Lifecycle

### T-10: activate_user

**Call:** `activate_user(user_id=$TEST_USER_ID, send_email=False)`  
**Expect:** no `error`; result may contain activation token

---

### T-11: get_user (verify ACTIVE)

**Call:** `get_user(user_id=$TEST_USER_ID)`  
**Expect:** `result["status"]` is `"ACTIVE"` or `"PROVISIONED"`

---

### T-12: suspend_user

**Call:** `suspend_user(user_id=$TEST_USER_ID)`  
**Expect:** no `error`

---

### T-13: unsuspend_user

**Call:** `unsuspend_user(user_id=$TEST_USER_ID)`  
**Expect:** no `error`

---

### T-14: deactivate_user (for cleanup)

**Call:** `deactivate_user(user_id=$TEST_USER_ID)`  
**Expect:** no `error`; user moves to `DEPROVISIONED`

---

### T-15: delete_deactivated_user ⚠️

**Call:** `delete_deactivated_user(user_id=$TEST_USER_ID)`  
**Expect:** no `error`  
**Verify:** `get_user(user_id=$TEST_USER_ID)` returns `"error"` (user gone)

---

### T-16: unlock_user (on existing user)

**Call:** `unlock_user(user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** no `error` (idempotent — safe even if not locked)

---

### T-17: reset_factors

⚠️ This clears all enrolled factors for the user. Use only on a dedicated test account.

**Call:** `reset_factors(user_id=$TEST_USER_ID)`  
⏭️ Skip — `$TEST_USER_ID` has already been deleted. Document the expected behavior:
- If called on an active user: no `error`, all factors removed
- Verify by calling `list_factors` afterward → empty list

---

### T-18: reactivate_user

⏭️ Only applies to users in `PROVISIONED` state with unconfirmed email. Skip if `$FIRST_ACTIVE_USER_ID` is `ACTIVE`.

---

## Section 3 — User Credentials

All credential tests run on `$FIRST_ACTIVE_USER_ID`.
⚠️ These affect the real account — use a dedicated test account in production.

### T-19: forgot_password

**Call:** `forgot_password(user_id=$FIRST_ACTIVE_USER_ID, send_email=False)`  
**Expect:** no `error`; result may include reset token or empty dict (org policy dependent)

---

### T-20: change_recovery_question 🔁

**Call:**
```
change_recovery_question(
  user_id=$FIRST_ACTIVE_USER_ID,
  current_password="<known password>",
  question="What is your runbook test value?",
  answer="runbook"
)
```
⏭️ Skip if current password is unavailable in test context.  
**Expect:** no `error`

_Restore by calling again with the original question/answer._

---

### T-21: expire_password

⏭️ Skip to avoid forcing re-login for a real user. Behavior:
- Returns a temp password (if `temp_password=True`) or empty dict
- User's `passwordChanged` resets

---

## Section 4 — User Factors

### T-22: list_supported_factors

**Call:** `list_supported_factors(user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** list of supported factor types; no `error`

---

### T-23: list_supported_security_questions

**Call:** `list_supported_security_questions(user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** list of question objects; no `error`

---

### T-24: list_factors

**Call:** `list_factors(user_id=$FIRST_ACTIVE_USER_ID)`  
**Expect:** list (may be empty); each item has `id`, `factorType`, `status`  
→ set `$FIRST_FACTOR_ID` = `items[0]["id"]` if list non-empty

---

### T-25: get_factor

⏭️ Skip if `$FIRST_FACTOR_ID` not set.

**Call:** `get_factor(user_id=$FIRST_ACTIVE_USER_ID, factor_id=$FIRST_FACTOR_ID)`  
**Expect:** `result["id"] == $FIRST_FACTOR_ID`

---

### T-26: enroll_factor 🔁

⚠️ Enrolling `token:software:totp` (TOTP) is test-safe and doesn't send messages.

```
enroll_factor(
  user_id=$FIRST_ACTIVE_USER_ID,
  factor_type="token:software:totp",
  provider="GOOGLE"
)
```
⏭️ Skip if TOTP is already enrolled.  
**Expect:** `result["id"]` set → `$NEW_FACTOR_ID`; status `"PENDING_ACTIVATION"`

**CLEANUP:** `unenroll_factor(user_id=$FIRST_ACTIVE_USER_ID, factor_id=$NEW_FACTOR_ID)`  
**Expect:** no `error`

---

### T-27: invalid factor returns error

**Call:** `get_factor(user_id=$FIRST_ACTIVE_USER_ID, factor_id="invalid-factor-000")`  
**Expect:** `"error"` in result

---

## Section 5 — User OAuth Tokens

⏭️ All token tests skip if `$FIRST_ACTIVE_USER_ID` has no OAuth refresh tokens.

### T-28: list_refresh_tokens_for_user_and_client

**Call:** `list_refresh_tokens_for_user_and_client(user_id=$FIRST_ACTIVE_USER_ID, client_id=$FIRST_APP_ID)`  
**Expect:** `items` is a list; no `error`  
→ set `$FIRST_TOKEN_ID` = `items[0]["id"]` if non-empty

---

### T-29: get_refresh_token_for_user_and_client

⏭️ Skip if `$FIRST_TOKEN_ID` not set.

**Call:** `get_refresh_token_for_user_and_client(user_id=$FIRST_ACTIVE_USER_ID, client_id=$FIRST_APP_ID, token_id=$FIRST_TOKEN_ID)`  
**Expect:** `result["id"] == $FIRST_TOKEN_ID`; no `error`

---

## Section 6 — User Role Targets

⏭️ All tests in this section skip if `$FIRST_ACTIVE_USER_ID` has no admin role assignments.

### T-30: find user with role

Call `list_users(limit=10)` and for each user call:  
`list_user_group_role_targets(user_id=<id>, role_assignment_id=<any_role_id>)` until one succeeds.

Alternatively use the Okta admin console to find a user with a `USER_ADMIN` or `GROUP_ADMIN` role.

→ set `$ROLE_USER_ID` and `$ROLE_ASSIGNMENT_ID`

---

### T-31: list_user_app_role_targets

**Call:** `list_user_app_role_targets(user_id=$ROLE_USER_ID, role_assignment_id=$ROLE_ASSIGNMENT_ID)`  
**Expect:** `items` is a list; no `error`

---

### T-32: list_user_group_role_targets

**Call:** `list_user_group_role_targets(user_id=$ROLE_USER_ID, role_assignment_id=$ROLE_ASSIGNMENT_ID)`  
**Expect:** `items` is a list; no `error`  
→ note existing group IDs to avoid assigning a duplicate

---

### T-33: get_user_role_targets

**Call:** `get_user_role_targets(user_id=$ROLE_USER_ID, role_id=$ROLE_ASSIGNMENT_ID)`  
**Expect:** dict with no `error`

---

### T-34: 🔁 assign_group_target_to_user_role → verify → unassign

⏭️ Skip if `$FIRST_GROUP_ID` is already in the role targets list.

**ASSIGN:** `assign_group_target_to_user_role(user_id=$ROLE_USER_ID, role_assignment_id=$ROLE_ASSIGNMENT_ID, group_id=$FIRST_GROUP_ID)`  
**Expect:** no `error`

**VERIFY:** `list_user_group_role_targets(...)` → `$FIRST_GROUP_ID` appears in `items[*]["id"]`

**CLEANUP:** `unassign_group_target_from_user_role(user_id=$ROLE_USER_ID, role_assignment_id=$ROLE_ASSIGNMENT_ID, group_id=$FIRST_GROUP_ID)`  
**Expect:** no `error`

**VERIFY:** `$FIRST_GROUP_ID` no longer in group targets

---

### T-35: invalid user/role returns error

**Call:** `list_user_app_role_targets(user_id="invalid-user-000", role_assignment_id="role-000")`  
**Expect:** `"error"` in result

---

## Section 7 — User Sessions

### T-36: revoke_user_sessions

⚠️ This logs the user out of all active browser sessions.

**Call:** `revoke_user_sessions(user_id=$FIRST_ACTIVE_USER_ID)`  
⏭️ Skip unless running against a dedicated test account.  
**Expect:** no `error`

---

## Summary

| Section | Tests | Notes |
|---------|-------|-------|
| Users (core) | T-1 – T-9 | Full CRUD cycle with test user |
| Lifecycle | T-10 – T-18 | Suspend/unsuspend/unlock on test user |
| Credentials | T-19 – T-21 | Minimal — avoid disrupting real users |
| Factors | T-22 – T-27 | TOTP enroll/unenroll cycle |
| OAuth Tokens | T-28 – T-29 | Read-only; skip if no tokens |
| Role Targets | T-30 – T-35 | Group target assign/unassign cycle |
| Sessions | T-36 | Destructive — dedicated test account only |
