# Dashboard Guide

Patterns and decisions for designing Home Assistant Lovelace dashboards.

## Table of Contents

- [Dashboard Structure](#dashboard-structure)
- [View Types](#view-types)
- [Card Sizing and Responsive Layout](#card-sizing-and-responsive-layout)
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
          {"type": "grid", "cards": [
            {"type": "heading", "heading": "Climate", "icon": "mdi:thermometer"},
            ...
          ]},
          {"type": "grid", "cards": [
            {"type": "heading", "heading": "Lights", "icon": "mdi:lightbulb"},
            ...
          ]}
        ]
      }
    ]
  }
}
```

Section `title` is soft-deprecated (frontend source marks it `@deprecated Use heading card instead`). It still parses and renders: the frontend converts a section `title` into a prepended `heading` card on **every config load** (`checkLovelaceConfig`), in YAML mode as well as storage mode, so existing configs are not broken — don't reject or flag a user's `title`. Prefer starting each section with an explicit `heading` card for new configs. Heading cards support `heading_style` (`"title"` or `"subtitle"`), `icon`, `tap_action`, and entity `badges`.

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
  "background": {"image": "/local/background.jpg", "opacity": 30, "size": "cover"}
}
```

`background.image` is a plain path or media-source reference (the `url(...)` wrapper belongs only to the legacy string form of `background`); `opacity` is an integer 0–100. Badges also accept full objects: `{"type": "entity", "entity": "person.jane", "show_name": true, "color": "accent", "visibility": [...]}`.

A `sections` view also supports a `header` (a markdown card plus badge positioning) and a `footer`:

```json
{
  "header": {"layout": "responsive", "badges_position": "top", "card": {"type": "markdown", "content": "# Welcome home"}},
  "footer": {"max_width": 600}
}
```

`header.layout`: `start` / `center` / `responsive`; `badges_position`: `top` / `bottom`.

---

## Card Sizing and Responsive Layout

How sections views lay out — required background for sizing cards across screen sizes:

- Each section is a **12-column grid** (cell height 56px, gap 8px). Cards default to the full 12 columns.
- Size cards with `grid_options`: `{"columns": 6, "rows": 2}`. `columns` accepts 1–12 or `"full"`; `rows` accepts a number or `"auto"`. The older `layout_options` (`grid_columns`/`grid_rows`) is deprecated — still parsed, never write it.
- Section columns reflow by available width (viewport minus sidebar; minimum section column width is 320px), clamped to the view's `max_columns` (default 4): roughly 1 column on phones, 2 around 700px, 3 around 1050px, more as width allows. Cards never reflow *within* a section — a card's `columns` value is fixed; what changes with width is the number of section columns shown, and the grid width of spanned sections (next point).
- A spanned section's grid widens with it: a `column_span: 2` section has a **24-column grid** (span × 12) on wide screens, but is 12 columns again once the layout collapses to one section column. Pick values that degrade well: in a `column_span: 2` section, `"columns": 6` gives 4-up on desktop and 2-up on phones; `"columns": 12` gives 2-up on desktop and full-width on phones; `"columns": "full"` is always a full row.
- Give graph/map cards explicit `grid_options` (`"columns": "full"` plus fixed `rows`) so they are never squeezed unreadable in a shared row.
- Responsive show/hide uses the `screen` visibility condition with any CSS media query: `{"condition": "screen", "media_query": "(max-width: 767px)"}`. These are **visibility-targeting examples you choose**, *not* section-reflow thresholds — sections reflow on content width (previous bullet), not on these fixed viewport widths. Convenient values: `(max-width: 767px)`, `(min-width: 768px) and (max-width: 1023px)`, `(min-width: 1024px)`; `(pointer: coarse)` targets touch devices.
- View badges wrap to multiple lines on narrow screens by default; the view `header` supports `"badges_wrap": "scroll"` for a single scrollable row.

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

