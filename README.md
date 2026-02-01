# Home Assistant Agent Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-agentskills.io-blue)](https://agentskills.io)

Community-contributed [Agent Skills](https://agentskills.io) for Home Assistant. These skills teach AI agents domain expertise for configuring and controlling Home Assistant, following the open [Agent Skills standard](https://agentskills.io/specification).

## Available Skills

| Skill | Description |
|---|---|
| [home-assistant-best-practices](skills/home-assistant-best-practices/) | Native HA constructs over templates, helper selection, automation modes, Zigbee button patterns, device control best practices, and safe refactoring. |

## Installation

### Agent Skills installer

```bash
npx skills add homeassistant-ai/skills
```

Works with AI coding agents that support the [Agent Skills standard](https://agentskills.io): Claude Code, Cursor, Copilot, VS Code, Gemini CLI, and others. To update: `npx skills update`

### Claude Code plugin

```
/plugin marketplace add homeassistant-ai/skills
/plugin install home-assistant-skills@homeassistant-ai-skills
```

### Claude Desktop / claude.ai

1. Download or clone this repository
2. Zip the skill folder: `cd skills && zip -r home-assistant-best-practices.zip home-assistant-best-practices/`
3. **Settings → Capabilities → Skills → Upload skill** → select the `.zip` file

## Skill Contents

The `home-assistant-best-practices` skill includes:

| File | Purpose |
|------|---------|
| `SKILL.md` | Decision workflow and quick-reference routing |
| `references/safe-refactoring.md` | Safe workflow for renaming entities, replacing helpers, restructuring automations |
| `references/automation-patterns.md` | Native conditions, triggers, waits, automation modes |
| `references/helper-selection.md` | Built-in helpers vs template sensors (with decision matrix) |
| `references/template-guidelines.md` | When templates ARE the right choice |
| `references/device-control.md` | Service calls, entity_id vs device_id, Zigbee buttons |
| `references/examples.yaml` | Compound examples combining multiple best practices |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on writing and submitting skills.

## License

MIT
