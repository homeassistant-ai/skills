# Helper Selection Guide

This document covers Home Assistant's built-in helpers and integrations that should be used instead of YAML template sensors or complex automations. When no dedicated helper covers your need, the **template helper** (created via the UI / config-entry flow, not YAML `template:`) is the right escape hatch — see [Template Helpers](#template-helpers).

## Table of Contents
1. [Numeric Aggregation](#numeric-aggregation) - min_max, statistics
2. [Rate and Change](#rate-and-change) - derivative, threshold, trend
3. [Time-Based Tracking](#time-based-tracking) - utility_meter, history_stats, integration (Riemann sum)
4. [State Storage](#state-storage) - input_boolean, input_number, input_select, input_text, input_datetime, input_button
5. [Counting and Timing](#counting-and-timing) - counter, timer
6. [Scheduling](#scheduling) - schedule, time of day (tod)
7. [Entity Grouping](#entity-grouping) - group, binary sensor groups
8. [Probabilistic Inference](#probabilistic-inference) - bayesian
9. [Data Smoothing](#data-smoothing) - filter
10. [Random Values](#random-values) - random
11. [Climate Control](#climate-control) - generic_thermostat, generic_hygrostat, mold_indicator
12. [Domain Conversion](#domain-conversion) - switch_as_x
13. [Template Helpers](#template-helpers) - template (escape hatch when no dedicated helper fits)

## How Helpers Are Created

Helpers reach Home Assistant through two different creation mechanisms — which one a helper uses determines whether you submit flat fields in a single step or step through a config flow:

- **Storage-collection helpers** — created via a per-domain WebSocket collection command (`<domain>/create`, e.g. `input_boolean/create`, `counter/create`) with flat, structured fields: `input_boolean`, `input_number`, `input_select`, `input_text`, `input_datetime`, `input_button`, `counter`, `timer`, `schedule`, `zone`, `person`, `tag`. (`schedule` additionally offers an optional YAML mode.)
- **Config-entry-flow helpers** — created through the generic config-entry flow (`config_entries/flow`, handler = the helper domain), often a multi-step flow that begins with a sub-type menu (see [Menu-Based Helpers](#menu-based-helpers)): `template`, `group`, `utility_meter`, `derivative`, `min_max`, `threshold`, `integration`, `statistics`, `trend`, `random`, `filter`, `tod`, `generic_thermostat`, `generic_hygrostat`, `switch_as_x`, `bayesian`, `mold_indicator`.

## Menu-Based Helpers

Several helper integrations — most prominently **`template`**, **`group`**, and **`random`** — start with a sub-type menu before showing fields. The field set isn't known until a sub-type is picked.

| Helper | Sub-types (pick one first) |
|--------|---------------------------|
| `template` | `sensor`, `binary_sensor`, `button`, `switch`, `light`, `cover`, `fan`, `lock`, `select`, `number`, `image`, `vacuum`, `weather`, `alarm_control_panel`, `event`, `update` |
| `group` | `binary_sensor`, `button`, `cover`, `event`, `fan`, `light`, `lock`, `media_player`, `notify`, `sensor`, `switch`, `valve` |
| `random` | `sensor`, `binary_sensor` |

Advance the menu by submitting `{"next_step_id": "<sub-type>"}` to the first step; the resulting form's fields become available in the next step. The chosen sub-type is then written into the stored config entry as `template_type` / `group_type` etc. by the integration's validator — those are storage keys, not inputs the caller submits.

---

## Numeric Aggregation

### min_max

**Use for:** Combining multiple sensors to get min, max, mean, median, sum, or last value across all of them.

**Instead of:**
```yaml
# WRONG - Template sensor for averaging
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
# RIGHT - min_max helper
sensor:
  - platform: min_max
    name: "Average Temperature"
    type: mean
    entity_ids:
      - sensor.temp_bedroom
      - sensor.temp_living
      - sensor.temp_kitchen
```

**Available types:** `min`, `max`, `mean`, `median`, `last`, `sum`

**Key behaviors:**
- Ignores `unknown` states (except `sum` which goes to unknown)
- Returns error if unit of measurement differs between sensors
- For spiky values, filter with statistics sensor first

**Common uses:**
- Average house temperature from multiple room sensors
- Maximum power consumption across circuits
- Sum of all solar panel production sensors

---

### statistics

**Use for:** Statistical analysis over time for a single sensor (mean, median, stdev, change, variance, etc.).

**Instead of:**
```yaml
# WRONG - Complex template tracking history
template:
  - sensor:
      - name: "Temperature Change"
        state: "{{ states('sensor.temp') | float - state_attr('sensor.temp', 'last_value') | float(0) }}"
```

**Use this:**
```yaml
# RIGHT - Statistics helper
sensor:
  - platform: statistics
    name: "Temperature Change (5 min)"
    entity_id: sensor.temperature
    state_characteristic: change
    max_age:
      minutes: 5
    sampling_size: 50
```

**Available characteristics:**
- `mean`, `median`, `average_linear`, `average_step`, `average_timeless`
- `standard_deviation`, `variance`
- `change`, `change_second`, `change_sample`
- `count`, `count_binary_on`, `count_binary_off`
- `total`, `noisiness`
- `datetime_newest`, `datetime_oldest`, `datetime_value_max`, `datetime_value_min`
- `value_max`, `value_min`, `quantiles`

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
# WRONG - Template calculating delta manually
template:
  - sensor:
      - name: "Power Rate"
        state: "{{ (states('sensor.power') | float - states('sensor.power_previous') | float) / 60 }}"
```

**Use this:**
```yaml
# RIGHT - Derivative helper
sensor:
  - platform: derivative
    name: "Power Rate of Change"
    source: sensor.power
    unit_time: min
    time_window:
      minutes: 5
```

**Parameters:**
- `unit_time`: s, min, h, d - determines output unit (e.g., W/min)
- `time_window`: Smoothing window using Simple Moving Average
- `round`: Decimal places for output

**Key behaviors:**
- Without `time_window`, calculates between consecutive updates only
- Can show large negative spikes when source resets to 0 (total_increasing sensors)
- Use `force_update` option if source updates infrequently

**Common uses:**
- Energy production rate (kW from kWh sensor)
- Temperature change rate (detect HVAC efficiency)
- Water flow rate from cumulative meter

---

### threshold

**Use for:** Creating a binary sensor that turns on/off when a numeric sensor crosses a threshold.

**Instead of:**
```yaml
# WRONG - Template binary sensor
template:
  - binary_sensor:
      - name: "High Temperature"
        state: "{{ states('sensor.temperature') | float > 25 }}"
```

**Use this:**
```yaml
# RIGHT - Threshold helper
binary_sensor:
  - platform: threshold
    name: "High Temperature"
    entity_id: sensor.temperature
    upper: 25
    hysteresis: 1
```

**Parameters:**
- `upper`: Threshold for "on" when value exceeds
- `lower`: Threshold for "on" when value drops below
- `hysteresis`: Buffer zone to prevent rapid toggling

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
# WRONG - Template comparing against a stored previous value
template:
  - binary_sensor:
      - name: "Temperature Rising"
        state: "{{ states('sensor.temp') | float > state_attr('sensor.temp', 'prev') | float(0) }}"
```

**Use this:**
```yaml
# RIGHT - Trend helper. NOTE: `sensors:` is a MAPPING keyed by a slug (not a list)
binary_sensor:
  - platform: trend
    sensors:
      temp_rising:
        entity_id: sensor.temperature
        sample_duration: 1800    # seconds of history to consider
        min_gradient: 0.001      # units per SECOND to count as a trend
        max_samples: 120        # cap on samples kept (independent of sample_duration)
        invert: false            # true = detect a downward trend
```

**Key behaviors:**
- `min_gradient` is units **per second** (0.001 °/s ≈ 3.6 °/h).
- `invert: true` detects a *downward* trend.
- `sensors:` is a slug-keyed mapping (not a list), unlike most other `binary_sensor` platforms.

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
# WRONG - Automation with counter tracking monthly usage
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
# RIGHT - Utility meter
utility_meter:
  daily_energy:
    source: sensor.energy_consumption
    cycle: daily
  monthly_energy:
    source: sensor.energy_consumption
    cycle: monthly
```

**Cycle options:** `quarter-hourly`, `hourly`, `daily`, `weekly`, `monthly`, `bimonthly`, `quarterly`, `yearly`

**Advanced features:**
- **Tariffs:** Track peak/off-peak separately
- **Offset:** Start cycle on specific day (e.g., billing date)
- **Cron:** Custom reset schedules
- **Delta:** For sensors that report delta values

```yaml
# Utility meter with tariffs
utility_meter:
  daily_energy:
    source: sensor.energy_consumption
    cycle: daily
    tariffs:
      - peak
      - offpeak
```

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
sensor:
  - platform: history_stats
    name: "Lights on today"
    entity_id: light.living_room
    state: "on"
    type: time
    start: "{{ now().replace(hour=0, minute=0, second=0) }}"
    end: "{{ now() }}"
```

**Types:**
- `time`: Duration in hours
- `ratio`: Percentage of time
- `count`: Number of state changes to the monitored state

**Key behaviors:**
- Limited by recorder's `purge_keep_days`
- Updates when source changes or once per minute

**Common uses:**
- How long lights were on today
- Percentage of time home was occupied
- Count of door openings per day

---

### integration (Riemann sum)

**Use for:** Converting power (W) to energy (kWh), flow rate to volume, etc.

```yaml
sensor:
  - platform: integration
    name: "Solar Energy"
    source: sensor.solar_power
    unit_prefix: k
    unit_time: h
    method: left
    round: 2
```

**Methods:**
- `left`: Uses previous value for interval (recommended for sparse data)
- `right`: Uses new value for interval
- `trapezoidal`: Averages previous and new (can overestimate with gaps)

**Key behaviors:**
- For solar/sensors with gaps, use `left` method
- `max_sub_interval` forces updates even when source doesn't change

**Common uses:**
- Convert solar power (W) to energy production (kWh)
- Convert water flow rate to total consumption
- Convert gas flow to total usage

---

## State Storage

### input_boolean

**Use for:** Toggle switches for modes, flags, and conditions.

```yaml
input_boolean:
  guest_mode:
    name: "Guest Mode"
    icon: mdi:account-group
  vacation_mode:
    name: "Vacation Mode"
    icon: mdi:airplane
```

**Common uses:**
- Guest mode (disable certain automations)
- Vacation mode
- Manual override flags
- Feature toggles

### input_number

**Use for:** Storing numeric values that can be adjusted.

```yaml
input_number:
  target_temperature:
    name: "Target Temperature"
    min: 15
    max: 30
    step: 0.5
    unit_of_measurement: "°C"
    mode: slider
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
input_select:
  hvac_mode:
    name: "HVAC Mode"
    options:
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
input_text:
  notification_message:
    name: "Custom Notification"
    min: 0
    max: 255
    mode: text
```

**Modes:** `text`, `password`

**Common uses:**
- Custom messages
- Temporary storage
- User notes

### input_datetime

**Use for:** Storing date and/or time values.

```yaml
input_datetime:
  morning_alarm:
    name: "Morning Alarm"
    has_time: true
    has_date: false
  next_vacation:
    name: "Next Vacation"
    has_date: true
    has_time: false
```

**Common uses:**
- Alarm times
- Schedule times (wake-up, lights off)
- Future dates (vacation, events)

### input_button

**Use for:** Triggering automations manually.

```yaml
input_button:
  doorbell:
    name: "Doorbell"
    icon: mdi:bell
```

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
# WRONG - input_number with automation
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
# RIGHT - Counter helper
counter:
  coffee_count:
    name: "Coffees Today"
    initial: 0
    step: 1
    minimum: 0
    maximum: 100
    restore: true
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
# WRONG - Delay in automation
actions:
  - delay:
      minutes: 5
  - action: notify.mobile_app
    data:
      message: "Timer done!"
```

**Use this for pausable/restartable timers:**
```yaml
# RIGHT - Timer helper
timer:
  laundry:
    name: "Laundry Timer"
    duration: "01:00:00"
    restore: true
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
schedule:
  work_hours:
    name: "Work Hours"
    monday:
      - from: "09:00:00"
        to: "17:00:00"
    tuesday:
      - from: "09:00:00"
        to: "17:00:00"
    # ... etc
```

**Key behaviors:**
- Creates a binary sensor that's `on` during scheduled times
- Can have multiple blocks per day
- Editable via UI

**Instead of:**
```yaml
# WRONG - Template with weekday checks
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
binary_sensor:
  - platform: tod
    name: "Morning"
    after: "06:00"
    before: "12:00"

  - platform: tod
    name: "Night Time"
    after: sunset
    after_offset: "01:00:00"
    before: sunrise
```

**Common uses:**
- Time-of-day modes (morning, afternoon, evening, night)
- Daylight/darkness detection
- Simple time-based conditions

---

## Entity Grouping

### group

**Use for:** Combining entities for collective state and control.

```yaml
group:
  all_lights:
    name: "All Lights"
    entities:
      - light.living_room
      - light.bedroom
      - light.kitchen
    all: false  # ON if ANY member is on

  security_sensors:
    name: "Security Sensors"
    entities:
      - binary_sensor.front_door
      - binary_sensor.back_door
      - binary_sensor.window
    all: true  # ON only if ALL members are on
```

**Parameters:**
- `all: false` (default): Group is ON if ANY member is ON (OR logic)
- `all: true`: Group is ON only if ALL members are ON (AND logic)

**Key behaviors:**
- Groups inherit the domain of their members
- Light groups can be controlled as a single entity
- Binary sensor groups useful for "any door open" logic
- Created via the config-entry flow API, `group` is **menu-based**: submit `{"next_step_id": "<sub-type>"}` first (sub-types: `binary_sensor`, `button`, `cover`, `event`, `fan`, `light`, `lock`, `media_player`, `notify`, `sensor`, `switch`, `valve`), then provide `entities`. Sensor groups additionally require `type` (one of `last`, `first_available`, `max`, `mean`, `median`, `min`, `product`, `range`, `stdev`, `sum`). The stored config entry then carries `group_type` as a storage key.

**Instead of:**
```yaml
# WRONG - Template binary sensor for any-on logic
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

**Use this:**
```yaml
binary_sensor:
  - platform: bayesian
    name: "Kitchen In Use"
    prior: 0.3                  # baseline probability before any observation
    probability_threshold: 0.5  # turns on when posterior probability exceeds this
    observations:
      - entity_id: binary_sensor.kitchen_motion
        platform: state         # or numeric_state / template
        to_state: "on"
        prob_given_true: 0.95
        prob_given_false: 0.33
      - entity_id: sensor.kitchen_power
        platform: numeric_state
        above: 50
        prob_given_true: 0.8
        prob_given_false: 0.05
```

**Key behaviors:**
- Each observation contributes `prob_given_true` / `prob_given_false`; the sensor turns on when the combined posterior probability exceeds `probability_threshold`.
- Observation `platform` is `state`, `numeric_state` (uses `above`/`below`), or `template` (uses `value_template`).
- **YAML uses probabilities `0..1`; the UI config flow uses percentages `0..100`** — a common mismatch.

**Common uses:**
- "Someone is cooking" / "shower running" from motion + power + humidity
- Occupancy inference from several weak presence signals

---

## Data Smoothing

### filter

**Use for:** Smoothing noisy sensor data, throttling update frequency, or rejecting out-of-range values.

**Instead of:**
```yaml
# WRONG - Template sensor doing manual smoothing math
template:
  - sensor:
      - name: "Smoothed Power"
        state: >
          {% set h = states('sensor.power_history') | from_json %}
          {{ (h | sum / h | length) | round(2) }}
```

**Use this:**
```yaml
# RIGHT - Filter helper (UI creates one filter per entry; YAML supports chains)
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

**The UI config flow creates one filter per entry.** For chained pipelines (multiple filters applied in sequence), use YAML as above.

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
# WRONG - Template with range() / random()
template:
  - sensor:
      - name: "Random Number"
        state: "{{ range(0, 100) | random }}"
```

**Use this:**
```yaml
# RIGHT - Random helper (proper entity with state class, history, etc.)
sensor:
  - platform: random
    name: "Random Percentage"
    minimum: 0
    maximum: 100
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
binary_sensor:
  - platform: random
    name: "Random Boolean"
```

---

## Climate Control

### generic_thermostat

**Use for:** Turning a switch (or fan) into a thermostat that follows a temperature sensor.

```yaml
climate:
  - platform: generic_thermostat
    name: "Bedroom"
    heater: switch.bedroom_heater
    target_sensor: sensor.bedroom_temperature
    ac_mode: false
    cold_tolerance: 0.3
    hot_tolerance: 0.3
    min_temp: 15
    max_temp: 25
    min_cycle_duration: "00:05:00"
```

**Parameters (config flow):**
- Required: `name`, `heater` (switch or fan entity), `target_sensor` (temperature sensor), `ac_mode` (bool — set `true` to invert for cooling).
- Optional: `cold_tolerance` (default `0.3`), `hot_tolerance` (default `0.3`), `min_cycle_duration`, `max_cycle_duration`, `cycle_cooldown`, `keep_alive`, `min_temp`, `max_temp`, plus a presets step (`away_temp`, `comfort_temp`, `eco_temp`, `home_temp`, `sleep_temp`, `activity_temp`).

**Key behaviors:**
- `ac_mode: true` inverts logic (heater output activates for cooling)
- Tolerances prevent rapid cycling near the target
- YAML platform supports `initial_hvac_mode`, `precision`, `target_temp_step` — not exposed by the UI flow

---

### generic_hygrostat

**Use for:** Turning a switch (or fan) into a humidifier/dehumidifier controller that follows a humidity sensor.

```yaml
humidifier:
  - platform: generic_hygrostat
    name: "Bathroom Dehumidifier"
    device_class: dehumidifier
    humidifier: switch.bathroom_fan
    target_sensor: sensor.bathroom_humidity
    dry_tolerance: 3
    wet_tolerance: 3
    min_cycle_duration: "00:05:00"
```

**Parameters (config flow):**
- Required: `name`, `device_class` (`humidifier` or `dehumidifier`), `humidifier` (switch or fan entity), `target_sensor` (humidity sensor).
- Optional: `dry_tolerance` (default `3`), `wet_tolerance` (default `3`), `min_cycle_duration`.

---

### mold_indicator

**Use for:** Estimating mold/condensation risk from indoor temperature + humidity vs. a cold-surface (outdoor) temperature — instead of hand-rolling a dew-point template.

```yaml
sensor:
  - platform: mold_indicator
    indoor_temp_sensor: sensor.indoor_temp
    indoor_humidity_sensor: sensor.indoor_humidity
    outdoor_temp_sensor: sensor.outdoor_temp
    calibration_factor: 2.0
```

Outputs an estimated humidity-at-cold-surface percentage; mold risk rises above ~70%. **`calibration_factor` must be physically calibrated** to a known condensation point — it is not a value to guess.

---

## Domain Conversion

### switch_as_x

**Use for:** Exposing a `switch.*` entity as a different domain so it integrates correctly with voice assistants, dashboards, and HVAC logic.

**Instead of:**
```yaml
# WRONG - Template light wrapping a switch
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

**Use this** (UI / config flow — no YAML equivalent):
- `entity_id: switch.lamp_plug`
- `target_domain: light`

`switch_as_x` hides the original switch and registers a proper `light.*` entity that voice assistants and dashboards treat correctly.

**Parameters:**
- Required: `entity_id` (must be a `switch.*` entity), `target_domain` (one of `cover`, `fan`, `light`, `lock`, `siren`, `valve`).
- Optional: `invert` (bool, default `false`) — reverses on/off semantics (useful for normally-closed contacts).

UI-only — no YAML equivalent. The original switch entity is hidden once converted; the new domain entity inherits the switch's state.

---

## Template Helpers

When no dedicated helper covers your need, use the **template helper** — created via the config-entry flow / UI, **not** YAML `template:` platform sensors. Template helpers are first-class HA helpers: UI-editable, reloadable without restarting, and visible in the helper registry.

### template

**Use for:** Custom sensor/binary_sensor/switch/light/etc. logic that no dedicated helper (min_max, derivative, threshold, statistics, etc.) provides.

Menu-based — pick a sub-type first (see [Menu-Based Helpers](#menu-based-helpers) for the full sub-type list), then configure fields.

**template → sensor**
- Required: `name`, `state` (Jinja template returning the sensor value)
- Optional: `unit_of_measurement`, `device_class`, `state_class`, `device_id`, `availability` (template)

**template → binary_sensor**
- Required: `name`, `state` (Jinja template returning truthy/falsy)
- Optional: `device_class`, `device_id`, `availability` (template)

Other sub-types follow the same shape — a `state` template plus domain-appropriate metadata.

**Equivalent YAML platform** (for reference; prefer the helper):
```yaml
template:
  - sensor:
      - name: "Solar Net"
        state: "{{ states('sensor.solar_production') | float - states('sensor.house_consumption') | float }}"
        unit_of_measurement: "W"
        device_class: power
        state_class: measurement
  - binary_sensor:
      - name: "Someone Home"
        state: "{{ is_state('person.alice','home') or is_state('person.bob','home') }}"
        device_class: presence
```

See the [Decision Matrix](#decision-matrix) for when the template helper is the right choice vs. a dedicated helper — every pattern that has a dedicated helper (averaging, rate of change, thresholds, time-of-day, scheduling, any-on/all-on) should go through that helper first.

---

## Decision Matrix

| Need | Helper | Not |
|------|--------|-----|
| Average of multiple sensors | `min_max` (type: mean) | Template with math |
| Sum of multiple sensors | `min_max` (type: sum) | Template with math |
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
| Custom logic no other helper covers | `template` helper (via UI flow) | YAML `template:` platform sensor |