In sections views, prefer per-card `grid_options` on the section's own 12-column grid (see [Card Sizing and Responsive Layout](#card-sizing-and-responsive-layout)) — it's what the drag-and-drop editor writes. A nested grid card is still useful when a group must stay N-up at every viewport width.

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
| Climate | `climate-hvac-modes`, `climate-fan-modes`, `climate-preset-modes`, `climate-swing-modes`, `climate-swing-horizontal-modes`, `target-temperature`, `target-humidity` |
| Light | `light-brightness`, `light-color-temp`, `light-color-favorites` |
| Cover/Valve | `cover-open-close`, `cover-position`, `cover-position-favorite`, `cover-tilt`, `cover-tilt-position`, `cover-tilt-favorite`, `valve-open-close`, `valve-position`, `valve-position-favorite` |
| Fan | `fan-speed`, `fan-preset-modes`, `fan-direction`, `fan-oscillate` |
| Media | `media-player-playback` (configurable `controls`), `media-player-volume-slider`, `media-player-volume-buttons`, `media-player-source`, `media-player-sound-mode` |
| Weather | `temperature-forecast`, `precipitation-forecast` |
| Generic display | `trend-graph` (history sparkline; `hours_to_show`), `bar-gauge` (`min`/`max`) |
| Generic control | `toggle`, `button` (run an action), `numeric-input` (`style`: `"buttons"`/`"slider"`), `select-options`, `counter-actions`, `date-set` |
| Area card | `area-controls` |
| Domain-specific | `alarm-modes`, `lock-commands`, `lock-open-door`, `vacuum-commands`, `lawn-mower-commands`, `humidifier-modes`, `humidifier-toggle`, `update-actions`, `water-heater-operation-modes` |

Mode-list features accept `style`: `"dropdown"` or `"icons"`. Tile cards also support `features_position`: `"bottom"` (default) or `"inline"`.

**Weather features (2026.6):** `forecast_type` (`daily`/`twice_daily`/`hourly`), `days_to_show`/`hours_to_show`, `show_labels`; `precipitation-forecast` also takes `precipitation_type` (`amount`/`probability`).

**Media features:** `media-player-volume-slider` / `media-player-volume-buttons` accept `show_mute_button` (volume-buttons also `step`); `media-player-playback` `controls:` accepts transport buttons plus `volume_up`, `volume_down`, `volume_mute`, `shuffle`, `repeat`; `media-player-source` takes a `sources:` filter list and `media-player-sound-mode` a `sound_modes:` filter list.

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

Action types: `toggle`, `perform-action`, `more-info`, `navigate`, `url`, `assist`, `none`.

`perform-action` is the renamed `call-service` — existing `action: call-service` configs (and the older `service`/`service_data` keys) still work, so don't flag them as broken; write new ones with `perform-action`.

```json
{
  "tap_action": {
    "action": "perform-action",
    "perform_action": "light.turn_on",
    "target": {"entity_id": "light.kitchen"},
    "data": {"brightness_pct": 40},
    "confirmation": {"text": "Turn on the kitchen?"}
  }
}
```

Templates are not allowed inside actions — call a script instead.

### Visibility Conditions

Cards, sections, and badges all accept `visibility` (a list of conditions, implicitly AND-ed). Supported condition types: `state` (`state`/`state_not`), `numeric_state` (`above`/`below`), `screen` (`media_query`), `user` (`users`), `time` (`after`/`before`/`weekdays`), `location`, and nestable `and`/`or`/`not`.

```json
{
  "visibility": [
    {"condition": "user", "users": ["user_id_hex"]},
    {"condition": "numeric_state", "entity": "sensor.co2", "above": 1000},
    {"condition": "screen", "media_query": "(min-width: 1024px)"}
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

### Themes

Global styling is done with HA **themes** (YAML maps of CSS variables), not raw CSS. Themes are defined under `frontend: themes:` in YAML or installed via HACS, and selected per user (profile) or per view/card with the `theme` option. Define both modes so OS dark/light switching applies cleanly to both:

```yaml
frontend:
  themes:
    my_theme:
      modes:
        dark:
          ha-card-border-radius: "16px"
          primary-color: "#03a9f4"
        light:
          ha-card-border-radius: "16px"
          primary-color: "#0288d1"
