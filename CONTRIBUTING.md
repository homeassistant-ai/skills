# Contributing

Skills for this repository follow the [Agent Skills open standard](https://agentskills.io). See the [specification](https://agentskills.io/specification) for the full format reference.

## Skill Format

Structure each skill as a folder under `skills/` with a `SKILL.md` file:

```
skills/
  your-skill-name/
    SKILL.md              # Required
    references/           # Optional: additional docs loaded on demand
    scripts/              # Optional: utility scripts
    assets/               # Optional: static resources (templates, data files)
```

### SKILL.md requirements

- **YAML frontmatter** with `name` (letters, numbers, hyphens only; 64 chars max) and `description` (1024 chars max).
- **`metadata.version`** a monotonically incrementing integer written as a string (e.g. `"1"`) — the spec requires metadata values to be strings. Set to `0` when creating a new skill — CI assigns the real version automatically on merge. Do not edit this field manually.
- **`description`** in third person. Describe what the skill does and when to use it. Include keywords that help agents match tasks. Don't summarize the skill's workflow. Err toward over-triggering rather than under-triggering — a skill that loads when marginally relevant costs tokens; one that fails to load costs a wrong answer. Explicit `TRIGGER THIS SKILL WHEN` and `SYMPTOMS` sections listing observable agent behaviours match better than prose.
- **Body** under 500 lines. Split into reference files if approaching this limit.
- **Reference files** one level deep from SKILL.md—no nested references.
- **Cross-reference them with markdown links**, not inline code — CI validates both the path and the `#anchor`. Links resolve relative to the containing file, so inside `references/` a sibling is `x.md`, not `references/x.md`.
- **Forward slashes** in all file paths.
- **Bundled scripts**, if any, must be introduced by SKILL.md — when to reach for them and how to invoke them. An unreferenced script is dead weight the agent never finds.

See Anthropic's [skill authoring best practices](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/best-practices) for additional guidance.

## Guiding Principles

**The context window is a public good.** Every line is loaded on every invocation, by every agent. Challenge each paragraph: does its token cost justify its value?

**Domain-specific, not general.** The test is whether the knowledge is Home Assistant-specific — *not* whether a model already knows it. These skills install into agents ranging from frontier models to small local ones, so "the model knows this" is not something a reviewer can evaluate, and it is the wrong question anyway. Keep HA behaviour, version-pinned changes, and anywhere HA diverges from what the general syntax implies (`state_attr` returning `None` rather than an undefined, the `unavailable`/`unknown` sentinel states). Cut general programming tutorials, and text that only restates an identifier.

**Concise over verbose.** Provide patterns and quick-reference tables, not narrative explanations.

**Consistent terminology.** Choose one term for each concept and stick to it throughout the skill. Contrasting code blocks are marked `# WRONG — why` and `# RIGHT — why`, in that order; do not introduce AVOID/CORRECT, BAD/GOOD, or ❌/✅ variants. Reserve ❌/✅ for table status columns.

**Renamed HA terms keep a pointer to the old name.** When HA renames something user-facing, use the new term and note the old one with the version it changed in — `**Tools → Events** (named **Developer Tools** before 2026.8)`. Readers on older releases still see the old label in their UI, so a bare swap strands them. This has come up three times in two years: services → actions (2024.8), add-ons → Apps (2026.2), Developer Tools → Tools (2026.8).

**Explain the *why*, not bare commands.** A rule an agent understands survives paraphrase and transfers to the next case; a bare MUST/NEVER gets dropped the moment the situation differs slightly. Give the mechanism — *`device_id` breaks on re-add* beats *never use `device_id`*.

**Don't couple skills to specific tool names.** Reference HA concepts and REST APIs instead of naming specific MCP tools (e.g. `ha_rename_entity`, `ha_get_integration`). Tool names change and not all agents have the same toolset; the underlying HA APIs and concepts are stable.

**No opinionated conventions.** Skills in this repo are applied to any HA installation. Naming conventions, code style preferences, and other user-space opinions belong in a personal skill or instance-level `CLAUDE.md`, not here. Only include guidance that reflects official HA behaviour or well-established community consensus.

## Reporting Skill Problems

When a skill misleads your agent — broken dashboards, failed automations, wrong configurations — first search existing issues for the same skill and failure. If a matching issue exists, react with thumbs-up or comment with additional context. Otherwise, open a new issue with the **Report Bad Skill Advice** template. Let the agent fill it out — it holds the full context and can trace the failure to its source in the skill.

The template covers five sections: context, timeline, root cause, impact, and environment. A thorough report gives maintainers everything they need to fix the skill in one pass.

## Submitting a Skill

1. Fork this repository.
2. Create a folder under `skills/` with your skill name.
3. Write a `SKILL.md` following the format above.
4. Test your skill with real scenarios.
5. If you added or removed reference files, link them from `SKILL.md`'s reference table and update the **Skill Contents** table in `README.md`. CI checks that links resolve, but nothing detects a reference file that nothing links to.
6. Submit a pull request describing what your skill teaches and what problems it solves.
