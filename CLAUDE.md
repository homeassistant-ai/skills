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

To run the eval suite, use `claude plugin eval . --trust-plugin -j 4 --judge-model sonnet`.
Every case pins `execution.model: sonnet`, and `check_eval_cases.py` accepts only Sonnet or
Haiku: unpinned, a case runs on the session's model, and Opus costs more and can hide what the
skill adds. Run a second pass with `--model haiku`, which overrides the pin; the skill has to
work on small models too, and a larger model can cover a gap in the skill that Haiku shows.
When the `haiku` alias points to a model older than current small models, check a failure only
Haiku shows on a current one before it drives a skill change. `scripts/local_model_eval.py` runs
only cases with a regex grader, so an llm-only case needs one added first.
Sessions run one at a time by default; `-j 4` runs four at once on the same rate limit. The
default Haiku judge fails correct answers often enough to swamp run-to-run noise. A full run is
every case x 3 runs x 2 arms (with and without the skill), so start with `--tag smoke --runs 1
--ablation none`. `--json evals/results/<name>.json` writes the results JSON (the directory is
git-ignored), and `--no-publish` keeps the HTML report local; by default it is published to
claude.ai when the account supports it. Add `--keep-temp` to keep the transcripts; without it
only scores survive, plus the final answers that llm graders quote. A regex-only case keeps no
answer at all. With it, each run's `tracePath` in the results JSON points at its transcript.
Read, Glob and Grep are denied unless a case grants them in `allowed_tools`, and without them
only SKILL.md loads, so no change to `references/` can move a score. Every case grants exactly
those three, and `check_eval_cases.py` enforces it.

The results JSON records only aliases: each case's `sonnet` pin, `--model` and `--judge-model`.
An alias moves to a newer model on a release, so two results files with the same alias can
come from different models. `python scripts/eval_models.py <results.json>` prints the model
IDs the runs used, read from their transcripts, so it needs a `--keep-temp` run and exits 1
when a transcript is missing. The judge's model is recorded nowhere. Compare two results files
only when they show the same model IDs; after a release, rerun `main` as the new baseline.

Writing a case:
- Regex graders read only the final message (`last_message`), so text the skill loads cannot
  satisfy them, but a closing question scores zero. Put in the prompt whatever the agent would
  otherwise ask for: an entity ID, a floor name, that the vacuum's rooms are already mapped.
- Prefer a positive regex (the new key is present) over `not_contains` on the old one: the skill
  tells agents to cite an old name beside the new one ("named add-ons before 2026.2"), and a
  negative check fails that.
- Check structure with a regex and keep the llm judge for meaning. The Sonnet judge failed
  correct YAML in four graders (a `motion.detected` trigger line, a `floor_id` target); a
  regex on the key line cannot misread it.
- To run several cases together, give them a tag: a repeated `--case` keeps only the last one.
- Read both arms. A case that scores lower with the skill than without means the skill teaches
  something wrong; the `vacuum.clean_area` example once did.

Cases tagged `holdout` check that a skill fix generalizes: each tests a fixed behavior in a
scenario no fix was written from, and also fails the fix applied where it does not belong.
Read their answers only to check the graders and to score, never to design a fix; if one
exposes a gap, confirm the fix on a new case, not the same one. Change a holdout grader only
with source evidence that it is wrong, never because of which arm it helps. The five cases
held out in the first hillclimb (timer, button-event, media-player, template-attributes,
avg-temperature) were used for tuning since and are no longer a test set.

After each Home Assistant release, run the cases tagged `version-pinned` (`--tag
version-pinned`, keeping `--judge-model sonnet` for `arrive-home-automation`'s llm graders) and
read the release post's breaking changes. Together they cover what `check_ha_examples.py`
cannot see: renamed UI terms, changed behavior, claims in prose, and whether the skill still
steers the model right.

To check that a single prompt triggers the skill without an eval run, run it in a fresh
session from an empty directory and look for the `Skill` call in the stream:

```bash
claude -p "<prompt>" --plugin-dir <repo-root> --output-format stream-json --verbose --max-turns 1 --allowedTools Skill
```

`--max-turns 1` is enough — the call appears in the first response — so a check is one API
call (~25k tokens of system prompt and skill descriptions; `--model haiku` is the cheapest and
also the stricter test). `--plugin-dir` tests the working tree, not the installed plugin,
which may be releases behind. Disable other plugins for the run (`--settings` with an
`enabledPlugins` map): a plugin hook that orders skill use makes any prompt pass. The `Base
directory for this skill:` line in the output confirms which copy loaded. From inside a
Claude Code session, prefix `env -u CLAUDECODE` or the nested `claude` refuses to start.

`scripts/local_model_eval.py` runs cases against a local model the way ha-mcp serves the
skill: one `ha_get_skill_guide` tool on an OpenAI-compatible endpoint (LM Studio, llama.cpp,
Ollama), without Claude Code's system prompt filling a small context. It scores only the regex
graders, so its numbers do not compare with `claude plugin eval`; use it to compare two skill
versions (`--skill-dir`) on the same model. Set `--ctx-limit` just under the loaded context:
some servers crash on overflow instead of erroring. Its ha-mcp texts are copied from
`server.py` at the commit its docstring names; re-copy them when that file changes. It needs
`node`, like the case checker:

```bash
uv run --no-project --with pyyaml python scripts/local_model_eval.py --model <model> \
  --all-regex --runs 3 --out evals/results/<name>
```

## Reviewing Skill PRs

- Judge prose as agent-consumed context, not human docs — the Skill Authoring Principles above are the review bar (e.g. an operator→result lookup table beats narrative bullets, because agents land here holding one case to resolve)
- Skills make version-pinned claims about HA behavior — verify against source at the current tag (`gh api repos/home-assistant/core/releases/latest --jq .tag_name`; the plain list includes betas): `gh api repos/home-assistant/core/contents/<path>?ref=<tag> --jq .content | base64 -d`
- Purpose-specific trigger/condition keys and their `options` are listed in core at `homeassistant/components/<domain>/triggers.yaml` (and `conditions.yaml`), which `check_ha_examples.py` reads. The docs repo has one page per key: `gh api "repos/home-assistant/home-assistant.io/contents/source/_triggers?ref=current" --jq '.[].name'` (also `_conditions`, `_actions`)
- UI renames, terminology, and default changes appear only in release blog posts, not core source: `source/_posts/<date>-release-<version>.markdown` in the docs repo (e.g. `2026-08-05-release-20268.markdown`). Use `gh api` — plain `curl` is sandboxed here and returns empty
- **The blog says *what* changed, not *which version* it landed in.** Its prose often implies a feature pre-existed ("X now has conditions to match its triggers") when the whole component is new. Date a feature by fetching its path at the *previous* tag — a 404 at the previous tag that exists at the current one means the whole thing is new
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
