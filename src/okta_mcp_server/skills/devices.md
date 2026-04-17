════════════════════════════════════════
DEVICES
════════════════════════════════════════

Device statuses: `CREATED` → `ACTIVE` → `DEACTIVATED` / `SUSPENDED`

| Goal | Tool | Parameters |
|------|------|------------|
| List all devices | `list_devices` | (no params) |
| Filter by status | `list_devices` | `search='status eq "ACTIVE"'` |
| Filter by display name | `list_devices` | `search='profile.displayName co "Mac"'` |
| Filter by platform | `list_devices` | `search='profile.platform eq "MACOS"'` — also: `WINDOWS`, `ANDROID`, `IOS`, `CHROMEOS` |
| Include user details inline | `list_devices` | `expand="user"` |
| Get device by ID | `get_device` | `device_id` |
| List users on a device | `list_device_users` | `device_id` |

## Device Lifecycle

Device status flow: `CREATED` → `ACTIVE` → `DEACTIVATED` / `SUSPENDED`

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Activate device | `activate_device` | `device_id` |
| Deactivate device | `deactivate_device` | `device_id` |
| Suspend device | `suspend_device` | `device_id` |
| Unsuspend device | `unsuspend_device` | `device_id` |
| Delete device | `delete_device` | `device_id` — must be DEACTIVATED first |
