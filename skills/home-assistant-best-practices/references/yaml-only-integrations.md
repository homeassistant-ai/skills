# YAML-Only Integrations

Use managed YAML config editing (with backup, validation, and `check_config` verification) for integrations that have no config flow and no REST/WebSocket API for creation.

This does NOT apply to automations/scripts/scenes (use config APIs), UI-configured integrations, `.storage/` files (use REST/WebSocket APIs), or helpers like input_number/input_boolean (these have config flow).

## YAML-Only Integration Types

| Integration type | Post-edit action | Notes |
|---|---|---|
| `template` | Reload available | Prefer Template Helper (UI) when possible |
| `mqtt` (platform-based) | Reload available | Platform-style `mqtt:` sensors/switches; MQTT devices via config entry are separate |
| `group` (YAML-defined) | Reload available | Groups defined in YAML; UI groups use config entries |
| `command_line` | Restart required | Sensors, switches, binary sensors via shell commands |
| `rest` | Restart required | REST sensors, binary sensors |
| `shell_command` | Restart required | Named shell command definitions |
| `notify` (legacy platform-based) | Restart required | Most notify platforms now use config entries; only legacy platform-based definitions are YAML-only |
| `sensor` / `binary_sensor` | Restart required | Platform-style YAML definitions (e.g. `sensor: platform: xyz`) |
| `switch` / `light` / `fan` / `cover` / `climate` | Restart required | Platform-based YAML definitions |

Confirm with the user before triggering a restart — it briefly interrupts all automations and integrations.