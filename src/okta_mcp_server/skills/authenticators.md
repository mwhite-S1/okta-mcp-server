════════════════════════════════════════
AUTHENTICATORS
════════════════════════════════════════

Authenticators are the individual factor types available in your org
(password, email, Okta Verify push/TOTP, WebAuthn, phone SMS/voice,
security question, YubiKey). They feed into enrollment and sign-on policies.

## Core CRUD

| Goal | Tool | Parameters |
|------|------|------------|
| List all authenticators | `list_authenticators` | (no params) |
| Create authenticator | `create_authenticator` | `authenticator_data={key, name, ...}, activate=False` |
| Get authenticator | `get_authenticator` | `authenticator_id` |
| Replace authenticator | `replace_authenticator` | `authenticator_id, authenticator_data={name, settings, ...}` |

**Authenticator key values**: `okta_email`, `okta_password`, `okta_verify`, `phone_number`,
`security_question`, `webauthn`, `yubikey_token`, `custom_otp`, `google_otp`, `duo`

## Lifecycle

| Goal | Tool | Parameters |
|------|------|------------|
| Activate | `activate_authenticator` | `authenticator_id` |
| Deactivate | `deactivate_authenticator` | `authenticator_id` — removes from all policies |

## Methods

Each authenticator has one or more methods (e.g. Okta Verify has push, totp, signed_nonce).

| Goal | Tool | Parameters |
|------|------|------------|
| List methods | `list_authenticator_methods` | `authenticator_id` |
| Get method | `get_authenticator_method` | `authenticator_id, method_type` |
| Replace method config | `replace_authenticator_method` | `authenticator_id, method_type, method_data={settings}` |
| Activate method | `activate_authenticator_method` | `authenticator_id, method_type` |
| Deactivate method | `deactivate_authenticator_method` | `authenticator_id, method_type` |

**Method types**: `push`, `totp`, `signed_nonce`, `webauthn`, `email`, `sms`, `voice`, `password`, `security_question`

## Custom AAGUIDs (WebAuthn hardware key allowlisting)

AAGUIDs identify specific hardware key models (e.g. YubiKey 5 NFC UUID).
See `skill://detail/authenticators/aaguids` for known issues (`update_custom_aaguid` returns 405).

| Goal | Tool | Parameters |
|------|------|------------|
| List AAGUIDs | `list_custom_aaguids` | `authenticator_id` |
| Add AAGUID | `create_custom_aaguid` | `authenticator_id, aaguid="<uuid>", name="YubiKey 5 NFC"` |
| Get AAGUID | `get_custom_aaguid` | `authenticator_id, aaguid` |
| Replace AAGUID | `replace_custom_aaguid` | `authenticator_id, aaguid, name` |
| Update AAGUID (PATCH) | `update_custom_aaguid` | `authenticator_id, aaguid, name` ⚠ **returns 405** — use `replace_custom_aaguid` |
| Delete AAGUID | `delete_custom_aaguid` | `authenticator_id, aaguid` — requires confirmation |

## WebAuthn RP ID Verification

| Goal | Tool | Parameters |
|------|------|------------|
| Verify RP ID domain | `verify_rp_id_domain` | `authenticator_id, web_authn_method_type="webauthn", rp_id="example.com"` |
