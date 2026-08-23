# YAML-Only Integrations

Use managed YAML config editing (with backup, validation, and `check_config` verification) for integrations that have no config flow and no REST/WebSocket API for creation.

This does NOT apply to:

- Automations/scripts/scenes (use config APIs)
- `.storage/` files (use REST/WebSocket APIs)
- UI-configured integrations and helpers (config flow): `input_*` helpers, the UI Group Helper (Settings → Devices & Services → Helpers → Group), and most modern notify integrations

Old-style YAML `group:` blocks are still YAML-only and appear in the table below — only the UI Group Helper is excluded.

For sending notifications, prefer config-flow notify integrations (Mobile App, Telegram, etc.) and invoke them via their `notify.<integration_name>` action (e.g. `notify.mobile_app_phone`) from automations — not a YAML `notify:` platform definition.

## YAML-Only Integration Types

| Integration type | Post-edit action | Notes |
|---|---|---|
| `template` | `template.reload` | Simple template entities: prefer the UI Template Helper. Trigger-based templates and multi-entity blocks (shared triggers/variables) still require YAML. |
| `command_line` | `command_line.reload` | Sensors, switches, binary sensors via shell commands |
| `rest` | `rest.reload` | REST sensors, binary sensors |
| `shell_command` | `shell_command.reload` | Named shell command definitions |
| `mqtt` (platform-based) | `mqtt.reload` | Platform-style `mqtt:` sensors/switches. MQTT Discovery and MQTT device config entries are non-YAML alternatives for auto-published devices |
| `group` (YAML-defined) | `group.reload` | Old-style YAML groups. Prefer the UI Group Helper (Settings → Devices & Services → Helpers → Group) for new groups |
| `sensor` / `binary_sensor` (platform-style) | `homeassistant.restart` | Platform-style YAML — a top-level `sensor:` (or `binary_sensor:`) key with a block sequence of `- platform: <name>` entries — for platforms without a config flow. Many platforms now have config flows — check the integration's docs before assuming YAML is required |
| `switch` / `light` / `fan` / `cover` / `climate` (platform-style) | `homeassistant.restart` | Platform-style YAML — a top-level `switch:` / `light:` / etc. key with a block sequence of `- platform: <name>` entries — only for platforms that have no config flow. Check the integration's docs before assuming YAML is required |

## Post-Edit Actions

A YAML edit changes nothing until the integration re-reads the file. Which action applies is the second column above:

- **`<domain>.reload`** — where the integration offers one. It reloads that domain only; nothing else is interrupted.
- **`homeassistant.restart`** — the fallback for platform-style YAML, which has no reload action. **Confirm with the user first:** it briefly interrupts every automation and integration, not just the one you edited.

Run `homeassistant.check_config` first. `homeassistant.restart` validates the config itself and refuses to restart when it fails, so the risk isn't a broken instance — it's that a reload silently leaves the old config running, or that you spend the user's restart to discover a typo.
