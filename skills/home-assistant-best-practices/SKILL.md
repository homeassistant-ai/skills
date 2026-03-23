---
name: home-assistant-best-practices
description: >
  Best practices for HA automations, helpers, scripts, device controls, and dashboards.

  TRIGGER THIS SKILL WHEN:
  - Creating/editing automations, scripts, scenes, or dashboards
  - Choosing between template sensors and built-in helpers
  - Writing or restructuring triggers, conditions, or automation modes
  - Setting up Zigbee button/remote automations (ZHA or Zigbee2MQTT)
  - Renaming entities or migrating device_id to entity_id
  - Configuring dashboard cards or picking helpers to feed them
  - Looking up card types or domain-specific documentation

  SYMPTOMS:
  - Agent uses Jinja2 templates where native conditions/triggers/helpers exist
  - Agent uses device_id instead of entity_id
  - Agent modifies entity IDs without checking consumers
  - Agent chooses wrong automation mode (e.g., single for motion lights)
  - Agent hard-codes values or picks raw sensor over derived helper
  - Agent searches for HA config files on disk or generates YAML snippets
  - Agent tells user to edit configuration.yaml for UI-configured integrations
metadata:
  version: 2
---

# Home Assistant Best Practices

**Core principle:** Use native Home Assistant constructs wherever possible. Templates bypass validation, fail silently at runtime, and make debugging opaque.

## Decision Workflow

Follow this sequence when creating any automation:

### 0. Gate: modifying existing config?

If your change affects entity IDs or cross-component references — renaming entities, replacing template sensors with helpers, converting device triggers, or restructuring automations — read `references/safe-refactoring.md` first. That reference covers impact analysis, device-sibling discovery, config-entry data fields, storage dashboard patching, and post-change verification. Complete its workflow before proceeding.

Steps 1-5 below apply to new config or pattern evaluation.

### 1. Check for native condition/trigger
Before writing any template, check `references/automation-patterns.md` for native alternatives.

**Common substitutions:**
- `{{ states('x') | float > 25 }}` → `numeric_state` condition with `above: 25`
- `{{ is_state('x', 'on') and is_state('y', 'on') }}` → `condition: and` with state conditions
- `{{ now().hour >= 9 }}` → `condition: time` with `after: "09:00:00"`
- `wait_template: "{{ is_state(...) }}"` → `wait_for_trigger` with state trigger (caveat: different behavior when state is already true — see `references/safe-refactoring.md#trigger-restructuring`)

### 2. Check for built-in helper or Template Helper
Before creating a template sensor, check `references/helper-selection.md`.

**Common substitutions:**
- Sum/average multiple sensors → `min_max` integration
- Binary any-on/all-on logic → `group` helper
- Rate of change → `derivative` integration
- Cross threshold detection → `threshold` integration
- Consumption tracking → `utility_meter` helper

**If no built-in helper fits, use a Template Helper — not YAML.**
Create it via the HA config flow (MCP tool or API) or via the UI:
Settings → Devices & Services → Helpers → Create Helper → Template.
Only write `template:` YAML if explicitly requested or if neither path is available.

### 3. Select correct automation mode
Default `single` mode is often wrong. See `references/automation-patterns.md#automation-modes`.

| Scenario | Mode |
|----------|------|
| Motion light with timeout | `restart` |
| Sequential processing (door locks) | `queued` |
| Independent per-entity actions | `parallel` |
| One-shot notifications | `single` |

### 4. Use entity_id over device_id
`device_id` breaks when devices are re-added. See `references/device-control.md`.

**Exception:** Zigbee2MQTT autodiscovered device triggers are acceptable.

### 5. For Zigbee buttons/remotes
- **ZHA:** Use `event` trigger with `device_ieee` (persistent)
- **Z2M:** Use `device` trigger (autodiscovered) or `mqtt` trigger

See `references/device-control.md#zigbee-buttonremote-patterns`.

---

## Critical Anti-Patterns

