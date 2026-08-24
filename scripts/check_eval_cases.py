#!/usr/bin/env python3
"""Validate evals/<case>/case.yaml against the 1.1 case schema.

`claude plugin eval` is the real consumer of these files, but it is gated behind
early access, so its parser never runs here and a malformed case would otherwise
merge unnoticed. The schema below is transcribed by hand from the Zod definition
in the Claude Code 2.1.241 binary — re-derive it if schema_version moves off "1.1".

Cases live in evals/ at the plugin root, not under skills/. The harness rejects
any eval directory whose first segment names a loaded component directory
(commands, skills, agents, hooks, themes, output-styles, monitors, workflows,
bin), so a path under skills/ is discarded in favour of the default evals/ and
the cases are never found.

Checks: schema conformance, the grader objects' .strict() key sets and value
types, unique grader names within a case, regex patterns that compile *in the
JavaScript engine that runs them*, valid JS RegExp flags, directory/name
agreement, an empty allowed_tools (so no case needs an --allow-tools operator
grant), and a skill-fired grader that can actually prove a real skill loaded.

Does NOT check that a grader still means what it was written to mean. Judging
that is a review item.

Usage: python scripts/check_eval_cases.py [repo_root]   (default: .)
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter

import yaml

TOP_REQ = {"schema_version", "name", "graders", "execution"}
TOP_OK = TOP_REQ | {"description", "tags", "plugins", "context", "runs", "expected_outcome"}
EXEC_OK = {"prompt", "max_turns", "timeout_seconds", "model", "allowed_tools",
           "artifact_publish", "growthbook_overrides", "append_system_prompt", "env"}
# type -> (required keys, optional keys); each grader object is .strict()
GRADER = {
    "regex":       ({"type", "name", "pattern"}, {"target", "flags", "match", "weight", "arm"}),
    "tool_order":  ({"type", "name", "before", "after"}, {"weight", "arm"}),
    "tool_used":   ({"type", "name", "tool"}, {"input_match", "min", "max", "weight", "arm"}),
    "file_exists": ({"type", "name", "path"}, {"exists", "weight", "arm"}),
    "llm":         ({"type", "name", "criteria"}, {"focus", "weight", "arm"}),
    "baseline":    ({"type", "name", "baseline_file", "criteria"}, {"weight", "arm"}),
}
# Keys the schema types as plain strings, per grader type.
STRINGS = {
    "regex": ("name", "pattern", "flags"),
    "tool_order": ("name",),
    "tool_used": ("name", "tool", "input_match"),
    "file_exists": ("name", "path"),
    "llm": ("name", "criteria"),
    "baseline": ("name", "baseline_file", "criteria"),
}
TARGETS = ("trace", "last_message", "files")   # tFh(): enum, or {source: file, path}
ARMS = ("with-only", "both")                   # Gun()

NODE_SRC = r"""
const probes = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const out = [];
for (const p of probes) {
  let rx;
  try {
    rx = new RegExp(p.pattern, p.flags || '');
  } catch (e) {
    out.push(`${p.label}: pattern is not a valid JavaScript RegExp: ${e.message}`);
    continue;
  }
  for (const s of p.must_match || []) {
    rx.lastIndex = 0;
    if (!rx.test(s)) out.push(`${p.label}: pattern does not match ${JSON.stringify(s)}, which it must`);
  }
  for (const s of p.must_not_match || []) {
    rx.lastIndex = 0;
    if (rx.test(s)) out.push(`${p.label}: pattern matches ${JSON.stringify(s)}, which it must reject`);
  }
}
console.log(JSON.stringify(out));
"""


def whole(value):
    """True for a numeric whole number. YAML `2.0` is one; `True` and "2" are not.

    Avoids float() on an int: YAML integers are unbounded, and float(10**400)
    raises OverflowError rather than answering the question.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return True if isinstance(value, int) else value.is_integer()


