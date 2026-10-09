# Dashboard Card Types

A card's visual editor in the running instance shows fields that instance accepts, at its installed version. It is not the full list: a card can accept YAML-only options its editor omits, and a custom card may have no editor at all. A field missing from the editor is not proof that it is invalid. The lists below are the cards the card picker offers as of 2026.10.

## Where to Read a Card's Fields

Pick the row that matches the access you have. Do not install anything, or ask the user to, to reach a higher row.

| You have | Read the card's fields from |
|----------|-----------------------------|
| A tool that describes card types or card fields from the instance: in your tool list, or found with one query if your tools are behind a tool search | That tool, for built-in and installed custom cards |
| A browser on the HA UI | The card's visual editor (edit the dashboard, add or edit the card) |
| Neither | The card's docs page (see [Fetching Card Documentation](#fetching-card-documentation)). It describes the latest release and no custom cards |

## Available Card Types

**Core:** alarm-panel, area, button, calendar, clock, conditional, distribution, entities, entity-filter, entity, gauge, glance, grid, heading, history-graph, horizontal-stack, humidifier, iframe, light, logbook, map, markdown, media-control, picture-elements, picture-entity, picture-glance, picture, plant-status, sensor, shortcut, statistic, statistics-graph, thermostat, tile, todo-list, vertical-stack, weather-forecast

**Energy:** energy-carbon-consumed-gauge, energy-compare, energy-date-selection, energy-devices-detail-graph, energy-devices-graph, energy-distribution, energy-gas-graph, energy-grid-balance, energy-grid-neutrality-gauge, energy-sankey, energy-self-sufficiency-gauge, energy-solar-consumed-gauge, energy-solar-graph, energy-sources-table, energy-usage-graph, energy-water-graph, power-sankey, power-sources-graph, water-flow-sankey, water-sankey

**Legacy:** `shopping-list` still renders but cannot be added from the UI. Use `todo-list`.

## Fetching Card Documentation

```
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_dashboards/{page}.markdown
```

| Card | `{page}` |
|------|----------|
| Core or legacy card | the card type (e.g., `tile`, `grid`, `button`) |
| Any energy card | `energy` (one page for all of them). Its example writes `energy-compare-card`; the type is `energy-compare` |
| View type (`masonry`, `panel`, `sections`, `sidebar`) | the view type. It is the view's `"type"`, not a card: see [dashboard-guide #view-types](dashboard-guide.md#view-types) |

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
