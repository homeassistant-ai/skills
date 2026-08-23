---
name: home-assistant-best-practices
description: >
  Best practices for HA automations, helpers, scripts, and dashboards.

  TRIGGER THIS SKILL WHEN:
  - Creating or editing automations, scripts, scenes, dashboards, blueprints
  - Choosing template sensors, helpers, or Jinja macros
  - Restructuring triggers, conditions, or modes; button, remote, or event-entity automations
  - Renaming entities or migrating device_id to entity_id
  - Looking up card types or domain docs; writing AppDaemon apps
  - Deleting or restoring a backup, or upgrading Core or the OS

  SYMPTOMS:
  - Jinja2 templates where native options exist
  - device_id used instead of entity_id
  - Entity IDs changed without checking consumers
  - Wrong automation mode chosen
  - Raw sensor or hard-coded value used where a helper belongs
  - Direct .storage edits, or generated YAML snippets
  - User told to edit configuration.yaml for UI integrations
  - Hardcoded Blueprint entities or skipped selectors
  - Existing state changed with no recovery path
  - Jinja copy-pasted between templates
metadata:
  version: "21"
---

# Home Assistant Best Practices

**Core principle:** Use native Home Assistant constructs wherever possible. Templates bypass validation, fail silently at runtime, and make debugging opaque.

## Decision Workflow

Follow this sequence when creating any automation:

### 0. Gate: modifying existing config?

If your change affects entity IDs or cross-component references — renaming entities, replacing template sensors with helpers, converting device triggers, or restructuring automations — read [safe-refactoring](references/safe-refactoring.md) first. That reference covers impact analysis, device-sibling discovery, and post-change verification. Complete its workflow before proceeding.

Steps 1-5 below apply to new config or pattern evaluation.

