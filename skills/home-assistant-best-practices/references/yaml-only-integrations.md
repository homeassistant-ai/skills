# YAML-Only Integrations

Use managed YAML config editing (with backup, validation, and `check_config` verification) for integrations that have no config flow and no REST/WebSocket API for creation.

This does NOT apply to automations/scripts/scenes (use config APIs), UI-configured integrations and helpers (config flow) — including `template` (Template Helper), `group` (Group Helper), `input_*` helpers, and most modern notify integrations — or `.storage/` files (use REST/WebSocket APIs).

For sending notifications, prefer config-flow notify integrations (Mobile App, Telegram, MQTT, etc.) with the `notify.send_message` action from automations — not a YAML `notify:` platform definition.

## YAML-Only Integration Types

| Integration type | Post-edit action | Notes |
|---|---|---|
| `command_line` | `command_line.reload` | Sensors, switches, binary sensors via shell commands |
| `rest` | `rest.reload` | REST sensors, binary sensors |
| `shell_command` | `shell_command.reload` | Named shell command definitions |
| `mqtt` (platform-based) | `mqtt.reload` | Platform-style `mqtt:` sensors/switches. MQTT Discovery and MQTT device config entries are non-YAML alternatives for auto-published devices |
| `group` (YAML-defined) | `group.reload` | Old-style YAML groups. Prefer the UI Group Helper (Settings → Devices & Services → Helpers → Group) for new groups |
| `sensor` / `binary_sensor` (platform-style) | Restart required | Platform-style YAML definitions (e.g. `sensor: - platform: xyz`) for platforms without a config flow. Many platforms now have config flows — check the integration's docs before assuming YAML is required |
| `switch` / `light` / `fan` / `cover` / `climate` (platform-style) | Restart required | Same as above — only for platforms that have no config flow |

Confirm with the user before triggering a restart — it briefly interrupts all automations and integrations.
