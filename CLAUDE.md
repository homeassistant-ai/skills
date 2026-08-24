# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo Layout

One skill lives under `skills/<name>/`: `SKILL.md` plus `references/` (one level deep only),
and optional `scripts/`/`assets/`. `docs/plans/` is gitignored scratch space.

Eval cases live in a top-level `evals/<case>/case.yaml`, **not** under `skills/`. `claude
plugin eval` rejects any eval directory whose first segment names a loaded component directory
(`commands`, `skills`, `agents`, `hooks`, `themes`, `output-styles`, `monitors`, `workflows`,
`bin`) — and rejects it *softly*: it warns, falls back to the default `evals/`, and finds
nothing, so cases in the wrong place silently never run. `evals/` at the plugin root is the
default and needs no `experimental.evals` key.

**SKILL.md is in context on every trigger; `references/` load only when read.** That is why
SKILL.md body size is capped and why domain-niche content belongs in a reference file behind
a single routing row, not in the always-loaded table.

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
- `metadata.version` must be `"0"` on new skills — do not edit manually; CI assigns the real version on merge and syncs it into `.claude-plugin/plugin.json` (`.version`) and `.claude-plugin/marketplace.json` (`.metadata.version`) — three files, one source of truth
- `description` is capped at 1024 chars and runs close to it — measure the parsed length before adding trigger/symptom bullets

## Skill Authoring Principles

The wording of these content-quality principles is mirrored in `CONTRIBUTING.md`
(contributors); each file also carries guidance the other omits. When you change a shared
principle, change both — they have drifted before.

- **Context window conservation** — keep what is HA-specific, cut general programming advice; the test is the content itself, not whether a given model already knows it (skills run on frontier and small local models alike)
- **Conciseness** — provide patterns and quick-reference tables, not tutorials
- **Consistent terminology** — one term per concept throughout a skill; contrasting code blocks are `# WRONG — why` / `# RIGHT — why` (emoji only in table status columns). A renamed HA term uses the new name and cites the old one with its version ("named Developer Tools before 2026.8") — never a bare swap, since readers on older releases still see the old label
- **Symptom-based triggering** — the `description` frontmatter should describe observable agent behaviors that signal the skill is needed
- **No tool names** — reference HA REST APIs and concepts, never specific MCP tool names (e.g. `ha_rename_entity`); tool names vary by agent setup

## Validation

To validate locally:

```bash
uvx --from skills-ref agentskills validate skills/<skill-name>
```

Four more checks gate a merge. `agnix` and `lychee` run as release binaries pinned in
`.github/workflows/` — install those versions (lychee's release tag is `lychee-vX.Y.Z`, not
`vX.Y.Z`); `claude plugin validate` ships with the Claude Code CLI; the eval-case checker is
in-repo and needs only PyYAML:

```bash
agnix skills/ --target claude-code                              # spec conformance
lychee --offline --include-fragments --no-progress './**/*.md'  # local links + #anchors
claude plugin validate .                                        # plugin manifests
python scripts/check_eval_cases.py                              # evals/<case>/case.yaml
```

agnix catches what skills-ref's unenforced `metadata: dict[str, str]` annotation lets pass —
e.g. an unquoted integer version, which strict clients refuse. In CI (`links.yml`) lychee runs
that same local check on PRs touching `.md`/`.yaml`, plus external URLs weekly, dot-directories
excluded; it cannot see references written as inline code. `check_eval_cases.py` validates the
shape of eval cases against the `claude plugin eval` 1.1 schema — that command is gated behind
early access, so its own parser never runs here; the schema is transcribed by hand and needs
re-deriving if `schema_version` moves. It checks structure only and never runs a case. Regex
graders are compiled with `node`, not Python `re`: the two disagree (`re` rejects JS-valid
`(?<name>x)` and accepts Python-only `(?P<name>x)`), and without `node` that check is skipped
with a warning rather than failed.

Four things nothing checks, so all four stay review items: that every reference file is
still routed from SKILL.md, that `references/examples.yaml` still parses, that an eval
grader still means what it was written to mean, and that the descriptions in SKILL.md's
reference table and README's **Skill Contents** table still match what the files cover.
The last one drifts silently — link checking keeps the *file list* honest while the prose
beside it goes stale, so a row can point at the right file and still describe an older
version of it.

## Reviewing Skill PRs

- Judge prose as agent-consumed context, not human docs — the Skill Authoring Principles above are the review bar (e.g. an operator→result lookup table beats narrative bullets, because agents land here holding one case to resolve)
- Skills make version-pinned claims about HA behavior — verify against source at the current tag (`gh api repos/home-assistant/core/releases --jq '.[0].tag_name'`): `gh api repos/home-assistant/core/contents/<path>?ref=<tag> --jq .content | base64 -d`
- Purpose-specific trigger/condition keys aren't enumerable from core source — list them from the docs repo: `gh api "repos/home-assistant/home-assistant.io/contents/source/_triggers?ref=current" --jq '.[].name'` (also `_conditions`, `_actions`)
- UI renames, terminology, and default changes appear only in release blog posts, not core source: `source/_posts/<date>-release-<version>.markdown` in the docs repo (e.g. `2026-08-05-release-20268.markdown`). Use `gh api` — plain `curl` is sandboxed here and returns empty
- **The blog says *what* changed, not *which version* it landed in.** Its prose often implies a feature pre-existed ("X now has conditions to match its triggers") when the whole component is new. Date a feature by fetching its path at the *previous* tag — a 404 at the previous tag that exists at the current one means the whole thing is new
- Community PRs come from forks: base-repo `?ref=<pr-branch>` 404s; get the fork with `gh pr view <pr> --json headRepository` and fetch files from there
- Helper claims need **both** `config_flow.py` (flow submission) and the platform file's `PLATFORM_SCHEMA` (YAML) — they diverge in key names, value types, and which keys exist. Traps: `vol.Required(` usually puts the `CONF_*` on the *next* line, so grep drops fields and mis-attributes Required/Optional; resolve `CONF_*` to its string (`CONF_ROUND_DIGITS` is `"round"` in derivative, `"round_digits"` in min_max); `options_flow`-only fields are rejected at creation
- Verifying a claim confirms what it says, not whether it over-generalizes. Add a pass that tries to disprove ("which helpers does this NOT hold for?"), mechanically where possible — e.g. diff the two schemas' key sets in a script
