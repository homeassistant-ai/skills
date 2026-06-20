# Dashboard Guide

Patterns and decisions for designing Home Assistant Lovelace dashboards.

## Table of Contents

- [Dashboard Structure](#dashboard-structure)
- [View Types](#view-types)
- [Dashboard Strategies](#dashboard-strategies)
- [Built-in Cards](#built-in-cards)
- [Features](#features)
- [Badges](#badges)
- [Actions](#actions)
- [Custom Cards](#custom-cards)
- [CSS Styling](#css-styling)
- [HACS Integration](#hacs-integration)
- [Complete Example: Multi-View Dashboard](#complete-example-multi-view-dashboard)
- [Common Pitfalls](#common-pitfalls)
- [Modern Best Practices](#modern-best-practices)
- [Visual Iteration Workflow](#visual-iteration-workflow)

---

## Dashboard Structure

```json
{
  "title": "My Home",
  "icon": "mdi:home",
  "config": {
    "views": [
      {
        "title": "Overview",
        "path": "home",
        "type": "sections",
        "max_columns": 4,
        "sections": [
          {"title": "Climate", "cards": [...]},
          {"title": "Lights", "cards": [...]}
        ]
      }
    ]
  }
}
```

**url_path rules:**
- New dashboards must contain a hyphen: `my-dashboard` (not `mydashboard`)
- Use `lovelace` to target the built-in default dashboard
- `dashboard_id`: internal identifier (returned on create, used for update/delete)
- `url_path`: URL identifier (user-facing, used in dashboard URLs)

---

## View Types

| Type | Use for |
|------|---------|
| `sections` | Most dashboards (RECOMMENDED) — grid-based, responsive |
| `panel` | Full-screen single cards (maps, cameras, iframes) |
| `sidebar` | Two-column layouts with primary/secondary content |
| `masonry` | Legacy — auto-arranges cards, less control |

### View Configuration

```json
{
  "title": "View Name",
  "path": "unique-path",
  "type": "sections",
  "icon": "mdi:icon",
  "max_columns": 4,
  "sections": [...],
  "subview": false,
  "badges": ["sensor.entity_id"],
  "background": {"image": "url(/local/background.jpg)", "opacity": 0.3}
}
```

A `sections` view also supports a `header` (a markdown card plus badge positioning) and a `footer`:

```json
{
  "header": {"layout": "responsive", "badges_position": "top", "card": {"type": "markdown", "content": "# Welcome home"}},
  "footer": {"max_width": 600}
}
```

`header.layout`: `start` / `center` / `responsive`; `badges_position`: `top` / `bottom`.

---

## Dashboard Strategies

A **strategy** generates a dashboard (or a single view) from code instead of a static card list. The default Overview/Home dashboard an agent first encounters **is** a strategy dashboard — its raw config is just:

```yaml
strategy:
  type: original-states   # built-in strategy; auto-generates views from current entities/areas
views: []
```

A strategy can be set at dashboard level (`strategy:` at the top) or per view (`views: - strategy: {type: ...}`). Custom strategies use the `custom:` prefix; any extra keys are strategy-specific options. The only universal key is `type`.

```yaml
strategy:
  type: custom:my-area-dashboard
  # extra keys here are passed to the custom strategy
views: []
```

**"Take control":** to convert an auto-generated strategy dashboard into a static, hand-editable one, use the dashboard's three-dots menu → **Take control**. This is **one-way** — once taken over, the dashboard no longer auto-updates as new entities/areas appear. Editing its cards directly without taking control is a common failure mode — take control first, or edit the strategy options.

---

## Built-in Cards

| Category | Cards |
|----------|-------|
| **Modern Primary** | tile, area, button, grid |
| **Container** | vertical-stack, horizontal-stack, grid |
| **Logic** | conditional, entity-filter |
| **Display** | sensor, history-graph, statistics-graph, gauge, energy, calendar, distribution |
| **Legacy Control** | entity, entities, light, thermostat (use tile instead) |

**Default:** Use `tile` card for most entities. Use `references/dashboard-cards.md` to look up all card types or fetch card-specific docs.

### Tile Card

```json
{
  "type": "tile",
  "entity": "climate.bedroom",
  "name": "Master Bedroom",
  "icon": "mdi:thermostat",
  "features": [
    {"type": "target-temperature"},
    {"type": "climate-hvac-modes", "style": "dropdown"}
  ],
  "tap_action": {"action": "more-info"}
}
```

### Grid Card

```json
{
  "type": "grid",
  "columns": 3,
  "square": false,
  "cards": [
    {"type": "tile", "entity": "light.kitchen"},
    {"type": "tile", "entity": "light.dining"},
    {"type": "tile", "entity": "light.hallway"}
  ]
}
```

### Heading Card

The official way to label a section, replacing a bare section `title`. Supports a title/subtitle style, an icon, a tap action, and inline entity/button badges.

```json
{
  "type": "heading",
  "heading": "Kitchen",
  "heading_style": "title",
  "icon": "mdi:fridge",
  "tap_action": {"action": "navigate", "navigation_path": "/lovelace/kitchen"},
  "badges": [
    {"type": "entity", "entity": "sensor.kitchen_temperature", "show_state": true},
    {"type": "button", "icon": "mdi:lightbulb-off", "tap_action": {"action": "perform-action", "perform_action": "light.turn_off"}}
  ]
}
```

Use `"heading_style": "subtitle"` for sub-headers.

### Markdown Card

The only built-in card that renders Jinja2 templates — the go-to for computed/composite status text without a custom card.

```json
{
  "type": "markdown",
  "content": "Temp {{ states('sensor.living_room') }}°. Door {{ 'open' if is_state('binary_sensor.door','on') else 'closed' }}.",
  "entity_id": ["sensor.living_room", "binary_sensor.door"]
}
```

The card auto-detects entities referenced in the template; `entity_id` (a list) is an optional fallback for when that analysis misses some, forcing a re-render on those. `text_only: true` strips the card chrome for inline labels.

### Card Sizing in Sections (grid_options)

In a `sections` view each section is a 12-column grid. Size or span any card with `grid_options` — this replaces nested `vertical-stack`/`horizontal-stack` hacks.

```json
{
  "type": "tile",
  "entity": "light.kitchen",
  "grid_options": {"columns": 6, "rows": "auto"}
}
```

`columns`: 1–12, or `"full"` for full width. `rows`: an integer (fixed height) or `"auto"` (size to content — the default).

### Per-Entity Graph Colors

`history-graph` and `statistics-graph` cards accept a per-entity `color` via the entity object form:

```json
{
  "type": "history-graph",
  "entities": [
    {"entity": "sensor.living_room_temp", "name": "Living Room", "color": "red"},
    {"entity": "sensor.bedroom_temp", "color": "#1f77b4"}
  ]
}
```

`color` accepts a named color (`red`), hex (`'#ff0000'`), or `rgb(255, 0, 0)`.

---

## Features

Quick controls available on tile, area, humidifier, and thermostat cards.

| Domain | Feature types |
|--------|--------------|
| Climate | `climate-hvac-modes`, `climate-fan-modes`, `climate-preset-modes`, `climate-swing-modes`, `target-temperature` |
| Light | `light-brightness`, `light-color-temp` |
| Cover | `cover-open-close`, `cover-position`, `cover-tilt` |
| Fan | `fan-speed`, `fan-direction`, `fan-oscillate` |
| Media | `media-player-playback`, `media-player-volume-slider`, `media-player-volume-buttons`, `media-player-source`, `media-player-sound-mode` |
| Weather | `temperature-forecast`, `precipitation-forecast` |
| Valve | `valve-open-close`, `valve-position` |
| Lock | `lock-commands`, `lock-open-door` |
| Humidifier | `humidifier-modes`, `humidifier-toggle` |
| Water heater | `water-heater-operation-modes` |
| Select | `select-options` |
| Update | `update-actions` |
| Counter | `counter-actions` |
| Date | `date-set` |
| Lawn mower | `lawn-mower-commands` |
| Area card | `area-controls` |
| Favorites | `light-color-favorites`, `cover-position-favorite`, `cover-tilt-favorite`, `valve-position-favorite` |
| Other | `toggle`, `button`, `alarm-modes`, `numeric-input` |

**Weather features (2026.6):** `forecast_type` (`daily`/`twice_daily`/`hourly`), `days_to_show`/`hours_to_show`, `show_labels`; `precipitation-forecast` also takes `precipitation_type` (`amount`/`probability`).

**Media features:** `media-player-volume-slider` / `media-player-volume-buttons` accept `show_mute_button` (volume-buttons also `step`); `media-player-playback` `controls:` accepts transport buttons plus `volume_up`, `volume_down`, `volume_mute`, `shuffle`, `repeat`; `media-player-source` takes a `sources:` filter list and `media-player-sound-mode` a `sound_modes:` filter list.

### Tile Card Extras

Additional tile feature types beyond controls:
- `trend-graph` — 24-hour history sparkline for numeric entities
- `bar-gauge` — percentage bar for numeric entities
- `button` — a `perform-action` tap action runs automations/scripts directly from the tile

Feature `style` options: `"dropdown"` or `"icons"`

---

## Badges

Badges appear at the top of a view. The simple form is a list of entity IDs, but the **object form** unlocks more:

```json
{
  "badges": [
    "person.john",
    {
      "type": "entity",
      "entity": "sensor.kitchen_temperature",
      "show_name": true,
      "show_state": true,
      "color": "amber",
      "state_content": ["state", "last_changed"]
    }
  ]
}
```

- `type: entity` options: `show_name`, `show_state`, `show_icon`, `show_entity_picture`, `state_content` (`state`/`last_changed`/`last_updated`/an attribute), and per-badge `visibility`.
- **`color` accepts a color token or hex only — not a Jinja template.**

A **`type: shortcut`** badge (2026.5) is the badge-row counterpart of the shortcut card — a labelled action chip:

```json
{
  "type": "shortcut",
  "text": "Good night",
  "icon": "mdi:weather-night",
  "color": "indigo",
  "tap_action": {"action": "perform-action", "perform_action": "script.good_night"}
}
```

---

## Actions

```json
{
  "tap_action": {"action": "toggle"},
  "hold_action": {"action": "more-info"},
  "double_tap_action": {"action": "navigate", "navigation_path": "/lovelace/lights"}
}
```

Action types: `more-info`, `toggle`, `perform-action` (the service-call action), `navigate`, `url`, `assist`, `none`

`perform-action` is the renamed `call-service` — existing `action: call-service` configs (and the older `service`/`service_data` keys) still work, so don't flag them as broken; write new ones with `perform-action`.

### Visibility Conditions

Any card or badge accepts a `visibility` list (all conditions must pass to show). Condition types: `state`, `numeric_state`, `screen` (responsive — a CSS media query), `user`, `time`, `location`, and the `and`/`or`/`not` wrappers.

```json
{
  "visibility": [
    {"condition": "screen", "media_query": "(min-width: 1280px)"},
    {"condition": "numeric_state", "entity": "sensor.temperature", "above": 20},
    {"condition": "and", "conditions": [
      {"condition": "state", "entity": "sun.sun", "state": "above_horizon"},
      {"condition": "user", "users": ["user_id_hex"]}
    ]}
  ]
}
```

`screen` is the canonical way to show/hide cards by viewport (desktop vs. mobile).

---

## Custom Cards

Use custom JavaScript cards when built-in cards don't support your visualization.

### Minimal Custom Card

```javascript
class MyCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error("Please define an entity");
    this.config = config;
  }
  set hass(hass) {
    if (!this.content) {
      this.innerHTML = `<ha-card header="${this.config.title || 'My Card'}">
        <div class="card-content"></div>
      </ha-card>`;
      this.content = this.querySelector(".card-content");
    }
    const state = hass.states[this.config.entity];
    this.content.innerHTML = state ? `State: ${state.state}` : "Entity not found";
  }
  getCardSize() { return 2; }
}
customElements.define("my-card", MyCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "my-card", name: "My Card", description: "A custom card" });
```

Usage: `{"type": "custom:my-card", "entity": "sensor.temperature"}`

For isolated styling, use Shadow DOM (`this.attachShadow({ mode: "open" })`) and scope CSS inside the shadow root.

### Hosting

Use the HA dashboard resource API to convert inline code to a hosted URL, then register as a dashboard resource. Size limit: ~24KB source code.

### Custom Card Workflow

1. Write the card JavaScript class (see Minimal Custom Card above)
2. Register it as a dashboard resource via the HA REST API (`/api/config/lovelace/resources`) with `resource_type: "module"`
3. Use the card in your dashboard config with the `custom:` prefix

```json
{
  "type": "custom:quick-status-card",
  "entity": "sensor.temperature",
  "name": "Living Room"
}
```

---

## CSS Styling

### Theme Overrides

```css
:root {
  --primary-color: #03a9f4;
  --ha-card-background: rgba(26, 26, 46, 0.9);
  --ha-card-border-radius: 16px;
  --ha-card-box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
```

### Card-mod (Per-Card Styling)

Requires the `card-mod` HACS component:

```yaml
type: entities
card_mod:
  style: |
    ha-card {
      --ha-card-background: teal;
      color: var(--primary-color);
    }
entities:
  - light.bed_light
```

---

## HACS Integration

| Use case | Solution |
|----------|----------|
| Popular community card | HACS — search and install via HACS API |
| Small custom styling | Inline CSS — register via HA dashboard resource API |
| One-off custom card | Inline module — register via HA dashboard resource API |
| Large/complex card | HACS or filesystem (`/config/www/`) |

### Finding and Installing Cards

Search HACS for community cards by name/category, review repository details, then install. HACS install operations are destructive — clients will ask for user confirmation.

### Popular HACS Cards

- **mushroom** — Modern, clean card collection
- **button-card** — Highly customizable buttons
- **mini-graph-card** — Compact graphs
- **card-mod** — CSS styling for any card
- **layout-card** — Advanced layout control
- **apexcharts-card** — Professional charts

---

## Complete Example: Multi-View Dashboard

```json
{
  "views": [
    {
      "title": "Overview",
      "path": "home",
      "type": "sections",
      "max_columns": 4,
      "badges": ["person.john", "person.jane"],
      "sections": [
        {
          "title": "Quick Actions",
          "cards": [{
            "type": "grid",
            "columns": 4,
            "square": false,
            "cards": [
              {"type": "button", "name": "Lights", "icon": "mdi:lightbulb", "tap_action": {"action": "navigate", "navigation_path": "/lovelace/lights"}},
              {"type": "button", "name": "Climate", "icon": "mdi:thermostat", "tap_action": {"action": "navigate", "navigation_path": "/lovelace/climate"}},
              {"type": "button", "name": "Security", "icon": "mdi:shield-home", "tap_action": {"action": "navigate", "navigation_path": "/lovelace/security"}},
              {"type": "button", "name": "Energy", "icon": "mdi:lightning-bolt", "tap_action": {"action": "navigate", "navigation_path": "/lovelace/energy"}}
            ]
          }]
        },
        {
          "title": "Favorites",
          "cards": [{
            "type": "grid",
            "columns": 3,
            "square": false,
            "cards": [
              {"type": "tile", "entity": "light.living_room", "features": [{"type": "light-brightness"}]},
              {"type": "tile", "entity": "climate.bedroom", "features": [{"type": "target-temperature"}]},
              {"type": "tile", "entity": "lock.front_door"}
            ]
          }]
        }
      ]
    },
    {
      "title": "Lights",
      "path": "lights",
      "type": "sections",
      "icon": "mdi:lightbulb",
      "max_columns": 3,
      "sections": [
        {
          "title": "Living Room",
          "cards": [{
            "type": "grid",
            "columns": 3,
            "cards": [
              {"type": "tile", "entity": "light.overhead", "features": [{"type": "light-brightness"}]},
              {"type": "tile", "entity": "light.lamp", "features": [{"type": "light-brightness"}]},
              {"type": "tile", "entity": "light.accent", "features": [{"type": "light-color-temp"}]}
            ]
          }]
        }
      ]
    }
  ]
}
```

---

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| url_path rejected | New dashboards need a hyphen: `my-dashboard` not `mydashboard`. Use `lovelace` for the default dashboard. |
| Entity not found | Use full entity ID: `light.living_room` not `living_room` |
| Features not working | Match feature type to entity domain (e.g., `light-brightness` only works on `light.*`) |
| Custom card not loading | Check resource type is `module` and verify URL is accessible |
| Card too large for inline | Use HACS or filesystem instead |

---

## Modern Best Practices

- Use **sections** view type with grid-based layouts
- Use **tile** cards as primary card type (replaces legacy entity/light/climate cards)
- Use **grid** cards for multi-column layouts within sections
- Create **multiple views** with navigation paths (avoid single-view endless scrolling)
- Use **area** cards with navigation for hierarchical organization

### Recent Dashboard Features (2026.2–2026.6)

| Feature | Version | Details |
|---------|---------|---------|
| **Distribution card** | 2026.2 | Proportional horizontal bars across multiple entities (power monitoring, storage usage) |
| **Heading-card button badges** | 2026.2 | Inline `button` badges in heading cards for quick actions |
| **Section background colors** | 2026.4 | Sections support custom `background_color` with adjustable opacity |
| **Card favorites** | 2026.4 | Light color and cover/valve position favorites on tile/light cards (see the Favorites row in the Features table) |
| **Auto-height cards** | 2026.4 | Cards auto-adjust height based on content via the layout editor |
| **Shortcut badge** | 2026.5 | `type: shortcut` action chip in the badge row |
| **Media source / sound-mode features** | 2026.5 | `media-player-source`, `media-player-sound-mode` tile features |
| **Weather forecast features** | 2026.6 | `temperature-forecast`, `precipitation-forecast` tile features |
| **Per-entity graph color** | 2026.6 | `color` on each entity of `history-graph` / `statistics-graph` |

**Legacy patterns to avoid:**
- Single-view dashboards with all cards in one long scroll
- Excessive use of vertical-stack/horizontal-stack instead of grid
- Masonry view (auto-layout) — use sections for precise control
- Putting all entities in generic "entities" cards

---

## Visual Iteration Workflow

For iterative dashboard design with visual feedback, add a browser automation MCP server:

### Recommended MCP Servers

- **Playwright MCP** (`@anthropic/mcp-playwright`) — Take screenshots, interact with pages
- **Puppeteer MCP** — Similar browser automation capabilities
- **Browser DevTools MCP** — Inspect elements, debug layouts

### Workflow

```
1. Create/update dashboard via the HA config API
2. Navigate browser to dashboard URL (e.g., http://homeassistant.local:8123/lovelace/my-dashboard)
3. Take screenshot to see current layout
4. Analyze screenshot for issues (spacing, alignment, colors)
5. Adjust configuration and repeat
```

### Example with Playwright MCP

```
1. Get the HA base URL from the system overview (e.g., "http://homeassistant.local:8123")
2. Update dashboard config via the HA REST API
3. Navigate browser to {base_url}/lovelace/{url_path}
4. Take screenshot → analyze → adjust → repeat
```

### Benefits

- See actual rendered output, not just JSON config
- Catch visual issues (card overlap, responsive breakpoints)
- Verify custom card styling
- Test on different viewport sizes
