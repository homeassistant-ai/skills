---
name: home-assistant-best-practices
description: >
  Best practices for Home Assistant automations, helpers, scripts, and device controls.
  
  TRIGGER THIS SKILL WHEN:
  - Creating or editing HA automations, scripts, or scenes
  - Writing automation conditions or triggers
  - Creating template sensors or binary sensors
  - Using wait_template or wait_for_trigger
  - Choosing between device triggers and state triggers
  - Selecting automation modes (single/restart/queued/parallel)
  - Setting up Zigbee button/remote automations (ZHA or Zigbee2MQTT)
  - Deciding whether to use a built-in helper vs template sensor
  
  SYMPTOMS THAT TRIGGER THIS SKILL:
  - Agent defaults to Jinja2 templates where native constructs exist
  - Agent creates template sensors for simple aggregation (sum/min/max/mean)
  - Agent uses template conditions instead of native state/numeric_state conditions
  - Agent uses wait_template instead of wait_for_trigger
  - Agent uses device_id instead of entity_id in triggers/actions
  - Agent chooses wrong automation mode (e.g., single for motion lights)
---

# Home Assistant Best Practices

**Core principle:** Use native Home Assistant constructs wherever possible. Templates bypass validation, fail silently at runtime, and make debugging opaque.

## Decision Workflow

Follow this sequence when creating any automation:

### 1. Check for native condition/trigger
Before writing any template, check `references/automation-patterns.md` for native alternatives.

**Common substitutions:**
- `{{ states('x') | float > 25 }}` → `numeric_state` condition with `above: 25`
- `{{ is_state('x', 'on') and is_state('y', 'on') }}` → `condition: and` with state conditions
- `{{ now().hour >= 9 }}` → `condition: time` with `after: "09:00:00"`
- `wait_template: "{{ is_state(...) }}"` → `wait_for_trigger` with state trigger

### 2. Check for built-in helper
Before creating a template sensor, check `references/helper-selection.md`.

**Common substitutions:**
- Sum/average multiple sensors → `min_max` integration
- Binary any-on/all-on logic → `group` helper
- Rate of change → `derivative` integration
- Cross threshold detection → `threshold` integration
- Consumption tracking → `utility_meter` helper

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
| `wait_template: "{{ is_state(...) }}"` | `wait_for_trigger` with state trigger | Event-driven, not polling; waits for *change* | `references/automation-patterns.md#wait-actions` |
| `device_id` in triggers | `entity_id` (or `device_ieee` for ZHA) | device_id breaks on re-add | `references/device-control.md#entity-id-vs-device-id` |
| `mode: single` for motion lights | `mode: restart` | Re-triggers must reset the timer | `references/automation-patterns.md#automation-modes` |
| Template sensor for sum/mean | `min_max` helper | Declarative, handles unavailable states | `references/helper-selection.md#numeric-aggregation` |
| Template binary sensor with threshold | `threshold` helper | Built-in hysteresis support | `references/helper-selection.md#threshold` |

---

## Reference Files

Read these when you need detailed information:

| File | When to read | Key sections |
|------|--------------|--------------|
| `references/automation-patterns.md` | Writing triggers, conditions, waits, or choosing automation modes | `#native-conditions`, `#trigger-types`, `#wait-actions`, `#automation-modes`, `#ifthen-vs-choose`, `#trigger-ids` |
| `references/helper-selection.md` | Deciding whether to use a built-in helper vs template sensor | `#numeric-aggregation`, `#rate-and-change`, `#time-based-tracking`, `#counting-and-timing`, `#scheduling`, `#entity-grouping`, `#decision-matrix` |
| `references/template-guidelines.md` | Confirming templates ARE appropriate for a use case | `#when-templates-are-appropriate`, `#when-to-avoid-templates`, `#template-sensor-best-practices`, `#common-patterns`, `#error-handling` |
| `references/device-control.md` | Writing service calls, Zigbee button automations, or using target: | `#entity-id-vs-device-id`, `#service-calls-best-practices`, `#zigbee-buttonremote-patterns`, `#domain-specific-patterns` |
| `references/examples.yaml` | Need compound examples combining multiple best practices | — |