def num(value, lo, hi, label, w, integer=True):
    """Range-check a numeric field, reporting a bad type rather than raising on it."""
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        w(f"{label} must be a number, got {value!r}")
        return
    if integer and not whole(value):
        w(f"{label} must be a whole number, got {value!r}")
        return
    if not lo <= value <= hi:
        rng = "positive" if hi == float("inf") else (
            f"at least {lo}" if hi is None else f"{lo}..{hi}")
        w(f"{label} must be {rng}, got {value!r}")


def check_target(value, label, w):
    """tFh(): one of the enum strings, or {source: "file", path: <string>}."""
    if isinstance(value, str):
        if value not in TARGETS:
            w(f"{label} must be one of {', '.join(TARGETS)}, or a "
              f"{{source: file, path: ...}} mapping, got {value!r}")
        return
    if isinstance(value, dict):
        if value.get("source") != "file":
            w(f"{label} mapping must set source: file, got {value.get('source')!r}")
        if not isinstance(value.get("path"), str):
            w(f"{label} mapping needs a string path, got {value.get('path')!r}")
        return
    w(f"{label} must be a string or a {{source: file, path: ...}} mapping, got {value!r}")


def check_case(path, skills, err, probes):
    """Validate one case.yaml. Appends messages to err and probes; returns the parsed dict."""
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
    prompt = execution.get("prompt")
    # `prompt:` with no value parses as None. str(None) is "None", which is truthy,
    # so this must test the value itself rather than its str().
    if not isinstance(prompt, str) or not prompt.strip():
        w(f"execution.prompt must be a non-empty string, got {prompt!r}")
    if execution.get("allowed_tools"):
        w("allowed_tools is non-empty — the case then needs an --allow-tools grant to run")
    if "runs" in d:
        num(d["runs"], 1, 50, "runs", w)
    if "max_turns" in execution:
        num(execution["max_turns"], 1, 200, "max_turns", w)
    if "timeout_seconds" in execution:
        num(execution["timeout_seconds"], 1, 3600, "timeout_seconds", w)

    graders = d.get("graders") or []
    if not graders:
        w("graders must have at least one entry")
    seen = {}
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
        seen[name] = g

        for k in STRINGS[g["type"]]:
            if k in g and not isinstance(g[k], str):
                w(f"grader {name}: {k} must be a string, got {g[k]!r}")
        if "arm" in g and g["arm"] not in ARMS:
            w(f"grader {name}: arm must be one of {', '.join(ARMS)}, got {g['arm']!r}")
        if "weight" in g:
            num(g["weight"], 1e-12, float("inf"), f"grader {name}: weight", w, integer=False)
        if "target" in g:
            check_target(g["target"], f"grader {name}: target", w)
        if "focus" in g:
            check_target(g["focus"], f"grader {name}: focus", w)

        if g["type"] == "tool_used":
            for k in ("min", "max"):
                if k in g:
                    num(g[k], 0, float("inf"), f"grader {name}: {k}", w)
            lo, hi = g.get("min"), g.get("max")
            # min: 0, max: 0 is the documented "must not call" idiom, but min > max
            # describes a call count no run can produce. Uses whole() so the values
            # num() just accepted — 2.0 as well as 2 — are compared here too.
            if whole(lo) and whole(hi) and lo > hi:
                w(f"grader {name}: min {lo} exceeds max {hi} — no call count satisfies it")
        if g["type"] == "tool_order":
            for k in ("before", "after"):
                v = g.get(k)
                if not isinstance(v, str) and not (isinstance(v, dict) and "tool" in v):
                    w(f"grader {name}: {k} must be a tool name or a {{tool, input_match}} "
                      f"mapping, got {v!r}")
        if g["type"] == "file_exists" and "exists" in g and not isinstance(g["exists"], bool):
            w(f"grader {name}: exists must be true or false, got {g['exists']!r}")
        if g["type"] == "regex":
            if not re.fullmatch(r"[dgimsuvy]*", str(g.get("flags", ""))):
                w(f"grader {name}: flags must be JS RegExp flags (d g i m s u v y)")
            match = g.get("match", "contains")
            if match not in ("contains", "not_contains") and not re.fullmatch(r"count:\d+", str(match)):
                w(f"grader {name}: match must be contains | not_contains | count:N")
            if isinstance(g.get("pattern"), str):
                probes.append({"label": f"{rel}: grader {name}",
                               "pattern": g["pattern"], "flags": str(g.get("flags", ""))})

    check_skill_fired(rel, skills, seen.get("skill-fired"), err, probes)
    return d


