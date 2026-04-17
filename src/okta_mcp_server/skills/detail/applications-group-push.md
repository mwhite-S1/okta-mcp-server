# Applications: Group Push Mappings — Detail

## `targetGroupName` vs `targetGroupId` — mutually exclusive

When creating a push mapping, use **one or the other**, never both:

- `targetGroupName` — creates a **new** group in the target app with this name
- `targetGroupId` — links an **existing** group in the target app by its ID

```json
// Create new target group:
{"sourceGroupId": "00g...", "targetGroupName": "Engineering"}

// Link existing target group:
{"sourceGroupId": "00g...", "targetGroupId": "<app-group-id>"}
```

## Delete workflow — two steps required

A push mapping **must be INACTIVE** before it can be deleted. Skip step 1 and the delete will fail.

```
1. update_group_push_mapping(app_id, mapping_id, update={"status": "INACTIVE"})
2. delete_group_push_mapping(app_id, mapping_id, delete_target_group=False)
```

`delete_target_group` parameter is **required by the API** (pass `False` to keep the target group,
`True` to also delete it from the downstream app).
