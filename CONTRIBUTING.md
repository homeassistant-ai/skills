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
- **`description`** in third person. Describe what the skill does and when to use it. Include keywords that help agents match tasks. Don't summarize the skill's workflow.
- **Body** under 500 lines. Split into reference files if approaching this limit.
- **Reference files** one level deep from SKILL.md—no nested references.
- **Forward slashes** in all file paths.

See Anthropic's [skill authoring best practices](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/best-practices) for additional guidance.

## Guiding Principles

**The context window is a public good.** Only add what the agent doesn't already know. Challenge every paragraph: does its token cost justify its value?

**Concise over verbose.** Claude is smart. Provide domain-specific knowledge and patterns, not general explanations.

**Consistent terminology.** Choose one term for each concept and stick to it throughout the skill.

## Reporting Skill Problems

When a skill misleads your agent — broken dashboards, failed automations, wrong configurations — first search existing issues for the same skill and failure. If a matching issue exists, react with thumbs-up or comment with additional context. Otherwise, open a new issue with the **Report Bad Skill Advice** template. Let the agent fill it out — it holds the full context and can trace the failure to its source in the skill.

The template covers five sections: context, timeline, root cause, impact, and environment. A thorough report gives maintainers everything they need to fix the skill in one pass.

## Submitting a Skill

1. Fork this repository.
2. Create a folder under `skills/` with your skill name.
3. Write a `SKILL.md` following the format above.
4. Test your skill with real scenarios.
5. Submit a pull request describing what your skill teaches and what problems it solves.
