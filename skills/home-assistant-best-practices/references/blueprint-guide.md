# Blueprints

A **blueprint is a reusable, parameterized automation/script/template** — a skeleton whose device- and entity-specific parts are replaced by user-provided **inputs**. Author a blueprint only when a pattern will be instantiated more than once or shared/distributed. A one-off automation should stay a plain automation; don't blueprint what you'll use once.

## Table of Contents
1. [When to Author a Blueprint](#when-to-author-a-blueprint)
2. [Blueprint Metadata](#blueprint-metadata)
3. [Inputs and Selectors](#inputs-and-selectors)
4. [`target` Selector vs `entity` Selector](#target-selector-vs-entity-selector)
5. [Defaults](#defaults)
6. [Input Sections](#input-sections)
7. [Referencing Inputs (`!input`) and Templating](#referencing-inputs-input-and-templating)
8. [Versioning and Updates](#versioning-and-updates)
9. [Annotated Example](#annotated-example)
10. [Common Pitfalls](#common-pitfalls)

---

## When to Author a Blueprint

| Signal | Blueprint? |
|--------|-----------|
| Same logic wanted for several sensors/rooms/devices | Yes — parameterize the varying parts as inputs |
| Sharing/distributing to other users | Yes — a blueprint imports cleanly via `source_url` |
| A single automation for one specific set of entities | No — write a normal automation |
| Logic differs meaningfully per instance | No — a blueprint that needs many conditional inputs is usually two blueprints |

Blueprints exist for three domains, set by the `domain:` key: `automation`, `script`, and `template`. The input/selector rules below apply to all three; the surrounding body (`triggers`/`actions` vs `sequence` vs `sensor`/`binary_sensor`) is whatever that domain normally uses.

## Blueprint Metadata

Every blueprint opens with a `blueprint:` mapping:

```yaml
blueprint:
  name: Motion-Activated Light          # required; short and descriptive
  description: Turn a light on when motion is detected, off after a delay.
  domain: automation                    # required: automation | script | template
  author: Your Name                     # optional
  source_url: https://github.com/you/ha-blueprints/blob/main/motion_light.yaml
  homeassistant:
    min_version: "2024.10.0"           # optional; gate version-specific features (see note below)
  input:
    # ... see below
```

- **`source_url`** — the canonical URL of the blueprint file. Always set it. It enables **"Re-import blueprint"** (in-place updates when you publish a fix), provides attribution, and is what the *Import Blueprint* dialog stores. A blueprint without `source_url` can't be updated from source and is awkward to share.
- **`min_version`** — set it when the blueprint uses a feature added in a specific release (e.g. input sections need `2024.6.0`; the in-item `action:` key replacing `service:` needs `2024.8.0`; the plural `triggers:`/`conditions:`/`actions:` keys and the in-item `trigger:` key replacing `platform:` need `2024.10.0`). HA refuses to import the blueprint on older versions instead of failing mysteriously at runtime.
- **`domain`** must match the body: an `automation` blueprint has `triggers:`/`actions:`, a `script` blueprint has a `sequence:`, a `template` blueprint defines template entities.

## Inputs and Selectors

Every entity, device, area, number, or option a user should customize is an **input** with a **selector**. The selector determines the UI control and, critically, *validates and constrains* what the user can pick.

**Prefer a typed selector over free text.** A `text` selector for an entity forces users to type `light.living_room` correctly by hand — a typo passes validation and fails silently at runtime. An `entity` selector gives a filtered picker that can only yield valid, existing entities.

Common selectors:

| Selector | Yields | Use for |
|----------|--------|---------|
| `entity` | entity_id(s) | Picking specific entities; filter with `domain`, `device_class`, `integration` |
| `target` | a target dict (entities/devices/areas/floors/labels) | Anything you pass straight to a service call's `target:` |
| `device` | device_id(s) | Device triggers, or device-level actions (rare — prefer entities) |
| `area` / `floor` / `label` | area/floor/label id(s) | Scoping actions to a whole area/floor/label |
| `number` | number | Timeouts, brightness, thresholds; set `min`/`max`/`step`/`mode`/`unit_of_measurement` |
| `boolean` | true/false | On/off toggles |
| `select` | a chosen option | A fixed list of choices (`options:`) |
| `time` / `duration` | time / duration | Schedules and delays |
| `action` | a sequence of actions | Letting the user inject their own actions (e.g. "what to do when triggered") |
| `text` | free string | Genuinely free text only (messages, names) — never entity IDs |
| `object` | arbitrary YAML | Advanced structured input; last resort |

Constrain entity/device selectors so users can only pick valid targets:

```yaml
motion_sensor:
  name: Motion sensor
  selector:
    entity:
      domain: binary_sensor
      device_class: motion      # only motion binary_sensors are offered
```

Add `multiple: true` to accept a list. Filter by `integration:` when the blueprint is integration-specific.

## `target` Selector vs `entity` Selector

The issue this guide most often resolves. Both point at "what to control," but they produce different shapes:

- **`entity` selector → `entity_id`(s).** Use it when you need the id itself — for a `state` trigger's `entity_id`, a `states(...)` lookup in a template, or an action that specifically wants an entity.
- **`target` selector → a target dict** (`{entity_id, device_id, area_id, floor_id, label_id}`). Use it when the value flows straight into a service call's `target:`. It lets the user target entities, whole devices, or entire areas/floors/labels — more flexible for "act on these lights," where the user might prefer to say "all lights in the living room area."

```yaml
# target selector — pass directly to target:
target_light:
  selector:
    target:
      entity:
        domain: light
# ...
actions:
  - action: light.turn_on
    target: !input target_light        # accepts entity/device/area

# entity selector — you need the id for a trigger / template
motion_sensor:
  selector:
    entity:
      domain: binary_sensor
# ...
triggers:
  - trigger: state
    entity_id: !input motion_sensor    # needs a concrete entity_id
```

Rule of thumb: **controlling things → `target`; observing/templating a specific entity → `entity`.**

## Defaults

Provide `default:` for tuning inputs so the blueprint works out of the box:

```yaml
no_motion_wait:
  name: Wait time
  default: 120                          # sensible default → user can skip it
  selector:
    number: { min: 0, max: 3600, unit_of_measurement: seconds, mode: slider }
```

**Don't** default entity/device/target selectors — there's no universally-correct entity, so the user must choose. An input with no `default:` is required; an input with a `default:` is optional. Use this deliberately: required for the entities the blueprint acts on, optional (defaulted) for behavior tuning.

## Input Sections

Blueprints with many inputs become a wall of fields. Group them with sections (HA `2024.6.0`+). A section is an input entry that itself contains an `input:` map:

```yaml
input:
  devices:
    name: Devices
    icon: mdi:motion-sensor
    input:                              # nested inputs belong to this section
      motion_sensor: { name: Motion sensor, selector: { entity: { domain: binary_sensor, device_class: motion } } }
      target_light:  { name: Light(s),      selector: { target: { entity: { domain: light } } } }
  settings:
    name: Settings
    icon: mdi:cog
    collapsed: true                     # collapsed by default — advanced knobs out of the way
    input:
      no_motion_wait: { name: Wait time, default: 120, selector: { number: { min: 0, max: 3600 } } }
```

`!input` still references inputs by their own key (`!input motion_sensor`), regardless of which section they live in — section names are for display only.

## Referencing Inputs (`!input`) and Templating

Inside the blueprint body, reference an input with the `!input` YAML tag: `entity_id: !input motion_sensor`.

**The #1 blueprint bug:** `!input` is a YAML tag, **not** a template value — you cannot write `{{ !input x }}` or drop `!input` inside a Jinja expression. To use an input in a template, first expose it as a **variable**, then reference the variable:

```yaml
variables:
  brightness_pct: !input brightness     # bind input → variable at script level
# ...
actions:
  - action: light.turn_on
    target: !input target_light
    data:
      brightness_pct: "{{ brightness_pct }}"   # use the variable, never !input
```

For **templated triggers**, bind inputs through `trigger_variables:` (a separate top-level key evaluated before triggers fire). It supports **limited templates only** — no `states()`/`state_attr()` — and exists mainly to pass a blueprint `!input` into trigger options (see `automation-patterns.md#trigger-types`). Don't put state-based templates there.

`enabled:` on an individual trigger/condition/action also accepts a blueprint `!input` (evaluated once at load) — handy for optional behavior toggled by a `boolean` input (see `automation-patterns.md#enabled-on-individual-triggers-conditions-and-actions`).

## Versioning and Updates

Users import a blueprint once, then create automations from it. When you publish changes:

- **Renaming or removing an input key breaks every existing instance** — their stored `!input` references no longer resolve. Treat input keys as a public API.
- **Add** new inputs rather than changing old ones, and give every new input a `default:` so existing automations keep working after a re-import without the user touching them.
- Bump `min_version` if a change relies on a newer HA feature.
- Keep `source_url` stable — it's the update anchor. Users re-import from the same URL to pick up fixes.

## Annotated Example

A complete motion-light automation blueprint demonstrating every practice above:

```yaml
blueprint:
  name: Motion-Activated Light
  description: Turn a light (or area) on when motion is detected, off after a delay.
  domain: automation
  author: Your Name
  source_url: https://github.com/you/ha-blueprints/blob/main/motion_light.yaml
  homeassistant:
    min_version: "2024.10.0"                # modern triggers/actions syntax (input sections alone need only 2024.6.0)
  input:
    devices:
      name: Devices
      icon: mdi:motion-sensor
      input:
        motion_sensor:
          name: Motion sensor
          selector:
            entity:
              domain: binary_sensor
              device_class: motion          # constrained picker — no free text
        target_light:
          name: Light(s) to control
          selector:
            target:                          # target → user may pick lights OR an area
              entity:
                domain: light
    settings:
      name: Settings
      icon: mdi:cog
      collapsed: true
      input:
        no_motion_wait:
          name: Wait time
          description: Seconds to keep the light on after the last motion.
          default: 120                       # sensible default → optional input
          selector:
            number: { min: 0, max: 3600, unit_of_measurement: seconds, mode: slider }
        brightness:
          name: Brightness
          default: 100
          selector:
            number: { min: 1, max: 100, unit_of_measurement: "%" }

# Body — device-specific values come only from !input, never hardcoded:
mode: restart                                # re-trigger resets the timer
max_exceeded: silent

variables:
  brightness_pct: !input brightness          # expose input for use in a template

triggers:
  - trigger: state
    entity_id: !input motion_sensor          # entity selector → concrete entity_id
    to: "on"

actions:
  - action: light.turn_on
    target: !input target_light              # target selector → passed straight to target:
    data:
      brightness_pct: "{{ brightness_pct }}" # variable, not !input, inside the template
  - wait_for_trigger:
      - trigger: state
        entity_id: !input motion_sensor
        to: "off"
  - delay:
      seconds: !input no_motion_wait
  - action: light.turn_off
    target: !input target_light
```

## Common Pitfalls

| Pitfall | Do instead | Why |
|---------|-----------|-----|
| Free-text field for an entity/device | `entity` / `target` / `device` selector | Typed selectors validate the choice; a typo in text fails silently at runtime |
| Hardcoded `light.living_room` in the body | `!input` with a selector | Hardcoding defeats the entire purpose of a blueprint — it can't be reused |
| `!input` used directly in a template (`{{ !input x }}`) | Bind to a `variables:` entry, use the variable | `!input` is a YAML tag, not a template value — the template errors or ignores it |
| State-based template in `trigger_variables:` | Move logic into a template condition/trigger | `trigger_variables` allows limited templates only (no `states()`) |
| No `source_url` | Set it to the file's canonical URL | Enables in-place re-import/updates and sharing |
| No `default:` on tuning inputs | Add a sensible `default:` | Makes the input optional and the blueprint usable out of the box |
| `default:` on the entity the blueprint controls | Leave it required (no default) | There's no universally-correct entity; the user must choose |
| `entity` selector where you pass to `target:` | Use a `target` selector | `target` lets users pick areas/devices too and drops straight into `target:` |
| Renaming/removing input keys in an update | Add new inputs (with defaults); keep old keys | Existing automations reference keys by name and break on rename |
| Missing `min_version` for a used feature | Set `homeassistant.min_version` | HA blocks import on old versions instead of failing at runtime |
