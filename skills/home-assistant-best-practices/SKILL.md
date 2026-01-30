---
name: home-assistant-best-practices
description: >
  Use when creating or editing Home Assistant automations,
  helpers, scripts, scenes, or device controls via MCP.
  Symptoms: agent defaults to Jinja2 templates, creates
  template sensors for simple math, uses template conditions
  where native state/numeric conditions exist.
---

# Home Assistant Best Practices

## Overview

Use native Home Assistant syntax wherever possible. Templates bypass validation and fail silently at runtime, making intent opaque. Avoid them.

## When to Use This Skill

Symptoms that signal this skill applies:
- Agent writes `{{ is_state(...) }}` template conditions instead of native state conditions
- Agent creates template sensors for math that `min_max`, `statistics`, or other helpers handle
- Agent uses `wait_template` instead of `wait_for_trigger`
- Agent overloads automations with Jinja2 instead of using list syntax, NOT wrappers, or attribute conditions

## Quick Reference: Native Conditions Over Templates

See [Conditions](https://www.home-assistant.io/docs/scripts/conditions/) and [wait_for_trigger](https://www.home-assistant.io/docs/scripts/#wait-for-a-trigger) docs.

| Instead of this template | Use this native construct |
|---|---|
| `{{ states('sensor.x') in ['a', 'b'] }}` | `condition: state` with `state: ["a", "b"]` |
| `{{ not is_state('sensor.x', 'off') }}` | `condition: not` wrapping a state condition |
| `{{ state_attr('alarm.x', 'changed_by') == 'Guest' }}` | `condition: state` with `attribute: changed_by` |
| `{{ states('sensor.temp') \| float > 25 }}` | `condition: numeric_state` with `above: 25` |
| `{{ is_state('sensor.x', 'on') and is_state('sensor.y', 'on') }}` | `condition: and` with two state conditions |
| `wait_template: "{{ is_state('binary_sensor.motion', 'off') }}"` | `wait_for_trigger` with `trigger: state` and `to: "off"` |

### Why native constructs matter

- **Validation**: HA validates native conditions at save time; templates fail only at runtime.
- **Readability**: Native YAML conditions state intent directly; templates require Jinja2 parsing.
- **Trace debugging**: Automation traces show native condition results clearly; template conditions show only true/false.
- **Performance**: Native conditions execute directly; templates require compilation and interpretation.

## Helpers: Know What Exists

Before creating a template sensor, determine whether a built-in helper fits the job.

### Math and aggregation
- **[min_max](https://www.home-assistant.io/integrations/min_max/)**: Minimum, maximum, mean, median, sum, or last value across multiple sensors. Use `type: sum` with the same entity listed twice to double a value.
- **[statistics](https://www.home-assistant.io/integrations/statistics/)**: Statistical analysis (mean, median, standard deviation, variance, count) over a time window.
- **[derivative](https://www.home-assistant.io/integrations/derivative/)**: Rate of change of a sensor value over time.
- **[threshold](https://www.home-assistant.io/integrations/threshold/)**: Binary sensor that turns on/off when a numeric sensor crosses a threshold.
- **[utility_meter](https://www.home-assistant.io/integrations/utility_meter/)**: Tracks consumption (energy, gas, water) over configurable billing cycles.

### State and input
- **input_boolean**: On/off toggle for manual flags and modes.
- **input_number**: Numeric value for thresholds, setpoints, or parameters.
- **input_select**: Dropdown for selecting from a fixed set of options.
- **input_text**: Free-text storage.
- **input_datetime**: Date, time, or datetime storage.
- **input_button**: Trigger-only entity that fires an event when pressed.

### Organization and timing
- **counter**: Increment/decrement/reset integer counter.
- **timer**: Countdown timer with start/pause/cancel/finish events.
- **schedule**: Weekly schedule with on/off time blocks.
- **group**: Combines entities into a single entity. State reflects all-on, any-on, or similar logic depending on group type.

Use a native helper if it handles the math, aggregation, or logic. Create a template sensor only when no built-in helper covers the requirement.

## Common Mistakes

### 1. Template sensor for simple aggregation

**Wrong**: Create a template sensor with `{{ states('sensor.a') | float + states('sensor.b') | float }}` to sum two sensors.

**Right**: Use a `min_max` helper with `type: sum` for summing sensors, or `type: mean` for averaging.

### 2. Using templates where native conditions exist

See the Quick Reference table above. State membership, attribute checks, numeric comparisons, wait conditions, and AND/OR logic all have native equivalents that validate at save time and produce clear automation traces.
