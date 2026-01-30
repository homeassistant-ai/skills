---
name: home-assistant-best-practices
description: >
  Best practices for Home Assistant automations, helpers, scripts, scenes, and device controls via MCP.
  Use when: (1) Creating or editing HA automations, (2) Writing conditions or triggers, (3) Creating template sensors,
  (4) Using wait_template or similar constructs. Symptoms that trigger this skill: agent defaults to Jinja2 templates,
  creates template sensors for simple math, uses template conditions where native state/numeric conditions exist,
  uses wait_template instead of wait_for_trigger, overloads automations with Jinja2.
---

# Home Assistant Best Practices

Use native Home Assistant syntax wherever possible. Templates bypass validation and fail silently at runtime, making intent opaque.

## Native Conditions Over Templates

See [Conditions](https://www.home-assistant.io/docs/scripts/conditions/) and [wait_for_trigger](https://www.home-assistant.io/docs/scripts/#wait-for-a-trigger) docs.

| Instead of template | Use native construct |
|---|---|
| `{{ states('sensor.x') in ['a', 'b'] }}` | `condition: state` with `state: ["a", "b"]` |
| `{{ not is_state('sensor.x', 'off') }}` | `condition: not` wrapping a state condition |
| `{{ state_attr('alarm.x', 'changed_by') == 'Guest' }}` | `condition: state` with `attribute: changed_by` |
| `{{ states('sensor.temp') \| float > 25 }}` | `condition: numeric_state` with `above: 25` |
| `{{ is_state('sensor.x', 'on') and is_state('sensor.y', 'on') }}` | `condition: and` with two state conditions |
| `wait_template: "{{ is_state('binary_sensor.motion', 'off') }}"` | `wait_for_trigger` with `trigger: state` and `to: "off"` |

**Why native constructs matter:**
- **Validation**: HA validates native conditions at save time; templates fail only at runtime
- **Readability**: Native YAML states intent directly; templates require Jinja2 parsing
- **Trace debugging**: Automation traces show native condition results clearly; templates show only true/false
- **Performance**: Native conditions execute directly; templates require compilation

## Built-in Helpers

Before creating a template sensor, check if a built-in helper fits.

### Math and Aggregation
- **[min_max](https://www.home-assistant.io/integrations/min_max/)**: min, max, mean, median, sum, last across sensors. Use `type: sum` with same entity twice to double a value.
- **[statistics](https://www.home-assistant.io/integrations/statistics/)**: mean, median, standard deviation, variance, count over time window.
- **[derivative](https://www.home-assistant.io/integrations/derivative/)**: rate of change over time.
- **[threshold](https://www.home-assistant.io/integrations/threshold/)**: binary sensor when numeric sensor crosses threshold.
- **[utility_meter](https://www.home-assistant.io/integrations/utility_meter/)**: consumption tracking over billing cycles.

### State and Input
- **input_boolean**: on/off toggle for flags and modes
- **input_number**: numeric thresholds, setpoints, parameters
- **input_select**: dropdown for fixed options
- **input_text**: free-text storage
- **input_datetime**: date, time, or datetime storage
- **input_button**: trigger-only entity firing event when pressed

### Organization and Timing
- **counter**: increment/decrement/reset integer counter
- **timer**: countdown with start/pause/cancel/finish events
- **schedule**: weekly schedule with on/off time blocks
- **group**: combines entities into single entity with all-on/any-on logic

## Common Mistakes

### 1. Template sensor for simple aggregation

**Wrong**: Template sensor with `{{ states('sensor.a') | float + states('sensor.b') | float }}` to sum sensors.

**Right**: Use `min_max` helper with `type: sum` for summing, or `type: mean` for averaging.

### 2. Template conditions where native exists

State membership, attribute checks, numeric comparisons, wait conditions, and AND/OR logic all have native equivalents. See the table above.