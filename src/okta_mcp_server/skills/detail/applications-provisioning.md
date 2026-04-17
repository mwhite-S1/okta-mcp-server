# Applications: Provisioning Connections — Detail

## Token-based setup flow

```
1. update_default_provisioning_connection(app_id, {"authScheme": "TOKEN", "token": "<api-token>"})
2. activate_provisioning_connection(app_id)
3. get_default_provisioning_connection(app_id)   ← verify status = "ENABLED"
```

## `authScheme` values

- `"TOKEN"` — API token, passed as `{"authScheme": "TOKEN", "token": "<value>"}`
- `"OAUTH2"` — OAuth 2.0, passed as `{"authScheme": "OAUTH2", "credentials": {...}}`

Use TOKEN for most OIN apps. Use OAUTH2 for Org2Org or apps that support OAuth-based provisioning.

## `verify_provisioning_connection` — supported `app_name` values

These are the only valid values for the `app_name` parameter when completing OAuth consent:

- `office365`
- `google`
- `zoomus`
- `slack`

`verify_provisioning_connection(app_id, app_name="office365", code="...", state="...")`

Any other value will result in an error. The `code` and `state` come from the OAuth redirect
callback after the admin authorizes the connection.
