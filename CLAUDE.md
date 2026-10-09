# CLAUDE.md

## Repo Layout

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

Every skill is a `SKILL.md` with `name`/`description` frontmatter. Full authoring constraints: `CONTRIBUTING.md`. Two rules to check when editing a skill:
- `metadata.version` must be `"0"` on new skills — do not edit manually; CI assigns the real version on merge and syncs it into `.claude-plugin/plugin.json` (`.version`) and `.claude-plugin/marketplace.json` (`.metadata.version`) — three files, one source of truth
- `description` is capped at 1024 chars and runs close to it — measure the parsed length before adding trigger/symptom bullets: `uvx --from skills-ref agentskills read-properties skills/<skill-name> | jq '.description | length'`. Its first line tells agents to load the skill before answering or exploring; keep that line when trimming, because small models skip the skill without it (`CONTRIBUTING.md` has the numbers)

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

Four more checks gate a merge. CI installs `agnix` from PyPI unpinned, so it and `uvx
agnix@latest` both run the latest release; a new agnix rule can fail a PR that did not cause
it. `lychee` runs as a release binary pinned in `links.yml`; install that version (its release
tag is `lychee-vX.Y.Z`, not `vX.Y.Z`). `claude plugin validate` ships with the Claude Code CLI;
the eval-case checker is in-repo and needs only PyYAML (supplied by `uv run --with`):

```bash
uvx agnix@latest skills/ --target claude-code                         # spec conformance
lychee --offline --include-fragments --no-progress './**/*.md'        # local links + #anchors
claude plugin validate .                                              # plugin manifests
uv run --no-project --with pyyaml python scripts/check_eval_cases.py  # evals/<case>/case.yaml
```

agnix catches what skills-ref's unenforced `metadata: dict[str, str]` annotation lets pass —
e.g. an unquoted integer version, which strict clients refuse. Run it on `skills/`, not `.`:
repo-wide it adds prose heuristics about CLAUDE.md and AGENTS.md that CI leaves out on purpose.
In CI (`links.yml`) lychee runs that same local check on PRs touching `.md`/`.yaml`, plus
external URLs weekly, dot-directories excluded; it cannot see references written as inline
code. `check_eval_cases.py` validates the shape of eval cases against the `claude plugin eval`
1.1 schema. CI does not run `claude plugin eval` (it needs credentials and spends tokens), so
the harness's own parser never sees a case before merge; the schema is transcribed by hand and
needs re-deriving if `schema_version` moves. The checker checks structure only and never runs a
case. Regex graders are compiled with `node`, not Python `re`: the two disagree (`re` rejects
JS-valid `(?<name>x)` and accepts Python-only `(?P<name>x)`), and without `node` that check is
skipped with a warning rather than failed.

`check_ha_examples.py` (`ha-examples.yml`) checks every action, purpose-specific trigger and
condition in the skills' examples against Home Assistant's `services.yaml`, `triggers.yaml`
and `conditions.yaml`: the key exists, every `data:`/`options:` key is a field, and
`behavior` has a valid value. An example with a wrong field is worse than none, because the
agent copies it over what it would otherwise get right. It needs a `home-assistant/core`
checkout; this sparse one is a few MB:

```bash
git clone -q --depth 1 --filter=blob:none --sparse --branch <tag> https://github.com/home-assistant/core <dir>
git -C <dir> sparse-checkout set --no-cone '/homeassistant/components/*/services.yaml' \
  '/homeassistant/components/*/triggers.yaml' '/homeassistant/components/*/conditions.yaml' \
  /homeassistant/helpers/selector.py /homeassistant/const.py
uv run --no-project --with pyyaml python scripts/check_ha_examples.py --ha-core <dir>
```

PRs check against the tag pinned in `ha-examples.yml`; a weekly run checks the latest release.
Bump the pin in two cases. When the weekly run fails, a release changed something an example
uses: fix the example and bump the pin in the same PR. When a new example uses an action,
trigger or field from a release newer than the pin, the PR check reports it as unknown: bump
the pin in that PR. Those YAML files describe HA's UI, and a Python schema can accept keys they
do not list. After confirming in the schema that HA accepts a flagged key, add it to
`scripts/ha_examples_allowlist.yaml` with the reason.

