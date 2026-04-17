# Governance: Risk Rules — Detail

## `conflict_criteria` structure

Each criteria item in a risk rule requires these exact fields:

- `operation`: `"CONTAINS_ONE"` or `"CONTAINS_ALL"` — **NOT** `criteria-operation`
- `attribute`: always `"principal.effective_grants"`
- `value.type`: always `"ENTITLEMENTS"`
- `value.value`: list of `{"id": "<entitlement_id>", "values": [{"id": "<entitlement_value_id>"}]}`
- Each entitlement value ID **must belong to the entitlement** specified by `id`
- Use `list_entitlement_values` to get valid value IDs for an entitlement
- Use **two DIFFERENT entitlements** (one per criteria) for a valid SOD rule

```json
{
  "and": [
    {
      "name": "criteria-1",
      "attribute": "principal.effective_grants",
      "operation": "CONTAINS_ONE",
      "value": {
        "type": "ENTITLEMENTS",
        "value": [{"id": "<entitlement_id_A>", "values": [{"id": "<value_id_A>"}]}]
      }
    },
    {
      "name": "criteria-2",
      "attribute": "principal.effective_grants",
      "operation": "CONTAINS_ONE",
      "value": {
        "type": "ENTITLEMENTS",
        "value": [{"id": "<entitlement_id_B>", "values": [{"id": "<value_id_B>"}]}]
      }
    }
  ]
}
```

## `assess_risk_rules` — principal ORN prefix caveat

`principal_orn` must always use the `orn:okta:` prefix (NOT `orn:oktapreview:`):
```
orn:okta:directory:{orgId}:users:{userId}
```

`resource_orns` is **required** — pass bundle ORNs from `list_entitlement_bundles`:
```
orn:okta:governance:{orgId}:entitlement-bundles:{id}
```

Returns empty list when no risk rules are configured for the specified resources.

## Update restrictions

`update_risk_rule` — `type` and `resources` fields **cannot be updated**. Only `name`, `description`, `notes`, and `conflict_criteria` are mutable after creation.
