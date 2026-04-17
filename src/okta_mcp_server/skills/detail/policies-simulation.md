# Policies: Simulation — Detail

## `create_policy_simulation` — currently broken (HTTP 400)

**Do not use `create_policy_simulation` until the SDK issue is resolved.**

**Root cause:** The Okta Python SDK's `clear_empty_params` function strips required empty
arrays from the request body, producing a malformed request that Okta rejects with HTTP 400.

This may also require a tenant feature flag to be enabled. Both conditions must be satisfied
before this tool will work correctly.

**Workaround:** There is no direct workaround via this tool. For policy evaluation testing,
use the Okta Admin Console's built-in policy preview feature instead.
