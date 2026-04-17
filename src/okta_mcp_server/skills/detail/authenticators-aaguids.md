# Authenticators: Custom AAGUIDs — Detail

## `update_custom_aaguid` returns 405

**Do not use `update_custom_aaguid`.** Okta's API only supports GET/PUT/DELETE on the
custom AAGUID endpoint — there is no PATCH method. Calling `update_custom_aaguid` always
returns HTTP 405 Method Not Allowed.

**Use `replace_custom_aaguid` instead** (PUT):
```
replace_custom_aaguid(authenticator_id, aaguid="<uuid>", name="YubiKey 5 NFC")
```

## Context: hardware key allowlisting

AAGUIDs (Authenticator Attestation GUIDs) are UUIDs that identify specific hardware
security key models, such as:
- YubiKey 5 NFC: `fa2b99dc-9e39-4257-8f92-4a30d23c4118`
- YubiKey 5C NFC: `2fc0579f-8113-47ea-b116-bb5a8db9202a`

Configuring custom AAGUIDs on a WebAuthn authenticator restricts enrollment to only
the approved hardware models — users with unapproved keys will be blocked from enrolling.

## Full workflow

```
1. list_authenticators()  → find the WebAuthn authenticator ID
2. list_custom_aaguids(authenticator_id)  → see current allowlist
3. create_custom_aaguid(authenticator_id, aaguid="<uuid>", name="Model Name")
   OR replace_custom_aaguid(authenticator_id, aaguid="<uuid>", name="New Name")  ← update
4. delete_custom_aaguid(authenticator_id, aaguid)  ← remove from allowlist
```