| Anti-pattern | Use instead | Why | Reference |
|---|---|---|---|
| `condition: template` with `float > 25` | `condition: numeric_state` | Validated at load, not runtime | `references/automation-patterns.md#native-conditions` |
| `wait_template: "{{ is_state(...) }}"` | `wait_for_trigger` with state trigger | Event-driven, not polling; waits for *change* (see `references/safe-refactoring.md#trigger-restructuring` for semantic differences) | `references/automation-patterns.md#wait-actions` |
| `device_id` in triggers | `entity_id` (or `device_ieee` for ZHA) | device_id breaks on re-add | `references/device-control.md#entity-id-vs-device-id` |
| `mode: single` for motion lights | `mode: restart` | Re-triggers must reset the timer | `references/automation-patterns.md#automation-modes` |
| Template sensor for sum/mean | `min_max` helper | Declarative, handles unavailable states | `references/helper-selection.md#numeric-aggregation` |
| Template binary sensor with threshold | `threshold` helper | Built-in hysteresis support | `references/helper-selection.md#threshold` |
| Renaming entity IDs without impact analysis | Follow `references/safe-refactoring.md` workflow | Renames break dashboards, scripts, scenes, Config-Entry data, and storage dashboards silently | `references/safe-refactoring.md#entity-renames` |
| Renaming entities used by Config-Entry integrations (Better/Generic Thermostat, Min/Max, Threshold) without patching Config-Entry data | Scan and patch `core.config_entries` `data`+`options` fields | These integrations store entity_ids in Config Entry — not updated by entity registry renames | `references/safe-refactoring.md#config-entry-data--blind-spots-for-entity-registry-renames` |
| Patching Storage-Mode-Dashboards after HA restart | Patch via dashboard API (no restart needed), or patch file before restart | HA loads `.storage/lovelace.*` only at startup when edited directly | `references/safe-refactoring.md#storage-mode-dashboards-storagelovelace` |
| `template:` sensor/binary sensor in YAML | Template Helper (UI or config flow API) | Requires file edit and config reload; harder to manage | `references/template-guidelines.md` |
| Searching for or reading HA config files on disk | Use the HA REST/WebSocket API to manage config programmatically | HA is a remote system accessed via APIs; config files are not on the local filesystem | — |
| Generating YAML snippets for automations/scripts/scenes | Use the HA config API to create automations/scripts programmatically | API calls validate config, avoid syntax errors, and don't require manual file edits or restarts | `references/automation-patterns.md`, `references/examples.yaml` |
| Telling user to edit `configuration.yaml` for integrations | Direct user to Settings > Devices & Services in the HA UI | Most integrations are UI-configured; YAML integration config is rare and integration-specific | — |

---

## Reference Files

Read these when you need detailed information:

| File | When to read | Key sections |
|------|--------------|--------------|
| `references/safe-refactoring.md` | Renaming entities, replacing helpers, restructuring automations, or any modification to existing config | `#universal-workflow`, `#entity-renames`, `#config-entry-data--blind-spots-for-entity-registry-renames`, `#storage-mode-dashboards-storagelovelace`, `#helper-replacements`, `#trigger-restructuring` |
| `references/automation-patterns.md` | Writing triggers, conditions, waits, or choosing automation modes | `#native-conditions`, `#trigger-types`, `#wait-actions`, `#automation-modes`, `#ifthen-vs-choose`, `#trigger-ids` |
| `references/helper-selection.md` | Deciding whether to use a built-in helper vs template sensor | `#numeric-aggregation`, `#rate-and-change`, `#time-based-tracking`, `#counting-and-timing`, `#scheduling`, `#entity-grouping`, `#decision-matrix` |
| `references/template-guidelines.md` | Confirming templates ARE appropriate for a use case | `#when-templates-are-appropriate`, `#when-to-avoid-templates`, `#template-sensor-best-practices`, `#common-patterns`, `#error-handling` |
| `references/device-control.md` | Writing service calls, Zigbee button automations, or using target: | `#entity-id-vs-device-id`, `#service-calls-best-practices`, `#zigbee-buttonremote-patterns`, `#domain-specific-patterns` |
| `references/dashboard-guide.md` | Designing or modifying Lovelace dashboards — layout, view types, sections, custom cards, CSS styling, HACS | `#dashboard-structure`, `#view-types`, `#built-in-cards`, `#features`, `#custom-cards`, `#css-styling`, `#common-pitfalls` |
| `references/dashboard-cards.md` | Looking up available card types or fetching card-specific documentation | — |
| `references/domain-docs.md` | Looking up integration or domain documentation for service calls, entity attributes, or configuration | — |
| `references/examples.yaml` | Need compound examples combining multiple best practices | — |
