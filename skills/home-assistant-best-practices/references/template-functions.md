> **Native first.** Before reaching for a template, check
> [`automation-patterns.md`](automation-patterns.md) for a native trigger,
> condition, or action. This reference is for the cases where a template IS
> the right tool — dynamic service data, notification bodies, trigger-context
> access, and template helpers.

# Template Functions Reference

Home Assistant 2026.5 ships 200+ template functions, filters, and tests, each
with its own canonical page at `https://www.home-assistant.io/template-functions/<name>/`.
This file is an editorial selection of functions commonly seen in automations
and scripts — it
is a discovery aid, not a replacement for the canonical pages.

- **Full catalog (all categories):** <https://www.home-assistant.io/template-functions/>
- **Descriptions here are one-line summaries.** Parameters, return types, and
  examples live on each linked page — follow the link before relying on exact
  signatures.
- **Type** column shows the idiomatic call form: `fn` = function/global, `filter`
  = `value | name`, `test` = `value is name`. Many `fn` entries (e.g. `area_id`,
  `device_id`) also work as filters (`value | area_id`).

## Table of Contents

1. [States](#states)
2. [Entities, Devices, Areas, Floors, Labels](#entities-devices-areas-floors-labels)
3. [Date & Time](#date--time)
4. [Type Conversion & Numbers](#type-conversion--numbers)
5. [Collections](#collections)
6. [Strings](#strings)
7. [Regex](#regex)

---

## States

Core state access — a common template need in automations and scripts.

| Name | Type | Purpose |
|------|------|---------|
| [`states`](https://www.home-assistant.io/template-functions/states/) | fn | State value of an entity, or iterate over all states |
| [`state_attr`](https://www.home-assistant.io/template-functions/state_attr/) | fn | Value of a specific attribute of an entity |
| [`is_state`](https://www.home-assistant.io/template-functions/is_state/) | test | True if an entity is in a specific state |
| [`is_state_attr`](https://www.home-assistant.io/template-functions/is_state_attr/) | test | True if an entity attribute has a given value |
| [`has_value`](https://www.home-assistant.io/template-functions/has_value/) | test | True if the entity exists and is not `unknown`/`unavailable` |
| [`expand`](https://www.home-assistant.io/template-functions/expand/) | fn | Expand groups/zones into individual entity state objects |
| [`distance`](https://www.home-assistant.io/template-functions/distance/) | fn | Distance (km) between two points or from home |
| [`closest`](https://www.home-assistant.io/template-functions/closest/) | fn | The entity closest to a location, home, or another entity |
| [`state_translated`](https://www.home-assistant.io/template-functions/state_translated/) | fn | Translated state value (display only) |
| [`state_attr_translated`](https://www.home-assistant.io/template-functions/state_attr_translated/) | fn | Translated attribute value (display only) |

## Entities, Devices, Areas, Floors, Labels

Registry navigation — resolve and target by area/floor/label/device instead of
hard-coding entity lists.

| Name | Type | Purpose |
|------|------|---------|
| [`entity_name`](https://www.home-assistant.io/template-functions/entity_name/) | fn | Friendly name of an entity (preferred over the `friendly_name` attribute) |
| [`integration_entities`](https://www.home-assistant.io/template-functions/integration_entities/) | fn | Entity IDs belonging to an integration or config entry |
| [`is_hidden_entity`](https://www.home-assistant.io/template-functions/is_hidden_entity/) | test | True if the entity is hidden in the registry |
| [`area_id`](https://www.home-assistant.io/template-functions/area_id/) | fn | Area ID for an area name, entity ID, or device ID |
| [`area_name`](https://www.home-assistant.io/template-functions/area_name/) | fn | Friendly name of an area |
| [`area_entities`](https://www.home-assistant.io/template-functions/area_entities/) | fn | Entity IDs in an area |
| [`area_devices`](https://www.home-assistant.io/template-functions/area_devices/) | fn | Device IDs in an area |
| [`device_id`](https://www.home-assistant.io/template-functions/device_id/) | fn | Device ID for an entity ID or device name |
| [`device_entities`](https://www.home-assistant.io/template-functions/device_entities/) | fn | Entity IDs for a device |
| [`device_attr`](https://www.home-assistant.io/template-functions/device_attr/) | fn | A specific attribute of a device |
| [`floor_entities`](https://www.home-assistant.io/template-functions/floor_entities/) | fn | Entity IDs on a floor |
| [`floor_areas`](https://www.home-assistant.io/template-functions/floor_areas/) | fn | Area IDs on a floor |
| [`label_entities`](https://www.home-assistant.io/template-functions/label_entities/) | fn | Entity IDs with a given label |
| [`label_devices`](https://www.home-assistant.io/template-functions/label_devices/) | fn | Device IDs with a given label |
| [`labels`](https://www.home-assistant.io/template-functions/labels/) | fn | All label IDs, or labels of an entity/device/area |

## Date & Time

Prefer the native `for:` field on `state`/`numeric_state` triggers and
conditions over `now() - X.last_changed` duration math (see
[`automation-patterns.md`](automation-patterns.md)). Use these when a template
is genuinely needed.

| Name | Type | Purpose |
|------|------|---------|
| [`now`](https://www.home-assistant.io/template-functions/now/) | fn | Current local date and time |
| [`utcnow`](https://www.home-assistant.io/template-functions/utcnow/) | fn | Current UTC date and time |
| [`today_at`](https://www.home-assistant.io/template-functions/today_at/) | fn | Today's date at a specific time |
| [`as_timestamp`](https://www.home-assistant.io/template-functions/as_timestamp/) | fn | Convert a datetime/string to a UNIX timestamp |
| [`as_datetime`](https://www.home-assistant.io/template-functions/as_datetime/) | fn | Convert a string/timestamp to a datetime |
| [`as_local`](https://www.home-assistant.io/template-functions/as_local/) | fn | Convert a datetime to local time zone |
| [`as_timedelta`](https://www.home-assistant.io/template-functions/as_timedelta/) | fn | Parse an ISO-8601 duration into a timedelta |
| [`timedelta`](https://www.home-assistant.io/template-functions/timedelta/) | fn | Build a timedelta from numeric components |
| [`strptime`](https://www.home-assistant.io/template-functions/strptime/) | fn | Parse a time string with a format into a datetime |
| [`timestamp_custom`](https://www.home-assistant.io/template-functions/timestamp_custom/) | fn | Format a UNIX timestamp with a custom format |
| [`time_since`](https://www.home-assistant.io/template-functions/time_since/) | fn | Human-readable time elapsed since a datetime |
| [`time_until`](https://www.home-assistant.io/template-functions/time_until/) | fn | Human-readable time remaining until a datetime |

## Type Conversion & Numbers

| Name | Type | Purpose |
|------|------|---------|
| [`float`](https://www.home-assistant.io/template-functions/float/) | filter | Convert to float, with optional default on failure |
| [`int`](https://www.home-assistant.io/template-functions/int/) | filter | Convert to int, with optional default on failure |
| [`bool`](https://www.home-assistant.io/template-functions/bool/) | filter | Convert to boolean, with optional default |
| [`round`](https://www.home-assistant.io/template-functions/round/) | filter | Round to a number of decimal places |
| [`default`](https://www.home-assistant.io/template-functions/default/) | filter | Fallback value when undefined or none |
| [`is_number`](https://www.home-assistant.io/template-functions/is_number/) | test | True if the value converts to a finite number |
| [`average`](https://www.home-assistant.io/template-functions/average/) | fn | Arithmetic mean of a list |
| [`median`](https://www.home-assistant.io/template-functions/median/) | fn | Statistical median of a list |
| [`clamp`](https://www.home-assistant.io/template-functions/clamp/) | fn | Constrain a value between a min and max |
| [`remap`](https://www.home-assistant.io/template-functions/remap/) | fn | Remap a value from one numeric range to another |

## Collections

Iterating and filtering lists of entities/states.

| Name | Type | Purpose |
|------|------|---------|
| [`select`](https://www.home-assistant.io/template-functions/select/) | filter | Keep items that pass a test |
| [`selectattr`](https://www.home-assistant.io/template-functions/selectattr/) | filter | Keep items whose attribute passes a test |
| [`reject`](https://www.home-assistant.io/template-functions/reject/) | filter | Drop items that pass a test |
| [`rejectattr`](https://www.home-assistant.io/template-functions/rejectattr/) | filter | Drop items whose attribute passes a test |
| [`map`](https://www.home-assistant.io/template-functions/map/) | filter | Apply a filter / extract an attribute across a list |
| [`sort`](https://www.home-assistant.io/template-functions/sort/) | filter | Sort a list, optionally by attribute |
| [`unique`](https://www.home-assistant.io/template-functions/unique/) | filter | Remove duplicates |
| [`sum`](https://www.home-assistant.io/template-functions/sum/) | filter | Sum values, optionally by attribute |
| [`first`](https://www.home-assistant.io/template-functions/first/) | filter | First item of a list |
| [`last`](https://www.home-assistant.io/template-functions/last/) | filter | Last item of a list |
| [`from_json`](https://www.home-assistant.io/template-functions/from_json/) | fn | Parse a JSON string into an object |
| [`to_json`](https://www.home-assistant.io/template-functions/to_json/) | fn | Serialize a value to a JSON string |

## Strings

For notification messages, titles, and dynamic text — never for logic positions.

| Name | Type | Purpose |
|------|------|---------|
| [`join`](https://www.home-assistant.io/template-functions/join/) | filter | Join a list into a string with a separator |
| [`replace`](https://www.home-assistant.io/template-functions/replace/) | filter | Replace a substring |
| [`lower`](https://www.home-assistant.io/template-functions/lower/) | filter | Lowercase |
| [`upper`](https://www.home-assistant.io/template-functions/upper/) | filter | Uppercase |
| [`title`](https://www.home-assistant.io/template-functions/title/) | filter | Title-case |
| [`format`](https://www.home-assistant.io/template-functions/format/) | filter | printf-style formatting (`%s`, `%d`, `%f`) |
| [`truncate`](https://www.home-assistant.io/template-functions/truncate/) | filter | Truncate to a length with an ellipsis |
| [`slugify`](https://www.home-assistant.io/template-functions/slugify/) | filter | Convert to a slug |

## Regex

| Name | Type | Purpose |
|------|------|---------|
| [`regex_match`](https://www.home-assistant.io/template-functions/regex_match/) | filter | True if a string matches a pattern at the start |
| [`regex_search`](https://www.home-assistant.io/template-functions/regex_search/) | filter | True if a pattern occurs anywhere in a string |
| [`regex_replace`](https://www.home-assistant.io/template-functions/regex_replace/) | fn | Replace all matches of a pattern |
| [`regex_findall`](https://www.home-assistant.io/template-functions/regex_findall/) | fn | All matches of a pattern in a string |
