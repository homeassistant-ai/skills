# Domain Documentation

To get detailed documentation for any Home Assistant integration or entity domain, fetch from the official docs on demand.

## Fetching Domain Docs

```
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_integrations/{domain}.markdown
```

Replace `{domain}` with the integration name (e.g., `light`, `climate`, `mqtt`).

If the MCP server registers resource URI templates for domain docs, prefer those over raw GitHub fetches.

## Fetching Trigger, Condition, and Action Docs

Since 2026.7, every purpose-specific trigger and condition — and every action — has a dedicated doc page covering what it does, when to use it, its config shape, options, and worked examples. Fetch the page instead of guessing keys or options:

```
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_triggers/{trigger}.markdown
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_conditions/{condition}.markdown
https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_actions/{action}.markdown
```

`{trigger}`/`{condition}`/`{action}` use `<domain>.<name>` (e.g. `motion.detected`, `zone.in_zone`, `light.turn_on`). Rendered pages live at `https://www.home-assistant.io/triggers/<domain>.<name>/` (same pattern for `/conditions/` and `/actions/`). The generic trigger types (`state`, `numeric_state`, `time`, `time_pattern`, `homeassistant`) have pages in the same tree under their bare names.

Caveat: some pages still show the pre-2026.7 trigger `behavior` values `any`/`last`; the current values are `each`/`first`/`all` (conditions keep `any`/`all`).
