# Home Assistant Agent Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-agentskills.io-blue)](https://agentskills.io)

An **Agent Skill** is a plugin that teaches AI coding agents best practices for a specific technology, delivered as a portable Markdown knowledge pack.

This repository provides an Agent Skill for Home Assistant, following the open [Agent Skills standard](https://agentskills.io/specification). Install a skill and your agent gains Home Assistant best practices that persist across sessions.

## Included Skill

**[home-assistant-best-practices](skills/home-assistant-best-practices/):** Native HA constructs over templates, helper selection, automation modes, Zigbee button patterns, device control best practices, YAML-only integration management, dashboard configuration, and safe refactoring.

## Installation

### Agent Skills installer

Requires [Node.js 18+](https://nodejs.org/).

```bash
npx skills add homeassistant-ai/skills
```

Works with AI coding agents that support the [Agent Skills standard](https://agentskills.io): Claude Code, Cursor, Copilot, VS Code, Gemini CLI, and others. To update: `npx skills update`

### Claude Code plugin

Run each command separately inside Claude Code:

```
/plugin marketplace add homeassistant-ai/skills
```
```
/plugin install home-assistant-skills@home-assistant-skills
```

Run `/reload-plugins` or restart Claude Code for the skill to take effect.

### Claude Desktop / claude.ai

Both apps share the same Customize UI, reached via the left sidebar (Claude Desktop) or [claude.ai/customize](https://claude.ai/customize) (browser).

1. Enable code execution: Settings → Capabilities → turn on **Cloud code execution and file creation** (required for skills)
2. Customize → Plugins → Add → Add marketplace → Add from a repository
3. Enter `homeassistant-ai/skills` (or the full URL, `https://github.com/homeassistant-ai/skills`) → Sync

This installs the skill as a plugin synced from this repo — no download or zip needed. To update later, go to Plugins, click the `skills` marketplace tag, open its `⋯` menu, and choose **Check for updates** (or toggle **Sync automatically**).

<details>
<summary>Alternative: upload the skill manually as a zip</summary>

1. Enable code execution: Settings → Capabilities → turn on **Cloud code execution and file creation**
2. Download or clone this repository
3. Zip the skill folder: `cd skills && zip -r home-assistant-best-practices.zip home-assistant-best-practices/`
4. Customize → Skills → Add → Upload a skill

</details>

## Skill Contents

The `home-assistant-best-practices` skill includes:

| File | Purpose |
|------|---------|
| `SKILL.md` | Decision workflow and quick-reference routing |
| `references/safe-refactoring.md` | Safe workflow for renaming entities, replacing helpers, restructuring automations |
| `references/automation-patterns.md` | Native conditions, triggers, waits, automation modes |
| `references/helper-selection.md` | Built-in helpers vs template sensors (with decision matrix) |
| `references/template-guidelines.md` | When to use templates, when to avoid them, and sensor best practices |
| `references/yaml-only-integrations.md` | YAML-only integration types, post-edit actions (reload vs restart) |
| `references/device-control.md` | Service calls, entity_id vs device_id, Zigbee buttons |
| `references/scenes.md` | Scene authoring: config shape, snapshot/restore, snapshot-vs-script distinction |
| `references/dashboard-guide.md` | Dashboard layout, view types, sections, custom cards, CSS styling |
| `references/dashboard-cards.md` | Card type lookup and card-specific documentation |
| `references/domain-docs.md` | Integration and domain documentation for service calls, entity attributes |
| `references/examples.yaml` | Compound examples combining multiple best practices |
| `references/appdaemon.md` | AppDaemon apps: when to use vs. native HA, app structure, service calls, scheduling, error handling, safe refactoring impact |
| `references/blueprint-guide.md` | Blueprint authoring: metadata & `source_url`, inputs & selectors, `target` vs `entity`, defaults, `!input` templating, versioning |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on writing and submitting skills.

## License

MIT