### 1. Check for a purpose-specific, then generic native, trigger/condition
Since 2026.7 the default building blocks are purpose-specific triggers/conditions — `<domain>.<name>` keys (motion detected, battery low, door opened) with area/floor/label targets. Check for one that matches the intent first, then a generic native trigger/condition, and only then a template. See [automation-patterns #purpose-specific-triggers--conditions-default-since-20267](references/automation-patterns.md#purpose-specific-triggers--conditions-default-since-20267).

**Common substitutions:**
- List of individual sensor entities in a trigger → one purpose-specific trigger with an area/floor/label `target:`
- `{{ states('x') | float > 25 }}` → `numeric_state` condition with `above: 25`
- `{{ is_state('x', 'on') and is_state('y', 'on') }}` → `condition: and` with state conditions
- `{{ now().hour >= 9 }}` → `condition: time` with `after: "09:00:00"`
- `wait_template: "{{ is_state(...) }}"` → `wait_for_trigger` with state trigger (caveat: different behavior when state is already true — see [safe-refactoring #trigger-restructuring](references/safe-refactoring.md#trigger-restructuring))

### 2. Check for built-in helper or Template Helper
Before creating a template sensor, check [helper-selection](references/helper-selection.md).

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
Default `single` mode is often wrong. See [automation-patterns #automation-modes](references/automation-patterns.md#automation-modes).

| Scenario | Mode |
|----------|------|
| Motion light with timeout | `restart` |
| Sequential processing (door locks) | `queued` |
| Independent per-entity actions | `parallel` |
| One-shot notifications | `single` |

### 4. Use entity_id over device_id
`device_id` breaks when devices are re-added. See [device-control](references/device-control.md).

**Exception:** Zigbee2MQTT autodiscovered device triggers are acceptable.

### 5. For buttons and remotes
- **Any integration exposing an `event.*` entity:** Use `event.received` targeting that entity — a normal entity, so it can be renamed and survives a re-add when the integration keeps a stable unique ID
- **ZHA:** No event entities — use an `event` trigger with `device_ieee` (persistent)
- **Z2M:** Event entities are experimental and off by default — use a `device` trigger (autodiscovered) or `mqtt` trigger

See [device-control #buttonremote-patterns](references/device-control.md#buttonremote-patterns).

---

## Critical Anti-Patterns

| Anti-pattern | Use instead | Why | Reference |
|--------------|-------------|-----|-----------|
| `condition: template` with `float > 25` | `condition: numeric_state` | Validated at load, not runtime | [automation-patterns #native-conditions](references/automation-patterns.md#native-conditions) |
| `wait_template: "{{ is_state(...) }}"` | `wait_for_trigger` with state trigger | Event-driven, not polling; waits for *change* (see [safe-refactoring #trigger-restructuring](references/safe-refactoring.md#trigger-restructuring) for semantic differences) | [automation-patterns #wait-actions](references/automation-patterns.md#wait-actions) |
| `device_id` in triggers | `entity_id` (or `device_ieee` for ZHA) | device_id breaks on re-add | [device-control #entity-id-vs-device-id](references/device-control.md#entity-id-vs-device-id) |
| `mode: single` for motion lights | `mode: restart` | Re-triggers must reset the timer | [automation-patterns #automation-modes](references/automation-patterns.md#automation-modes) |
| `enabled: false` as a top-level key in `automations.yaml` | `automation.turn_off` (temporary) or entity registry disable (permanent) | Not a valid top-level key — rejected during schema validation; automation loads as `unavailable` | [automation-patterns #disabling-automations](references/automation-patterns.md#disabling-automations) |
| Template sensor for sum/mean | `min_max` helper | Declarative, handles unavailable states | [helper-selection #numeric-aggregation](references/helper-selection.md#numeric-aggregation) |
| Template binary sensor with threshold | `threshold` helper | Built-in hysteresis support | [helper-selection #threshold](references/helper-selection.md#threshold) |
| Renaming entity IDs without impact analysis | Follow [safe-refactoring](references/safe-refactoring.md) workflow | Renames break dashboards, scripts, scenes, Config-Entry data, and storage dashboards silently | [safe-refactoring #entity-renames](references/safe-refactoring.md#entity-renames) |
| Renaming members of Config-Entry-based groups (UI groups) without updating membership | Update group membership via Options Flow after the registry rename | The entity registry rename does not update `options.entities` in the Config Entry — group silently breaks | [safe-refactoring #config-entry-groups](references/safe-refactoring.md#config-entry-groups) |
| Renaming entities used by Config-Entry integrations (Better/Generic Thermostat, Min/Max, Threshold) without patching Config-Entry data | Scan and patch `core.config_entries` `data`+`options` fields | These integrations store entity_ids in Config Entry — not updated by entity registry renames | [safe-refactoring #config-entry-data--blind-spots-for-entity-registry-renames](references/safe-refactoring.md#config-entry-data--blind-spots-for-entity-registry-renames) |
| `template:` sensor/binary sensor in YAML | Template Helper (UI or config flow API) | Requires file edit and config reload; harder to manage | [template-guidelines](references/template-guidelines.md) |
| Editing `.storage/` files or other HA internal state directly | Use the HA REST/WebSocket API to manage state and config entries | `.storage/` files are HA's internal state database; direct edits bypass validation, risk corruption, and can be silently overwritten by HA | — |
| Writing raw YAML to `configuration.yaml` by hand for YAML-only integrations | Use managed YAML config editing with backup and validation | Unmanaged writes risk syntax errors, have no backup, and skip `check_config` — managed editing provides all three | [yaml-only-integrations](references/yaml-only-integrations.md) |
| Generating YAML snippets for automations/scripts/scenes | Use the HA config API to create automations/scripts programmatically | API calls validate config, avoid syntax errors, and don't require manual file edits or restarts | [automation-patterns](references/automation-patterns.md), [examples.yaml](references/examples.yaml) |
| Telling user to edit `configuration.yaml` for integrations | Direct user to Settings > Devices & Services in the HA UI | Most integrations are UI-configured; YAML integration config is rare and integration-specific | — |
| Referring to HA "add-ons" | Use the term "Apps" | HA renamed add-ons to Apps in 2026.2 — "Apps are standalone applications that run alongside Home Assistant" | — |
| `vacuum.send_command` with vendor room IDs | `vacuum.clean_area` with HA `area_id` (if segments are mapped) | Uses native HA areas, works across integrations — but requires segment-to-area mapping in entity settings first | [device-control #vacuum-control](references/device-control.md#vacuum-control) |
| Using `color_temp` (mireds) in light actions | Use `color_temp_kelvin` | The `color_temp` parameter was removed in 2026.3; only Kelvin is supported | [device-control #lights](references/device-control.md#lights) |
| Person/Device Tracker `entered_home`/`left_home` device triggers or `is_home`/`is_not_home` conditions | `state` trigger `to: home` / `to: not_home`, or `state` condition | These were removed in 2026.5 — state triggers and conditions are the correct replacements | [automation-patterns #presence-and-person-triggers-and-conditions-removed-in-20265](references/automation-patterns.md#presence-and-person-triggers-and-conditions-removed-in-20265) |
| Entity list in a trigger where an area/floor/label target fits | Purpose-specific trigger with `target: {area_id: ...}` | Automation follows area membership as devices change — no stale entity lists | [automation-patterns #purpose-specific-triggers--conditions-default-since-20267](references/automation-patterns.md#purpose-specific-triggers--conditions-default-since-20267) |
| Old purpose-specific keys (`battery.low`, `vacuum.docked`, `timer.time_remaining`, ...) or trigger `behavior: any`/`last` | Renamed 2026.7 keys (`battery.became_low`, ...) and `behavior: each`/`all` | Old keys no longer load; old behavior values raise a repair issue and face removal | [automation-patterns #purpose-specific-triggers--conditions-default-since-20267](references/automation-patterns.md#purpose-specific-triggers--conditions-default-since-20267) |
| AppDaemon: callbacks in `__init__`, uncancelled `run_in` timers, state in instance variables, hardcoded entity IDs | Register in `initialize()`, cancel before rescheduling, persist via `input_*` helpers, pass IDs through `self.args` | Each fails silently, resets on reload, or blocks reuse | [appdaemon #appdaemon-specific-anti-patterns](references/appdaemon.md#appdaemon-specific-anti-patterns) |
| Blueprints: hardcoded entities, free text where a selector belongs, `!input` inside a template, missing `source_url` | Typed `!input` selectors; bind an input to `variables:` before templating it; always set `source_url` | Hardcoding defeats reuse, text lets typos through, and `!input` is a YAML tag rather than a template value | [blueprint-guide #common-pitfalls](references/blueprint-guide.md#common-pitfalls) |
| Backups: full restore to undo one object edit, no backup before an irreversible operation (registry deletion, integration removal, Core/OS upgrade), calling an action "reversible" without naming its inverse | Roll the single object back; take the backup *before*; name the exact inverse or treat it as irreversible | A full restore reverts every unrelated change since and restarts HA; a backup taken afterward captures the damage | [backups #when-a-full-backup-earns-its-cost](references/backups.md#when-a-full-backup-earns-its-cost) |
| Restoring a backup, deleting a backup, or upgrading Core or the OS without explicit user confirmation | Ask, name the concrete effect, and wait for an answer — every time, backup or not | A full restore discards everything since the archive for all restored parts and restarts HA; a Supervisor partial restore overwrites only the selected archive parts; deletion destroys a recovery point; a Core/OS upgrade is high-impact and its recovery path IS the pre-upgrade backup | [backups](references/backups.md) |
| The same non-trivial Jinja expression repeated across templates | Once a native trigger/condition and a built-in helper are ruled out, define it once as a macro in `config/custom_templates/*.jinja` and import it | One definition to fix when the rule changes, instead of copies that drift apart | [template-guidelines #reusable-macros](references/template-guidelines.md#reusable-macros) |
| `trigger`, `this`, `value_json`, or a `{% set %}` variable used inside an imported macro | Pass it to the macro as an argument | An import does not carry the caller's context — the variable is undefined inside the macro, so it renders empty and any attribute access on it errors (HA's own functions like `states` are globals and do work) | [template-guidelines #imports-do-not-carry-the-callers-context](references/template-guidelines.md#imports-do-not-carry-the-callers-context) |

---

## Reference Files

Read these when you need detailed information:

| File | When to read |
|------|--------------|
| [safe-refactoring](references/safe-refactoring.md) | Renaming entities, replacing helpers, restructuring automations, or any modification to existing config |
| [automation-patterns](references/automation-patterns.md) | Writing triggers, conditions, waits, variables, or choosing automation modes; capturing action responses; documenting/annotating steps; disabling automations; `continue_on_error`, stopping a sequence, repeat, if/then vs choose, parallel, trigger IDs |
| [helper-selection](references/helper-selection.md) | Deciding whether to use a built-in helper vs template sensor — aggregation, rate of change, thresholds, time-in-state, counting/timing, scheduling, grouping, probabilistic inference, smoothing, climate, domain conversion, decision matrix |
| [template-guidelines](references/template-guidelines.md) | Confirming templates ARE appropriate for a use case; sharing Jinja logic between templates with `custom_templates` macros |
| [yaml-only-integrations](references/yaml-only-integrations.md) | Creating or editing YAML-only integrations that have no config flow (e.g. `command_line`, platform-based `mqtt`, `rest`) |
| [device-control](references/device-control.md) | Writing actions, button/remote automations, or using target: |
| [scenes](references/scenes.md) | Authoring or activating scenes; snapshot/restore patterns; snapshot-vs-script distinction |
| [dashboard-guide](references/dashboard-guide.md) | Designing or modifying Lovelace dashboards — layout, view types, strategies, sections, cards, badges, CSS styling, HACS |
| [dashboard-cards](references/dashboard-cards.md) | Looking up available card types or fetching card-specific documentation |
| [domain-docs](references/domain-docs.md) | Looking up integration/domain documentation, or the dedicated doc page for a specific trigger, condition, or action |
| [examples.yaml](references/examples.yaml) | Need compound examples combining multiple best practices |
| [appdaemon](references/appdaemon.md) | AppDaemon apps: when to use vs. native HA, app structure, actions, scheduling, error handling, safe refactoring impact |
| [blueprint-guide](references/blueprint-guide.md) | Authoring reusable blueprints: metadata & `source_url`, inputs & selectors, `target` vs `entity`, defaults, input sections, `!input` templating, versioning |
| [backups](references/backups.md) | Deciding whether an operation needs a backup first; choosing between a full restore, a partial restore, and rolling one object back; what an archive actually contains; encryption keys and the emergency kit; restore verification; what HA does and does not protect when deleting a backup |