```

### Card-mod (Per-Card Styling)

Requires the `card-mod` HACS component. Use sparingly: it patches frontend internals via shadow-DOM selectors, which makes it a frequent source of breakage after HA upgrades — prefer native options and theme variables where they exist, and re-test card-mod styling after every HA update:

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

- **mushroom** — Modern, clean card collection (v5+ aligns with the native tile card; its template card covers Jinja-driven icon/color/content)
- **button-card** — Highly customizable buttons with JS templating
- **mini-graph-card** — Compact graphs; lighter-weight than apexcharts-card
- **card-mod** — CSS styling for any card (see upgrade caveat above)
- **apexcharts-card** — Professional charts; heavy (ships a full charting library), best kept to dedicated analytics views
- **layout-card** — Pre-sections layout control; superseded by sections views for new dashboards, still useful for legacy masonry views

Custom cards predating sections views (early 2024) that haven't updated since are often dormant or superseded by native equivalents — check a repository's release activity before recommending it.

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
          "type": "grid",
          "cards": [{
            "type": "heading",
            "heading": "Quick Actions",
            "icon": "mdi:gesture-tap-button"
          }, {
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
          "type": "grid",
          "cards": [
            {"type": "heading", "heading": "Favorites", "icon": "mdi:star"},
            {"type": "tile", "entity": "light.living_room", "features": [{"type": "light-brightness"}], "grid_options": {"columns": 6}},
            {"type": "tile", "entity": "climate.bedroom", "features": [{"type": "target-temperature"}], "grid_options": {"columns": 6}},
            {"type": "tile", "entity": "lock.front_door", "grid_options": {"columns": 6}}
          ]
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
          "type": "grid",
          "cards": [
            {"type": "heading", "heading": "Living Room", "icon": "mdi:sofa"},
            {"type": "tile", "entity": "light.overhead", "features": [{"type": "light-brightness"}], "grid_options": {"columns": 4}},
            {"type": "tile", "entity": "light.lamp", "features": [{"type": "light-brightness"}], "grid_options": {"columns": 4}},
            {"type": "tile", "entity": "light.accent", "features": [{"type": "light-color-temp"}], "grid_options": {"columns": 4}}
          ]
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
| Section title ignored/flagged | Section `title` is deprecated — use a `heading` card as the section's first card |
| Cards sized with `layout_options` | Deprecated — use `grid_options` (`columns`/`rows`) |
| Map card markers show entity-name initials instead of values | `label_mode` is a **per-entity** option, not card-level: `"entities": [{"entity": "sensor.x", "label_mode": "state"}]` |
| Cards lay out differently in spanned sections | A spanned section's grid widens with it (24 columns in a `column_span: 2` section) but is 12 when collapsed — see [Card Sizing and Responsive Layout](#card-sizing-and-responsive-layout) |
| Map entities missing from map card | Only entities with `latitude`/`longitude` attributes are plotted — use template sensors carrying coordinates as attributes for fixed locations |

---

## Modern Best Practices

- Use **sections** view type with grid-based layouts
- Use **tile** cards as primary card type (replaces legacy entity/light/climate cards)
- Size cards with per-card **`grid_options`** on the section's 12-column grid; reserve nested grid cards for groups that must stay N-up at every width
- Create **multiple views** with explicit `path` slugs (deep-linkable; avoid single-view endless scrolling); use `subview: true` with an explicit `back_path` for drill-down views
- Use **area** cards with navigation for hierarchical organization
- Start sections with **heading** cards (`title`/`subtitle` styles); subtitle headings work well for inline caveats

### Recent Dashboard Features (2026.2–2026.6)

| Feature | Version | Details |
|---------|---------|---------|
| **Distribution card** | 2026.2 | Proportional horizontal bars across multiple entities (power monitoring, storage usage) |
| **Heading button badges** | 2026.2 | `{"type": "button"}` badges on heading cards run actions inline |
| **Section background colors** | 2026.4 | Section `background` accepts `{"color": ..., "opacity": ...}` (or `true`) |
| **Card favorites** | 2026.4 | Light color favorites and cover position favorites display on tile/light cards |
| **Auto-height cards** | 2026.4 | Cards auto-adjust height based on content via the layout editor |
| **Shortcut card + badge** | 2026.5 | One-tap navigate (dashboard/view/area/device), URL, Assist, or action with smart defaults |
| **Media player tile features** | 2026.5 | `media-player-source`, `media-player-sound-mode`, configurable playback `controls` |
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

### Screenshot Caveats

- Test at widths that cross section-column reflow points. Sections views have no fixed pixel breakpoints — column count is computed as `floor((content_width − padding + gap) / (column_min_width + gap))`, clamped to `max_columns`, where `column_min_width` defaults to 320px. So transitions land at roughly 360px (1-col), 700px (2-col), and 1050px (3-col) of **content** width (viewport minus sidebar and padding — add ~256px for an expanded sidebar to get the viewport width). Separately, any `screen` visibility conditions only prove out at the specific widths they target, so also shoot at those.
- History-backed cards (graphs, statistics) hydrate **asynchronously over the websocket** after page load. On instances with slow recorder queries a screenshot can capture charts half-drawn — wait several seconds, or reload and re-shoot, before concluding a chart is broken. A later screenshot that renders fully means the config is fine.
