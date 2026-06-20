---
name: home-assistant-best-practices
description: >
  Best practices for HA automations, helpers, scripts, controls, and dashboards.

  TRIGGER THIS SKILL WHEN:
  - Creating or editing automations, scripts, scenes, or dashboards
  - Choosing between template sensors and built-in helpers
  - Restructuring triggers, conditions, or automation modes
  - Setting up Zigbee button/remote automations
  - Renaming entities or migrating device_id to entity_id
  - Configuring dashboard cards or selecting helpers
  - Looking up card types or domain docs
  - Writing or reviewing AppDaemon apps

  SYMPTOMS:
  - Agent uses Jinja2 templates where native options exist
  - Agent uses device_id instead of entity_id
  - Agent changes entity IDs without checking consumers
  - Wrong automation mode
  - Agent hard-codes values or uses raw sensor over helper
  - Agent edits .storage, writes YAML, or generates YAML snippets
  - Agent tells user to edit configuration.yaml for UI integrations
metadata:
  version: 8
---

# Home Assistant Best Practices

**Core principle:** Use native Home Assistant constructs wherever possible. Templates bypass validation, fail silently at runtime, and make debugging opaque.

## Decision Workflow

Follow this sequence when creating any automation:

### 0. Gate: modifying existing config?

If your change affects entity IDs or cross-component references — renaming entities, replacing template sensors with helpers, converting device triggers, or restructuring automations — read `references/safe-refactoring.md` first. That reference covers impact analysis, device-sibling discovery, and post-change verification. Complete its workflow before proceeding.

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
|--------------|-------------|-----|-----------|
| `condition: template` with `float > 25` | `condition: numeric_state` | Validated at load, not runtime | `references/automation-patterns.md#native-conditions` |
| `wait_template: "{{ is_state(...) }}"` | `wait_for_trigger` with state trigger | Event-driven, not polling; waits for *change* (see `references/safe-refactoring.md#trigger-restructuring` for semantic differences) | `references/automation-patterns.md#wait-actions` |
| `device_id` in triggers | `entity_id` (or `device_ieee` for ZHA) | device_id breaks on re-add | `references/device-control.md#entity-id-vs-device-id` |
| `mode: single` for motion lights | `mode: restart` | Re-triggers must reset the timer | `references/automation-patterns.md#automation-modes` |
| `enabled: false` as a top-level key in `automations.yaml` | `automation.turn_off` (temporary) or entity registry disable (permanent) | Not a valid top-level key — rejected during schema validation; automation loads as `unavailable` | `references/automation-patterns.md#disabling-automations` |
| Template sensor for sum/mean | `min_max` helper | Declarative, handles unavailable states | `references/helper-selection.md#numeric-aggregation` |
| Template binary sensor with threshold | `threshold` helper | Built-in hysteresis support | `references/helper-selection.md#threshold` |
| Renaming entity IDs without impact analysis | Follow `references/safe-refactoring.md` workflow | Renames break dashboards, scripts, scenes, Config-Entry data, and storage dashboards silently | `references/safe-refactoring.md#entity-renames` |
| Renaming members of Config-Entry-based groups (UI groups) without updating membership | Update group membership via Options Flow after the registry rename | The entity registry rename does not update `options.entities` in the Config Entry — group silently breaks | `references/safe-refactoring.md#config-entry-groups` |
| Renaming entities used by Config-Entry integrations (Better/Generic Thermostat, Min/Max, Threshold) without patching Config-Entry data | Scan and patch `core.config_entries` `data`+`options` fields | These integrations store entity_ids in Config Entry — not updated by entity registry renames | `references/safe-refactoring.md#config-entry-data--blind-spots-for-entity-registry-renames` |
| `template:` sensor/binary sensor in YAML | Template Helper (UI or config flow API) | Requires file edit and config reload; harder to manage | `references/template-guidelines.md` |
| Editing `.storage/` files or other HA internal state directly | Use the HA REST/WebSocket API to manage state and config entries | `.storage/` files are HA's internal state database; direct edits bypass validation, risk corruption, and can be silently overwritten by HA | — |
| Writing raw YAML to `configuration.yaml` by hand for YAML-only integrations | Use managed YAML config editing with backup and validation | Unmanaged writes risk syntax errors, have no backup, and skip `check_config` — managed editing provides all three | `references/yaml-only-integrations.md` |
| Generating YAML snippets for automations/scripts/scenes | Use the HA config API to create automations/scripts programmatically | API calls validate config, avoid syntax errors, and don't require manual file edits or restarts | `references/automation-patterns.md`, `references/examples.yaml` |
| Telling user to edit `configuration.yaml` for integrations | Direct user to Settings > Devices & Services in the HA UI | Most integrations are UI-configured; YAML integration config is rare and integration-specific | — |
| Referring to HA "add-ons" | Use the term "Apps" | HA renamed add-ons to Apps in 2026.2 — "Apps are standalone applications that run alongside Home Assistant" | — |
| `vacuum.send_command` with vendor room IDs | `vacuum.clean_area` with HA `area_id` (if segments are mapped) | Uses native HA areas, works across integrations — but requires segment-to-area mapping in entity settings first | `references/device-control.md#vacuum-control` |
| Using `color_temp` (mireds) in light service calls | Use `color_temp_kelvin` | The `color_temp` parameter was removed in 2026.3; only Kelvin is supported | `references/device-control.md#lights` |
| Person/Device Tracker `entered_home`/`left_home` device triggers or `is_home`/`is_not_home` conditions | `state` trigger `to: home` / `to: not_home`, or `state` condition | These were removed in 2026.5 — state triggers and conditions are the correct replacements | `references/automation-patterns.md#presence-and-person-triggers-and-conditions-removed-in-20265` |
| Registering callbacks or calling `self.turn_on()`/`self.get_state()` in `__init__()` | Register everything in `initialize()` | Plugin connection not established during `__init__` — calls fail silently | `references/appdaemon.md#app-structure-and-lifecycle` |
| Calling `run_in` on repeated triggers without cancelling the previous handle | `cancel_timer(self._off_handle)` before each new `run_in` | Every trigger stacks an independent timer — devices toggle unpredictably | `references/appdaemon.md#scheduling-and-timers` |
| Storing persistent state in instance variables | Use HA `input_number`, `input_boolean`, or `input_text` helpers | Instance variables reset on app reload or daemon restart | `references/appdaemon.md#state-management-and-inter-app-communication` |
| Hardcoding entity IDs inside the class body | Pass entity IDs via `self.args` in `apps.yaml` | Hardcoded IDs prevent reuse and require code edits per installation | `references/appdaemon.md#appsyaml-configuration` |

