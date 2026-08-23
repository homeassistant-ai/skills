# Device Control Patterns

Best practices for controlling devices, triggering from buttons and remotes, and structuring actions.

> **Check for a purpose-specific trigger first.** Since 2026.7 the default building block is
> a purpose-specific trigger/condition — `motion.detected`, `door.opened`,
> `switch.turned_on`, `temperature.crossed_threshold` — aimed at a `target:` that accepts an
> area, floor, or label instead of a list of entity IDs. The generic `state` patterns in this
> file remain correct and are the right answer when no purpose-specific block matches, but
> check for one before reaching for them; see
> [automation-patterns #purpose-specific-triggers--conditions-default-since-20267](automation-patterns.md#purpose-specific-triggers--conditions-default-since-20267).
>
> This does not soften the entity-over-device rule below — it strengthens it. A
> purpose-specific `target:` takes `entity_id` / `area_id` / `floor_id` / `label_id` (and
> `device_id`, which you should still avoid), and targeting an area is what removes the stale
> entity list *and* the `device_id` at once.

## Table of Contents
1. [Entity ID vs Device ID](#entity-id-vs-device-id)
2. [Action Best Practices](#action-best-practices)
3. [Button/Remote Patterns](#buttonremote-patterns)
4. [Domain-Specific Patterns](#domain-specific-patterns)
5. [Vacuum Control](#vacuum-control)
6. [Response Data](#response-data)
7. [Common Mistakes](#common-mistakes)
8. [Quick Reference: Action Structure](#quick-reference-action-structure)
9. [Quick Reference: Trigger Types for Devices](#quick-reference-trigger-types-for-devices)

---

## Entity ID vs Device ID

### The Core Problem

`device_id` is a Home Assistant internal identifier that **changes when a device is re-added** (e.g., after Zigbee mesh repair, integration re-setup, or hardware replacement). Automations using `device_id` will break silently.

`entity_id` is user-controllable, stable across device re-adds, and can be renamed for clarity.

### Device Triggers vs State Triggers

```yaml
# ❌ WRONG - device_id changes if device is re-added
triggers:
  - trigger: device
    device_id: abc123def456
    domain: binary_sensor
    type: motion

# ✅ RIGHT - entity_id is stable and renameable
#    (generic fallback — check motion.detected with an area target first)
triggers:
  - trigger: state
    entity_id: binary_sensor.hallway_motion
    to: "on"
```

### When Device ID is Acceptable

The only cases where `device_id` might be acceptable:

1. **Device-only triggers** - Some devices expose triggers without entities (see Zigbee section)
2. **Temporary automations** - Quick tests you'll delete
3. **UI-created automations** - The UI defaults to device triggers; convert to entity triggers for production

---

## Action Best Practices

### Use target: Structure

Modern Home Assistant actions use the `target:` key to specify entities, areas, or devices:

```yaml
actions:
  - action: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness_pct: 100
```

### Target Types

| Type | Use case | Persistence |
|------|----------|-------------|
| `entity_id` | Specific entities | ✅ Stable (recommended) |
| `area_id` | All entities in a room | ✅ Stable |
| `device_id` | All entities on a device | ❌ Changes on re-add |

### Multiple Targets

```yaml
# Multiple entities
target:
  entity_id:
    - light.living_room
    - light.kitchen
    - light.bedroom

# Area targeting (all lights in living room)
target:
  area_id: living_room

# Combined (entities + areas)
target:
  entity_id: light.hallway
  area_id:
    - bedroom
    - bathroom
```

### Template in Targets

```yaml
# Dynamic entity selection
target:
  entity_id: "{{ state_attr('sensor.motion_zone', 'light_entity') }}"

# All lights currently on (advanced)
target:
  entity_id: >
    {{ states.light
       | selectattr('state', 'eq', 'on')
       | map(attribute='entity_id')
       | list }}
```

---

## Button/Remote Patterns

### First: does the integration expose an `event.*` entity?

Many integrations now represent a stateless button press as an **event entity** rather than
a bus event or a device trigger. Where one exists and is stable, it is the best target — a
normal entity, so it can be renamed, is reachable by area or label, and survives a device
re-add as long as the integration assigns a stable unique ID. Trigger on it with
`event.received`:

```yaml
triggers:
  - trigger: event.received
    target:
      entity_id: event.living_room_remote_button
    options:
      event_type:
        - double_short_release   # values are integration-defined; read them off the entity
```

The available `event_type` values come from the entity's own `event_types` attribute —
read them rather than guessing. A plain `state` trigger on the entity fires on *any* event
type, which is the right choice only when you genuinely want all of them.

Two Zigbee stacks are exceptions:

- **ZHA has no event platform**, so ZHA remotes use the `zha_event` pattern below.
- **Zigbee2MQTT's event entities are experimental and off by default** — they need
  `homeassistant: {experimental_event_entities: true}`, and Z2M documents both the feature
  and its event-type names as subject to change. Prefer its autodiscovered `device` trigger
  or an `mqtt` trigger unless the user has already opted in.

### ZHA (Zigbee Home Automation)

ZHA buttons fire `zha_event` events. Use **event triggers** with `device_ieee` (the device's IEEE address), which is **persistent** across re-adds.

```yaml
# ✅ ZHA button trigger - device_ieee is persistent
triggers:
  - trigger: event
    event_type: zha_event
    event_data:
      device_ieee: "00:15:8d:00:07:26:f2:8a"
      command: "toggle"
```

For a complete multi-button remote with trigger_id + choose, see [examples.yaml](examples.yaml) Example 2.

#### Finding ZHA Event Data

1. Go to **Tools → Events** (named **Developer Tools** before 2026.8)
2. Subscribe to `zha_event`
3. Press your button
4. Copy the `device_ieee` and `command` values

### Zigbee2MQTT (Z2M)

Z2M creates **MQTT device triggers** that are autodiscovered. These are acceptable because Z2M manages the device-to-trigger mapping.

```yaml
# ✅ Z2M device trigger - autodiscovered
triggers:
  - trigger: device
    device_id: abc123def456  # OK for Z2M, managed by autodiscovery
    domain: mqtt
    type: action
    subtype: single

# Alternative: MQTT topic trigger (more explicit)
triggers:
  - trigger: mqtt
    topic: "zigbee2mqtt/Bedroom Button/action"
    payload: "single"
```

#### Z2M Device Trigger Discovery

1. Open your device in **Settings → Devices**
2. Look for available triggers under "Automations"
3. The UI will show valid trigger types and subtypes

### Z2M vs ZHA Comparison

| Aspect | ZHA | Zigbee2MQTT |
|--------|-----|-------------|
| Trigger type | `event` trigger | `device` trigger or `mqtt` trigger |
| Identifier | `device_ieee` (persistent) | `device_id` (autodiscovered) |
| Event name | `zha_event` | MQTT device trigger |
| Button actions | `command` field | `type` and `subtype` |

---

## Domain-Specific Patterns

### Lights

**Color temperature:** Always use `color_temp_kelvin` (e.g., `3000`). The legacy `color_temp` parameter (in mireds) was removed in 2026.3.

```yaml
# Turn on with brightness and transition
actions:
  - action: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness_pct: 80
      transition: 2
      color_temp_kelvin: 3000

# Turn on multiple lights differently
actions:
  - action: light.turn_on
    target:
      entity_id: light.main
    data:
      brightness_pct: 100
  - action: light.turn_on
    target:
      entity_id: light.accent
    data:
      brightness_pct: 30
      rgb_color: [255, 147, 41]
```

### Climate

```yaml
# Set temperature with HVAC mode
actions:
  - action: climate.set_temperature
    target:
      entity_id: climate.living_room
    data:
      temperature: 22
      hvac_mode: heat

# Set preset mode
actions:
  - action: climate.set_preset_mode
    target:
      entity_id: climate.living_room
    data:
      preset_mode: away
```

### Covers (Blinds/Shades)

```yaml
# Set to specific position (0 = closed, 100 = open)
actions:
  - action: cover.set_cover_position
    target:
      entity_id: cover.living_room_blinds
    data:
      position: 50

# Tilt control
actions:
  - action: cover.set_cover_tilt_position
    target:
      entity_id: cover.living_room_blinds
    data:
      tilt_position: 75
```

### Media Players

```yaml
# Play media
actions:
  - action: media_player.play_media
    target:
      entity_id: media_player.living_room_speaker
    data:
      media_content_id: "https://example.com/audio.mp3"
      media_content_type: music

# Set volume (0.0 to 1.0)
actions:
  - action: media_player.volume_set
    target:
      entity_id: media_player.living_room_speaker
    data:
      volume_level: 0.5
```

### Notifications

```yaml
# Mobile app notification
actions:
  - action: notify.mobile_app_phone
    data:
      title: "Motion Detected"
      message: "Motion in {{ entity_name(trigger.entity_id) }}"
      data:
        tag: "motion-alert"
        actions:
          - action: "DISMISS"
            title: "Dismiss"
          - action: "VIEW_CAMERA"
            title: "View Camera"

# Persistent notification
actions:
  - action: notify.persistent_notification
    data:
      title: "Reminder"
      message: "Check the laundry"
      notification_id: "laundry_reminder"
```

---

## Vacuum Control

```yaml
# Start cleaning
actions:
  - action: vacuum.start
    target:
      entity_id: vacuum.roborock

# Return to dock
actions:
  - action: vacuum.return_to_base
    target:
      entity_id: vacuum.roborock

# Clean specific areas (2026.3+ — uses HA areas, not vendor room IDs)
# Requires mapping vacuum segments to HA areas in entity settings first
# Supported integrations include Matter, Ecovacs, Roborock (list may grow)
actions:
  - action: vacuum.clean_area
    target:
      entity_id: vacuum.roborock
    data:
      area_id:
        - kitchen
        - living_room
```

**Prefer `vacuum.clean_area`** when the user has mapped vacuum segments to HA areas (entity settings). It works across supported integrations without vendor lock-in.

**Fallback:** When the integration doesn't support `clean_area` or segments aren't mapped, use `vacuum.send_command` with integration-specific parameters:

```yaml
# Integration-specific room cleaning (fallback)
actions:
  - action: vacuum.send_command
    target:
      entity_id: vacuum.roborock
    data:
      command: app_segment_clean
      params:
        - 16  # Vendor-specific room ID
        - 17
```

Suggest the user configure segment-to-area mapping when possible to avoid vendor lock-in.

---

## Response Data

Some actions return data. Use `response_variable` to capture it:

```yaml
actions:
  - action: weather.get_forecasts
    target:
      entity_id: weather.home
    data:
      type: hourly
    response_variable: forecast
  - action: notify.mobile_app_phone
    data:
      message: "Tomorrow's high: {{ forecast['weather.home'].forecast[0].temperature }}°C"
```

---

## Common Mistakes

### ❌ Using entity_id in data instead of target

```yaml
# WRONG (deprecated)
actions:
  - action: light.turn_on
    data:
      entity_id: light.living_room
      brightness: 255

# RIGHT
actions:
  - action: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness: 255
```

### ❌ Hardcoding device_id for regular devices

```yaml
# WRONG - breaks on device re-add
actions:
  - action: light.turn_on
    target:
      device_id: abc123def456

# RIGHT
actions:
  - action: light.turn_on
    target:
      entity_id: light.living_room
```

### ❌ Forgetting action data structure

```yaml
# WRONG - brightness_pct at wrong level
actions:
  - action: light.turn_on
    target:
      entity_id: light.living_room
    brightness_pct: 100

# RIGHT - brightness_pct inside data
actions:
  - action: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness_pct: 100
```

---

## Quick Reference: Action Structure

```yaml
actions:
  - action: domain.service_name   # Required
    target:                       # Optional but recommended
      entity_id: entity.id        # Single or list
      area_id: area_name          # Single or list
      device_id: device_id        # Avoid except for Z2M
    data:                         # Action-specific parameters
      parameter: value
    response_variable: result     # Capture response (if needed)
```

## Quick Reference: Trigger Types for Devices

Read left to right and stop at the first column that applies.

| Device type | Purpose-specific (check first) | Generic fallback | Zigbee specifics |
|-------------|-------------------------------|------------------|------------------|
| Button/Remote | `event.received` on the `event.*` entity, when one exists | `state` on the `event.*` entity (fires on any event type) | ZHA: `event` trigger on `zha_event` + `device_ieee`. Z2M: `device` or `mqtt` trigger |
| Motion sensor | `motion.detected` / `motion.cleared` | `state` | — |
| Door/Window | `door.opened` / `door.closed`, `window.opened` / `window.closed` | `state` | — |
| Temperature | `temperature.crossed_threshold` / `temperature.changed` | `numeric_state` or `state` | — |
| Switch | `switch.turned_on` / `switch.turned_off` | `state` | — |
| Battery | `battery.became_low` / `battery.no_longer_low` | `numeric_state` | — |

Two rules survive whichever column you land in: **don't key a trigger off a `device_id`**
outside the cases in [When Device ID is Acceptable](#when-device-id-is-acceptable), and
**prefer a `target:` over a list of entity IDs** when the automation is really about "this
area" rather than these specific entities — the area keeps working as devices are added,
swapped, or removed.
