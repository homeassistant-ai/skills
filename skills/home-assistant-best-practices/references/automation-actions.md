# Automation Actions

This document covers the `actions:` block of automations and scripts, plus `mode:` and `variables:`, and how to document and disable automations. For triggers and conditions, see [triggers-and-conditions](triggers-and-conditions.md).

## Table of Contents
1. [Wait Actions](#wait-actions)
2. [Automation Modes](#automation-modes)
3. [Continue on Error](#continue-on-error)
4. [Stopping a Sequence](#stopping-a-sequence)
5. [Variables](#variables)
6. [Capturing Action Responses](#capturing-action-responses)
7. [Repeat Actions](#repeat-actions)
8. [if/then vs choose](#ifthen-vs-choose)
9. [Parallel Actions](#parallel-actions)
10. [Documenting Automations & Scripts](#documenting-automations--scripts)
11. [Disabling Automations](#disabling-automations)

---

## Wait Actions

### wait_for_trigger (Preferred)

Waits for a trigger to fire after the wait starts.

```yaml
# Wait for door to close
- wait_for_trigger:
    - trigger: state
      entity_id: binary_sensor.door
      to: "off"
  timeout:
    minutes: 5
  continue_on_timeout: false  # Stop automation if timeout

# Wait for any of multiple triggers
- wait_for_trigger:
    - trigger: state
      entity_id: binary_sensor.door
      to: "off"
    - trigger: event
      event_type: mobile_app_notification_action
      event_data:
        action: "CLOSE_DOOR"
```

### wait_template (Use Sparingly)

Waits until the template is true. HA re-renders it when a referenced entity changes state, and at the start of every minute if it uses `now()`. **Immediately continues if already true.**

```yaml
# Only use when wait_for_trigger cannot express the condition
- wait_template: "{{ states('sensor.temperature') | float > 25 }}"
  timeout:
    minutes: 10
```

**Key difference:**
- `wait_for_trigger` waits for a **change** to occur
- `wait_template` waits for a **condition** to be true (passes immediately if already true)

### Checking Wait Results

Both waits set `wait.completed` and `wait.remaining`:

```yaml
- wait_for_trigger:
    - trigger: state
      entity_id: binary_sensor.door
      to: "off"
  timeout:
    minutes: 5

- if:
    - "{{ not wait.completed }}"
  then:
    - action: notify.mobile_app
      data:
        message: "Door still open after 5 minutes!"
```

### delay

Pauses the sequence for a fixed time. Accepts a time string, a units dict, or a template. Prefer `wait_for_trigger` when waiting for an *event* rather than a fixed duration.

```yaml
- delay: "00:01:30"                 # HH:MM:SS
- delay: {minutes: 1, seconds: 30}  # units dict (combinable)
- delay: "{{ states('input_number.delay_seconds') | int }}"   # template → seconds
```

---

## Automation Modes

The `mode` determines what happens when an automation triggers while already running.

### single (Default)

New triggers are ignored while running. A warning is logged.

**Best for:** One-shot notifications, actions that shouldn't overlap.

```yaml
automation:
  - alias: "Doorbell notification"
    mode: single
    triggers:
      - trigger: state
        entity_id: binary_sensor.doorbell
        to: "on"
    actions:
      - action: notify.mobile_app
        data:
          message: "Someone at the door!"
```

### restart

Stops the current run and starts fresh. Timer-based actions are reset.

**Best for:** Motion-activated lights with timeout, retriggerable delays.

```yaml
mode: restart  # Re-trigger resets the timer
```

See [examples.yaml](examples.yaml) Example 1 for a complete motion-light automation using restart + wait_for_trigger.

### queued

Queues new triggers to run after current run completes.

**Best for:** Sequential actions, door locks, garage doors.

```yaml
automation:
  - alias: "Garage door controller"
    mode: queued
    max: 5  # Maximum queue size
    triggers:
      - trigger: state
        entity_id: input_boolean.garage_door_trigger
        to: "on"
    actions:
      - action: cover.toggle
        target:
          entity_id: cover.garage_door
      - delay:
          seconds: 20  # Wait for door to fully open/close
```

### parallel

Runs multiple instances simultaneously.

**Best for:** Per-entity actions with `trigger.entity_id`, notifications that shouldn't block.

```yaml
automation:
  - alias: "Window open too long"
    mode: parallel
    max: 10  # Maximum parallel runs
    triggers:
      - trigger: state
        entity_id:
          - binary_sensor.window_bedroom
          - binary_sensor.window_kitchen
          - binary_sensor.window_living
        to: "on"
        for:
          minutes: 30
    actions:
      - action: notify.mobile_app
        data:
          message: "{{ trigger.to_state.name }} has been open for 30 minutes"
```

### max_exceeded

Control logging when max runs are exceeded:

```yaml
automation:
  - alias: "Quiet automation"
    mode: single
    max_exceeded: silent  # No warning logged
```

---

## Continue on Error

Any automation action can be set to continue execution even if it fails, using the `continue_on_error` key. Since 2026.3, this is also configurable in the visual editor (three-dots menu on any action).

```yaml
actions:
  - action: light.turn_on
    target:
      entity_id: light.patio
    continue_on_error: true  # Automation proceeds even if this fails
  - action: notify.mobile_app
    data:
      message: "Light action attempted"
```

**Use sparingly** — silently swallowing errors makes debugging harder. Best for non-critical actions (e.g., logging, optional notifications) where a failure shouldn't block the rest of the automation.

### Admin-only actions in user-started scripts

Some actions refuse a non-admin caller — since 2026.9 these include `update.install`, `update.skip` and `update.clear_skipped`. The check reads the user on the run's context:

| Started by | Admin-only action |
|---|---|
| An automation, however triggered (a manual run too), or a script it calls | Runs — every automation run gets a fresh context with no user |
| An admin (UI, dashboard button, their long-lived token) | Runs |
| A non-admin user (dashboard button, their long-lived token) | Fails with `Unauthorized` |

`continue_on_error: true` does not fix the non-admin row: it swallows `Unauthorized` like any other runtime error, so the script carries on without the update installed. To let non-admins start it on purpose, have the button call `automation.trigger` on an automation that runs the action (a helper change that triggers the automation also works) — this deliberately grants every user who can press the button that admin-only action.

---

## Stopping a Sequence

`stop:` halts the rest of the sequence cleanly — clearer than nesting everything inside a `choose`/`if` guard.

```yaml
- stop: "reason shown in the trace"

# Mark the run as failed (red in the trace, propagates to callers):
- stop: "unexpected state"
  error: true

# Return a value from a script and halt:
- stop: "done"
  response_variable: my_result
```

---

## Variables

Compute a value once and reuse it — keeps sequences DRY and avoids repeating long templates.

```yaml
# Mid-sequence (scoped to the remaining steps of this run):
- variables:
    brightness: 100
    targets:
      - light.kitchen
      - light.living_room

# Automation/script top level (full templates; usable in conditions and actions):
variables:
  threshold: 25
```

`trigger_variables:` is a separate top-level key evaluated **before** triggers fire — it supports **limited templates only** (no `states()`/`state_attr()`), mainly for passing a blueprint `!input` into trigger options. Don't put state-based templates there.

### Keys render in order, one at a time

A `variables:` block renders one key at a time, each rendered result feeding the context for the next. A key that reads a name declared **further down the same block** reads it while it is still undefined.

```yaml
# WRONG — `total` is still undefined when `msg` renders
variables:
  msg: "Total: {{ total }}"
  total: "{{ states('sensor.a') | float(0) + states('sensor.b') | float(0) }}"

# RIGHT — declare before use
variables:
  total: "{{ states('sensor.a') | float(0) + states('sensor.b') | float(0) }}"
  msg: "Total: {{ total }}"
```

What the forward read costs depends on how the template uses the name (behavior as of 2026.7):

| Use of the undefined name | Result |
|---|---|
| `x.attr`, `x['k']`, arithmetic, `<`/`>`/`<=`/`>=`, `\| int`, `\| float` | Raises `UndefinedError`, logs ERROR — **aborts the run** |
| `{{ x }}`, `{% if x %}`, `{% for i in x %}`, `'p' ~ x` | Empty and falsy, logs WARNING — runs on into the else branch |
| `x \| length`, `x == y`, `x != y` | `0` / `False` / `True` — **no log and no trace entry** |

For the aborting row, [`continue_on_error:`](#continue-on-error) is no escape — it is an action option, a top-level block is not an action, and on a mid-sequence step it cannot suppress a render error. A default like `| int(0)` does not save it either: the default covers an unconvertible value, not an undefined name. In the silent row, watch `!=`: `{% if later != 'x' %}` on a name that is not defined yet takes the **then** branch, leaving nothing behind to explain why.

Not a problem when the name also exists in an enclosing scope — the reference then resolves outward to that value. The two placements diverge on that collision, though: a top-level `variables:` block **skips** a key already present in the incoming scope, so the incoming value stands and the block's own definition never takes effect for that run, while a mid-sequence `- variables:` step renders and **overwrites** it. Staging a computation across consecutive `variables:` steps is therefore mid-sequence only.

When an automation declares both `trigger_variables:` and `variables:`, the two render as one sequential mapping with `trigger_variables:` first, so a `variables:` key may read a `trigger_variables:` key but not the reverse. That holds for names declared in only one of the two: a name in both merges into a single entry that keeps the `trigger_variables:` position but takes the `variables:` template, so it renders early — before any `trigger_variables:` key declared after it. The separate attach-time render noted above happens before any `variables:` key exists.

---

## Capturing Action Responses

`response_variable` captures the data an action returns (e.g. `weather.get_forecasts`, `calendar.get_events`, `todo.get_items`) into a variable for later steps — the only native mechanism for response-aware actions.

```yaml
- action: weather.get_forecasts
  target:
    entity_id: weather.home
  data:
    type: daily
  response_variable: forecast
- action: notify.mobile_app
  data:
    message: "High today: {{ forecast['weather.home'].forecast[0].temperature }}°"
```

---

## Repeat Actions

Four repeat variants are available:

```yaml
# Repeat N times
- repeat:
    count: 3
    sequence:
      - action: light.toggle
        target:
          entity_id: light.bedroom

# Repeat while condition is true
- repeat:
    while:
      - condition: state
        entity_id: binary_sensor.door
        state: "on"
    sequence:
      - action: notify.mobile_app
        data:
          message: "Door still open"
      - delay:
          minutes: 5

# Repeat until condition is true
- repeat:
    until:
      - condition: numeric_state
        entity_id: sensor.temperature
        below: 25
    sequence:
      - delay:
          minutes: 1

# Repeat for each item in a list
- repeat:
    for_each:
      - "light.kitchen"
      - "light.bedroom"
      - "light.hallway"
    sequence:
      - action: light.turn_off
        target:
          entity_id: "{{ repeat.item }}"
```

Access `repeat.index` (1-based) and `repeat.item` (for `for_each`) inside the sequence.

---

## if/then vs choose

### if/then/else

Use for simple binary conditions:

```yaml
actions:
  - if:
      - condition: state
        entity_id: sun.sun
        state: "below_horizon"
    then:
      - action: light.turn_on
        target:
          entity_id: light.porch
    else:
      - action: light.turn_off
        target:
          entity_id: light.porch
```

### choose

Use for multiple branches (like switch/case):

```yaml
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: "morning"
        sequence:
          - action: scene.turn_on
            target:
              entity_id: scene.morning

      - conditions:
          - condition: trigger
            id: "evening"
        sequence:
          - action: scene.turn_on
            target:
              entity_id: scene.evening

    default:
      - action: light.turn_off
        target:
          area_id: living_room
```

---

## Parallel Actions

The `parallel:` action runs a group of actions **concurrently** within one sequence. This is distinct from `mode: parallel` (see [Automation Modes](#automation-modes)), which controls concurrency of whole automation *runs*. Steps inside a nested `sequence:` still run in order.

```yaml
actions:
  - parallel:
      - action: notify.person1
        data:
          message: "Sent at the same time"
      - sequence:
          - wait_for_trigger:
              - trigger: state
                entity_id: binary_sensor.motion
                to: "on"
          - action: notify.person2
```

---

## Documenting Automations & Scripts

Two fields document *intent* (the why, not the what):

- **`description:`** — a top-level automation/script field for the overall purpose.
- **`note:`** (2026.6) — a per-block annotation on any individual trigger, condition, or action (including `wait_*`, `choose` branches, `if`/`then`/`else`, `parallel`, `repeat`, and nested `sequence` steps). Scripts have no triggers, so notes there apply to sequence steps and conditions only. The YAML key is the **singular `note:`** (not `notes:`) — the editor surfaces it as a "Notes" field, but the docs never show the key string, so don't guess the plural.

```yaml
description: "Turn on the porch light at dusk; skip if already on."
triggers:
  - trigger: sun
    event: sunset
    note: "Dusk, not full dark — sunset event is ~civil twilight."
actions:
  - action: light.turn_on
    target:
      entity_id: light.porch
    note: "Brightness intentionally left at last value."
```

`note:` is **stored documentation only** — it persists in the saved/edited config but is stripped from the running automation object at runtime, so don't rely on reading it back. Keep notes concise (intent, assumptions, why a threshold/mode/entity was chosen).

---

## Disabling Automations

Home Assistant provides two distinct ways to disable an automation, with different persistence and behavior.

### Method 1: Turn Off (Temporary, State Machine)

`automation.turn_off` disables the automation's configured triggers — it will not fire automatically. The entity remains in the state machine with state `off` and can still be invoked via the `automation.trigger` action.

```yaml
- action: automation.turn_off
  target:
    entity_id: automation.my_automation
  data:
    stop_actions: true  # default: true — stops currently running actions
```

| Attribute | Value |
| --- | --- |
| `stop_actions` | Optional. Stops currently active action runs. **Defaults to `true`.** |
| Survives reload? | Yes — state is stored in `core.restore_state` |
| Survives restart? | Only if the automation has an `id:` field — `core.restore_state` matches by `entity_id`, which is derived from `alias:` without `id:` and is unstable if automations are added, removed, or have conflicting aliases |
| Entity in state machine? | Yes — state is `off` |
| Re-enable via | `automation.turn_on` |

**`initial_state` override:** If the automation YAML contains an explicit `initial_state` value, it overrides the stored state after a restart (`true` forces on, `false` forces off regardless of stored state).

### Method 2: Registry Disable (Permanent, via Entity Registry)

Disabling an automation via *Settings → Automations → open automation → ⋮ → Settings → Enabled toggle* sets `disabled_by: user` in `core.entity_registry`. The entity is removed from the state machine entirely.

| Attribute | Value |
| --- | --- |
| Survives reload? | Yes — stored in `core.entity_registry` |
| Survives restart? | Yes |
| Entity in state machine? | **No** — `GET /api/states/<entity_id>` returns 404 |
| Requires `id:` field? | Yes — the `id:` field in `automations.yaml` becomes the automation's `unique_id`, which is required for an entity registry entry |
| Re-enable via | UI toggle (*Settings → Automations → open automation → ⋮ → Settings → Enabled toggle*) or WebSocket API (`config/entity_registry/update` with `{"disabled_by": null}`) |

**Note:** The list toggle on the Automations page (`/config/automation/dashboard`) calls `automation.turn_on`/`turn_off` (Method 1). The *Enabled toggle* under *Settings → Automations → open automation → ⋮ → Settings → Enabled toggle* modifies the entity registry (Method 2). Both can be active simultaneously — an automation can be registry-enabled but in state `off`, or registry-disabled but with a stored `on` state.

### WRONG: `enabled: false` in automations.yaml

```yaml
# WRONG — enabled: is not a valid top-level key
- alias: My Automation
  enabled: false       # not a valid top-level key
  triggers: ...
```

`enabled:` is **not** a valid top-level key in `automations.yaml`. Home Assistant rejects unknown keys during schema validation, so the automation loads as `unavailable`.

```yaml
# RIGHT — disable temporarily via action (Method 1)
- action: automation.turn_off
  target:
    entity_id: automation.my_automation

# RIGHT — disable permanently via entity registry (Method 2)
# UI: Settings → Automations → open automation → ⋮ → Settings → Enabled toggle
# Or via WebSocket API: config/entity_registry/update (disabled_by: user)
```

### `enabled:` on individual triggers, conditions, and actions

While `enabled:` is not valid as a *top-level* automation key (above), it **is** valid on any individual trigger, condition, or action — as a boolean or a blueprint `!input`. A disabled element is skipped without disabling the whole automation. It also accepts a **limited template** (variables / blueprint inputs only — no `states()`), evaluated **once when the automation loads**.

```yaml
triggers:
  - trigger: sun
    event: sunset
    enabled: false                       # statically disabled
  - trigger: time
    at: "15:30:00"
    enabled: "{{ enable_afternoon }}"    # limited template over a variable/!input; evaluated once at load
actions:
  - action: notify.notify
    enabled: false
```
