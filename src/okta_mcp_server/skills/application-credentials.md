════════════════════════════════════════
APPLICATION CREDENTIALS & KEY ROTATION
════════════════════════════════════════

Three credential types per application:
- **SSO signing keys** — X.509 certs for SAML/WS-Fed signing (`/credentials/keys`)
- **CSRs** — Certificate signing requests to bring-your-own CA (`/credentials/csrs`)
- **OAuth JWKs** — Public keys for `private_key_jwt` client auth (`/credentials/jwks`)
- **OAuth client secrets** — Shared secrets for `client_secret_*` auth (`/credentials/secrets`)

## SSO Signing Keys (SAML / WS-Fed)

| Goal | Tool | Parameters |
|------|------|------------|
| List keys | `list_application_keys` | `app_id` |
| Generate new key | `generate_application_key` | `app_id, validity_years=2` — does NOT auto-activate |
| Get key | `get_application_key` | `app_id, key_id` |
| Clone key to another app | `clone_application_key` | `app_id, key_id, target_app_id` |

**Key rotation flow**: generate → clone to IdP metadata target → update app credentials → update SP metadata

## Certificate Signing Requests (CSRs)

| Goal | Tool | Parameters |
|------|------|------------|
| List CSRs | `list_application_csrs` | `app_id` |
| Generate CSR | `generate_application_csr` | `app_id, subject={countryName, organizationName, commonName, ...}` |
| Get CSR | `get_application_csr` | `app_id, csr_id` |
| Publish signed cert | `publish_application_csr` | `app_id, csr_id, signed_certificate="-----BEGIN CERTIFICATE-----..."` |
| Revoke CSR | `revoke_application_csr` | `app_id, csr_id` — requires confirmation |

## OAuth 2.0 Client JWKs (private_key_jwt)

| Goal | Tool | Parameters |
|------|------|------------|
| List JWKs | `list_application_jwks` | `app_id` |
| Add JWK | `add_application_jwk` | `app_id, key_data={kty, use, n, e, ...}` |
| Get JWK | `get_application_jwk` | `app_id, key_id` |
| Activate JWK | `activate_application_jwk` | `app_id, key_id` |
| Deactivate JWK | `deactivate_application_jwk` | `app_id, key_id` |
| Delete JWK | `delete_application_jwk` | `app_id, key_id` — requires confirmation |

## OAuth 2.0 Client Secrets

Multiple active secrets support zero-downtime rotation. The secret value is
only returned at creation — it cannot be retrieved later.

| Goal | Tool | Parameters |
|------|------|------------|
| List secrets | `list_oauth2_client_secrets` | `app_id` — values masked, only metadata |
| Create secret | `create_oauth2_client_secret` | `app_id` — save the returned value immediately |
| Get secret metadata | `get_oauth2_client_secret` | `app_id, secret_id` |
| Activate secret | `activate_oauth2_client_secret` | `app_id, secret_id` |
| Deactivate secret | `deactivate_oauth2_client_secret` | `app_id, secret_id` |
| Delete secret | `delete_oauth2_client_secret` | `app_id, secret_id` — requires confirmation |

**Rotation flow**: create new → update client to use new → verify → deactivate old → delete old