Three things nothing checks, so all three stay review items: that every reference file is still
routed from SKILL.md, that an eval grader still means what it was written to mean, and that the
descriptions in SKILL.md's reference table and README's **Skill Contents** table still match
what the files cover. The last one drifts silently — link checking keeps the *file list* honest
while the prose beside it goes stale, so a row can point at the right file and still describe
an older version of it.

## Evals

Running the suite, comparing results, writing a case, trigger checks and local-model runs are in
[evals/CLAUDE.md](evals/CLAUDE.md). It loads on its own when a session works in `evals/`; read it
before running an eval or testing a `description` change. Three rules hold even without it:

- Every case pins `execution.model: haiku`, and `check_eval_cases.py` rejects anything above Sonnet.
- Cases tagged `holdout`: read their answers only to check the graders and to score, never to design a fix. Change a holdout grader only with source evidence that it is wrong.
- After each Home Assistant release, run the cases tagged `version-pinned` and read the release post's breaking changes.

## Reviewing Skill PRs

- Judge prose as agent-consumed context, not human docs — the Skill Authoring Principles above are the review bar (e.g. an operator→result lookup table beats narrative bullets, because agents land here holding one case to resolve)
- Skills make version-pinned claims about HA behavior — verify against source at the current tag (`gh api repos/home-assistant/core/releases/latest --jq .tag_name`; the plain list includes betas): `gh api repos/home-assistant/core/contents/<path>?ref=<tag> --jq .content | base64 -d`
- Purpose-specific trigger/condition keys and their `options` are listed in core at `homeassistant/components/<domain>/triggers.yaml` (and `conditions.yaml`), which `check_ha_examples.py` reads. The docs repo has one page per key: `gh api "repos/home-assistant/home-assistant.io/contents/source/_triggers?ref=current" --jq '.[].name'` (also `_conditions`, `_actions`)
- UI renames, terminology, and default changes appear only in release blog posts, not core source: `source/_posts/<date>-release-<version>.markdown` in the docs repo (e.g. `2026-08-05-release-20268.markdown`). Fetch it with `gh api`
- **The blog says *what* changed, not *which version* it landed in.** Its prose often implies a feature pre-existed ("X now has conditions to match its triggers") when the whole component is new. Date a feature by fetching its path at the *previous* tag — a 404 at the previous tag that exists at the current one means the whole thing is new
- Codex reviews a PR when it opens or leaves draft, not after a push. For another review, an owner, member or collaborator comments exactly `/review`; a workflow turns that into the `@codex review` request and counts it against the hourly limit
- Community PRs come from forks: base-repo `?ref=<pr-branch>` 404s; get the fork with `gh pr view <pr> --json headRepository` and fetch files from there
- Helper claims need **both** `config_flow.py` (flow submission) and the platform file's `PLATFORM_SCHEMA` (YAML) — they diverge in key names, value types, and which keys exist. Traps: `vol.Required(` usually puts the `CONF_*` on the *next* line, so grep drops fields and mis-attributes Required/Optional; resolve `CONF_*` to its string (`CONF_ROUND_DIGITS` is `"round"` in derivative, `"round_digits"` in min_max); `options_flow`-only fields are rejected at creation
- Verifying a claim confirms what it says, not whether it over-generalizes. Add a pass that tries to disprove ("which helpers does this NOT hold for?"), mechanically where possible — e.g. diff the two schemas' key sets in a script

## Code Review Rules

Codex posts only high-priority findings (P0 and P1) on GitHub. Report each problem below as P1, so it is not dropped:
- An example (action, trigger, condition, field, YAML key) that Home Assistant would reject or that uses a removed key. Agents copy examples over what they would otherwise get right.
- A changed claim about Home Assistant behavior or a version ("since 2026.7", "removed in 2026.5") with no source: core code at a release tag, or the release blog post.
- A reference file that no SKILL.md row routes to, or a SKILL.md or README table row whose description no longer matches its file.
- An MCP tool name (e.g. `ha_rename_entity`) in skill content. Skills name HA APIs and concepts, not tools.
- A renamed HA term used without its old name and the version it changed ("named Developer Tools before 2026.8").
- An eval case outside `evals/<case>/case.yaml`, a regex grader that no longer checks what its name and comment say, or a changed grader in a `holdout` case without source evidence that it was wrong.
- A manual edit to `metadata.version`.
