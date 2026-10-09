#!/usr/bin/env python3
"""Summarise local_model_eval runs by label: ingestion (`reads`) rate and mean
score / per-grader pass (the "does the change matter" view).

`local_model_eval.py` writes one <case>-<label>-r<n>.json per run, each carrying a
`label`, a `model`, a `score`, a `graders` map of boolean grader verdicts, and a
`reads` list of files the model loaded. This groups those runs by their `label`
field and prints, for each label: how many runs there were, the reads rate (what
fraction actually loaded the skill — a change can fix the answer while silently
breaking ingestion), the mean score with per-run scores, per-grader pass counts,
and any distinct error values. Run one invocation with `--label baseline,post` to
print both arms together and read the delta across BOTH dimensions; there is no
separate compare tool because the delta is meant to be judged by a human on both.

Grader verdicts are counted as stored: `local_model_eval.grade()` already returns
the correct truth value for both `contains` and `not_contains` graders, so nothing
is flipped.

Usage: python scripts/summarise_runs.py [--case <case> ...] [--out DIR] \
      [--label baseline,post] [--model <substr>]

DIR defaults to `evals/results`; pass the producer's own --out directory here
(e.g. `--out evals/results/<name>`) so the summarizer finds the runs it wrote.
With no --case it summarises every case found in DIR. Exits non-zero when a
requested case has no runs or a requested label is missing, so CI fails too.
"""
import argparse
import glob
import json
import os
import sys
from collections import defaultdict


def _emit(label, runs):
    """Print one label/arm's ingestion and score stats."""
    run_count = len(runs)
    loaded = sum(1 for run in runs if "SKILL.md" in (run.get("reads") or []))
    reads_rate = loaded / run_count if run_count else float("nan")
    mean_score = sum(run.get("score", 0) for run in runs) / run_count if run_count else float("nan")
    grades = defaultdict(lambda: [0, 0])
    for run in runs:
        for grader_name, verdict in (run.get("graders") or {}).items():
            grades[grader_name][0] += 1 if verdict else 0
            grades[grader_name][1] += 1
    errors = sorted({run.get("error") for run in runs if run.get("error")})
    model_seen = next((run.get("model") for run in runs if run.get("model")), "?")
    print(f"=== {label}   runs={run_count}   model={model_seen}")
    print(f"   reads_rate(SKILL loaded) = {loaded}/{run_count} = {reads_rate:.3f}" if run_count else "   (no runs)")
    print(f"   mean score = {mean_score:.3f}   scores={[round(run.get('score', 0), 2) for run in runs]}" if run_count else "")
    for grader_name, (pass_count, total_count) in sorted(grades.items()):
        print(f"     {grader_name}: {pass_count}/{total_count} pass = {(pass_count / total_count if total_count else 0):.3f}")
    if errors:
        print("   ERRORS:", ", ".join(errors))


def summarise(case, out, labels, model_filter) -> int:
    """Group the case's runs by label, print per-label stats, return exit status."""
    found = {}
    for file_path in sorted(glob.glob(os.path.join(out, f"{case}-*-r*.json"))):
        try:
            record = json.load(open(file_path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            print(f"  skip {os.path.basename(file_path)}: {error}")
            continue
        run_label = record.get("label")
        if not run_label or (labels and run_label not in labels):
            continue
        if record.get("case") != case:
            continue
        model = record.get("model") or ""
        if model_filter and model_filter not in model:
            continue
        found.setdefault(run_label, []).append(record)

    if not found:
        print(f"no runs for case {case!r} in {out}")
        return 1

    missing = [label for label in (labels or []) if label not in found]
    if missing:
        print("missing requested labels:", ", ".join(missing))
        return 1

    for run_label in sorted(found):
        runs = found[run_label]
        group_models = sorted({(run.get("model") or "<no-model>") for run in runs})
        if len(group_models) == 1:
            _emit(run_label, runs)
        else:
            print(f"=== {run_label}   {len(group_models)} models present:")
            for model_name in group_models:
                subset = [run for run in runs if (run.get("model") or "<no-model>") == model_name]
                _emit(model_name, subset)
    return 0


def discover_cases(out):
    """Case names present in DIR, read from each run's stored `case` field."""
    cases = set()
    for file_path in glob.glob(os.path.join(out, "*.json")):
        try:
            record = json.load(open(file_path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if record.get("case"):
            cases.add(record["case"])
    return sorted(cases)


def main() -> int:
    """Parse argv into cases + optional filters and summarise each case."""
    parser = argparse.ArgumentParser(
        description="Summarise local_model_eval runs by label (reads rate, mean score, per-grader pass).",
        epilog="Run one invocation with --label baseline,post to print both arms together.",
    )
    parser.add_argument("--out", default="evals/results", metavar="DIR",
                       help="producer output directory (default: evals/results)")
    parser.add_argument("--case", action="append", dest="cases", metavar="CASE",
                       help="case name; repeat for several (default: every case in --out)")
    parser.add_argument("--label", default=None, metavar="LABELS",
                       help="comma-separated labels to compare (e.g. baseline,post)")
    parser.add_argument("--model", default=None, metavar="SUBSTR",
                       help="substring model filter")
    args = parser.parse_args()

    labels = None
    if args.label is not None:
        chosen = [label for label in args.label.split(",") if label]
        if not chosen:
            parser.error("--label requires at least one label")
        labels = chosen

    cases = sorted(set(args.cases)) if args.cases else discover_cases(args.out)
    if not cases:
        print(f"no cases with runs in {args.out}")
        return 1

    status = 0
    for case in cases:
        status |= summarise(case, args.out, labels, args.model)
    return status


if __name__ == "__main__":
    sys.exit(main())
