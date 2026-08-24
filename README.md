# Home Assistant Agent Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-agentskills.io-blue)](https://agentskills.io)

An **Agent Skill** is a plugin that teaches AI coding agents best practices for a specific technology, delivered as a portable Markdown knowledge pack.

This repository provides an Agent Skill for Home Assistant, following the open [Agent Skills standard](https://agentskills.io/specification). Install a skill and your agent gains Home Assistant best practices that persist across sessions.

## Included Skill

**[home-assistant-best-practices](skills/home-assistant-best-practices/):** Native HA constructs over templates, helper selection, automation modes, button and remote patterns, device control, scenes, blueprints, YAML-only integration management, dashboard configuration, AppDaemon apps, backups and recovery, and safe refactoring.

## Installation

### Agent Skills installer

Requires [Node.js 22.20+](https://nodejs.org/).

```bash
npx skills add homeassistant-ai/skills
```

Works with AI coding agents that support the [Agent Skills standard](https://agentskills.io): Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and 70+ others. To update: `npx skills update`

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
3. Select or enter `homeassistant-ai/skills` (or the full URL, `https://github.com/homeassistant-ai/skills`) → Sync

This installs the skill as a plugin synced from this repo — no download or zip needed. **Sync automatically** is on by default, so later updates arrive on their own.

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
| [`SKILL.md`](skills/home-assistant-best-practices/SKILL.md) | Decision workflow and quick-reference routing |
| [`references/safe-refactoring.md`](skills/home-assistant-best-practices/references/safe-refactoring.md) | Safe workflow for renaming entities, replacing helpers, restructuring automations; config-entry and storage-dashboard blind spots |
| [`references/automation-patterns.md`](skills/home-assistant-best-practices/references/automation-patterns.md) | Purpose-specific and native triggers/conditions, waits, variables, automation modes, control flow (choose, repeat, parallel), disabling automations |
| [`references/helper-selection.md`](skills/home-assistant-best-practices/references/helper-selection.md) | Built-in helpers vs template sensors (with decision matrix) |
| [`references/template-guidelines.md`](skills/home-assistant-best-practices/references/template-guidelines.md) | When to use templates, when to avoid them, sensor best practices, reusable `custom_templates` macros |
| [`references/yaml-only-integrations.md`](skills/home-assistant-best-practices/references/yaml-only-integrations.md) | YAML-only integration types, post-edit actions (reload vs restart) |
| [`references/device-control.md`](skills/home-assistant-best-practices/references/device-control.md) | Actions and targeting, entity_id vs device_id, buttons and remotes, domain-specific patterns |
| [`references/scenes.md`](skills/home-assistant-best-practices/references/scenes.md) | Scene authoring: config shape, snapshot/restore, snapshot-vs-script distinction |
| [`references/dashboard-guide.md`](skills/home-assistant-best-practices/references/dashboard-guide.md) | Dashboard layout, view types, strategies, sections, cards, badges, custom cards, CSS styling, HACS |
| [`references/dashboard-cards.md`](skills/home-assistant-best-practices/references/dashboard-cards.md) | Card type lookup and card-specific documentation |
| [`references/domain-docs.md`](skills/home-assistant-best-practices/references/domain-docs.md) | Integration and domain documentation (actions, entity attributes); doc pages for specific triggers, conditions, and actions |
| [`references/examples.yaml`](skills/home-assistant-best-practices/references/examples.yaml) | Compound examples combining multiple best practices |
| [`references/appdaemon.md`](skills/home-assistant-best-practices/references/appdaemon.md) | AppDaemon apps: when to use vs. native HA, app structure, actions, scheduling, error handling, safe refactoring impact |
| [`references/blueprint-guide.md`](skills/home-assistant-best-practices/references/blueprint-guide.md) | Blueprint authoring: metadata & `source_url`, inputs & selectors, `target` vs `entity`, defaults, `!input` templating, versioning |
| [`references/backups.md`](skills/home-assistant-best-practices/references/backups.md) | Full instance backups vs rolling one object back, when an operation needs a backup first, what an archive contains, encryption keys, restore verification, backup deletion |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on writing and submitting skills.

## License

MIT
