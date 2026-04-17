# Governance: Entitlements — Detail

## `list_entitlements` — filter required

`list_entitlements` **without a filter** or with a non-enrolled app returns **400 or 404**.

You **must** provide `parent.externalId eq "..."` with a governance-enrolled app ID:
```
filter='parent.externalId eq "0oa..." AND parent.type eq "APPLICATION"'
```

Combining with name search:
```
filter='parent.externalId eq "0oa..." AND name co "admin"'
```

If you don't know which app IDs are governance-enrolled, use `list_applications` and
look for apps with governance entitlements, or check `get_resource_entitlement_settings`
for a specific app.

## `create_entitlement_bundle` — non-empty `entitlements` required

`entitlements` must be **non-empty** — passing `[]` returns:
```
400 "field /entitlements is missing"
```

Minimum valid bundle body:
```json
{
  "name": "Bundle Name",
  "target": {"externalId": "0oa...", "type": "APPLICATION"},
  "entitlements": [{"id": "esp...", "values": [{"id": "ent..."}]}]
}
```

## `update_entitlement_bundle` (PUT) — required fields

This is a full PUT replacement. The following fields are **required** even though the spec
marks some as optional — omitting any causes 400 errors:

- `id` — the bundle ID
- `targetResourceOrn` — the full app ORN
- `target` — `{"externalId": "0oa...", "type": "APPLICATION"}`
- `status` — must be `"ACTIVE"` (omitting causes: `400 "PUT API does not support replacing null status"`)

Always retrieve the bundle with `get_entitlement_bundle` first and include all fields from the response.
