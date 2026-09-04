# Helper Selection Guide

This document covers Home Assistant's built-in helpers and integrations that should be used instead of YAML template sensors or complex automations. When no dedicated helper covers your need, the **Template Helper** (created through the config flow, not YAML `template:`) is the right escape hatch — see [Template Helpers](#template-helpers).

## Table of Contents
1. [How Helpers Are Created](#how-helpers-are-created)
2. [Menu-Based Helpers](#menu-based-helpers)
3. [Reading the Examples in This File](#reading-the-examples-in-this-file) - config-flow fields vs. YAML platform shape
4. [Numeric Aggregation](#numeric-aggregation) - min_max, statistics
5. [Rate and Change](#rate-and-change) - derivative, threshold, trend
6. [Time-Based Tracking](#time-based-tracking) - utility_meter, history_stats, integration (Riemann sum)
7. [State Storage](#state-storage) - input_boolean, input_number, input_select, input_text, input_datetime, input_button
8. [Counting and Timing](#counting-and-timing) - counter, timer
9. [Scheduling](#scheduling) - schedule, time of day (tod)
10. [Entity Grouping](#entity-grouping) - group, binary sensor groups
11. [Probabilistic Inference](#probabilistic-inference) - bayesian
12. [Data Smoothing](#data-smoothing) - filter
13. [Random Values](#random-values) - random
14. [Climate Control](#climate-control) - generic_thermostat, generic_hygrostat, mold_indicator
15. [Domain Conversion](#domain-conversion) - switch_as_x
16. [Template Helpers](#template-helpers) - template (escape hatch when no dedicated helper fits)
17. [Decision Matrix](#decision-matrix) - which helper for which need

## How Helpers Are Created

Helpers reach Home Assistant through two different creation mechanisms — which one a helper uses determines whether you submit flat fields in a single step or step through a config flow:

- **Storage-collection helpers** — created via a per-domain WebSocket collection command (`<domain>/create`, e.g. `input_boolean/create`, `counter/create`) with flat, structured fields: `input_boolean`, `input_number`, `input_select`, `input_text`, `input_datetime`, `input_button`, `counter`, `timer`, `schedule`, `zone`, `person`, `tag`. (All of these also accept YAML config except `tag`, which has none.)
- **Config-flow helpers** — created through the generic config-entry flow (`config_entries/flow`, handler = the helper domain), often a multi-step flow that begins with a sub-type menu (see [Menu-Based Helpers](#menu-based-helpers)): `template`, `group`, `utility_meter`, `derivative`, `min_max`, `threshold`, `integration`, `statistics`, `trend`, `random`, `filter`, `tod`, `generic_thermostat`, `generic_hygrostat`, `switch_as_x`, `bayesian`, `mold_indicator`, `history_stats`.

## Menu-Based Helpers

Several helper integrations — most prominently **`template`**, **`group`**, and **`random`** — start with a sub-type menu before showing fields. The field set isn't known until a sub-type is picked.

| Helper | Sub-types (pick one first) |
|--------|---------------------------|
| `template` | `sensor`, `binary_sensor`, `button`, `switch`, `light`, `cover`, `fan`, `lock`, `select`, `number`, `image`, `vacuum`, `weather`, `alarm_control_panel`, `event`, `update`, `device_tracker` |
| `group` | `binary_sensor`, `button`, `cover`, `event`, `fan`, `light`, `lock`, `media_player`, `notify`, `sensor`, `switch`, `valve` |
| `random` | `sensor`, `binary_sensor` |

Advance the menu by submitting `{"next_step_id": "<sub-type>"}` to the first step; the resulting form's fields become available in the next step. The chosen sub-type is then written into the stored config entry as `template_type` / `group_type` etc. by the integration's validator — those are storage keys, not inputs the caller submits.

## Reading the Examples in This File

Each helper below shows the **flat field set its creation mechanism accepts** — the config-flow
step fields, or the storage-collection `<domain>/create` fields. That is the one representation
the UI form, a raw `config_entries/flow` call, and any programmatic helper API all consume;
core reuses the same `CONF_*` constants for both paths, so the keys match.

The older `sensor:` → `- platform: <helper>` YAML platform shape is **not** shown, because a
helper created that way is not editable in the UI — its config lives in a file, not in a
config entry — and applying a change needs a file edit plus a reload or a restart. To write
one anyway (the user asked for YAML, or you need a YAML-only key), use the YAML root from the
table below with managed YAML editing: see [yaml-only-integrations](yaml-only-integrations.md).

**The post-edit action is per helper, not a blanket restart.** These ship a `<domain>.reload`
that re-reads their YAML platform config: `min_max`, `filter`, `derivative`, `trend`,
`statistics`, `bayesian`, `history_stats`, `generic_thermostat`, `group`, `template`. These
have none, so a YAML change needs `homeassistant.restart` — confirm with the user first:
`threshold`, `tod`, `integration`, `mold_indicator`, `random`, `switch_as_x`,
`generic_hygrostat`, and `utility_meter` (whose services are `reset`/`calibrate` only).

**`YAML-only:` lines are verified against core 2026.8.3** (2026.9 notes against core 2026.9.0). Those keys exist on the YAML
platform schema and have no config-flow field, so needing one is a reason to write YAML.
A helper with no `YAML-only:` line has no such keys. Where the two shapes differ or the flow
cannot express a case (`trend`, `tod`, `bayesian`, `filter`, `template`), both are shown.

**`unique_id` is the one exception, and never a reason to choose YAML.** Most YAML platform
schemas accept it; no flow does, because a flow-created helper gets one from its config entry.
It is therefore omitted from the `YAML-only:` lines below. (`threshold` and `random` are the
odd ones out — their YAML platforms accept *no* `unique_id`, so a YAML-defined entity there
cannot be renamed or given an area from the UI.)

**Two global conventions**, so they are not repeated per helper:
- **Duration fields are mappings in flows** (`minutes: 5`), while the YAML platforms also
  accept the `"00:05:00"` string. Exceptions are called out where they exist.
- **The entity_id is derived from `name`** for both mechanisms, so a helper created as
  "Average Temperature" becomes `sensor.average_temperature`. Renaming it later does not move
  the entity_id.

**Where a `YAML-only:` key sends you, the YAML root differs per helper** — it is not always
`sensor:`:

| Helper | YAML root |
|---|---|
| `min_max`, `statistics`, `derivative`, `integration`, `history_stats`, `filter`, `random`, `mold_indicator` | `sensor:` → `- platform: <helper>` |
| `threshold`, `trend`, `tod`, `bayesian` | `binary_sensor:` → `- platform: <helper>` |
| `generic_thermostat` | `climate:` → `- platform: generic_thermostat` |
| `generic_hygrostat` | `humidifier:` → `- platform: generic_hygrostat` |
| `utility_meter` | top-level `utility_meter:` → slug → fields (no `platform:`) |
| `template` | top-level `template:` → `- sensor:` / `- binary_sensor:` / … |
| `group` (old style) | top-level `group:` → slug → fields |
| `switch_as_x` | none — config flow only |

---

## Numeric Aggregation

### min_max

**Use for:** Combining multiple sensors to get min, max, mean, median, sum, or last value across all of them.

**Instead of:**
```yaml
# WRONG — Template sensor for averaging
template:
  - sensor:
      - name: "Average Temperature"
        state: >
          {{ ((states('sensor.temp_bedroom') | float) +
              (states('sensor.temp_living') | float) +
              (states('sensor.temp_kitchen') | float)) / 3 }}
```

**Use this:**
```yaml
# RIGHT — min_max helper (config-flow fields)
name: "Average Temperature"
type: mean               # required
entity_ids:
  - sensor.temp_bedroom
  - sensor.temp_living
  - sensor.temp_kitchen
round_digits: 2          # required in the flow, default 2
```

Note the key is `round_digits` here — `derivative` and `integration` spell the same idea `round`.

**Available types:** `min`, `max`, `mean`, `median`, `last`, `range`, `sum`

**Key behaviors:**
- Ignores `unknown` states (except `sum` which goes to unknown)
- Returns error if unit of measurement differs between sensors
- For spiky values, filter with statistics sensor first
- Always `state_class: measurement`, so the recorder compiles `mean`/`min`/`max` and never `sum` (`DEFAULT_STATISTICS` in `sensor/recorder.py`)
- Energy Dashboard consequence: a `sum` of energy (kWh) sensors plots nothing and is flagged `entity_state_class_measurement_no_last_reset`. Adding `last_reset` silences that issue but still plots nothing; energy sources need `total` or `total_increasing`. Add each energy sensor as its own dashboard source instead, which the dashboard sums for display. The grid `stat_rate` slot is the opposite case: it requires `measurement` with `device_class: power`, which a `sum` of power sensors satisfies (gas and water `stat_rate` take `volume_flow_rate` instead)
- Since 2026.3, `device_class` is inherited only when every entity in `entity_ids` carries the same one, evaluated once at setup

**Common uses:**
- Average house temperature from multiple room sensors
- Maximum power consumption across circuits
- Sum of solar power (W) across arrays; for kWh use [integration](#integration-riemann-sum)

---

### statistics

**Use for:** Statistical analysis over time for a single sensor (mean, median, stdev, change, variance, etc.).

**Instead of:**
```yaml
# WRONG — Complex template tracking history
template:
  - sensor:
      - name: "Temperature Change"
        state: "{{ states('sensor.temp') | float - state_attr('sensor.temp', 'last_value') | float(0) }}"
```

**Use this:**
```yaml
# RIGHT — statistics helper (config-flow submission, THREE steps — not one payload)
# --- step 1 (user) ---
name: "Temperature Change (5 min)"
entity_id: sensor.temperature
# --- step 2 (state_characteristic) ---
state_characteristic: change   # options depend on sensor vs binary_sensor source
# --- step 3 (options) ---
sampling_size: 50
max_age:                       # duration mapping
  minutes: 5
keep_last_sample: false
percentile: 50                 # only used by the percentile characteristic
precision: 2
```

**Available characteristics — numeric source** (27):
`average_linear`, `average_step`, `average_timeless`, `change`, `change_sample`,
`change_second`, `count`, `datetime_newest`, `datetime_oldest`, `datetime_value_max`,
`datetime_value_min`, `distance_95_percent_of_values`, `distance_99_percent_of_values`,
`distance_absolute`, `mean`, `mean_circular`, `median`, `noisiness`, `percentile`,
`standard_deviation`, `sum`, `sum_differences`, `sum_differences_nonnegative`, `total`,
`value_max`, `value_min`, `variance`

**Binary-sensor source** (8): `average_step`, `average_timeless`, `count`, `count_on`,
`count_off`, `datetime_newest`, `datetime_oldest`, `mean`

The flow offers only the set valid for the chosen source, which is why
`state_characteristic` is its own step. The binary values are `count_on` / `count_off` —
`count_binary_on` / `count_binary_off` are the internal constant *names*, not accepted values.

**Key behaviors:**
- Time-based (`max_age`) vs count-based (`sampling_size`) buffering
- If using `max_age`, ensure frequent enough readings to cover the period
- Different from Long-Term Statistics (which is automatic for sensors with `state_class`)

**Common uses:**
- Humidity change over last hour
- Standard deviation of power readings (detect anomalies)
- Count of motion sensor activations in last 24 hours

---

## Rate and Change

### derivative

**Use for:** Calculating rate of change over time.

**Instead of:**
```yaml
# WRONG — Template calculating delta manually
template:
  - sensor:
      - name: "Power Rate"
        state: "{{ (states('sensor.power') | float - states('sensor.power_previous') | float) / 60 }}"
```

**Use this:**
```yaml
# RIGHT — derivative helper (config-flow fields)
name: "Power Rate of Change"
source: sensor.power
unit_time: h             # required in the flow, default h
round: 2                 # required in the flow, default 2
time_window:             # duration mapping, required in the flow
  minutes: 5
unit_prefix: k           # optional
max_sub_interval:        # optional duration mapping
  minutes: 1
```

**Parameters:**
- `unit_time`: `s`, `min`, `h`, `d` — determines output unit (e.g. W/min)
- `time_window`: smoothing window using a Simple Moving Average
- `round`: decimal places for output (the key is `round`, not `round_digits`)
- `max_sub_interval`: forces a recalculation when the source stops updating

**YAML-only:** `unit` — override the derived output unit outright. Reaching for it is a
legitimate reason to write the YAML platform.

**Key behaviors:**
- Without `time_window`, calculates between consecutive updates only
- Can show large negative spikes when source resets to 0 (total_increasing sensors)
- When the source updates infrequently, set `max_sub_interval` so the derivative decays to
  zero instead of holding its last value

**Common uses:**
- Energy production rate (kW from kWh sensor)
- Temperature change rate (detect HVAC efficiency)
- Water flow rate from cumulative meter

---

### threshold

**Use for:** Creating a binary sensor that turns on/off when a numeric sensor crosses a threshold.

**Instead of:**
```yaml
# WRONG — Template binary sensor
template:
  - binary_sensor:
      - name: "High Temperature"
        state: "{{ states('sensor.temperature') | float > 25 }}"
```

**Use this:**
```yaml
# RIGHT — threshold helper (config-flow fields)
name: "High Temperature"
entity_id: sensor.temperature
upper: 25                # supply upper, lower, or both
hysteresis: 1            # required in the flow, default 0
```

**Parameters:**
- `upper`: threshold for "on" when the value exceeds it
- `lower`: threshold for "on" when the value drops below it
- `hysteresis`: buffer zone to prevent rapid toggling
- Supplying neither `upper` nor `lower` is rejected (`need_lower_upper`)

**YAML-only:** `device_class`. Note the YAML platform accepts **no** `unique_id` here, so a
YAML-defined threshold sensor cannot be renamed or assigned an area from the UI — a further
reason to create it through the flow.

**Hysteresis explained:**
```
With upper: 25 and hysteresis: 1:
- Turns ON when value rises ABOVE 26 (25 + 1)
- Turns OFF when value falls BELOW 24 (25 - 1)
```

**Common uses:**
- Low battery warning (lower threshold)
- High humidity alert
- Air quality threshold alerts
- Detect temperature rising/falling (use with derivative)

---

### trend

**Use for:** A binary sensor that turns on when a numeric sensor is trending up (or down) over time — directly, without chaining `derivative` → `threshold`.

**Instead of:**
```yaml
# WRONG — Template comparing against a stored previous value
template:
  - binary_sensor:
      - name: "Temperature Rising"
        state: "{{ states('sensor.temp') | float > state_attr('sensor.temp', 'prev') | float(0) }}"
```

**Use this:**
```yaml
# RIGHT — trend helper (config-flow submission, NOT configuration.yaml)
# --- step 1 (user) ---
name: "Temperature Rising"
entity_id: sensor.temperature
# --- step 2 (settings) ---
attribute: null          # optional — track an attribute instead of the state
invert: false            # true = detect a downward trend
```

**The tuning fields are not available at creation.** `sample_duration`, `min_gradient`,
`max_samples`, and `min_samples` live in the **options** flow only — submitting them during
creation fails with *extra keys not allowed*. Create the helper first, then reconfigure it to
set them, or write the YAML platform (below), which takes all of them up front.

**The two shapes differ here.** The YAML platform nests everything under a slug-keyed
`sensors:` **mapping** (not a list), unlike most other `binary_sensor` platforms:

```yaml
# YAML platform shape — only when writing configuration.yaml
binary_sensor:
  - platform: trend
    sensors:
      temp_rising:
        entity_id: sensor.temperature
        sample_duration: 1800
        min_gradient: 0.001
```

**YAML-only:** `device_class`, `friendly_name`, plus the four tuning fields above.

**Key behaviors:**
- `min_gradient` is units **per second** (0.001 °/s ≈ 3.6 °/h).
- `sample_duration` is a plain number of seconds in both shapes — not a duration mapping.
- `invert: true` detects a *downward* trend.

**Common uses:**
- Temperature/pressure rising or falling
- Battery draining
- A value drifting before it crosses a hard threshold

---

## Time-Based Tracking

### utility_meter

**Use for:** Tracking consumption with periodic resets (energy, water, gas billing cycles).

**Instead of:**
```yaml
# WRONG — Automation with counter tracking monthly usage
automation:
  - alias: "Reset monthly energy"
    triggers:
      - trigger: time
        at: "00:00:00"
    conditions:
      - "{{ now().day == 1 }}"
    actions:
      - action: input_number.set_value
        target:
          entity_id: input_number.monthly_energy
        data:
          value: 0
```

**Use this:**
```yaml
# RIGHT — utility_meter helper (config-flow fields)
name: "Daily Energy"
source: sensor.energy_consumption
cycle: daily                  # required — the key is `cycle`, not `meter_type`
offset: 0                     # required, default 0 — NUMBER OF DAYS (0-28) in the flow
tariffs: []                   # required, default [] — e.g. ["peak", "offpeak"]
net_consumption: false        # required, default false
delta_values: false           # required, default false
periodically_resetting: true  # required, default true
always_available: false       # optional, default false
```

One meter per flow submission — the YAML shape's slug-keyed mapping creates several at once.

**Cycle options:** `none`, `quarter-hourly`, `hourly`, `daily`, `weekly`, `monthly`, `bimonthly`, `quarterly`, `yearly`.
`cycle` is required in the flow, so `none` is how you say "never resets" there; the YAML
platform has no `none` — omit `cycle` instead.

**Advanced features:**
- **Tariffs:** Track peak/off-peak separately — creates a `select` entity to switch between them
- **Offset:** Shift the cycle start (e.g. a billing date)
- **Delta:** For sensors that report delta values rather than a running total

**YAML-only:** `cron` — custom reset schedules as a cron expression; the flow offers only
the fixed `cycle` list. A non-standard billing period is the usual reason to
write the YAML platform.

**Value type differs:** the flow's `offset` is a **number of days** (0–28); the YAML
platform's `offset` is a duration (`cv.time_period`).

Then use automation to switch tariffs:
```yaml
automation:
  - alias: "Switch to peak tariff"
    triggers:
      - trigger: time
        at: "07:00:00"
    actions:
      - action: utility_meter.select_tariff
        target:
          entity_id: utility_meter.daily_energy
        data:
          tariff: peak
```

**Common uses:**
- Daily/monthly energy consumption
- Water usage per billing cycle
- Gas consumption tracking

---

### history_stats

**Use for:** Statistics about how long/often an entity has been in a specific state.

```yaml
# history_stats helper (config-flow submission, THREE steps — not one payload)
# --- step 1 (user) ---
name: "Lights on today"
entity_id: light.living_room
type: time                    # time | ratio | count, default time
# --- step 2 (state) ---
state:                        # a LIST — several states can be counted together
  - "on"
# --- step 3 (options) ---
start: "{{ today_at() }}"     # supply exactly two of start / end / duration
end: "{{ now() }}"
state_class: measurement
additional_settings:          # collapsed section
  min_state_duration:
    minutes: 1
```

**Types:**
- `time`: Duration in hours
- `ratio`: Percentage of time
- `count`: Number of state changes to the monitored state


**Key behaviors:**
- Limited by recorder's `purge_keep_days`
- Updates when source changes or once per minute
- `state` is a list in both shapes — several states can be counted together
- `duration` is a duration mapping; `start` / `end` are templates

**Common uses:**
- How long lights were on today
- Percentage of time home was occupied
- Count of door openings per day

---

### integration (Riemann sum)

**Use for:** Converting power (W) to energy (kWh), flow rate to volume, etc.

```yaml
# integration (Riemann sum) helper (config-flow fields)
name: "Solar Energy"
source: sensor.solar_power
method: left             # required, default trapezoidal
unit_time: h             # required, default h
unit_prefix: k           # optional
round: 2                 # optional
max_sub_interval:        # optional duration mapping
  minutes: 1
```

**Methods:**
- `left`: Uses previous value for interval (recommended for sparse data)
- `right`: Uses new value for interval
- `trapezoidal`: Averages previous and new (can overestimate with gaps)

**Do not set `unit`.** It was removed from this platform: `PLATFORM_SCHEMA` wraps
`cv.removed("unit")`, which **raises** *"The 'unit' option has been removed"* and fails the
config rather than ignoring the key. The unit is derived from the source plus
`unit_prefix`/`unit_time`.

**Key behaviors:**
- For solar/sensors with gaps, use `left` method
- `max_sub_interval` forces updates even when source doesn't change

**Common uses:**
- Convert solar power (W) to energy production (kWh)
- Convert water flow rate to total consumption
- Convert gas flow to total usage

---

## State Storage

These are **storage-collection helpers**: the fields below are the `<domain>/create` payload.
The YAML shape nests the same fields under a slug you choose (`input_boolean:` → `guest_mode:`
→ fields); through `<domain>/create` there is no slug — HA derives the entity_id from `name`.
Renaming such a helper later does not move its entity_id, so pick the name deliberately.

**Pitfall — `initial` resets state on every restart:** `input_boolean`, `input_number`, `input_select`, `input_text`, and `input_datetime` all accept an `initial` field. If `initial` is present in the config, HA forces that value on every restart instead of restoring the last saved state.
- Omit `initial` to preserve state across restarts.
- Use `initial` only when the helper must always start at a fixed value.

### input_boolean

**Use for:** Toggle switches for modes, flags, and conditions.

```yaml
# input_boolean — input_boolean/create fields
name: "Guest Mode"       # required
icon: mdi:account-group
initial: false           # omit to restore the last state across restarts
```

**Common uses:**
- Guest mode (disable certain automations)
- Vacation mode
- Manual override flags
- Feature toggles

### input_number

**Use for:** Storing numeric values that can be adjusted.

```yaml
# input_number — input_number/create fields
name: "Target Temperature"   # required
min: 15                      # required
max: 30                      # required
step: 0.5                    # default 1
unit_of_measurement: "°C"
mode: slider                 # slider (default) or box
```

**Modes:** `slider`, `box`

**Common uses:**
- User-adjustable thresholds
- Target temperatures
- Timer durations
- Brightness levels

### input_select

**Use for:** Dropdown selection of predefined options.

```yaml
# input_select — input_select/create fields
name: "HVAC Mode"        # required
options:                 # required, must be non-empty and unique
  - "auto"
  - "cool"
  - "heat"
  - "off"
icon: mdi:thermostat
```

**Common uses:**
- Scene selection
- Mode selection
- Status tracking
- Multi-state toggles

### input_text

**Use for:** Storing text strings.

```yaml
# input_text — input_text/create fields
name: "Custom Notification"   # required
min: 0                        # default 0
max: 255                      # default 100
mode: text                    # text (default) or password
pattern: null                 # optional regex the value must match
```

**Modes:** `text`, `password`

**Common uses:**
- Custom messages
- Temporary storage
- User notes

### input_datetime

**Use for:** Storing date and/or time values.

```yaml
# input_datetime — input_datetime/create fields
name: "Morning Alarm"    # required
has_time: true           # at least one of has_date / has_time must be true
has_date: false
```

**Common uses:**
- Alarm times
- Schedule times (wake-up, lights off)
- Future dates (vacation, events)

### input_button

**Use for:** Triggering automations manually.

```yaml
# input_button — input_button/create fields
name: "Doorbell"         # required
icon: mdi:bell
```

**Trigger on a press:** since 2026.9, `trigger: button.pressed` accepts an `input_button`
helper as its target. On 2026.8 and earlier it only accepts `button` entities, so a helper
press needs a state trigger on the helper entity.

**Common uses:**
- Manual triggers for automations
- Dashboard buttons
- Test triggers

---

## Counting and Timing

### counter

**Use for:** Tracking counts with increment/decrement/reset.

**Instead of:**
```yaml
# WRONG — input_number with automation
input_number:
  coffee_count:
    min: 0
    max: 100
automation:
  - alias: "Increment coffee"
    triggers: ...
    actions:
      - action: input_number.set_value
        data:
          value: "{{ states('input_number.coffee_count') | int + 1 }}"
```

**Use this:**
```yaml
# RIGHT — counter helper (counter/create fields)
name: "Coffees Today"    # required
initial: 0               # default 0
step: 1                  # default 1
minimum: 0               # default null (no floor)
maximum: 100             # default null (no ceiling)
restore: true            # default true
```

**Actions:** `counter.increment`, `counter.decrement`, `counter.reset`, `counter.set_value`

**Key behaviors:**
- `restore: true` preserves value across restarts
- Respects min/max boundaries

**Common uses:**
- Daily counts (coffees, workouts)
- Usage tracking
- Sequential numbering

---

### timer

**Use for:** Countdown timers that fire events when finished.

**Instead of:**
```yaml
# WRONG — Delay in automation
actions:
  - delay:
      minutes: 5
  - action: notify.mobile_app
    data:
      message: "Timer done!"
```

**Use this for pausable/restartable timers:**
```yaml
# RIGHT — timer helper (timer/create fields)
name: "Laundry Timer"    # required
duration: "01:00:00"     # default 0
restore: true            # default false
```

**Actions:** `timer.start`, `timer.pause`, `timer.cancel`, `timer.finish`, `timer.change`

**Events fired:**
- `timer.started`
- `timer.paused`
- `timer.cancelled`
- `timer.finished`
- `timer.restarted`

**Key behaviors:**
- Can be started with custom duration: `timer.start` with `duration: "00:30:00"`
- `restore: true` continues timer after restart
- Can be controlled from dashboard

**Common uses:**
- Laundry/dryer reminders
- Cooking timers
- Activity timers with pause/resume

---

## Scheduling

### schedule

**Use for:** Weekly on/off schedules.

```yaml
# schedule — schedule/create fields
name: "Work Hours"       # required
monday:
  - from: "09:00:00"
    to: "17:00:00"
tuesday:
  - from: "09:00:00"
    to: "17:00:00"
# each weekday key defaults to [] when omitted
```

**Key behaviors:**
- Creates a binary sensor that's `on` during scheduled times
- Can have multiple blocks per day
- Editable via UI

**Instead of:**
```yaml
# WRONG — Template with weekday checks
template:
  - binary_sensor:
      - name: "Work Hours"
        state: >
          {{ now().weekday() < 5 and
             now().hour >= 9 and
             now().hour < 17 }}
```

**Common uses:**
- Work hours / business hours
- Quiet hours
- HVAC schedules
- Lighting schedules

---

### time of day (tod)

**Use for:** Binary sensor based on current time (sunrise/sunset or fixed times).

```yaml
# tod helper (config-flow fields)
name: "Morning"
after_time: "06:00:00"    # required
before_time: "12:00:00"   # required
```

**The two shapes use different key names — this trips up copy-paste.** The flow takes
`after_time` / `before_time` and accepts **clock times only**. The YAML platform takes
`after` / `before` and additionally accepts the sun events `sunrise` / `sunset` plus
`after_offset` / `before_offset`:

```yaml
# YAML platform shape — required for sun-relative windows
binary_sensor:
  - platform: tod
    name: "Night Time"
    after: sunset
    after_offset: "01:00:00"
    before: sunrise
```

**YAML-only:** sun events as `after`/`before` values, `after_offset`, `before_offset`.
A sun-relative window is a legitimate reason to write the YAML platform — or
use a `sun` condition in the automation instead of a helper.

**Common uses:**
- Time-of-day modes (morning, afternoon, evening, night)
- Daylight/darkness detection
- Simple time-based conditions

---

## Entity Grouping

### group

**Use for:** Combining entities for collective state and control.

**Menu-based** — submit `{"next_step_id": "<sub-type>"}` first (sub-types: `binary_sensor`,
`button`, `cover`, `event`, `fan`, `light`, `lock`, `media_player`, `notify`, `sensor`,
`switch`, `valve`), then the fields for that sub-type. The stored config entry carries
`group_type` as a storage key — not an input you submit.

```yaml
# group → light (config-flow fields, after next_step_id: light)
name: "All Lights"       # required
entities:                # required
  - light.living_room
  - light.bedroom
  - light.kitchen
hide_members: false      # required, default false
all: false               # required, default false — ON if ANY member is on
```

**Fields vary by sub-type — `all` is not universal.** Every sub-type takes `name`,
`entities`, `hide_members`. Beyond that:

| Sub-type | Additional fields |
|---|---|
| `binary_sensor`, `light`, `switch` | `all` (false = ON if any member is on; true = ON only if all are) |
| `sensor` | `type` (required: `last`, `first_available`, `max`, `mean`, `median`, `min`, `product`, `range`, `stdev`, `sum`). `ignore_non_numeric` is **options-flow only** — not accepted at creation |
| `button`, `cover`, `event`, `fan`, `lock`, `media_player`, `notify`, `valve` | none — `all` is **not** accepted |

Sensor groups accept members from `sensor`, `number`, and `input_number`.

**Key behaviors:**
- Groups inherit the domain of their members
- Light groups can be controlled as a single entity
- Binary sensor groups useful for "any door open" logic
- `hide_members: true` hides the individual members from the UI, leaving only the group

**Old-style YAML `group:` is a different thing** — a domain-agnostic mapping under a top-level
`group:` key that predates the helper. It is still supported and takes only `name`, `entities`,
`all`, and `icon`; it produces a `group.*` entity rather than a native entity of the members'
domain. Prefer the helper.

**Instead of:**
```yaml
# WRONG — Template binary sensor for any-on logic
template:
  - binary_sensor:
      - name: "Any Door Open"
        state: >
          {{ is_state('binary_sensor.front_door', 'on') or
             is_state('binary_sensor.back_door', 'on') }}
```

**Common uses:**
- All lights in an area
- Any motion sensor active
- All doors/windows closed
- Group control in dashboards

---

## Probabilistic Inference

### bayesian

**Use for:** Inferring an unmeasurable state (someone cooking, showering, room occupied) from several probabilistic signals — instead of hand-tuning a template with stacked `and`/`or`/threshold logic.

**The one helper whose flow cannot be expressed as a flat field set.** Observations are added
**one per flow round-trip** through an observation-type menu (`state`, `numeric_state`,
`template`), so there is no single payload carrying an `observations` list. The YAML shape
below is therefore the clearest spec of the configuration; build it in the flow one
observation at a time.

```yaml
# bayesian — YAML platform shape. NOTE THE SCALE: every probability here is 0..1.
# The config flow wants the SAME numbers as PERCENTAGES (0.3 -> 30). Copying these
# values into a flow is accepted and silently means 0.3%.
binary_sensor:
  - platform: bayesian
    name: "Kitchen In Use"
    prior: 0.3                  # flow: 30
    probability_threshold: 0.5  # flow: 50
    observations:
      - entity_id: binary_sensor.kitchen_motion
        platform: state         # or numeric_state / template
        to_state: "on"
        prob_given_true: 0.95   # flow: 95, and the flow also requires a `name` here
        prob_given_false: 0.33  # flow: 33
      - entity_id: sensor.kitchen_power
        platform: numeric_state
        above: 50
        prob_given_true: 0.8    # flow: 80
        prob_given_false: 0.05  # flow: 5
```

**Four differences between the shapes:**

| | YAML platform | Config flow |
|---|---|---|
| Probability scale | `0..1` (`prior: 0.3`) | percentages `0..100` (`prior: 30`), and exactly 0 or 100 is rejected |
| Observations | one `observations:` list | one submission per observation, via a type menu |
| Per-observation `name` | not accepted | **required** on every observation |
| `prob_given_false` | optional | required |

**Key behaviors:**
- Each observation contributes `prob_given_true` / `prob_given_false`; the sensor turns on when the combined posterior probability exceeds `probability_threshold`.
- Observation `platform` is `state`, `numeric_state` (uses `above`/`below`), or `template` (uses `value_template`).
- Two `numeric_state` observations on the **same entity** may not have overlapping
  `above`/`below` ranges — the YAML platform rejects the config with `overlapping_ranges`.
- The observation schemas are closed: an unexpected key fails validation rather than being ignored.


**Common uses:**
- "Someone is cooking" / "shower running" from motion + power + humidity
- Occupancy inference from several weak presence signals

---

## Data Smoothing

### filter

**Use for:** Smoothing noisy sensor data, throttling update frequency, or rejecting out-of-range values.

**Instead of:**
```yaml
# WRONG — Template sensor doing manual smoothing math
template:
  - sensor:
      - name: "Smoothed Power"
        state: >
          {% set h = states('sensor.power_history') | from_json %}
          {{ (h | sum / h | length) | round(2) }}
```

**Use this:**
```yaml
# RIGHT — filter helper (config-flow submission, TWO steps), one filter per entry
# --- step 1 (user) ---
name: "Filtered Temperature"
entity_id: sensor.outdoor_temp
filter: outlier          # picks which fields step 2 offers — see the table below
# --- step 2 (the chosen filter's step) ---
window_size: 4
radius: 2.0
precision: 2             # available on every filter type
```

**Two things are YAML-only here.** The flow creates exactly one filter per config entry, so
**chains** need YAML. The flow's source picker also accepts `sensor` entities only, while the
YAML platform accepts `sensor`, `binary_sensor`, **and** `input_number` — so filtering a
binary sensor or an input_number needs YAML too. For a chain, write the `filters:` list:

```yaml
# YAML platform shape — required for chains
sensor:
  - platform: filter
    name: "Filtered Temperature"
    entity_id: sensor.outdoor_temp
    filters:
      - filter: outlier
        window_size: 4
        radius: 2.0
      - filter: lowpass
        time_constant: 10
      - filter: time_simple_moving_average
        window_size: "00:05"
        precision: 2
```

(You can also chain by pointing one filter helper's `entity_id` at another's output entity.)

**Filter types** (one per UI entry, or multiple in a YAML list):

| Filter | Required | Optional | Notes |
|--------|----------|----------|-------|
| `lowpass` | — | `window_size` (int, default 1), `time_constant` (int, default 10) | Suppresses high-frequency noise. |
| `outlier` | — | `window_size` (int, default 1), `radius` (float, default 2.0) | Drops samples > `radius` standard deviations from the window mean. |
| `range` | — | `lower_bound` (float), `upper_bound` (float) | Clamps to bounds. Supply at least one. |
| `throttle` | — | `window_size` (int, default 1) | Sample-count throttle: emit every Nth value. |
| `time_throttle` | `window_size` (duration) | — | Time-based throttle. UI picker disables days; YAML accepts standard `cv.time_period` syntax including days. |
| `time_simple_moving_average` | `window_size` (duration) | `type` (`last`, default) | Time-windowed SMA. Same UI-vs-YAML duration distinction as `time_throttle`. |

All filters accept optional `precision` (default `2`).

---

## Random Values

### random

**Use for:** Generating random numeric or boolean values (for testing, demos, or simulated occupancy).

**Instead of:**
```yaml
# WRONG — Template with range() / random()
template:
  - sensor:
      - name: "Random Number"
        state: "{{ range(0, 100) | random }}"
```

**Use this:**
```yaml
# RIGHT — random → sensor (config-flow fields, after next_step_id: sensor)
name: "Random Percentage"
minimum: 0               # default 0
maximum: 100             # default 20
unit_of_measurement: "%"
```

Menu-based — pick `sensor` (numeric) or `binary_sensor` (boolean).

**random → sensor**
- Required: `name`
- Optional: `minimum` (default `0`), `maximum` (default `20`), `device_class`, `unit_of_measurement`

**random → binary_sensor**
- Required: `name`
- Optional: `device_class`

Binary-sensor variant (boolean coin-flip — no min/max needed):
```yaml
# random → binary_sensor (after next_step_id: binary_sensor)
name: "Random Boolean"
```

The YAML platform accepts no `unique_id` for either sub-type, so a YAML-defined random sensor
is not UI-editable. There is no reason to prefer YAML for this helper.

---

## Climate Control

### generic_thermostat

**Use for:** Turning a switch (or fan) into a thermostat that follows a temperature sensor.

```yaml
# generic_thermostat helper (config-flow submission, TWO steps)
# --- step 1 (user) ---
name: "Bedroom"                # required
heater: switch.bedroom_heater  # required — a switch or fan entity
target_sensor: sensor.bedroom_temperature   # required — a temperature sensor
ac_mode: false                 # required — true inverts for cooling
cold_tolerance: 0.3            # required, default 0.3
hot_tolerance: 0.3             # required, default 0.3
min_cycle_duration:            # optional duration mapping
  minutes: 5
max_cycle_duration: null       # optional duration mapping
cycle_cooldown: null           # optional duration mapping
keep_alive: null               # optional duration mapping
min_temp: 15                   # optional
max_temp: 25                   # optional
# --- step 2 (presets) — all optional ---
away_temp: 16
comfort_temp: 21
eco_temp: 18
home_temp: 20
sleep_temp: 17
activity_temp: 20
```

**YAML-only:** `initial_hvac_mode`, `precision`, `target_temp_step`, `target_temp`.
Needing a fixed startup mode or a custom temperature step is a legitimate
reason to write the YAML platform.

**Value type differs:** the duration fields are mappings (`minutes: 5`) in the flow; the
YAML platform also accepts the `"00:05:00"` string form.

**Key behaviors:**
- `ac_mode: true` inverts logic (heater output activates for cooling)
- Tolerances prevent rapid cycling near the target

---

### generic_hygrostat

**Use for:** Turning a switch (or fan) into a humidifier/dehumidifier controller that follows a humidity sensor.

```yaml
# generic_hygrostat helper (config-flow fields)
name: "Bathroom Dehumidifier"   # required
device_class: dehumidifier      # required — humidifier or dehumidifier
humidifier: switch.bathroom_fan # required — a switch or fan entity
target_sensor: sensor.bathroom_humidity   # required — a humidity sensor
dry_tolerance: 3                # required, default 3
wet_tolerance: 3                # required, default 3
min_cycle_duration:             # optional duration mapping
  minutes: 5
```

**YAML-only, and there are many:** `min_humidity`, `max_humidity`, `target_humidity`,
`keep_alive`, `initial_state`, `away_humidity`, `away_fixed`, `sensor_stale_duration`.
This helper's flow is markedly thinner than its YAML platform — an away preset
or a stale-sensor timeout requires YAML.

---

### mold_indicator

**Use for:** Estimating mold/condensation risk from indoor temperature + humidity vs. a cold-surface (outdoor) temperature — instead of hand-rolling a dew-point template.

```yaml
# mold_indicator helper (config-flow fields)
name: "Mold Indicator"                        # required, default "Mold Indicator"
indoor_temp_sensor: sensor.indoor_temp        # required
indoor_humidity_sensor: sensor.indoor_humidity # required
outdoor_temp_sensor: sensor.outdoor_temp      # required
calibration_factor: 2.0                       # required in the flow, optional in YAML
```


Outputs an estimated humidity-at-cold-surface percentage; mold risk rises above ~70%. **`calibration_factor` must be physically calibrated** to a known condensation point — it is not a value to guess.

---

## Domain Conversion

### switch_as_x

**Use for:** Exposing a `switch.*` entity as a different domain so it integrates correctly with voice assistants, dashboards, and HVAC logic.

**Instead of:**
```yaml
# WRONG — Template light wrapping a switch
template:
  - light:
      - name: "Lamp"
        turn_on:
          action: switch.turn_on
          target:
            entity_id: switch.lamp_plug
        turn_off:
          action: switch.turn_off
          target:
            entity_id: switch.lamp_plug
        state: "{{ is_state('switch.lamp_plug', 'on') }}"
```

**Use this** (config-flow fields — no YAML equivalent at all):
```yaml
# switch_as_x helper (config-flow fields)
entity_id: switch.lamp_plug   # required — must be a switch.* entity
target_domain: light          # required
invert: false                 # default false
```

`switch_as_x` hides the original switch and registers a proper `light.*` entity that voice assistants and dashboards treat correctly.

**Parameters:**
- Required: `entity_id` (must be a `switch.*` entity), `target_domain` (one of `cover`, `fan`, `light`, `lock`, `siren`, `valve`).
- Optional: `invert` (bool, default `false`) — reverses on/off semantics (useful for normally-closed contacts).

UI-only — no YAML equivalent. The original switch entity is hidden once converted; the new domain entity inherits the switch's state.

---

## Template Helpers

When no dedicated helper covers your need, use the **Template Helper** — created through the config flow, **not** YAML `template:` platform sensors, except for the cases in the YAML-only table below. Template helpers are first-class HA helpers: UI-editable, reloadable without restarting, and visible in the helper registry.

### template

**Use for:** Custom sensor/binary_sensor/switch/light/etc. logic that no dedicated helper (min_max, derivative, threshold, statistics, etc.) provides.

Menu-based — pick a sub-type first (see [Menu-Based Helpers](#menu-based-helpers) for the full sub-type list), then configure fields.

**`availability` is nested, not flat.** Every sub-type puts `availability` (and
`location_accuracy`) inside a collapsed **`additional_options`** section. A flat
`availability:` at the top of the payload fails validation. HA flattens the section when it
sets the entry up, which is why the YAML platform shape shows the key at the top level.

**template → sensor**
- Required: `name`, `state` (Jinja template returning the sensor value)
- Optional: `unit_of_measurement`, `device_class`, `state_class`, `device_id`; `availability` inside `additional_options`

**template → binary_sensor**
- Required: `name`, `state` (Jinja template returning truthy/falsy)
- Optional: `device_class`, `device_id`; `availability` inside `additional_options`

**template → device_tracker** (the native replacement for the legacy `device_tracker.see` action)
- Required: `name`, and **either** `in_zones` (a list of zone entity_ids the device is considered in) **or** both `latitude` and `longitude` (templates)
- Optional: `device_id`; `availability` and `location_accuracy` inside `additional_options`
- **YAML-only:** `icon`, `picture`, and `attributes` for extra attributes of your own (added in 2026.9, YAML-only), plus `unique_id`, as everywhere. `attributes` cannot set the entity's own: `source_type`, `in_zones`, `tracking_type`, `latitude`, `longitude` and `gps_accuracy` are rejected there
- Not valid as config keys in **either** shape: `location_name`, `battery_level`, `source_type`, `host_name`, `mac_address`, `gps_accuracy`

Other sub-types follow the same shape — a `state` template plus domain-appropriate metadata.

```yaml
# template → sensor (config-flow fields, after next_step_id: sensor)
name: "Solar Net"        # required
state: "{{ states('sensor.solar_production') | float(0) - states('sensor.house_consumption') | float(0) }}"
unit_of_measurement: "W"
device_class: power
state_class: measurement
device_id: null          # optional — attach the entity to an existing device
additional_options:      # collapsed section — availability lives HERE, not at top level
  availability: "{{ has_value('sensor.solar_production') and has_value('sensor.house_consumption') }}"
```

**Do not submit `unique_id`** — the flow assigns one from the config entry. It is a
YAML-platform field only.

**State restoration (2026.8+):** `fan`, `cover`, and `device_tracker` template entities
restore their previous state after a restart, so they resume where they left off instead
of coming back blank.

**The YAML platform shape** — needed for the cases the flow cannot express (below), and for
defining several entities at once:
```yaml
template:
  - sensor:
      - name: "Solar Net"
        unique_id: solar_net
        state: "{{ states('sensor.solar_production') | float(0) - states('sensor.house_consumption') | float(0) }}"
        unit_of_measurement: "W"
        device_class: power
        state_class: measurement
  - binary_sensor:
      - name: "Someone Home"
        unique_id: someone_home
        state: "{{ is_state('person.alice','home') or is_state('person.bob','home') }}"
        device_class: presence
```

**YAML-only for template entities** (flow fields verified at 2026.8.3; the 2026.9 notes against core 2026.9.0):

| YAML-only | Why the flow cannot do it |
|---|---|
| **Trigger-based templates** (`triggers:` / `action:` / `variables:` on the block, and per-entity `conditions:` since 2026.9) | The flow has no trigger step. Its per-sub-type action fields (`press`, `turn_on`, `set_value`, …) are entity *commands*, not a trigger block's `actions:` |
| `attributes:` (extra state attributes; on every platform since 2026.9) | No field in the flow |
| Several entities in one block | One entity per config entry |

(`unique_id` is not in this table: the flow assigns one. See the note at the top of this file.)

Needing a trigger, `attributes:`, or several entities in one block is a legitimate reason to
write `template:` YAML — see
[template-guidelines](template-guidelines.md), which covers when templates are the right tool
at all.

See the [Decision Matrix](#decision-matrix) for when the Template Helper is the right choice vs. a dedicated helper — every pattern that has a dedicated helper (averaging, rate of change, thresholds, time-of-day, scheduling, any-on/all-on) should go through that helper first.

---

## Decision Matrix

| Need | Helper | Not |
|------|--------|-----|
| Average of multiple sensors | `min_max` (type: mean) | Template with math |
| Sum of multiple sensors | `min_max` (type: sum) | Template with math |
| Sum of energy (kWh) sensors for the Energy Dashboard | Add each sensor as its own dashboard source | `min_max` (type: sum): `measurement` never compiles `sum` statistics |
| Average over time | `statistics` | Template tracking history |
| Rate of change | `derivative` | Template calculating delta |
| On/off at threshold | `threshold` | Template binary sensor |
| Sensor trending up/down | `trend` | Template with derivative + threshold |
| Consumption per period | `utility_meter` | Counter with reset automation |
| Time in state | `history_stats` | Template tracking timestamps |
| Power to energy | `integration` | Template approximating |
| User toggle | `input_boolean` | - |
| User number | `input_number` | - |
| User selection | `input_select` | - |
| Count events | `counter` | input_number + automation |
| Countdown timer | `timer` | delay + input_datetime |
| Weekly schedule | `schedule` | Template with weekday checks |
| Time of day mode | `tod` | Template with time checks |
| Any-on / all-on | `group` | Template binary sensor |
| Smooth noisy sensor | `filter` | Statistics with `mean` (filter is purpose-built for this) |
| Throttle update rate | `filter` (`throttle`/`time_throttle`) | Custom automation with delays |
| Reject out-of-range values | `filter` (`range`) | Template with bounds check |
| Thermostat from switch + temp sensor | `generic_thermostat` | Automation with hysteresis logic |
| Humidifier from switch + humidity sensor | `generic_hygrostat` | Automation with hysteresis logic |
| Mold/condensation risk from temp + humidity | `mold_indicator` | Dew-point template |
| Infer an unmeasurable state from several signals | `bayesian` | Template with stacked and/or logic |
| Switch presented as light/cover/lock | `switch_as_x` | Template light/cover/lock |
| Random sensor value | `random` | Template with `range()` |
| Custom logic no other helper covers | `template` helper (via config flow) | YAML `template:` platform sensor |
| Template entity that must update on a trigger, or carry `attributes:` | YAML `template:` block — the flow has no equivalent | Forcing it into the flow |
