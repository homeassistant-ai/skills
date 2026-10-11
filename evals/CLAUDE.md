# Evals

Run the commands here from the repo root, except the trigger check, which runs from an empty
directory.

## Running the suite

To run the eval suite, use `claude plugin eval . --trust-plugin -j 4 --judge-model sonnet`.
Every case pins `execution.model: haiku`, and `check_eval_cases.py` accepts only Haiku or
Sonnet: unpinned, a case runs on the session's model, and a larger model costs more and can hide
what the skill adds. With the skill, Sonnet 5.5 scored 1.00 on all 28 cases in one run each, so
it can show a regression but not an improvement; Haiku 5.5 scored 0.96 and a run costs about a
fifth as much. Run a second pass with `--model sonnet`, which overrides the pin, to tell a gap
in the skill from a limit of the small model. Haiku does not stand in for small local models:
check those with `scripts/local_model_eval.py`, which runs only cases with a regex grader, so
an llm-only case needs one added first.
Sessions run one at a time by default; `-j 4` runs four at once on the same rate limit. The
default Haiku judge failed correct answers often enough to swamp run-to-run noise (seen in
September 2026, not rechecked on Haiku 5.5). A full run is
every case x 3 runs x 2 arms (with and without the skill), so start with `--tag smoke --runs 1
--ablation none`. `--json evals/results/<name>.json` writes the results JSON (the directory is
git-ignored), and `--no-publish` keeps the HTML report local; by default it is published to
claude.ai when the account supports it. Add `--keep-temp` to keep the transcripts; without it
only scores survive, plus the final answers that llm graders quote. A regex-only case keeps no
answer at all. With it, each run's `tracePath` in the results JSON points at its transcript.
Read, Glob and Grep are denied unless a case grants them in `allowed_tools`, and without them
only SKILL.md loads, so no change to `references/` can move a score. Every case grants exactly
those three, and `check_eval_cases.py` enforces it.

With `--ablation none` (skill arm only) `skill-fired` counts toward the score; leave it out when
comparing with a two-arm run. Exit code 1 means a case scored below the pass mark, not a failed
session. Before acting on a one-run drop, rerun with `--case <name> --runs 3`.

## Comparing results

The results JSON records only aliases: each case's `haiku` pin, `--model` and `--judge-model`.
An alias moves to a newer model on a release, so two results files with the same alias can
come from different models. `python scripts/eval_models.py <results.json>` prints the model
IDs the runs used, read from their transcripts, so it needs a `--keep-temp` run and exits 1
when a transcript is missing. The judge's model is recorded nowhere. Compare two results files
only when they show the same model IDs; after a release, rerun `main` as the new baseline.

## Writing a case

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

## Holdout cases

Cases tagged `holdout` check that a skill fix generalizes: each tests a fixed behavior in a
scenario no fix was written from, and also fails the fix applied where it does not belong.
Read their answers only to check the graders and to score, never to design a fix; if one
exposes a gap, confirm the fix on a new case, not the same one. Change a holdout grader only
with source evidence that it is wrong, never because of which arm it helps. The five cases
held out in the first hillclimb (timer, button-event, media-player, template-attributes,
avg-temperature) were used for tuning since and are no longer a test set.

## After a Home Assistant release

After each Home Assistant release, run the cases tagged `version-pinned` (`--tag
version-pinned`, keeping `--judge-model sonnet` for `arrive-home-automation`'s llm graders) and
read the release post's breaking changes. Together they cover what `check_ha_examples.py`
cannot see: renamed UI terms, changed behavior, claims in prose, and whether the skill still
steers the model right.

## Trigger check

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

If a plugin stays loaded, `--setting-sources project` drops all user-level plugins; the `init`
record's `skills` list shows what loaded. Run a prompt three times to get a rate. To test another
description, copy `.claude-plugin/` and `skills/` (plus `evals/` for `claude plugin eval <dir>`),
edit the copy and pass it as `--plugin-dir`. `local_model_eval.py --skill-dir` needs the whole
skill folder, `references/` included.

## Local models

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

`scripts/summarise_runs.py` adds up those per-run files by label: for the command above run
`python scripts/summarise_runs.py --out evals/results/<name> --label baseline,post`, which prints
both arms' mean score, per-grader pass rate, and reads rate (fraction of runs that loaded the skill).

ha-mcp blocks writes until the call carries a key found only in the served skill (`strict_bps.py`,
on by default), and no eval reaches that gate. So a low load rate describes questions, text
answers and plugin installs, not ha-mcp writes.
