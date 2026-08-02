# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Skill Format

Every skill is a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: skill-name-here
description: >
  When to activate this skill and what symptoms it addresses.
---
```

Full authoring constraints: `CONTRIBUTING.md`. The one CI cannot catch:
- `metadata.version` must be `0` on new skills — do not edit manually; CI assigns the real version on merge

## Skill Authoring Principles

- **Context window conservation** — only include domain-specific knowledge that agents lack; omit general programming advice
- **Conciseness** — provide patterns and quick-reference tables, not tutorials
- **Consistent terminology** — one term per concept throughout a skill
- **Symptom-based triggering** — the `description` frontmatter should describe observable agent behaviors that signal the skill is needed
- **No tool names** — reference HA REST APIs and concepts, never specific MCP tool names (e.g. `ha_rename_entity`); tool names vary by agent setup

## Validation

To validate locally:

```bash
uvx skills-ref validate skills/<skill-name>
```

## Reviewing Skill PRs

- Judge prose as agent-consumed context, not human docs — the Skill Authoring Principles above are the review bar (e.g. an operator→result lookup table beats narrative bullets, because agents land here holding one case to resolve)
- Skills make version-pinned claims about HA behavior — verify against source at the release tag: `gh api repos/home-assistant/core/contents/<path>?ref=2026.7.4 --jq .content | base64 -d`
- Community PRs come from forks: base-repo `?ref=<pr-branch>` 404s; get the fork with `gh pr view <pr> --json headRepository` and fetch files from there
