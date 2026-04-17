════════════════════════════════════════
DIRECTORY AGENT POOLS
════════════════════════════════════════

Agent pools group on-premises agents (AD/LDAP) that sync with Okta. Each pool
has agents that can be updated independently or as a batch during maintenance windows.

## Agent Pools

| Goal | Tool | Parameters |
|------|------|------------|
| List all pools | `list_agent_pools` | (no params) |
| Filter by type | `list_agent_pools` | `pool_type="AD"` — also: `LDAP`, `APP`, `IDP`, `MFA`, `RADIUS` |

Each pool shows: id, name, type, agents (with health, version, last-connected).

## Agent Pool Updates

Update jobs move agents to a newer version. They run during a configured maintenance window.

**Update statuses**: `SCHEDULED` → `RUNNING` → `COMPLETED` / `FAILED` / `STOPPED` / `PAUSED`

| Goal | Tool | Parameters |
|------|------|------------|
| List updates for a pool | `list_agent_pool_updates` | `pool_id` |
| List only scheduled | `list_agent_pool_updates` | `pool_id, scheduled=True` |
| Get a specific update | `get_agent_pool_update` | `pool_id, update_id` |
| Create update job | `create_agent_pool_update` | `pool_id, update_data={agentType, agents, name, schedule}` |
| Modify update job | `update_agent_pool_update` | `pool_id, update_id, update_data={...}` |
| Delete update job | `delete_agent_pool_update` | `pool_id, update_id` — only non-started or stopped jobs |

## Update Job Lifecycle

| Goal | Tool | Parameters |
|------|------|------------|
| Start (activate) | `activate_agent_pool_update` | `pool_id, update_id` |
| Pause mid-run | `pause_agent_pool_update` | `pool_id, update_id` |
| Resume after pause | `resume_agent_pool_update` | `pool_id, update_id` |
| Retry after failure | `retry_agent_pool_update` | `pool_id, update_id` — only failed agents retried |
| Stop permanently | `stop_agent_pool_update` | `pool_id, update_id` — cannot be resumed |
| Cancel (deactivate) | `deactivate_agent_pool_update` | `pool_id, update_id` — scheduled only |

## Pool-Level Settings

| Goal | Tool | Parameters |
|------|------|------------|
| Get auto-update settings | `get_agent_pool_update_settings` | `pool_id` |
| Update auto-update settings | `update_agent_pool_update_settings` | `pool_id, settings_data={continueOnError, releaseChannel, ...}` |
