════════════════════════════════════════
NETWORK ZONES
════════════════════════════════════════

| Goal | Tool | Parameters |
|------|------|------------|
| List all zones | `list_network_zones` | (no params) |
| Active zones only | `list_network_zones` | `filter='status eq "ACTIVE"'` |
| Get zone by ID | `get_network_zone` | `zone_id` |

**Note:** The correct tool for full zone replacement is `replace_network_zone` (PUT). There is no partial-update tool for network zones.
