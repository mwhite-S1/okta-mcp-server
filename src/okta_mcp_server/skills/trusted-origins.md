════════════════════════════════════════
TRUSTED ORIGINS
════════════════════════════════════════

Trusted origins define the URLs (CORS / redirect) that Okta allows cross-origin requests from.
Status: `ACTIVE` | `INACTIVE`

## Lookup

| Goal | Tool | Key Parameters |
|------|------|----------------|
| List all trusted origins | `list_trusted_origins` | `filter='status eq "ACTIVE"'` (optional) |
| Get by ID | `get_trusted_origin` | `trusted_origin_id` |

## CRUD

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Create | `create_trusted_origin` | `name, origin, scopes=[{"type":"CORS"}]` |
| Replace (full update) | `replace_trusted_origin` | `trusted_origin_id, origin_data={...}` |
| Delete | `delete_trusted_origin` | `trusted_origin_id` |

## Lifecycle

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Activate | `activate_trusted_origin` | `trusted_origin_id` |
| Deactivate | `deactivate_trusted_origin` | `trusted_origin_id` |

**Scope types:** `CORS` (cross-origin API calls), `REDIRECT` (sign-in redirect URLs).
Create example:
```
create_trusted_origin(
    name="My App",
    origin="https://app.example.com",
    scopes=[{"type": "CORS"}, {"type": "REDIRECT"}]
)
```