---

## Reference Files

Read these when you need detailed information:

| File | When to read | Key sections |
|------|--------------|--------------|
| `references/safe-refactoring.md` | Renaming entities, replacing helpers, restructuring automations, or any modification to existing config | `#universal-workflow`, `#entity-renames`, `#helper-replacements`, `#trigger-restructuring`, `#config-entry-data--blind-spots-for-entity-registry-renames`, `#storage-mode-dashboards-storagelovelace` |
| `references/automation-patterns.md` | Writing triggers, conditions, waits, variables, or choosing automation modes; capturing action responses; disabling automations | `#native-conditions`, `#trigger-types`, `#wait-actions`, `#automation-modes`, `#continue-on-error`, `#stopping-a-sequence`, `#variables`, `#capturing-action-responses`, `#repeat-actions`, `#ifthen-vs-choose`, `#parallel-actions`, `#trigger-ids`, `#disabling-automations` |
| `references/helper-selection.md` | Deciding whether to use a built-in helper vs template sensor | `#how-helpers-are-created`, `#menu-based-helpers`, `#numeric-aggregation`, `#rate-and-change`, `#time-based-tracking`, `#counting-and-timing`, `#scheduling`, `#entity-grouping`, `#probabilistic-inference`, `#data-smoothing`, `#random-values`, `#climate-control`, `#domain-conversion`, `#template-helpers`, `#decision-matrix` |
| `references/template-guidelines.md` | Confirming templates ARE appropriate for a use case | `#when-templates-are-appropriate`, `#when-to-avoid-templates`, `#template-sensor-best-practices`, `#common-patterns`, `#error-handling` |
| `references/yaml-only-integrations.md` | Creating or editing YAML-only integrations that have no config flow (e.g. `command_line`, platform-based `mqtt`, `rest`) | `#yaml-only-integration-types`, `#post-edit-actions` |
| `references/device-control.md` | Writing service calls, Zigbee button automations, or using target: | `#entity-id-vs-device-id`, `#service-calls-best-practices`, `#zigbee-buttonremote-patterns`, `#domain-specific-patterns` |
| `references/scenes.md` | Authoring or activating scenes; snapshot/restore patterns; snapshot-vs-script distinction | `#scene-config-shape`, `#activating-a-scene`, `#snapshot--restore-scenecreate`, `#apply-states-without-storing-sceneapply` |
| `references/dashboard-guide.md` | Designing or modifying Lovelace dashboards — layout, view types, strategies, sections, cards, badges, CSS styling, HACS | `#dashboard-structure`, `#view-types`, `#dashboard-strategies`, `#built-in-cards`, `#features`, `#badges`, `#custom-cards`, `#css-styling`, `#common-pitfalls` |
| `references/dashboard-cards.md` | Looking up available card types or fetching card-specific documentation | — |
| `references/domain-docs.md` | Looking up integration or domain documentation for service calls, entity attributes, or configuration | — |
| `references/examples.yaml` | Need compound examples combining multiple best practices | — |
| `references/appdaemon.md` | AppDaemon apps: when to use vs. native HA, app structure, service calls, scheduling, error handling, safe refactoring impact | — |
