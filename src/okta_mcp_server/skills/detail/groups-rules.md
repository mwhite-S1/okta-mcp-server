# Groups: Dynamic Rules — Detail

## `create_group_rule` — full `rule_data` structure

Rules start **INACTIVE** after creation — always call `activate_group_rule` immediately after.

```
1. create_group_rule(rule_data={
     "name": "Auto-assign Engineering",
     "conditions": {
       "expression": {
         "type": "urn:okta:expression:1.0",
         "value": "user.department eq \"Engineering\""
       }
     },
     "actions": {
       "assignUserToGroups": { "groupIds": ["00g..."] }
     }
   })
2. activate_group_rule(rule_id)   ← always activate after creating
```

## Expression type literal

The `type` field in `conditions.expression` must be exactly:
```
"urn:okta:expression:1.0"
```

Any other value will be rejected.

## Common expression examples

```
user.department eq "Engineering"
user.title sw "Manager"
user.employeeType eq "Contractor"
String.stringContains(user.email, "@acme.com")
```

Use `get_user_profile_attributes()` to verify attribute names are real before creating a rule.

## Delete flow

Must deactivate before deleting:
```
1. deactivate_group_rule(rule_id)
2. delete_group_rule(rule_id)
```
