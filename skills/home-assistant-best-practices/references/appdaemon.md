# AppDaemon Best Practices

AppDaemon is the right tool when native HA automations reach their limits: complex
multi-step logic, stateful workflows, external API orchestration, or anything that
benefits from a real programming language. It is **not** a replacement for HA
automations in general — use it only when native tools are genuinely insufficient.


## Table of Contents

1. [When to Use AppDaemon (vs. Native HA)](#when-to-use-appdaemon-vs-native-ha)
2. [App Structure and Lifecycle](#app-structure-and-lifecycle)
3. [Listening to State Changes](#listening-to-state-changes)
4. [Calling HA Services](#calling-ha-services)
5. [Scheduling and Timers](#scheduling-and-timers)
6. [State Management and Inter-App Communication](#state-management-and-inter-app-communication)
7. [Logging](#logging)
8. [apps.yaml Configuration](#appsyaml-configuration)
9. [Error Handling](#error-handling)
10. [AppDaemon-Specific Anti-Patterns](#appdaemon-specific-anti-patterns)
11. [Impact on Safe Refactoring](#impact-on-safe-refactoring)
12. [Post-Edit Actions](#post-edit-actions)


## When to Use AppDaemon (vs. Native HA)

| Situation | Recommended tool |
| --------- | ---------------- |
| Simple trigger → action | Native automation |
| Condition chains, choose/if-then | Native automation |
| Multi-step stateful logic (e.g. presence simulation)  | AppDaemon |
| Looping, retries with backoff | AppDaemon |
| External API orchestration (REST, polling, WebSocket) | AppDaemon |
| Mathematical/statistical processing at runtime | AppDaemon |
| Cross-entity coordination with shared in-memory state | AppDaemon |
| Reusable logic applied to multiple entity groups | AppDaemon (parameterized class) |
| Debugging complex timing issues with detailed logging | AppDaemon |

**Anti-pattern:** Rewriting working HA automations in AppDaemon "for cleanliness."
AppDaemon adds operational complexity (separate process, Python dependency, restart
cycles) that is only justified when native automations genuinely cannot express the logic.

## App Structure and Lifecycle

Every AppDaemon app is a Python class that inherits from `Hass`:

```python
from appdaemon.plugins.hass import Hass

class MyApp(Hass):

    def initialize(self):
        """Called once when AppDaemon starts or the app is reloaded."""
        # Register callbacks here — not in __init__
        self.listen_state(self.on_motion, "binary_sensor.hallway_motion", new="on")

    def on_motion(self, entity, attribute, old, new, **kwargs):
        """Callback signature: entity, attribute, old value, new value, **kwargs."""
        self.turn_on("light.hallway")
```

**Rules:**

- **Always register callbacks in `initialize()`**, never in `__init__()`. AppDaemon
    calls `initialize()` after the plugin connection is established; `__init__()` runs
    before that and HA API calls will fail silently.
  
    Store handles from `listen_state()`, `listen_event()`, or `run_*()` only if you need to cancel a specific listener or timer during runtime (e.g., for one-shot listeners). For reload safety, this is not required—AppDaemon automatically cleans up all listeners and timers on reload.

## Listening to State Changes

### Basic State Listener

```python
def initialize(self):
    # Fire when entity changes to a specific state
    self.listen_state(self.on_door_open, "binary_sensor.front_door", new="on")

    # Fire on any state change
    self.listen_state(self.on_temp_change, "sensor.living_room_temperature")

    # Fire when a specific attribute changes
    self.listen_state(
        self.on_brightness_change,
        "light.living_room",
        attribute="brightness"
    )

    # Fire after entity has been in state for a duration (seconds)
    self.listen_state(
        self.on_motion_timeout,
        "binary_sensor.hallway_motion",
        new="off",
        duration=300  # 5 minutes
    )

def on_door_open(self, entity, attribute, old, new, **kwargs):
    self.log(f"{entity} changed from {old} to {new}")
```

### Passing Extra Arguments

```python
def initialize(self):
    self.listen_state(
        self.on_motion,
        "binary_sensor.hallway_motion",
        new="on",
        light="light.hallway", # custom kwarg passed through to callback
        brightness_pct=80
    )

def on_motion(self, entity, attribute, old, new, **kwargs):
    self.turn_on(kwargs["light"], brightness_pct=kwargs["brightness_pct"])
```

### Getting Current State

```python
# Get state value
state = self.get_state("binary_sensor.door") # "on" / "off"

# Get a specific attribute
brightness = self.get_state("light.living_room", attribute="brightness")

# Get full state dict (includes 'state', 'attributes', 'last_changed', 'last_updated')
attrs = self.get_state("light.living_room", attribute="all")

# Safe numeric conversion — always guard against None / "unavailable"
temp = self.get_state("sensor.temperature")
if temp not in (None, "unavailable", "unknown"):
    value = float(temp)
```

### Listening to Events

```python
def initialize(self):
    # ZHA button event
    self.listen_event(
        self.on_zha_event,
        "zha_event",
        device_ieee="00:15:8d:00:07:26:f2:8a"
    )

def on_zha_event(self, event_name, data, **kwargs):
    command = data.get("command")
    if command == "toggle":
        self.toggle("light.bedroom")
```

## Calling HA Services

### turn_on / turn_off / toggle

```python
# Simple on/off/toggle
self.turn_on("light.kitchen")
self.turn_off("light.kitchen")
self.toggle("light.kitchen")

# With service data
self.turn_on("light.kitchen", brightness_pct=80, color_temp_kelvin=3000)
```

### call_service

Use `call_service` for any domain/service not covered by convenience methods.
**Format: `domain/service_name` (slash, not dot).**

```python
# Climate
self.call_service(
    "climate/set_temperature",
    entity_id="climate.living_room",
    temperature=22,
    hvac_mode="heat"
)

# Notify
self.call_service(
    "notify/mobile_app_phone",
    title="Motion Detected",
    message=f"Motion in hallway"
)

# Cover
self.call_service(
    "cover/set_cover_position",
    entity_id="cover.living_room_blinds",
    position=50
)
```

### Targeting Areas

```python
# Turn off all lights in an area
self.call_service(
    "light/turn_off",
    area_id="living_room"
)
```

## Scheduling and Timers

### One-Shot Delay

```python
def initialize(self):
    self._off_handle = None
    self.listen_state(self.on_motion, "binary_sensor.hallway_motion", new="on")

def on_motion(self, entity, attribute, old, new, **kwargs):
    # Cancel previous timer before scheduling a new one
    if self._off_handle:
        self.cancel_timer(self._off_handle)
    self.turn_on("light.hallway")
    self._off_handle = self.run_in(self.turn_off_cb, 300) # 300 seconds

def turn_off_cb(self, **kwargs):
    self.turn_off("light.hallway")
    self._off_handle = None
```

**Anti-pattern:** Calling `run_in` from a motion callback without cancelling the
previous handle first. Every motion event stacks a new independent timer — the light
will switch off and potentially back on unpredictably. Always cancel first.

### Recurring Schedules

```python
def initialize(self):
    # Fixed time every day
    self.run_daily(self.morning_routine, "07:00:00")

    # Every N seconds (starting now)
    self.run_every(self.poll_api, self.datetime(), 60)

    # Sunrise / sunset with optional offset (seconds)
    self.run_at_sunrise(self.on_sunrise)
    self.run_at_sunset(self.on_sunset, offset=-1800) # 30 min before sunset
```

### Cancelling Handles

```python
def initialize(self):
    self._state_handle = self.listen_state(self.on_change, "binary_sensor.door")
    self._timer_handle = self.run_in(self.timeout_cb, 60)

def cancel_manually(self):
    if self._state_handle:
        self.cancel_listen_state(self._state_handle)
        self._state_handle = None
    if self._timer_handle:
        self.cancel_timer(self._timer_handle)
        self._timer_handle = None
```

AppDaemon cancels all registered handles automatically when an app is unloaded or
restarted. Manual cancellation is needed when you want to stop a specific callback
mid-run based on logic conditions.

## State Management and Inter-App Communication

### Instance Variables (in-memory only)

```python
def initialize(self):
    self._count = 0 # Reset on every app reload / daemon restart

def on_trigger(self, entity, attribute, old, new, **kwargs):
    self._count += 1
    self.log(f"Triggered {self._count} times this session")
```

**Warning:** Instance variables are lost on hot-reload and daemon restart. For
persistent state, use HA input helpers.

### Persisting State via HA Helpers

```python
# Read
raw_count = self.get_state("input_number.motion_counter")
count = int(float(raw_count)) if raw_count not in (None, "unavailable", "unknown") else 0

# Write
self.call_service(
    "input_number/set_value",
    entity_id="input_number.motion_counter",
    value=count + 1
)

# Boolean flag
self.call_service(
    "input_boolean/turn_on",
    entity_id="input_boolean.presence_confirmed"
)
```

### Inter-App Communication via Events

```python
# App A: fire a custom event (flat kwargs)
self.fire_event("MY_APP_EVENT", source="app_a", value=42)

# App B: subscribe to it
def initialize(self):
    self.listen_event(self.on_custom_event, "MY_APP_EVENT")

def on_custom_event(self, event_name, data, **kwargs):
    self.log(f"Received from {data['source']}: {data['value']}")
```

## Logging

```python
self.log("Normal operational message") # INFO (default)
self.log("Detailed debug info", level="DEBUG")
self.log("Something unexpected happened", level="WARNING")
self.log("Service call failed", level="ERROR")
```

**Best practices:**

- Include entity names and current values in log messages so `appdaemon.log` is
  readable without cross-referencing the HA state history.
- Use `level="DEBUG"` for high-frequency state change details; keep `INFO` for
  meaningful transitions only.
- Avoid expensive f-string expressions at `DEBUG` level in hot paths — guard with
  a condition if the expression requires additional `get_state()` calls.

## apps.yaml Configuration

### Basic App Entry

```yaml
# /config/appdaemon/apps/apps.yaml

motion_light_hallway:
  module: motion_light # Python filename without .py
  class: MotionLight # Class name inside the file
  entity_motion: binary_sensor.hallway_motion
  entity_light: light.hallway
  timeout: 300
```

### Parameterized App — Multiple Instances

Define the logic once in Python, instantiate multiple times in `apps.yaml`:

```python
# motion_light.py
from appdaemon.plugins.hass import Hass

class MotionLight(Hass):

    def initialize(self):
        # Ensure required args are present
        for required in ("entity_light", "entity_motion"):
            if required not in self.args:
                self.log(f"{required} is required in apps.yaml", level="ERROR")
                return
        self._light   = self.args["entity_light"]
        self._timeout = self.args.get("timeout", 180)
        self._off_handle = None
        self.listen_state(
            self.on_motion,
            self.args["entity_motion"],
            new="on"
        )

    def on_motion(self, entity, attribute, old, new, **kwargs):
        if self._off_handle:
            self.cancel_timer(self._off_handle)
        self.turn_on(self._light)
        self._off_handle = self.run_in(self.turn_off_cb, self._timeout)

    def turn_off_cb(self, **kwargs):
        self.turn_off(self._light)
        self._off_handle = None
```

```yaml
# apps.yaml

motion_light_hallway:
  module: motion_light
  class: MotionLight
  entity_motion: binary_sensor.hallway_motion
  entity_light: light.hallway
  timeout: 300

motion_light_kitchen:
  module: motion_light
  class: MotionLight
  entity_motion: binary_sensor.kitchen_motion
  entity_light: light.kitchen
  timeout: 120
```

This parameterized pattern is a primary AppDaemon strength: no code duplication,
entity IDs stay in configuration rather than source code.

### Packages (Subdirectory Organisation)

```
/config/appdaemon/apps/
  lighting/
    __init__.py        # required when using dotted module paths; not needed for flat module names
    motion_light.py
  presence/
    __init__.py  # required for dotted module paths
    tracker.py
```

```yaml
motion_light_hallway:
  module: lighting.motion_light
  class: MotionLight
  entity_motion: binary_sensor.hallway_motion
  entity_light: light.hallway
```

## Error Handling

### Defensive State Reads

```python
def get_temperature(self):
    raw = self.get_state("sensor.outside_temperature")
    if raw in (None, "unavailable", "unknown"):
        self.log("Temperature sensor unavailable", level="WARNING")
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        self.log(f"Unexpected temperature value: {raw!r}", level="ERROR")
        return None
```

### Accessing args Safely

```python
def initialize(self):
    # Use .get() with a default rather than direct key access
    self._timeout   = self.args.get("timeout", 180)
    self._log_level = self.args.get("log_level", "INFO")

    # Required args: fail loudly with a clear message
    if "entity_light" not in self.args:
        self.log("entity_light is required in apps.yaml", level="ERROR")
        return
    self._light = self.args["entity_light"]
```

### Verifying Service Call Outcomes

AppDaemon does not raise exceptions for failed service calls. Verify critical
outcomes by reading entity state after a short delay:

```python
def initialize(self):
    # ...existing code...
    self._verify_handle = None

def set_thermostat(self, temp):
    self.call_service(
        "climate/set_temperature",
        entity_id="climate.living_room",
        temperature=temp
    )
    if hasattr(self, "_verify_handle") and self._verify_handle:
        self.cancel_timer(self._verify_handle)
    self._verify_handle = self.run_in(self.verify_thermostat, 5, expected=temp)

def verify_thermostat(self, **kwargs):
    actual = self.get_state("climate.living_room", attribute="temperature")
    if actual in (None, "unavailable", "unknown"):
        self.log("Could not verify thermostat — sensor unavailable", level="WARNING")
        return
    expected = kwargs.get("expected")
    if expected is None:
        self.log("verify_thermostat called without expected — cannot verify", level="ERROR")
        return
    if abs(float(actual) - float(expected)) > 0.5:
        self.log(
            f"Thermostat did not accept setpoint {expected} "
            f"(actual: {actual})",
            level="WARNING"
        )
```

## AppDaemon-Specific Anti-Patterns

| Anti-pattern | Use instead | Why |
| ------------ | ----------- | --- |
| Calling `self.turn_on()` / `self.get_state()` in `__init__()` | Register everything in `initialize()` | Plugin connection not established during `__init__` — calls fail silently |
| Calling `run_in` on repeated triggers without cancelling the previous handle | `cancel_timer(self._off_handle)` before each new `run_in` | Every trigger stacks an independent timer — devices toggle unpredictably |
| Storing persistent state in instance variables | Use HA `input_number`, `input_boolean`, or `input_text` helpers  | Instance variables reset on app reload or daemon restart |
| Hardcoding entity IDs inside the class body | Pass entity IDs via `self.args` in `apps.yaml` | Hardcoded IDs prevent reuse and require code edits per installation |
| Accessing `self.get_state()` result without guarding for `"unavailable"` / `"unknown"` | `if new not in (None, "unavailable", "unknown")` | Unavailable sensors cause `float()` / `int()` to raise `ValueError` |
| Polling state with a tight `run_every` loop | `listen_state` with `duration` parameter | Polling wastes CPU and bloats the log; `listen_state(duration=N)` is event-driven |
| call_service("light.turn_on", ...) — dot notation | call_service("light/turn_on", ...) — slash notation | AppDaemon requires domain/service format; dot notation will cause the call to silently do nothing or log a warning, depending on the version. |
| `self.args["key"]` without `.get()` | `self.args.get("key", default)` | Missing key in `apps.yaml` raises `KeyError` at startup with no useful error message |
| Writing a new AppDaemon app for logic that native HA can express | Use native automation, `choose`, `repeat`, or `wait_for_trigger` | AppDaemon adds a separate process, Python dependency, and longer restart cycle |

## Impact on Safe Refactoring

AppDaemon apps reference HA entity IDs as string literals in Python files **and**
as argument values in `apps.yaml`. When renaming HA entities, search AppDaemon
sources in addition to the standard HA config components listed in
`references/safe-refactoring.md#step-2-search-all-consumers`.

**Additional locations to include in the Step 2 checklist:**

| Location | What to search |
| -------- | -------------- |
| `/config/appdaemon/apps/**/*.py` | Old entity ID as a string literal or default in `self.args.get(...)` |
| `/config/appdaemon/apps/apps.yaml` | Old entity ID as a value in any app argument |

After updating, hot-reload is automatic (AppDaemon watches file changes). Confirm
in `appdaemon.log` that the app reloaded without errors.

## Post-Edit Actions

| Change type | Required action |
| ----------- | --------------- |
| New or edited `.py` app file | AppDaemon hot-reloads automatically on file save (requires `production_mode: false`, which is the default) |
| Edit to `apps.yaml` | Hot-reload automatic; verify in `appdaemon.log` |
| Edit to `appdaemon.yaml` (daemon config) | Restart the AppDaemon App — **Settings → Apps → AppDaemon → Restart** |
| HA entity rename consumed by an app | Update all `.py` files and `apps.yaml`; hot-reload triggers automatically |
| New Python package dependency | Add to AppDaemon App configuration (`python_packages` list) and restart the App |

**Note:** In HA 2026.2+, add-ons are referred to as **Apps**. The AppDaemon add-on
appears under **Settings → Apps**.
