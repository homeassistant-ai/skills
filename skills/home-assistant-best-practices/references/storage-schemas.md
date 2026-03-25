# Storage Schemas Reference

This document covers the JSON schema for Home Assistant `.storage/` files
that agents may need to read or write directly via `write_file` or SSH.

> ⚠️ Always read the existing `.storage/` file before writing — use it as the
> canonical schema reference. Never reconstruct schemas from memory.

---

## input_number

**File:** `/config/.storage/input_number`

```json
{
  "version": 1,
  "minor_version": 1,
  "key": "input_number",
  "data": {
    "items": [
      {
        "id": "my_helper",
        "name": "Display Name",
        "min": 0.0,
        "max": 100.0,
        "step": 0.5,
        "initial": 21.0,
        "mode": "box",
        "unit_of_measurement": "°C",
        "icon": "mdi:thermometer"
      }
    ]
  }
}
```

**Key notes:**
- Keys are `min` / `max` — **not** `minimum` / `maximum`
- Same key names as in `configuration.yaml` YAML config
- `initial`, `unit_of_measurement`, `icon` are optional
- `mode`: `"box"` or `"slider"`
- `id` must match the `unique_id` in `core.entity_registry`

**After writing:** call `input_number/reload` or restart HA.

---

## input_boolean

**File:** `/config/.storage/input_boolean`

```json
{
  "version": 1,
  "minor_version": 1,
  "key": "input_boolean",
  "data": {
    "items": [
      {
        "id": "my_flag",
        "name": "Display Name",
        "icon": "mdi:toggle-switch"
      }
    ]
  }
}
```

**Key notes:**
- No `initial` field — state is not persisted here
- `icon` is optional

---

## entity_registry (cleanup)

**File:** `/config/.storage/core.entity_registry`

Structure: `{ "data": { "entities": [ {...}, ... ] } }`

To remove stale entries (e.g. after a helper was deleted via UI but
its zombie persists):

```python
import json, shutil
shutil.copy('/config/.storage/core.entity_registry',
            '/config/.storage/core.entity_registry.bak')
with open('/config/.storage/core.entity_registry', 'r') as f:
    reg = json.load(f)
reg['data']['entities'] = [
    e for e in reg['data']['entities']
    if e.get('unique_id') != 'the_id_to_remove'
]
with open('/config/.storage/core.entity_registry', 'w') as f:
    json.dump(reg, f)
```

**After writing:** restart HA (reload is not sufficient for registry changes).
