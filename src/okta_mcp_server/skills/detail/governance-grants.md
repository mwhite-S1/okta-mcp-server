# Governance: Grants — Detail

## `create_grant` discriminated union on `grantType`

The shape of the grant object varies by `grantType`. All types require `targetPrincipal`.

| grantType | Required extra fields |
|-----------|----------------------|
| `"ENTITLEMENT-BUNDLE"` | `entitlementBundleId` |
| `"ENTITLEMENT"` | `target`, `entitlements` |
| `"CUSTOM"` | `target`; optional `entitlements` |
| `"POLICY"` | `target` |

All types:
- **Required**: `targetPrincipal: {"externalId": "00u...", "type": "OKTA_USER"}`
- **Optional**: `scheduleSettings`, `action` ("ALLOW"/"DENY"), `actor` ("API"/"ACCESS_REQUEST"/"NONE"/"ADMIN")

## Create grant examples

**Bundle grant:**
```json
{
  "grantType": "ENTITLEMENT-BUNDLE",
  "entitlementBundleId": "gbun...",
  "targetPrincipal": {"externalId": "00u...", "type": "OKTA_USER"}
}
```

**Entitlement grant:**
```json
{
  "grantType": "ENTITLEMENT",
  "target": {"externalId": "0oa...", "type": "APPLICATION"},
  "entitlements": [{"id": "esp...", "values": [{"id": "ent..."}]}],
  "targetPrincipal": {"externalId": "00u...", "type": "OKTA_USER"}
}
```

**ENTITLEMENT type (alternate form):**
```json
{
  "grantType": "ENTITLEMENT",
  "target": {"externalId": "0oa...", "type": "APPLICATION"},
  "entitlements": [{"id": "esp..."}],
  "targetPrincipal": {"externalId": "00u...", "type": "OKTA_USER"}
}
```

## `update_grant` (PUT) caveat

**Must include all system fields** from the GET response — not just writable fields.
The API validates all schema fields including read-only ones (`id`, `_links`, `created`,
`createdBy`, `lastUpdated`, `lastUpdatedBy`, `status`). Omitting any causes validation errors.

## `patch_grant` limitation

`patch_grant` **only supports updating `scheduleSettings.expirationDate`**.
This is NOT a JSON Patch operations endpoint. Only pass:
```json
{"id": "gra...", "scheduleSettings": {"expirationDate": "2027-01-01T00:00:00Z"}}
```
