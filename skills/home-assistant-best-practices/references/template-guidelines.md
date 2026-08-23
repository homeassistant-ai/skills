> **Prefer a Template Helper over YAML.**
> Before writing any `template:` block, create a Template Helper via the HA config flow (MCP tool or API) or via the UI:
> Settings → Devices & Services → Helpers → Create Helper → Template.
> Use `template:` YAML only when explicitly requested or when neither programmatic nor UI access is available.

# Template Guidelines

This document covers when templates ARE the right choice in Home Assistant, and best practices for writing reliable templates.

## Table of Contents
1. [When Templates Are Appropriate](#when-templates-are-appropriate)
2. [When to Avoid Templates](#when-to-avoid-templates)
3. [Template Sensor Best Practices](#template-sensor-best-practices)
4. [Automation Template Best Practices](#automation-template-best-practices)
5. [Common Patterns](#common-patterns)
6. [Error Handling](#error-handling)
7. [Performance Considerations](#performance-considerations)
8. [Reusable Macros](#reusable-macros)

---

## When Templates Are Appropriate

Templates are the RIGHT choice when:

### 1. Dynamic Action Data

You need to pass dynamic values to actions based on entity states or trigger context.

```yaml
actions:
  - action: light.turn_on
    target:
      entity_id: light.bedroom
    data:
      brightness_pct: "{{ states('input_number.default_brightness') | int }}"
      kelvin: "{{ 6500 if is_state('binary_sensor.daytime', 'on') else 2700 }}"
```

### 2. Dynamic Notification Messages

Messages that include runtime information:

```yaml
actions:
  - action: notify.mobile_app
    data:
      message: >
        {{ trigger.to_state.name }} has been {{ trigger.to_state.state }}
        for {{ trigger.for.total_seconds() | int // 60 }} minutes.
```

### 3. Processing Raw Data Sources

MQTT, REST, and command line sensors often provide raw data that needs transformation:

```yaml
# REST sensor with JSON response
rest:
  - resource: "http://api.example.com/data"
    sensor:
      - name: "Temperature"
        value_template: "{{ value_json.current.temperature }}"
        unit_of_measurement: "°C"
```

### 4. Accessing Trigger Context

Using `trigger.` variables in automations:

```yaml
actions:
  - action: notify.mobile_app
    data:
      message: >
        {{ trigger.to_state.name }} changed from
        {{ trigger.from_state.state }} to {{ trigger.to_state.state }}
```

### 5. Complex String Formatting

When you need formatted output that can't be achieved with native constructs:

```yaml
template:
  - sensor:
      - name: "Friendly Uptime"
        state: >
          {% set uptime = states('sensor.system_uptime') | float(0) %}
          {% set days = (uptime // 86400) | int %}
          {% set hours = ((uptime % 86400) // 3600) | int %}
          {% set minutes = ((uptime % 3600) // 60) | int %}
          {{ days }}d {{ hours }}h {{ minutes }}m
```

### 6. Attribute Extraction

Creating sensors from entity attributes:

```yaml
template:
  - sensor:
      - name: "Current Song Artist"
        state: "{{ state_attr('media_player.spotify', 'media_artist') }}"
```

### 7. Complex Conditional State

When the state depends on multiple factors that can't be expressed with native conditions:

```yaml
template:
  - sensor:
      - name: "Comfort Level"
        state: >
          {% set temp = states('sensor.temperature') | float(20) %}
          {% set humidity = states('sensor.humidity') | float(50) %}
          {% if temp >= 20 and temp <= 24 and humidity >= 40 and humidity <= 60 %}
            Comfortable
          {% elif temp < 18 or humidity < 30 %}
            Too Cold/Dry
          {% elif temp > 26 or humidity > 70 %}
            Too Hot/Humid
          {% else %}
            Acceptable
          {% endif %}
```

### 8. Entity Iteration

Processing multiple entities dynamically:

```yaml
template:
  - sensor:
      - name: "Open Windows Count"
        state: >
          {{ states.binary_sensor
             | selectattr('attributes.device_class', 'eq', 'window')
             | selectattr('state', 'eq', 'on')
             | list
             | count }}
```

### 9. Date/Time Calculations

Time differences, formatting, and calculations:

```yaml
template:
  - sensor:
      - name: "Days Until Event"
        state: >
          {% set event_date = as_datetime(states('input_datetime.event')) %}
          {% set today = now().replace(hour=0, minute=0, second=0, microsecond=0) %}
          {{ ((event_date - today).days) }}
        unit_of_measurement: "days"
```

---

## When to Avoid Templates

Do NOT use templates when a native alternative exists:

| Don't Use Template | Use Native |
|-------------------|------------|
| `{{ states('x') in ['a', 'b'] }}` | `condition: state` with `state: ["a", "b"]` |
| `{{ states('x') \| float > 25 }}` | `condition: numeric_state` with `above: 25` |
| `{{ now().hour >= 9 }}` | `condition: time` with `after: "09:00:00"` |
| `{{ is_state('sun.sun', 'below_horizon') }}` | `condition: sun` with `after: sunset` |
| `wait_template: "{{ is_state(...) }}"` | `wait_for_trigger` with state trigger |
| Template sensor summing values | `min_max` helper with `type: sum` |
| Template binary sensor with threshold | `threshold` helper |
| Template sensor averaging over time | `statistics` helper |

See [automation-patterns](automation-patterns.md) and [helper-selection](helper-selection.md) for comprehensive alternatives.

---

## Template Sensor Best Practices

### Always Include unique_id

```yaml
template:
  - sensor:
      - name: "My Sensor"
        unique_id: my_custom_sensor  # Enables UI customization
        state: "{{ states('sensor.source') }}"
```

### Always Define Availability

Prevent errors and unknown states:

```yaml
template:
  - sensor:
      - name: "Safe Sensor"
        unique_id: safe_sensor
        availability: >
          {{ has_value('sensor.source_a') and
             has_value('sensor.source_b') }}
        state: >
          {{ states('sensor.source_a') | float +
             states('sensor.source_b') | float }}
```

### Use Appropriate Device Class

Helps with unit conversion and graph display:

```yaml
template:
  - sensor:
      - name: "Calculated Temperature"
        device_class: temperature
        unit_of_measurement: "°C"
        state_class: measurement
        state: "{{ states('sensor.raw_temp') | float / 10 }}"
```

### Use state_class for Long-Term Statistics (Recommended for Numeric Sensors)

**If long-term statistics are needed, set `state_class`.** Without it, HA writes no
long-term statistics — the sensor will not appear in `statistics_meta` or in History graphs.
`state_class` is optional for diagnostic or one-shot sensors where statistics are not required.
(Verified on HA 2026.3: `statistics_meta` empty without `state_class`, entry created after adding it.)

> **Energy Dashboard note:** `state_class` alone is not sufficient for Energy Dashboard
> visibility. The sensor also needs `device_class: energy` (or `power`, `gas`, etc.) to
> appear as a selectable source. A sensor with `state_class` but no matching `device_class`
> will have long-term statistics but will not appear in the Energy Dashboard configuration.

Also mirror `device_class` from the source sensor where applicable (e.g., `duration`, `temperature`, `energy`).

```yaml
template:
  - sensor:
      - name: "Power Usage"
        device_class: power
        unit_of_measurement: "W"
        state_class: measurement  # enables long-term statistics (omit if not needed)
        state: "{{ states('sensor.amps') | float * 230 }}"
```

### Use Trigger-Based for Efficiency

Trigger-based templates only update when sources change:

```yaml
template:
  - triggers:                    # Recommended plural form (HA 2024.10+)
      - trigger: state
        entity_id:
          - sensor.temp_bedroom
          - sensor.temp_living
    sensor:
      - name: "Average Temperature"
        state: >
          {% set temps = [
            states('sensor.temp_bedroom') | float(0),
            states('sensor.temp_living') | float(0)
          ] %}
          {{ (temps | sum / temps | count) | round(1) }}
        unit_of_measurement: "°C"
        state_class: measurement
```

**Benefits of trigger-based:**
- Only evaluates when trigger fires (not on every state change)
- Access to `trigger` variable
- More efficient for complex templates

### YAML Block Structure Conventions (HA 2024.10+)

**Use plural keys in trigger-based template blocks.** Since HA 2024.10 the recommended syntax
uses `triggers:` and `actions:` (plural). The singular forms still work — there is no deprecation
and no warnings — but all official HA docs now use plural. Write new templates in plural form.

**Consolidate state-based entities of the same type in one block.** Multiple state-based
`sensor` or `binary_sensor` entries without individual triggers belong in a single block —
not in separate blocks per entity. Trigger-based blocks (with their own `triggers:` section)
must be separate regardless of entity type, since each block defines its own trigger context:

```yaml
# GOOD — state-based sensors: one block, multiple entries:
template:
  - binary_sensor:
      - name: "Motion Room A"
        unique_id: motion_room_a
        state: "{{ ... }}"
      - name: "Motion Room B"
        unique_id: motion_room_b
        state: "{{ ... }}"

# BAD — state-based sensors split across separate blocks:
template:
  - binary_sensor:
      - name: "Motion Room A"
        unique_id: motion_room_a_avoid
        state: "{{ ... }}"
  - binary_sensor:
      - name: "Motion Room B"
        unique_id: motion_room_b_avoid
        state: "{{ ... }}"
```

> **Trigger-based blocks are always separate** — a block with `triggers:` defines its own
> update context and cannot share a block with entries of a different trigger configuration.
> Only consolidate entries that share the same trigger context (or are all state-based).

**Follow HA's 2-space indentation rule ([HA YAML Style Guide](https://developers.home-assistant.io/docs/documenting/yaml-style-guide/)).** In template blocks, list items under `sensor:` / `binary_sensor:` are indented 2 spaces relative to the key — which, combined with the `- ` sequence marker, results in 4 visual columns from the parent dash. This is the style used consistently in the official HA template integration documentation.

```yaml
# Standard — 2-space indent per level (HA Style Guide, matches official docs):
- binary_sensor:
    - name: "My Sensor"
      state: "{{ ... }}"

# Non-standard — compact notation (valid YAML, but absent from official HA docs):
- binary_sensor:
  - name: "My Sensor"
```

---

## Automation Template Best Practices

### Use Shorthand Syntax

For template conditions, use the shorthand:

```yaml
# Shorthand (preferred)
conditions:
  - "{{ trigger.to_state.attributes.brightness > 100 }}"

# Long form (equivalent but verbose)
conditions:
  - condition: template
    value_template: "{{ trigger.to_state.attributes.brightness > 100 }}"
```

### Use Multiline Strings

For readability in complex templates:

```yaml
actions:
  - action: notify.mobile_app
    data:
      message: >
        {% if is_state('binary_sensor.door', 'on') %}
          Warning: Door is open!
        {% else %}
          All secure.
        {% endif %}
```

### Access Trigger Context Properly

```yaml
automation:
  - triggers:
      - trigger: state
        entity_id: light.bedroom
    actions:
      - action: notify.mobile_app
        data:
          message: >
            Light changed from {{ trigger.from_state.state }}
            to {{ trigger.to_state.state }}
            Entity: {{ trigger.entity_id }}
            Brightness: {{ trigger.to_state.attributes.brightness | default('N/A') }}
```

---

## Common Patterns

### Safe State Access

Always use `states()` function, not `states.sensor.x.state`:

```yaml
# GOOD - Returns 'unknown' if entity doesn't exist
{{ states('sensor.temperature') }}

# BAD - Errors if entity doesn't exist
{{ states.sensor.temperature.state }}
```

### Safe Numeric Conversion

```yaml
# GOOD - Default value if conversion fails
{{ states('sensor.temperature') | float(0) }}

# BAD - Errors if state is 'unavailable' or 'unknown'
{{ states('sensor.temperature') | float }}
```

### Check for Valid State

```yaml
{% if has_value('sensor.temperature') %}
  Temperature is {{ states('sensor.temperature') }}°C
{% else %}
  Temperature unavailable
{% endif %}
```

### Multiple States Check

```yaml
{% if is_state('light.a', 'on') and is_state('light.b', 'on') %}
  Both lights on
{% endif %}
```

### List of States

```yaml
{% if states('alarm_control_panel.home') in ['armed_home', 'armed_away', 'armed_night'] %}
  Alarm is armed
{% endif %}
```

### Attribute Access with Default

`state_attr` returns `None` when the attribute is absent (a light that is off has no
`brightness`) or the entity does not exist. Jinja's `default` substitutes only for an
**undefined** name, and `None` is defined — so it passes straight through and the template
renders the string `None`.

```yaml
# BAD - renders "None" while the light is off
{{ state_attr('light.bedroom', 'brightness') | default(0) }}

# GOOD - the second argument makes default replace any falsy value, None included
{{ state_attr('light.bedroom', 'brightness') | default(0, true) }}

# GOOD - a type filter's default covers None and converts in one step
{{ state_attr('light.bedroom', 'brightness') | int(0) }}
```

The same trap applies to `| default(...)` after anything that can yield `None`
(`state_attr`, `.get()`, an attribute that exists but is null) — pass `true` or use
`int()`/`float()` — but they are not equivalent. `default(x, true)` replaces **any** falsy
value, so a real `0`, `False` or `''` becomes the default too; `int(x)`/`float(x)` fall back
only when the **conversion fails**, so a real `0` stays `0` and `False` converts to `0`.
Where a falsy value is meaningful, use the conversion filter, or test explicitly — see
[Handle None Attributes](#handle-none-attributes).

### Time Since State Change

```yaml
{% set last_changed = states.binary_sensor.motion.last_changed %}
{% set seconds = (now() - last_changed).total_seconds() %}
{{ (seconds / 60) | round(0) }} minutes ago
```

### Filter Entities by Attribute

```yaml
{% set open_windows = states.binary_sensor
   | selectattr('attributes.device_class', 'defined')
   | selectattr('attributes.device_class', 'eq', 'window')
   | selectattr('state', 'eq', 'on')
   | list %}
{{ open_windows | count }} windows open
```

### Iterate with Index

```yaml
{% for light in states.light %}
  {{ loop.index }}: {{ light.name }} is {{ light.state }}
{% endfor %}
```

### Format Lists Human-Readable

```yaml
{% set items = ['apples', 'oranges', 'bananas'] %}
{{ items[:-1] | join(', ') }} and {{ items[-1] }}
{# Output: apples, oranges and bananas #}
```

---

## Error Handling

### Default Values

```yaml
# For numeric operations
{{ states('sensor.x') | float(default=0) }}
{{ states('sensor.x') | int(default=-1) }}

# For attribute access - `true` is required, because state_attr returns None
{{ state_attr('light.x', 'brightness') | default(100, true) }}

# For a missing or unavailable entity - test it; no default filter will catch it
{{ states('sensor.missing') if has_value('sensor.missing') else 'Unknown' }}
```

**A default filter cannot rescue a missing entity.** `states()` returns the *string*
`"unknown"` for an entity that does not exist (and `"unavailable"` for one that is
offline). Both are non-empty strings, so both are truthy: `| default('Unknown', true)`
leaves them untouched and the template renders `unknown`. `has_value()` is the test that
covers missing, `unknown`, and `unavailable` in one call — in a full template. Limited
template contexts (a blueprint's `trigger_variables:`, `enabled:`) have no `states()` or
`has_value()`; see [blueprint-guide #referencing-inputs-input-and-templating](blueprint-guide.md#referencing-inputs-input-and-templating).

### Availability Template

```yaml
template:
  - sensor:
      - name: "Calculated Value"
        availability: "{{ has_value('sensor.input') }}"
        state: "{{ states('sensor.input') | float * 2 }}"
```

### Check Before Use

```yaml
{% if is_state_attr('media_player.tv', 'is_volume_muted', false) %}
  Volume: {{ state_attr('media_player.tv', 'volume_level') | float * 100 }}%
{% else %}
  Muted
{% endif %}
```

### Handle None Attributes

```yaml
{% set attr = state_attr('sensor.x', 'some_attr') %}
{% if attr is not none %}
  Attribute value: {{ attr }}
{% else %}
  Attribute not available
{% endif %}
```

---

## Performance Considerations

### Avoid Expensive Operations in Value Templates

Templates in `value_template` for sensors update on EVERY state change of the source entity.

```yaml
# EXPENSIVE - Runs on every source state change
template:
  - sensor:
      - name: "Expensive Sensor"
        state: >
          {% for entity in states %}  {# Iterates ALL entities #}
            ...
          {% endfor %}
```

> The legacy per-domain template-sensor form (`sensor:` → `- platform:` → `sensors:` → `value_template:`, i.e. a `template` platform nested under a domain key) was **removed in HA 2026.6** and no longer loads. Use the top-level `template:` integration key with `state:`, as above.

### Use Trigger-Based Templates for Complex Logic

```yaml
# EFFICIENT - Only runs when specified triggers fire
template:
  - triggers:
      - trigger: time_pattern
        minutes: "/5"  # Every 5 minutes
    sensor:
      - name: "Complex Calculation"
        state: >
          {% set total = 0 %}
          {% for sensor in states.sensor | selectattr('attributes.device_class', 'eq', 'energy') %}
            {% set total = total + states(sensor.entity_id) | float(0) %}
          {% endfor %}
          {{ total }}
```

### Cache Complex Calculations

If you need the same value in multiple places, create one template sensor and reference it:

```yaml
# ONE template sensor
template:
  - sensor:
      - name: "House Occupancy Count"
        state: >
          {{ states.person | selectattr('state', 'eq', 'home') | list | count }}

# Reference it elsewhere
automation:
  - condition: numeric_state
    entity_id: sensor.house_occupancy_count
    above: 0
```

### Use Variables for Repeated Access

```yaml
{% set temp = states('sensor.temperature') | float(0) %}
{% set humidity = states('sensor.humidity') | float(0) %}

{% if temp > 25 and humidity > 70 %}
  Hot and humid
{% elif temp > 25 %}
  Hot (temp: {{ temp }}°C)
{% endif %}
```

---

## Reusable Macros

Jinja macros live in `config/custom_templates/` and let several templates share one definition. Reach for them only once a template is already the right tool — a native trigger/condition and a built-in helper ruled out (see [When to Avoid Templates](#when-to-avoid-templates)). A macro de-duplicates templates you were going to write anyway; it is not a reason to write more of them. HA's own bar: once the same template appears in two or three places, save it once and reuse it.

| Situation | Use |
|-----------|-----|
| One template needs the value | A `{% set %}` variable in that template |
| Several templates need the same *value* | One cached template sensor the others reference (see [Cache Complex Calculations](#cache-complex-calculations)) |
| Several templates apply the same *logic* to different entities (battery-level thresholds, occupancy rules, unit conversion) | A macro |

### Macro Setup

The `.jinja` file requires filesystem access to the config directory — there is no UI or config-flow path for it. Without file access, hand the user the file content and the reload step instead of working around it. The consuming template is unaffected: the same `{% from %}` import works inside a Template Helper's state template, so preferring a Template Helper over a `template:` YAML block still applies.

| Step | Detail |
|------|--------|
| Create `config/custom_templates/` | HA does not create it; a missing directory is not an error, it just yields no macros |
| Add a `*.jinja` file | Subdirectories are scanned too; only the `.jinja` extension is loaded |
| Import by path relative to `custom_templates/` | `battery.jinja`, or `sensors/battery.jinja` for a file in a subdirectory |
| Call `homeassistant.reload_custom_templates` | Admin action, no restart. Required after every edit — HA holds the sources in memory. `homeassistant.reload_all` includes it |


```jinja
{# config/custom_templates/battery.jinja #}
{% macro battery_state(entity_id) -%}
  {%- set level = states(entity_id) | int(-1) -%}
  {%- if level < 0 -%}unknown
  {%- elif level <= 15 -%}critical
  {%- elif level <= 30 -%}low
  {%- else -%}ok
  {%- endif -%}
{%- endmacro %}
```

```yaml
template:
  - sensor:
      - name: "Phone Battery Status"
        unique_id: phone_battery_status
        state: >
          {% from 'battery.jinja' import battery_state %}
          {{ battery_state('sensor.phone_battery') }}
```

The import goes inside every template that uses the macro — imports are per-template, not global.

### Imports Do Not Carry the Caller's Context

The costliest mistake. An imported macro sees the template environment's globals, but none of the calling template's variables — a missing one renders empty and logs `Template variable warning: ... is undefined`, while attribute access on it (`trigger.entity_id`) fails the render outright.

| Available inside an imported macro | NOT available |
|------------------------------------|---------------|
| `states`, `state_attr`, `is_state`, `is_state_attr`, `expand`, `has_value`, `now()` and the rest of HA's template functions and filters | `trigger`, `this`, `value_json`, variables bound from a Blueprint `!input`, `repeat`, and anything `{% set %}` in the calling template |

```jinja
{# BAD — `this` and `trigger` are undefined here; the attribute access errors #}
{% macro describe() -%}
  {{ this.entity_id }} fired from {{ trigger.entity_id }}
{%- endmacro %}

{# GOOD — the caller passes them in #}
{% macro describe(entity_id, source) -%}
  {{ entity_id }} fired from {{ source }}
{%- endmacro %}
```

`{% from 'battery.jinja' import battery_state with context %}` does expose the caller's variables, but ties the macro to one caller's variable names. Pass arguments instead.

### Macros That Return Values

A macro produces **text**. A macro meant to yield a number, boolean, or list returns a string of one instead, so `{{ battery_level('sensor.phone') | float }}` silently parses its own output rather than passing a number through.

For a real return value, give the macro a `returns` argument and convert it with the `as_function` filter:

```jinja
{# config/custom_templates/battery.jinja #}
{% macro macro_is_low(entity_id, returns) -%}
  {%- set level = states(entity_id) | int(-1) -%}
  {% do returns(level >= 0 and level <= 15) %}
{%- endmacro %}
```

```jinja
{% from 'battery.jinja' import macro_is_low %}
{% set is_low = macro_is_low | as_function %}
{{ 'charge it' if is_low('sensor.phone_battery') else 'fine' }}
```

`as_function` strips a leading `macro_` from the name — hence the convention of prefixing the macro and dropping it on the function.

### State Tracking Is Unaffected

`states()` and the other state functions called inside an imported macro register their entities as dependencies exactly as they would inline, so template sensors still update on state changes. No extra wiring needed.

### Macro Pitfalls

| Symptom | Cause |
|---------|-------|
| `TemplateNotFound` | File is not under `config/custom_templates/`, does not end in `.jinja`, or `reload_custom_templates` has not run since it was added |
| Edits have no effect | Sources are cached in memory — call `homeassistant.reload_custom_templates` |
| Empty output where a caller variable should be, or `'trigger' is undefined` in the log | Context does not cross an import — pass it as a macro argument |

---

## Quick Reference: Functions and Filters

### State Functions

| Function | Purpose |
|----------|---------|
| `states('entity_id')` | Get entity state (string) |
| `state_attr('entity_id', 'attr')` | Get attribute value |
| `is_state('entity_id', 'state')` | Check if entity has state |
| `is_state_attr('entity_id', 'attr', 'value')` | Check attribute value |
| `has_value('entity_id')` | True if not unknown/unavailable |
| `entity_name('entity_id')` | Get entity display name; preferred over `friendly_name` attribute (2026.4+) |
| `state_attr_translated('entity_id', 'attr')` | Get translated attribute value, e.g., fan modes, HVAC actions (2026.4+) |

### Common Filters

| Filter | Purpose |
|--------|---------|
| `float(default)` | Convert to float |
| `int(default)` | Convert to int |
| `round(precision)` | Round number |
| `default(value, true)` | Fallback; the `true` is what catches `None` |
| `timestamp_custom(format)` | Format timestamp |
| `from_json` | Parse JSON string |
| `to_json` | Convert to JSON string |
| `regex_match(pattern)` | Regex match |
| `regex_replace(find, replace)` | Regex replace |

### Time Functions

| Function | Purpose |
|----------|---------|
| `now()` | Current datetime |
| `utcnow()` | Current UTC datetime |
| `today_at('HH:MM')` | Today at specific time |
| `as_timestamp(dt)` | Convert to Unix timestamp |
| `as_datetime(ts)` | Convert from timestamp |
| `as_timedelta(string)` | Parse duration string |

### Collection Filters

| Filter | Purpose |
|--------|---------|
| `selectattr('attr', 'eq', 'value')` | Filter by attribute |
| `rejectattr('attr', 'eq', 'value')` | Exclude by attribute |
| `map(attribute='state')` | Extract attribute from list |
| `list` | Convert to list |
| `count` | Count items |
| `first` / `last` | Get first/last item |
| `sum` / `min` / `max` | Aggregate values |
