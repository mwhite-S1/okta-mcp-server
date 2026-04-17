════════════════════════════════════════
MULTI-STEP WORKFLOWS
════════════════════════════════════════

Chain these tool calls within a single turn for complete outcomes. Resolve all IDs before acting — never stop at a partial result.

## ONBOARD A NEW USER
```
1. create_user(profile={firstName, lastName, email, login, department, ...})
2. add_user_to_group(group_id, user_id)              ← repeat for each group
3. assign_user_to_application(app_id,
     app_user={"id": user_id})                       ← repeat for each app
4. activate_user(user_id, send_email=True)
```

## OFFBOARD A USER
```
1. list_users(search='profile.login eq "user@example.com"')  → get user_id
2. suspend_user(user_id)          ← immediately blocks all logins
3. deactivate_user(user_id)       ← required before deletion
4. delete_deactivated_user(user_id)  ← permanent; confirm with user first
```

## INVESTIGATE WHY A USER CANNOT SIGN IN
```
1. list_users(search='profile.login eq "user@example.com"')  → check status
2. LOCKED_OUT  → unlock_user(user_id)
   SUSPENDED   → unsuspend_user(user_id)
   PASSWORD_EXPIRED → reset_password(user_id, send_email=True)
3. list_factors(user_id)  → confirm MFA is enrolled
4. get_logs(
     filter='actor.alternateId eq "user@example.com"
             and eventType eq "user.session.start"',
     since="<past 7 days>")  → review recent failures
```

## AUDIT A USER'S ACCESS
```
1. list_users(search='profile.login eq "user@example.com"')  → get user_id
2. list_applications(filter='user.id eq "user_id"')          → directly assigned apps
3. get_logs(filter='actor.id eq "user_id"', since="...")     → recent activity
```

## GRANT APP ACCESS TO A GROUP
```
1. list_groups(search='profile.name eq "GroupName"')  → get group_id
2. list_applications(q="AppName")                     → get app_id
3. assign_group_to_application(app_id, group_id)
```

## RESET MFA FOR A USER
```
1. list_users(search='profile.login eq "user@example.com"')  → get user_id
2. list_factors(user_id)  → see what's enrolled
3. reset_factors(user_id)               ← wipes all; user re-enrolls next sign-in
   OR unenroll_factor(user_id, factor_id)  ← removes one specific factor
```

## CREATE A DYNAMIC GROUP RULE
```
1. list_groups(search='profile.name eq "TargetGroup"')  → get group_id
2. get_user_profile_attributes()  → verify the attribute name is real
3. create_group_rule(rule_data={
     "name": "Auto-assign by Department",
     "conditions": {
       "expression": {
         "type": "urn:okta:expression:1.0",
         "value": "user.department eq \"Engineering\""
       }
     },
     "actions": {
       "assignUserToGroups": { "groupIds": ["group_id"] }
     }
   })
4. activate_group_rule(rule_id)   ← always activate; rules start INACTIVE
```

## CHECK POLICY COMPLIANCE
```
1. list_policies(type="PASSWORD", status="ACTIVE")  → get active policies
2. get_policy(policy_id)          → read settings
3. list_policy_rules(policy_id)   → see all rules
4. get_logs(
     filter='eventType eq "policy.evaluate_sign_on"
             and outcome.result eq "DENY"',
     since="...")  → see denials
```

## INVESTIGATE A SECURITY INCIDENT (who did X)
```
1. get_logs(filter='eventType eq "user.account.update_profile"',
            since="...")         → find the change event
2. Extract actor.id from the event
3. get_user(user_id=actor.id)    → identify who made the change
4. get_logs(filter='actor.id eq "actor_id"',
            since="...")         → see all their actions in the window
```

## PROCESS AN ACCESS REQUEST
```
1. list_access_requests(filter='status eq "PENDING"')  → find pending requests
2. get_access_request(request_id)  → review details
3. approve_access_request(request_id)
   OR deny_access_request(request_id)
```
