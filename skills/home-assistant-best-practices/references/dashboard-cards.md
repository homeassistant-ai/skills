# Dashboard Card Types

Home Assistant provides 41 built-in card types. For card-specific documentation, fetch from GitHub on demand.

## Available Card Types

alarm-panel, area, button, calendar, clock, conditional, energy, entities, entity-filter, entity, gauge, glance, grid, heading, history-graph, horizontal-stack, humidifier, iframe, light, logbook, map, markdown, masonry, media-control, panel, picture-elements, picture-entity, picture-glance, picture, plant-status, sections, sensor, shopping-list, sidebar, statistic, statistics-graph, thermostat, tile, todo-list, vertical-stack, weather-forecast

## Fetching Card Documentation

To get detailed documentation for a specific card type, fetch from the Home Assistant docs:

```
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_dashboards/{card_type}.markdown
```

Replace `{card_type}` with the card name from the list above (e.g., `tile`, `grid`, `button`).

If the MCP server provides resource URIs, use `ha://docs/cards/{card_type}` instead.

## Quick Card Selection Guide

| Need | Card |
|------|------|
| Control any entity | `tile` (modern default) |
| Layout multiple cards in columns | `grid` |
| Navigation button | `button` with `tap_action: navigate` |
| Room overview with controls | `area` |
| Historical data graph | `history-graph` or `statistics-graph` |
| Sensor value display | `sensor` or `gauge` |
| Show/hide cards conditionally | `conditional` |
| Embed external page | `iframe` |
| Rich text / instructions | `markdown` |
| Camera or image with overlays | `picture-elements` |
