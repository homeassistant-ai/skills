# Storage Schemas Reference

This document covers the JSON schema for Home Assistant `.storage/` files
that agents may need to read or write directly.

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

**Key notes:** Keys are `min`/`max` (not `minimum`/`maximum` as in YAML config), `initial`, `unit_of_measurement`, and `icon` are optional, `mode` is `"box"` or `"slider"`, the `id` value (e.g. `my_helper`) becomes the `unique_id` in `core.entity_registry` and the `entity_id` is `input_number.<id>` (e.g. `input_number.my_helper`).

**After writing:** call the `input_number.reload` service (Reloading → Input Numbers in Developer Tools), or restart HA.

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

**Key notes:** No `initial` field (state is not stored here), `icon` is optional.

---

## entity_registry (cleanup)

**File:** `/config/.storage/core.entity_registry`

Structure: `{ "data": { "entities": [ {...}, ... ] } }`

To remove stale entries (e.g. after a helper was removed without proper cleanup and its entry persists in the registry):

> ⚠️ `core.entity_registry` is ~2–3 MB — too large for the HA REST file API.
> Use a method that supports large file reads and writes (e.g. SSH, terminal access,
> or a file manager add-on).

Steps: back up the file, read and parse the JSON structure, remove the entry where `unique_id` matches the stale entity (e.g. `input_number.my_helper` → `unique_id: "my_helper"`), write the modified JSON back, and restart HA (a reload is not sufficient for registry changes).
