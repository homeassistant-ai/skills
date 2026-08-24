#!/usr/bin/env python3
"""Validate every skills/*/evals/<case>/case.yaml against the 1.1 case schema.

`claude plugin eval` is the real consumer of these files, but it is gated behind
early access, so its parser never runs here and a malformed case would otherwise
merge unnoticed. The schema below is transcribed by hand from the Zod definition
in the Claude Code 2.1.241 binary — re-derive it if schema_version moves off "1.1".

Checks: schema conformance, the grader objects' .strict() key sets, unique grader
names within a case, regex patterns that compile, valid JS RegExp flags,
directory/name agreement, an empty allowed_tools (so no case needs an
--allow-tools operator grant to run), and a skill-fired indicator on every case.

Does NOT check that a grader still means what it was written to mean. Judging
that is a review item.

Usage: python scripts/check_eval_cases.py [skills_root]   (default: skills)
"""
import glob
import os
import re
import sys
from collections import Counter

import yaml

TOP_REQ = {"schema_version", "name", "graders", "execution"}
TOP_OK = TOP_REQ | {"description", "tags", "plugins", "context", "runs", "expected_outcome"}
EXEC_OK = {"prompt", "max_turns", "timeout_seconds", "model", "allowed_tools",
           "artifact_publish", "growthbook_overrides", "append_system_prompt", "env"}
GRADER = {  # type -> (required keys, optional keys); each grader object is .strict()
    "regex":       ({"type", "name", "pattern"}, {"target", "flags", "match", "weight", "arm"}),
    "tool_order":  ({"type", "name", "before", "after"}, {"weight", "arm"}),
    "tool_used":   ({"type", "name", "tool"}, {"input_match", "min", "max", "weight", "arm"}),
    "file_exists": ({"type", "name", "path"}, {"exists", "weight", "arm"}),
    "llm":         ({"type", "name", "criteria"}, {"focus", "weight", "arm"}),
    "baseline":    ({"type", "name", "baseline_file", "criteria"}, {"weight", "arm"}),
}


def check_case(path, err):
    """Validate one case.yaml. Appends messages to err; returns the parsed dict or None."""
    rel = os.path.relpath(path)
    case_dir = os.path.basename(os.path.dirname(path))
    w = lambda m: err.append(f"{rel}: {m}")
    try:
        d = yaml.safe_load(open(path, encoding="utf-8"))
    except yaml.YAMLError as e:
        w(f"does not parse as YAML: {e}")
        return None
    if not isinstance(d, dict):
        w("top level is not a mapping")
        return None

    if d.get("name") != case_dir:
        w(f"name {d.get('name')!r} does not match its directory {case_dir!r}")
    for k in sorted(TOP_REQ - set(d)):
        w(f"missing required key {k}")
    for k in sorted(set(d) - TOP_OK):
        w(f"unknown top-level key {k}")
    if d.get("schema_version") != "1.1" or not isinstance(d.get("schema_version"), str):
        w('schema_version must be the string "1.1"')

    execution = d.get("execution")
    if not isinstance(execution, dict):
        w("execution must be a mapping")
        execution = {}
    for k in sorted(set(execution) - EXEC_OK):
        w(f"unknown execution key {k}")
    if not str(execution.get("prompt", "")).strip():
        w("execution.prompt is empty — the case has nothing to run")
    if execution.get("allowed_tools"):
        w("allowed_tools is non-empty — the case then needs an --allow-tools grant to run")
    if not 0 < d.get("runs", 3) <= 50:
        w("runs must be 1..50")
    if not 0 < execution.get("max_turns", 10) <= 200:
        w("max_turns must be 1..200")
    if not 0 < execution.get("timeout_seconds", 300) <= 3600:
        w("timeout_seconds must be 1..3600")

    graders = d.get("graders") or []
    if not graders:
        w("graders must have at least one entry")
    seen = set()
    for g in graders:
        if not isinstance(g, dict):
            w("grader is not a mapping")
            continue
        req, opt = GRADER.get(g.get("type"), (None, None))
        if req is None:
            w(f"unknown grader type {g.get('type')!r} "
              f"(expected one of: {', '.join(sorted(GRADER))})")
            continue
        name = g.get("name", "<unnamed>")
        for k in sorted(req - set(g)):
            w(f"grader {name}: missing {k}")
        for k in sorted(set(g) - req - opt):
            w(f"grader {name}: unknown key {k} (the grader schema is strict)")
        if name in seen:
            w(f"duplicate grader name {name}")
        seen.add(name)
        if g["type"] == "regex":
            if not re.fullmatch(r"[dgimsuvy]*", str(g.get("flags", ""))):
                w(f"grader {name}: flags must be JS RegExp flags (d g i m s u v y)")
            match = g.get("match", "contains")
            if match not in ("contains", "not_contains") and not re.fullmatch(r"count:\d+", str(match)):
                w(f"grader {name}: match must be contains | not_contains | count:N")
            try:
                re.compile(g["pattern"])
            except (re.error, KeyError, TypeError) as e:
                w(f"grader {name}: pattern does not compile: {e}")
    if "skill-fired" not in seen:
        w("no skill-fired grader — a failing case could not be told apart from "
          "the skill never triggering")
    return d


def main(root="skills"):
    err = []
    total = 0
    types = Counter()
    for evals_dir in sorted(glob.glob(os.path.join(root, "*", "evals"))):
        paths = sorted(glob.glob(os.path.join(evals_dir, "*", "case.yaml")))
        if not paths:
            err.append(f"{os.path.relpath(evals_dir)}: contains no <case>/case.yaml")
            continue
        for p in paths:
            d = check_case(p, err)
            total += 1
            if d:
                types.update(g.get("type") for g in (d.get("graders") or []) if isinstance(g, dict))
        print(f"{os.path.relpath(evals_dir)}: {len(paths)} cases")
    print(f"total: {total} cases, {sum(types.values())} graders {dict(types)}")
    for e in err:
        print(f"  ! {e}")
    print("FAIL" if err else "OK")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "skills"))
