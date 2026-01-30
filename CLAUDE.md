# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a community-contributed collection of **Agent Skills** for Home Assistant, following the open [Agent Skills standard](https://agentskills.io/specification). Skills teach AI agents domain expertise for configuring and controlling Home Assistant. The repository doubles as a Claude Code plugin (see `.claude-plugin/plugin.json`).

## Repository Structure

- `skills/<skill-name>/SKILL.md` — each skill lives in its own folder with a `SKILL.md` file
- `CONTRIBUTING.md` — skill authoring guidelines and submission workflow
- `.claude-plugin/plugin.json` — Claude Code plugin metadata

## Skill Format

Every skill is a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: skill-name-here
description: >
  When to activate this skill and what symptoms it addresses.
---
```

Constraints from CONTRIBUTING.md:
- Max **500 lines** per SKILL.md
- Reference files must be **one level deep** only (e.g. `references/example.yaml`)
- Use **forward slashes** in all file paths
- Optional subdirectories: `references/` (additional docs), `scripts/` (utility scripts)

## Skill Authoring Principles

- **Context window conservation** — only include domain-specific knowledge that agents lack; omit general programming advice
- **Conciseness** — provide patterns and quick-reference tables, not tutorials
- **Consistent terminology** — one term per concept throughout a skill
- **Symptom-based triggering** — the `description` frontmatter should describe observable agent behaviors that signal the skill is needed

## Validation

CI runs `skills-ref validate` on every PR and push to `main` that touches `skills/**`. To validate locally:

```bash
pip install skills-ref
python -m skills_ref.cli validate skills/<skill-name>
```
