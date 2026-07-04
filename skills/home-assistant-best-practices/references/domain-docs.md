# Domain Documentation

To get detailed documentation for any Home Assistant integration or entity domain, fetch from the official docs on demand.

## Fetching Domain Docs

```
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_integrations/{domain}.markdown
```

Replace `{domain}` with the integration name (e.g., `light`, `climate`, `mqtt`).

If the MCP server registers resource URI templates for domain docs, prefer those over raw GitHub fetches.

## Fetching Trigger, Condition, and Action Docs

Since 2026.7, every purpose-specific trigger and condition — and every service action — has a dedicated doc page covering what it does, when to use it, its config shape, options, and worked examples. Fetch the page instead of guessing keys or options:

```
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_triggers/{trigger}.markdown
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_conditions/{condition}.markdown
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_actions/{action}.markdown
```

`{trigger}`/`{condition}`/`{action}` use `<domain>.<name>` (e.g. `motion.detected`, `zone.in_zone`, `light.turn_on`). Rendered pages live at `https://www.home-assistant.io/triggers/<domain>.<name>/` (same pattern for `/conditions/` and `/actions/`). The generic trigger types (`state`, `numeric_state`, `time`, `time_pattern`, `homeassistant`) have pages in the same tree under their bare names.

Caveat: some pages still show the pre-2026.7 trigger `behavior` values `any`/`last`; the current values are `each`/`first`/`all` (conditions keep `any`/`all`).

## Common Domains

| Domain | Description |
|--------|-------------|
| `light` | Light control (brightness, color, temperature) |
| `switch` | On/off switches |
| `climate` | HVAC and thermostat control |
| `cover` | Blinds, shades, garage doors |
| `fan` | Fan speed and oscillation |
| `lock` | Door locks |
| `media_player` | Media playback and volume |
| `vacuum` | Robot vacuum control |
| `sensor` | Numeric and text sensors |
| `binary_sensor` | On/off sensors (motion, door, window) |
| `automation` | Automation management |
| `script` | Script management |
| `scene` | Scene activation |
| `input_boolean` | Toggle helpers |
| `input_number` | Numeric input helpers |
| `input_select` | Dropdown helpers |
| `input_datetime` | Date/time helpers |
| `mqtt` | MQTT broker and entities |
| `zha` | Zigbee Home Automation |
| `notify` | Notification services |
| `tts` | Text-to-speech |
| `camera` | Camera feeds and snapshots |
| `weather` | Weather forecasts |
| `person` | Person/presence tracking |
| `zone` | Geographic zones |
