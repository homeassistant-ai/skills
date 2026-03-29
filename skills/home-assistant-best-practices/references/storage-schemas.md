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

**Key notes:** min/max (not minimum/maximum), optional: initial, unit_of_measurement, icon, mode: "box" or "slider", id becomes unique_id in core.entity_registry, entity_id is input_number.<id>.

**After writing:** call input_number.reload or restart HA.

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

**Key notes:** initial field absent (state not stored), icon optional.

**After writing:** call input_boolean.reload or restart HA.

---

## entity_registry (cleanup)

**File:** `/config/.storage/core.entity_registry`

Structure: `{ "data": { "entities": [ {...}, ... ] } }`

> ⚠️ ~2–3 MB — too large for the HA REST file API; use SSH, terminal, or file manager add-on.

To remove stale entries:

Steps: back up file, read/parse JSON, remove entry for stale entity (e.g., for input_number.my_helper, remove where unique_id is "my_helper"), write modified JSON back, restart HA (reload insufficient).
