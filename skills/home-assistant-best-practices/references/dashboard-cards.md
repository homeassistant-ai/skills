# Dashboard Card Types

A card's visual editor in the running instance is its definition: the form lists the fields and options that instance accepts. Custom cards supply their own editors the same way. The lists below are the cards the card picker offers as of 2026.10.

## Where Card Definitions Come From

Pick the row that matches the access you already have. Do not search for, install or ask for a tool to reach a higher row.

| You have | Read the card's fields from |
|----------|-----------------------------|
| A tool, already in your tool list, that describes card types or card fields from the instance | That tool. It covers built-in and installed custom cards at the installed version |
| A browser on the HA UI | The card's visual editor (edit the dashboard, add or edit the card) |
| Neither | The card's docs page (see [Fetching Card Documentation](#fetching-card-documentation)). It describes the latest release and no custom cards |

## Available Card Types

**Core:** alarm-panel, area, button, calendar, clock, conditional, distribution, entities, entity-filter, entity, gauge, glance, grid, heading, history-graph, horizontal-stack, humidifier, iframe, light, logbook, map, markdown, media-control, picture-elements, picture-entity, picture-glance, picture, plant-status, sensor, shortcut, statistic, statistics-graph, thermostat, tile, todo-list, vertical-stack, weather-forecast

**Energy:** energy-carbon-consumed-gauge, energy-compare, energy-date-selection, energy-devices-detail-graph, energy-devices-graph, energy-distribution, energy-gas-graph, energy-grid-balance, energy-grid-neutrality-gauge, energy-sankey, energy-self-sufficiency-gauge, energy-solar-consumed-gauge, energy-solar-graph, energy-sources-table, energy-usage-graph, energy-water-graph, power-sankey, power-sources-graph, water-flow-sankey, water-sankey

`energy` is not a card type; it is the docs page for the energy cards.

**Legacy:** `shopping-list` still renders but cannot be added from the UI. Use `todo-list`.

**Note:** The view types (`masonry`, `panel`, `sections`, `sidebar`) share the docs URL pattern. They are set at the view level via `"type"` in view config, NOT inside card arrays. See [dashboard-guide #view-types](dashboard-guide.md#view-types).

## Fetching Card Documentation

```
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_dashboards/{page}.markdown
```

| Card | `{page}` |
|------|----------|
| Core or legacy card | the card type (e.g., `tile`, `grid`, `button`) |
| Any energy card | `energy` (one page for all of them) |

## Quick Card Selection Guide

| Need | Card |
|------|------|
| Control any entity | `tile` (modern default) |
| Layout multiple cards in columns | `grid` |
| One-tap launcher: navigate, URL, Assist or an action | `shortcut` (2026.5+), e.g. `{"type": "shortcut", "tap_action": {"action": "assist"}}`; text key `label`. `button` with a `tap_action` only before 2026.5 |
| Room overview with controls | `area` |
| Historical data graph | `history-graph` or `statistics-graph` |
| Sensor value display | `sensor` or `gauge` |
| Proportional data across entities | `distribution` |
| Show/hide cards conditionally | `conditional` |
| Embed external page | `iframe` |
| Rich text / instructions | `markdown` |
| Camera or image with overlays | `picture-elements` |