def check_skill_fired(rel, skills, g, err, probes):
    """The skill-fired grader must be able to prove a skill loaded, not just be named so.

    A name alone proves nothing: an `llm` grader called skill-fired passes a name
    check while telling you nothing about whether the Skill tool ran.
    """
    w = lambda m: err.append(f"{rel}: {m}")
    if g is None:
        w("no skill-fired grader — a failing case could not be told apart from "
          "the skill never triggering")
        return
    if g.get("type") != "tool_used":
        w(f"skill-fired must be a tool_used grader, not {g.get('type')!r} — "
          "only that type inspects the trace for a tool call")
        return
    if g.get("tool") != "Skill":
        w(f"skill-fired must set tool: Skill, not {g.get('tool')!r}")
    min_calls = g.get("min", 1)
    if not whole(min_calls) or min_calls < 1:
        w(f"skill-fired must require at least one call (min >= 1), got {min_calls!r}")
    if "max" in g and (not whole(g["max"]) or g["max"] < 1):
        # max: 0 would assert the skill must NOT load — the opposite of the point.
        w(f"skill-fired must allow at least one call (max >= 1), got {g['max']!r}")
    pattern = g.get("input_match")
    if not isinstance(pattern, str) or not pattern:
        w("skill-fired needs an input_match, or it passes when any skill loads")
        return
    if not skills:
        w("skill-fired cannot be checked: no skills/<name>/ directory to match against")
        return
    # Disprove as well as confirm: it must match a real skill and reject a made-up one.
    probes.append({
        "label": f"{rel}: grader skill-fired input_match",
        "pattern": pattern,
        "flags": "",
        "must_match": [json.dumps({"skill": s}) for s in skills]
                      + [json.dumps({"skill": f"plugin:{s}"}) for s in skills],
        "must_not_match": [json.dumps({"skill": "no-such-skill"})],
    })


def check_regexes(probes, err):
    """Compile probes with node, the engine that actually runs them."""
    if not probes:
        return
    node = shutil.which("node")
    if node is None:
        # Python `re` disagrees with JS at the edges — it rejects JS-valid
        # `(?<name>x)` — so a failure here is not evidence the pattern is bad.
        # Warn; do not fail a run on a machine that simply lacks node.
        print("  warning: node not found — regex patterns were NOT validated against "
              "the JavaScript engine that runs them")
        return
    try:
        r = subprocess.run([node, "-e", NODE_SRC], input=json.dumps(probes),
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        err.append(f"could not run node to validate regex patterns: {e}")
        return
    if r.returncode != 0:
        err.append(f"node failed while validating regex patterns: {r.stderr.strip()[:300]}")
        return
    err.extend(json.loads(r.stdout))


def main(root="."):
    err = []
    probes = []
    types = Counter()
    skills = sorted(os.path.basename(p.rstrip(os.sep))
                    for p in glob.glob(os.path.join(root, "skills", "*", "")))
    paths = sorted(glob.glob(os.path.join(root, "evals", "*", "case.yaml")))
    if not paths:
        err.append(f"{os.path.join(root, 'evals')}: contains no <case>/case.yaml")
    for p in paths:
        d = check_case(p, skills, err, probes)
        if d:
            types.update(g.get("type") for g in (d.get("graders") or []) if isinstance(g, dict))
    check_regexes(probes, err)
    print(f"{len(paths)} cases, {sum(types.values())} graders {dict(types)}, "
          f"{len(skills)} skills")
    for e in sorted(err):
        print(f"  ! {e}")
    print("FAIL" if err else "OK")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
