# Triggers and Conditions

This document covers the `triggers:` and `conditions:` blocks of an automation: native Home Assistant triggers and conditions that should be used instead of templates. For actions, modes, variables, and disabling automations, see [automation-actions](automation-actions.md).

## Table of Contents
1. [Native Conditions](#native-conditions)
2. [Trigger Types](#trigger-types)
3. [Trigger IDs](#trigger-ids)

---

## Native Conditions

### State Condition

The most common condition type. Supports multiple states, attributes, and duration.

```yaml
# Single state
condition: state
entity_id: light.living_room
state: "on"

# Multiple acceptable states (OR logic)
condition: state
entity_id: vacuum.robot
state:
  - "cleaning"
  - "returning"

# Attribute check
condition: state
entity_id: climate.thermostat
attribute: hvac_action
state: "heating"

# Duration check (entity has been in state for X time)
condition: state
entity_id: binary_sensor.motion
state: "off"
for:
  minutes: 5
```

### Numeric State Condition

For numeric comparisons. Always prefer over template conditions with `| float`.

```yaml
# Above threshold
condition: numeric_state
entity_id: sensor.temperature
above: 25

# Below threshold
condition: numeric_state
entity_id: sensor.humidity
below: 30

# Range
condition: numeric_state
entity_id: sensor.battery
above: 20
below: 80

# Attribute numeric check
condition: numeric_state
entity_id: sun.sun
attribute: elevation
below: -6
```

### Time Condition

For time-based restrictions. Handles midnight crossing automatically.

```yaml
# Time range (handles midnight crossing!)
condition: time
after: "22:00:00"
before: "06:00:00"

# Weekday filter
condition: time
weekday:
  - mon
  - tue
  - wed
  - thu
  - fri

# Combined
condition: time
after: "09:00:00"
before: "17:00:00"
weekday:
  - mon
  - tue
  - wed
  - thu
  - fri
```

> **A one-sided window anchors at midnight — it does not carve a slot out of the day.**
> A `condition: time` with only `before: "21:00:00"` is true from **00:00 to 21:00**, so it still
> matches 01:00, 04:00 and 06:00; with only `after: "21:00:00"` it is true from 21:00 to midnight.
> To restrict to daytime, give **both** bounds (`after: "06:00:00"` *and* `before: "21:00:00"`).
> A window spans midnight only when `after` is later than `before` (e.g. `after: "22:00:00"`,
> `before: "06:00:00"`).

### Sun Condition

For sunrise/sunset-based logic with optional offsets.

```yaml
# After sunset
condition: sun
after: sunset

# Before sunrise with offset
condition: sun
before: sunrise
before_offset: "01:00:00"

# After sunset by 30 minutes
condition: sun
after: sunset
after_offset: "00:30:00"
```

### Zone Condition

For presence detection based on zones.

```yaml
condition: zone
entity_id: person.john
zone: zone.home

# Or check if NOT in zone
condition: not
conditions:
  - condition: zone
    entity_id: person.john
    zone: zone.home
```

### And/Or/Not Conditions

Combine conditions with logical operators.

```yaml
# AND (default when multiple conditions listed)
condition: and
conditions:
  - condition: state
    entity_id: light.kitchen
    state: "on"
  - condition: numeric_state
    entity_id: sensor.brightness
    below: 100

# OR
condition: or
conditions:
  - condition: state
    entity_id: person.john
    state: "home"
  - condition: state
    entity_id: person.jane
    state: "home"

# NOT
condition: not
conditions:
  - condition: state
    entity_id: alarm_control_panel.home
    state: "armed_away"

# Shorthand syntax
conditions:
  - and:
      - condition: state
        entity_id: input_boolean.guest_mode
        state: "on"
      - condition: time
        after: "08:00:00"
```

### Template Condition Shorthand

When you must use a template, use the shorthand syntax:

```yaml
# Shorthand (preferred when template is necessary)
conditions:
  - "{{ trigger.to_state.attributes.brightness > 100 }}"

# Long form (equivalent)
conditions:
  - condition: template
    value_template: "{{ trigger.to_state.attributes.brightness > 100 }}"
```

### Trigger Condition

Matches *which* trigger started the run, by trigger `id` — the clean way to branch on the trigger (see [Trigger IDs](#trigger-ids)) instead of templating `trigger.id`. Only true when the run was started by a trigger (false in scripts and manual runs).

```yaml
condition: trigger
id: motion_on        # a single id, or a list (OR semantics):
# id:
#   - motion_on
#   - motion_off
```

---

## Trigger Types

### Purpose-Specific Triggers & Conditions (default since 2026.7)

HA organizes triggers and conditions by real-world intent (motion detected, door opened, battery low, temperature crossed threshold) rather than by technical entity domain. Introduced in 2026.2 and expanded each release, this family **left Labs and became the default automation-building experience in 2026.7**. It is not UI-only sugar: these are first-class config — `trigger: <domain>.<name>` / `condition: <domain>.<name>` with `target:` and `options:` blocks — and round-trip through the config API like any other automation config. (The step-level `note:` field is separate additive syntax — see [automation-actions #documenting-automations--scripts](automation-actions.md#documenting-automations--scripts).)

```yaml
triggers:
  - trigger: motion.detected
    target:
      area_id: living_room        # entity_id / device_id / area_id / floor_id / label_id
    options:
      behavior: each              # multi-target semantics: each (default) / first / all
      for: "00:00:30"             # optional dwell time
conditions:
  - condition: battery.is_low
    target:
      label_id: critical_devices
    options:
      behavior: any               # conditions combine with any (default) / all
```

**Prefer these over the generic triggers below when one matches the intent:**

- **Targets, not entity lists.** Target an area/floor/label ("motion in the living room") and the automation follows area membership as sensors are added, swapped, or removed — no entity list to maintain. This also replaces most remaining legitimate uses of device triggers.
- **No `unavailable`/`unknown` traps.** Each block handles unavailable states and event-entity re-fire quirks internally.
- **Cross-entity-type.** "Door opened" fires whether the door is a contact sensor or a motorized cover.
- **Integration-extensible.** Integrations register their own (e.g. `zwave_js.*`), so the catalog grows over time.

**Multi-target `behavior` enums differ between triggers and conditions:**

- Triggers: `each` (default) / `first` / `all`. The pre-2026.6 values `any` and `last` were renamed to `each` and `all` — they still work but raise a repair issue and face removal. Never emit them (some official doc pages still show the old values mid-migration).
- Conditions: `any` (default) / `all` — unchanged.

**Keys renamed in 2026.7 (trigger keys unless marked *(condition)*) — old keys no longer work:**

| Old | New |
|-----|-----|
| `battery.low` | `battery.became_low` |
| `battery.not_low` | `battery.no_longer_low` |
| `lawn_mower.docked` | `lawn_mower.returned_to_dock` |
| `schedule.turned_on` | `schedule.block_started` |
| `schedule.turned_off` | `schedule.block_ended` |
| `timer.time_remaining` | `timer.remaining_time_reached` |
| `update.update_became_available` | `update.became_available` |
| `vacuum.docked` | `vacuum.returned_to_dock` |
| `climate.target_temperature` (condition) | `climate.is_target_temperature` |
| `climate.target_humidity` (condition) | `climate.is_target_humidity` |

The low-battery keys `battery.became_low`/`no_longer_low` (and conditions `battery.is_low`/`is_not_low`) read only a battery `binary_sensor`, a low flag. A device that reports only a percentage `sensor` never fires them: use `battery.level_crossed_threshold` for it, and add both triggers when a label or area target holds both kinds.

**Discovering what exists:** every purpose-specific trigger and condition (and every action) has a dedicated documentation page covering its config shape, options, and examples — fetch it on demand instead of guessing keys; see [domain-docs #fetching-trigger-condition-and-action-docs](domain-docs.md#fetching-trigger-condition-and-action-docs). The trees span 50+ domains (~190 trigger and ~150 condition pages, generic types included): battery, motion, occupancy, door/window/gate/garage_door, climate, media_player, sun, timer, schedule, vacuum, lawn_mower, zone, event, vibration, moon, and more. The catalog grows every release, so check the doc tree rather than this list when a domain you need isn't named here.

| Version | Added to the catalog |
|---|---|
| 2026.7 | Sun family: `sun.sunrise`, `sun.sunset`, `sun.dawn`, `sun.dusk`, `sun.solar_noon`, `sun.solar_midnight`, elevation triggers |
| 2026.8 | Moon family (`moon.phase_changed` trigger; `moon.is_phase` / `moon.is_waning` / `moon.is_waxing` conditions) and vibration family (`vibration.detected` / `vibration.cleared` triggers; `vibration.is_detected` / `vibration.is_not_detected` conditions). Do not emit either on 2026.7 |
| 2026.9 | Sun family again: `sun.golden_hour_started` / `_ended` and `sun.blue_hour_started` / `_ended`, each taking `options.period`: `any` (default) / `morning` / `evening`, plus `sun.midnight_sun_started` / `_ended` and `sun.polar_night_started` / `_ended` for polar latitudes; conditions `sun.is_golden_hour` / `sun.is_blue_hour` with the same `options.period`, and `sun.is_midnight_sun` / `sun.is_polar_night` |

Since 2026.7, `options.for` durations on **conditions** are primed from recorded history, so a freshly created or reloaded condition does not restart its duration clock from zero. Trigger `for:` clocks still reset as described in [`for:` duration resets](#for-duration-resets-on-restart-and-on-unavailable).

The generic triggers below remain fully supported and are the right choice when no purpose-specific block matches the intent (attribute changes, template-derived conditions, webhooks, MQTT, etc.). As with everything in this file, create and update automations through the config API — the YAML shows the config shape, not a file to hand-edit.

### State Trigger

The workhorse trigger. Fires on entity state changes.

```yaml
# Basic state change to specific value
triggers:
  - trigger: state
    entity_id: binary_sensor.motion
    to: "on"

# From specific state
triggers:
  - trigger: state
    entity_id: light.bedroom
    from: "off"
    to: "on"

# Any state change (omit to/from)
triggers:
  - trigger: state
    entity_id: sensor.temperature

# Attribute change
triggers:
  - trigger: state
    entity_id: climate.thermostat
    attribute: current_temperature

# Duration trigger (entity has been in state for X)
triggers:
  - trigger: state
    entity_id: light.porch
    to: "on"
    for:
      minutes: 30

# Multiple entities
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.motion_kitchen
      - binary_sensor.motion_hallway
    to: "on"
```

### Numeric State Trigger

Fires when crossing a threshold.

```yaml
triggers:
  - trigger: numeric_state
    entity_id: sensor.temperature
    above: 25
    for:
      minutes: 5
```

### `for:` duration resets on restart and on `unavailable`

A `for:` clause (on `state` / `numeric_state` triggers, and on the `state` condition) measures
**continuous** time the entity has held the matching state. The clock resets to zero whenever that
continuity breaks — including two cases that are easy to miss:

- **Every Home Assistant restart.** On restart the state is *restored* but `last_changed` is
  re-stamped to start-up time, so the duration clock restarts from zero. The same applies to
  `{{ now() - x.last_changed }}` duration math in templates.
- **A momentary `unavailable`.** Cloud-, Wi-Fi- and hub-backed entities routinely flick to
  `unavailable` for a few seconds; each blip resets the clock.

So a long `for:` (e.g. several hours) is **unreliable as a safety backstop** — frequent restarts or
blips keep knocking it back and it may never reach the threshold.

**Robust pattern:** stamp a persistent `input_datetime` on the *genuine* transition you care about,
then gate on elapsed time since the stamp:

```yaml
# 1. On the real transition, record when it happened:
triggers:
  - trigger: state
    entity_id: climate.bedroom
    from: "off"
    to: "cool"
actions:
  - action: input_datetime.set_datetime
    target:
      entity_id: input_datetime.cooling_started
    data:
      datetime: "{{ now() }}"

# 2. Elsewhere, test elapsed time — the timestamp attribute is restart- and unavailable-proof:
conditions:
  - "{{ state_attr('input_datetime.cooling_started', 'timestamp') is not none and now().timestamp() - state_attr('input_datetime.cooling_started', 'timestamp') >= 10800 }}"
```

An `input_datetime` restores its value across restarts and is untouched by `unavailable` blips, so
only the real start/stop events move it.

**Diagnosing:** if a `last_changed` looks wrong, compare it against a stable entity such as `sun.sun`.
When several entities' `last_changed` all jumped to the same time — one that isn't sunrise/sunset —
that was a restart re-stamp, not a real state change.

> 2026.7+ primes `options.for` duration tracking for purpose-specific **conditions** from recorded
> history, so those don't restart from zero on creation/reload. The resets described here still
> apply to trigger `for:` clauses and to `last_changed`-based template math.

### `unavailable` arms a numeric state trigger

The trigger tracks each entity as *armed* or not, judged on the **new** state alone. An entity
becomes armed when it evaluates as **not matching**, and a fire needs an armed entity to then
match. On the plain-state path, `unavailable` and `unknown` count as not matching rather than
raising, so they arm the trigger instead of being ignored. Any *other* non-numeric value (a text
state such as `idle`, or an entity absent from the state machine) raises instead, which logs a
warning and returns, leaving the armed flag as it was. A text state therefore neither arms nor
disarms: `unavailable`, then `idle`, then a matching number still fires.

Two consequences, neither involving a threshold being crossed:

- **After a restart.** The trigger builds its armed set when it attaches, and HA writes
  `unavailable` for every registry entity that has no state yet, so the entity is armed. Its first
  real reading past the threshold then fires.
- **After a blip.** An entity that flicks to `unavailable` and back is re-armed, so the same
  unchanged value fires again.

`for:` does not prevent either case. The re-armed entity matches, the unchanged value keeps
matching for the whole window, so the trigger fires late rather than not at all.

**A guard costs real crossings.** Rejecting a non-numeric `from_state` also drops genuine
crossings that passed through `unavailable` (1400 to `unavailable` to 1600), and with `for:` a blip
inside the window cancels the timer and re-arms, so that crossing never fires at all. Guard only
where a false fire costs more than a missed one, such as switching a high-power load. As with
[`trigger.event`](#event-trigger), `trigger.from_state` is `LoggingUndefined` for non-state
triggers, so short-circuit on `trigger.platform` first:

```yaml
# WRONG — raises UndefinedError when a non-state trigger fires the same automation
conditions:
  - "{{ trigger.from_state.state not in ['unavailable', 'unknown'] }}"

# RIGHT — platform check first; is_number also rejects text states such as `idle`
conditions:
  - condition: template
    value_template: >
      {{ trigger.platform == 'numeric_state'
         and trigger.from_state is not none
         and is_number(trigger.from_state.state) }}
```

### Time Trigger

Fires at specific times.

```yaml
# Fixed time
triggers:
  - trigger: time
    at: "07:00:00"

# Input datetime helper
triggers:
  - trigger: time
    at: input_datetime.morning_alarm

# Time pattern (every 5 minutes)
triggers:
  - trigger: time_pattern
    minutes: "/5"

# Every hour at :30
triggers:
  - trigger: time_pattern
    minutes: 30
```

### Sun Trigger

Fires at sunrise/sunset with optional offset.

```yaml
triggers:
  - trigger: sun
    event: sunset
    offset: "-00:30:00"  # 30 minutes before sunset
```

### Event Trigger

Fires on Home Assistant events.

```yaml
# ZHA button event
triggers:
  - trigger: event
    event_type: zha_event
    event_data:
      device_ieee: "00:11:22:33:44:55:66:77"
      command: "on"

# Custom event
triggers:
  - trigger: event
    event_type: my_custom_event
```

**Multi-trigger guard for `trigger.event`:** In automations mixing event and non-event triggers, `trigger.event` is `LoggingUndefined` for non-event triggers. Attribute access (`.data`, `.split()`) raises `UndefinedError`; `in` on a bare `LoggingUndefined` silently returns `False`. Use `trigger.platform == 'event'` as a short-circuit guard:

```yaml
# WRONG — trigger.event.data raises UndefinedError when a non-event trigger fires
conditions:
  - "{{ 'light.kitchen' in trigger.event.data.entity_id }}"

# RIGHT — guard prevents evaluating trigger.event on non-event triggers
conditions:
  - "{{ trigger.platform == 'event' and 'light.kitchen' in trigger.event.data.entity_id }}"
```

**Firing an event** (the action counterpart of this trigger) — useful for decoupling automations (one fires `my_event`, several others trigger on it):

```yaml
actions:
  - event: my_custom_event
    event_data:
      source: kitchen
      value: "{{ states('sensor.power') }}"   # templates work directly; event_data_template is no longer needed
```

### MQTT Trigger

Fires on MQTT messages.

```yaml
triggers:
  - trigger: mqtt
    topic: "zigbee2mqtt/button/action"
    payload: "single"
```

### Device Trigger (Use Sparingly)

Device triggers key off an opaque `device_id` rather than a readable `entity_id`. Prefer a purpose-specific trigger with a `target:`, or failing that an entity-based `state` trigger — both are self-documenting and easier to maintain.

```yaml
# Prefer a state trigger on a readable entity_id where practical
triggers:
  - trigger: device
    domain: mqtt
    device_id: abc123
    type: action
    subtype: single
```

A matching **`condition: device`** variant exists (`device_id`, `domain`, `entity_id`, `type`) with the same trade-off — prefer a purpose-specific condition, or a `state`/`numeric_state` condition on a readable `entity_id`.

### Zone Trigger

Fires when a person or device tracker enters or leaves a zone.

```yaml
triggers:
  - trigger: zone
    entity_id: person.john
    zone: zone.home
    event: enter   # "enter" or "leave"
```

To *check* zone membership in a condition rather than trigger on the transition, see [Zone Condition](#zone-condition).

### Native Zone Triggers & Conditions (2026.6+)

2026.6 added native, **any-zone** zone primitives (not just home); with the rest of the purpose-specific family they became default (non-Labs) in 2026.7. They serialize as the standard `<domain>.<name>` shape with `options:` and `target:` blocks:

- **Triggers:** `zone.entered`, `zone.left`, `zone.occupancy_detected`, `zone.occupancy_cleared`
- **Conditions:** `zone.in_zone`, `zone.not_in_zone`, `zone.occupancy_is_detected`, `zone.occupancy_is_not_detected`

```yaml
# Trigger — fires when a tracked person/device enters a zone
triggers:
  - trigger: zone.entered
    target:
      entity_id: person.john      # person or device_tracker
    options:
      zone: zone.office
      behavior: each              # "each" (default), "all", or "first"
      # for: "00:05:00"           # optional dwell time
```

Triggers take `behavior: each` (default), `all`, or `first`; the matching **conditions** use a *different* enum — `behavior: any` (default) or `all` (see [Purpose-Specific Triggers & Conditions](#purpose-specific-triggers--conditions-default-since-20267)). The classic flat [Zone Trigger](#zone-trigger) / [Zone Condition](#zone-condition) and plain `state` triggers remain supported.

> The `entered_home`/`left_home`/`is_home`/`is_not_home` device automations were removed in **2026.5** (see [below](#presence-and-person-triggers-and-conditions-removed-in-20265)) — 2026.6 only *adds* these any-zone primitives as the native successor.

### Template Trigger

Fires when a Jinja template renders truthy. Prefer `state`/`numeric_state` whenever the change can be expressed natively — reach for the template trigger only for cross-entity or derived conditions.

```yaml
triggers:
  - trigger: template
    value_template: "{{ states('sensor.temp') | float > 25 and is_state('binary_sensor.window', 'on') }}"
    for: "00:05:00"   # optional: template must stay true this long before firing
```

### Calendar Trigger

Fires at the start or end of a calendar event, with an optional offset. Prefer this over a `state` trigger on the calendar entity, which only tracks one event at a time.

```yaml
triggers:
  - trigger: calendar
    entity_id: calendar.work
    event: start          # "start" or "end"
    offset: "-00:15:00"   # optional: fire 15 min before the event
```

Exposes `trigger.calendar_event` with `.summary`, `.start`, `.end`, `.description`, `.location` for filtering by event details.

### Webhook Trigger

Fires when an HTTP request hits `/api/webhook/<webhook_id>`. The canonical way to trigger HA from external systems (scripts, IFTTT, other servers).

```yaml
triggers:
  - trigger: webhook
    webhook_id: "my-secret-hook-id"
    allowed_methods: [POST, PUT]   # optional; default POST + PUT
    local_only: true               # optional; default true — set false for external callers
```

Read the payload via `trigger.json`, `trigger.data` (form-encoded), `trigger.query`, or `trigger.headers`.

### Home Assistant Trigger

Fires when HA finishes starting or begins shutting down.

```yaml
triggers:
  - trigger: homeassistant
    event: start   # "start" or "shutdown"
```

Use `start` for boot-time setup (restore state, resync devices). `shutdown` handlers get only ~20 seconds before HA stops — keep them short.

> **Don't recompute a user-settable value on `start`.** A boot-time recompute (e.g. re-deriving a
> mode from sensors) overwrites any manual override on every restart. For user-settable state, let
> the helper restore its value (omit `initial:` — see [helper-selection](helper-selection.md)) and only *re-sync
> dependent flags* from the restored value on start.

### Conversation Trigger

Fires when a voice/Assist sentence matches. The match syntax supports `[optional]` words, `(a|b)` alternatives, and `{slot}` wildcards.

```yaml
triggers:
  - trigger: conversation
    command:
      - "party time"
      - "play {album} by {artist}"
```

Captured wildcards are available as `trigger.slots.<name>`; the full text is `trigger.sentence`. To make the assistant speak a dynamic reply, use the `set_conversation_response` action (`- set_conversation_response: "Done"`; `~` clears a previously set response).

### Tag Trigger

Fires when an NFC/QR tag is scanned.

```yaml
triggers:
  - trigger: tag
    tag_id: "A7-6B-90-5F"
    device_id: 0e19cd3c...   # optional: limit to one specific scanner device
```

### Geolocation Trigger

Fires when a transient entity from a geolocation feed (NWS alerts, GDACS, fire-service feeds, USGS quakes) enters or leaves a zone. Keyed by the feed `source`, not a fixed `entity_id`.

```yaml
triggers:
  - trigger: geo_location
    source: nsw_rural_fire_service_feed
    zone: zone.fire_alert
    event: enter   # "enter" or "leave"
```

### Persistent Notification Trigger

Fires on persistent-notification lifecycle changes (e.g. react to an integration posting an error notice).

```yaml
triggers:
  - trigger: persistent_notification
    update_type: [added, updated]     # any of: added, removed, updated (current never reaches triggers); omit for all
    notification_id: invalid_config   # optional: filter to one notification
```

**Since 2026.9, re-posting an existing `notification_id` fires `updated`, not `added`.** Integrations re-post their notices under a fixed ID, so a trigger on `added` alone catches only the first post while that notice is still showing — list `updated` alongside it. Before 2026.9 every create fired `added` and `updated` never fired.

### Presence and Person Triggers and Conditions (Removed in 2026.5)

The `entered_home`/`left_home` device trigger types and `is_home`/`is_not_home` device condition types for `person` and `device_tracker` domains were **removed in 2026.5**. Use state triggers and conditions instead.

```yaml
# WRONG — device trigger types removed in 2026.5
triggers:
  - trigger: device
    domain: person
    type: entered_home
    entity_id: person.john

# RIGHT — state trigger
triggers:
  - trigger: state
    entity_id: person.john
    to: "home"

# RIGHT — state condition
condition: state
entity_id: person.john
state: "home"
```

2026.7 presence semantics to keep in mind:

- A person located by a home presence scanner (router/Bluetooth) may report **no latitude/longitude** — don't read coordinates to infer home presence; use the state or the `in_zones` attribute.
- Person and device_tracker entities expose `in_zones` (all zones containing them, smallest first). Zone entity states (person counts) are derived from it, so a person counts in **every** overlapping zone they're inside, not just one.
- A position-aware device_tracker's state is the **smallest** containing zone (previously: the zone whose center is closest).

For non-home zone presence, prefer the native zone family (see [Native Zone Triggers & Conditions](#native-zone-triggers--conditions-20266)) or `#zone-condition`.

### Timer Entity Triggers (2026.5+)

Timer lifecycle events are purpose-specific triggers: `timer.started`, `timer.finished`, `timer.paused`, `timer.restarted`, `timer.cancelled`, plus `timer.remaining_time_reached` (renamed from `timer.time_remaining` in 2026.7), which fires at a set remaining time.

```yaml
triggers:
  - trigger: timer.remaining_time_reached
    target:
      entity_id: timer.cooking
    options:
      remaining: "00:05:00"
```

The legacy `event`-trigger form (`event_type: timer.finished` with `event_data: {entity_id: ...}`) still works, but the purpose-specific form supports targets and is preferred.

### Media Player Triggers/Conditions (2026.5+)

Media players have purpose-specific triggers (`media_player.started_playing`, `media_player.paused_playing`, `media_player.stopped_playing`, `media_player.turned_on`, `media_player.turned_off`, `media_player.muted`, `media_player.unmuted`, `media_player.volume_changed`, `media_player.volume_crossed_threshold`) and matching conditions (`media_player.is_playing`, `media_player.is_paused`, `media_player.is_not_playing`, `media_player.is_on`, `media_player.is_off`, `media_player.is_muted`, `media_player.is_unmuted`, `media_player.is_volume`).

```yaml
triggers:
  - trigger: media_player.started_playing
    target:
      entity_id: media_player.living_room
    options:
      for: "00:00:30"   # optional: playback must continue this long
```

The generic forms still apply where no purpose-specific block fits (e.g. `state` with `to: "idle"`, or `numeric_state` on `attribute: volume_level`).

---

## Trigger IDs

Assign IDs to triggers for use in conditions and choose:

```yaml
automation:
  - alias: "Multi-trigger automation"
    triggers:
      - trigger: state
        entity_id: binary_sensor.motion
        to: "on"
        id: "motion_on"

      - trigger: state
        entity_id: binary_sensor.motion
        to: "off"
        for:
          minutes: 5
        id: "motion_off"

    actions:
      - choose:
          - conditions:
              - condition: trigger
                id: "motion_on"
            sequence:
              - action: light.turn_on
                target:
                  entity_id: light.hallway

          - conditions:
              - condition: trigger
                id: "motion_off"
            sequence:
              - action: light.turn_off
                target:
                  entity_id: light.hallway
```

Access trigger info in templates with `trigger.id`, `trigger.entity_id`, `trigger.to_state`, etc.
