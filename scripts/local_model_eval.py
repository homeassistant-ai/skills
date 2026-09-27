#!/usr/bin/env python3
"""Run eval cases against a local model the way ha-mcp serves the skill.

`claude plugin eval` runs cases through Claude Code, whose system prompt and
tool set fill most of a small model's context. Local-model users more often
reach the skill through an MCP client (Open WebUI, for example) talking to
ha-mcp. This script imitates that path against any OpenAI-compatible chat
endpoint (LM Studio, llama.cpp, Ollama).

The model gets ha-mcp's server instructions as the system prompt (skip them
with --no-instructions: not every client forwards them) and one tool,
ha_get_skill_guide: no arguments returns SKILL.md, `file` returns that file,
any other path is refused with the list of valid paths. The texts are copied
from ha-mcp src/ha_mcp/server.py at commit 0d56b896 (homeassistant-ai/ha-mcp
PR #2556); re-copy them when that file changes. Two texts are this script's
own: an MCP tool error reaches the model as text, sent here as a JSON object
with `error` and `suggestions`, and ha-mcp rejects an unexpected argument
through its schema validation, whose exact message is not copied.

There are no Home Assistant tools, so the config must be in the final answer.
The answer is scored with the case's regex graders only, compiled in node as
the eval harness does; llm and tool_used graders are skipped, so a score here
does not compare with `claude plugin eval`. A run that ends without an answer
(out of turns, or over --ctx-limit) scores 0.

Each run is written to <out>/<case>-<label>-r<n>.json. An existing file is
skipped, so a stopped batch resumes; it must have been written with the same
settings. A run whose request fails at the endpoint (server down, model
unloaded, a context overflow the server reports) is not written, and the
script exits 1; lower --ctx-limit if the server reports overflows.

Usage:
  python scripts/local_model_eval.py --model <model> --out <dir> \
      (--case <case> [--case <case> ...] | --all-regex) [--runs 3] \
      [--label <label>] [--skill-dir <dir>] [--base-url http://localhost:1234] \
      [--no-instructions] [--max-turns 10] [--ctx-limit 96000]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
TOOL = "ha_get_skill_guide"
SKILL = "home-assistant-best-practices"
REQUEST_TIMEOUT_S = 1500  # a slow local model can take minutes per reply
MIN_CALIBRATION_TOKENS = 1000  # ignore token counts too small to give a stable ratio

# Texts copied from ha-mcp server.py at 0d56b896. A backslash at a line end
# joins the lines, so each paragraph is one line, as in ha-mcp.
USE_BEFORE = """\
Use BEFORE: creating or editing automations, scripts, scenes, helpers, or \
dashboards; writing triggers, conditions, actions, wait_template, or service \
calls; renaming entities or migrating device_id to entity_id; calling \
ha_config_set_automation, ha_config_set_script, ha_config_set_helper, \
ha_config_set_dashboard, or ha_set_entity."""

ALIASES = """\
Replaces (and supersedes) the prior tools: ha_list_resources, \
ha_read_resource, and ha_get_skill_home_assistant_best_practices. If you were \
going to call any of those, call this instead."""

BPS_HINT = """\
You now have this best-practice reference in your context. Pass \
`MandatoryBPS=false` on subsequent write-tool calls in this session \
(ha_config_set_automation / _script / _scene / _helper / _dashboard / _yaml) \
to avoid re-receiving the canonical reference files inline."""

INSTRUCTIONS = f"""\
IMPORTANT: This server provides best-practice skills that MUST be consulted \
before performing matching actions. Read the SKILL.md for the matching skill \
— it contains a Reference Files table that maps tasks to specific \
reference files. You MUST read the referenced files that match your current \
task before proceeding. Do NOT load all reference files upfront — only \
the ones the table directs you to.

How to access: Read the skill via MCP resources (resources/read with the \
skill:// URI) — if you can read these instructions, you should be able \
to access resources as well. If for any reason you cannot access MCP \
resources, call {TOOL}() with no arguments as a fallback: it returns \
SKILL.md, then pass file='<path>' for a reference file. If you can access \
resources normally, do not waste time or tokens on that tool.
"""

TOOL_DESCRIPTION = """\
Get the bundled Home Assistant best-practices skill. CALL THIS FIRST before \
performing matching actions.

Call with no arguments to read SKILL.md: the workflow, the common mistakes, \
and a table that says which reference file to read for each task. Then read \
only the files that table points to.

"""

FILE_PARAM = """\
Path of the file to read, exactly as SKILL.md links it \
(e.g. 'references/automation-patterns.md'). Omit to read SKILL.md."""

HOW_TO_USE = f"""\
Call {TOOL}(file='<path>') for the reference files the table above points to \
for your task, using the path exactly as linked (e.g. \
'references/automation-patterns.md'). Read only those; do not load every file."""

# Runs each [pattern, flags, text] as a JavaScript RegExp, as the eval harness does.
NODE_GRADER = ("const q=JSON.parse(require('fs').readFileSync(0,'utf8'));"
               "process.stdout.write(JSON.stringify(q.map(([p,f,t])=>new RegExp(p,f).test(t))))")


class EndpointError(Exception):
    """The chat endpoint did not return a usable reply."""


def skill_description(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1])["description"].strip()


def system_prompt(desc: str) -> str:
    return INSTRUCTIONS + f"\n### Skill: {SKILL} (skill://{SKILL}/SKILL.md)\n{desc}"


def tool_schema(desc: str) -> dict:
    description = (TOOL_DESCRIPTION + f"### {SKILL} (skill://{SKILL}/SKILL.md)\n{desc}"
                   f"\n\n{USE_BEFORE}\n\n{ALIASES}")
    params = {"type": "object", "additionalProperties": False, "properties": {
        "file": {"type": "string", "default": "SKILL.md", "description": FILE_PARAM}}}
    return {"type": "function", "function": {"name": TOOL, "description": description, "parameters": params}}


def skill_files(skill_dir: Path) -> list:
    """Regular files inside the skill, as ha-mcp lists them: symlinks and files
    that resolve outside the skill are left out."""
    root = skill_dir.resolve()
    return sorted(f.relative_to(skill_dir).as_posix() for f in skill_dir.rglob("*")
                  if f.is_file() and not f.is_symlink() and f.resolve().is_relative_to(root))


def serve(skill_dir: Path, args: dict) -> dict:
    """ha_get_skill_guide's response, keys in ha-mcp's order."""
    extra = set(args) - {"file"}
    if extra:
        return {"error": f"Unexpected argument(s): {', '.join(sorted(extra))}."}
    file = args.get("file") or "SKILL.md"
    files = skill_files(skill_dir)
    if file not in files:  # an exact match also refuses traversal and absolute paths
        return {"error": f"Unknown file {file!r} in skill {SKILL!r}.",
                "suggestions": [f"Pass one of these paths exactly as written: {', '.join(files)}",
                                f"Call {TOOL}() with no arguments to read SKILL.md, whose table says which file to read."]}
    response = {} if file == "SKILL.md" else {"skill_content_hint": BPS_HINT}
    response.update(success=True, file=file, uri=f"skill://{SKILL}/{file}",
                    content=(skill_dir / file).read_text(encoding="utf-8"))
    if file == "SKILL.md":
        response["how_to_use"] = HOW_TO_USE
    return response


def call_tool(skill_dir: Path, tool_call: dict) -> tuple:
    """Return the tool name, the parsed arguments and the tool's response."""
    function = tool_call.get("function") if isinstance(tool_call.get("function"), dict) else {}
    name = function.get("name")
    raw = function.get("arguments") or "{}"
    try:
        args = json.loads(raw)
    except json.JSONDecodeError:
        args = raw
    if name != TOOL or not isinstance(args, dict):
        return name, args, {"success": False, "error": f"Unknown tool {name!r} or bad arguments."}
    return name, args, serve(skill_dir, args)


def chat(base_url: str, model: str, messages: list, tools: list) -> tuple:
    """Return the reply message and the prompt token count the server reports."""
    body = json.dumps({"model": model, "messages": messages, "tools": tools, "stream": False}).encode()
    request = urllib.request.Request(base_url.rstrip("/") + "/v1/chat/completions", data=body,
                                     headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_S) as r:
            reply = json.loads(r.read())
        message = reply["choices"][0]["message"]
        if not isinstance(message, dict):
            raise TypeError(f"message is {type(message).__name__}, not an object")
        tool_calls = message.get("tool_calls")
        if tool_calls and not (isinstance(tool_calls, list) and all(isinstance(c, dict) for c in tool_calls)):
            raise TypeError("tool_calls is not a list of objects")
        usage = reply.get("usage")
        prompt_tokens = usage.get("prompt_tokens") if isinstance(usage, dict) else None
        return message, prompt_tokens if isinstance(prompt_tokens, int) else None
    except urllib.error.HTTPError as e:
        raise EndpointError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e
    except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError,
            KeyError, IndexError, TypeError) as e:
        raise EndpointError(f"{type(e).__name__}: {e}") from e


def grade(graders: list, text: str) -> dict:
    query = [[g["pattern"], g.get("flags", ""), text] for g in graders]
    out = subprocess.run(["node", "-e", NODE_GRADER], input=json.dumps(query),
                         capture_output=True, text=True, check=True).stdout
    grades = {}
    for g, matched in zip(graders, json.loads(out)):
        grades[g["name"]] = matched if g.get("match", "contains") == "contains" else not matched
    return grades


def run_case(a, case: dict, desc: str) -> dict:
    """One conversation: tool calls until the model answers, then grade the answer."""
    tools = [tool_schema(desc)]
    messages = [] if a.no_instructions else [{"role": "system", "content": system_prompt(desc)}]
    messages.append({"role": "user", "content": case["execution"]["prompt"]})
    calls, reads, final, error = [], [], "", None
    chars_per_token = 4.0  # a first guess; each reply's prompt_tokens corrects it
    started = time.time()
    for _ in range(a.max_turns):
        # Refuse a prompt that would overflow the loaded context: some servers
        # crash on overflow instead of returning an error.
        size = len(json.dumps(messages)) + len(json.dumps(tools))
        if size / chars_per_token > a.ctx_limit:
            error = f"context overflow: estimated {int(size / chars_per_token)} tokens, limit {a.ctx_limit}"
            break
        msg, prompt_tokens = chat(a.base_url, a.model, messages, tools)
        if prompt_tokens and prompt_tokens > MIN_CALIBRATION_TOKENS:
            chars_per_token = size / prompt_tokens
        messages.append({"role": "assistant", **{k: v for k, v in msg.items() if k in ("content", "tool_calls")}})
        if not msg.get("tool_calls"):
            final = msg.get("content") or ""
            break
        for tool_call in msg["tool_calls"]:
            name, args, out = call_tool(a.skill_dir, tool_call)
            calls.append({"name": name, "args": args})
            if "content" in out:
                reads.append(out["file"])
            # ha-mcp sends tool results as compact UTF-8 JSON, not \u escapes.
            messages.append({"role": "tool", "tool_call_id": tool_call.get("id", ""),
                             "content": json.dumps(out, ensure_ascii=False, separators=(",", ":"))})
    if not final and not error:
        error = f"reached maximum number of turns ({a.max_turns})"
    grades = grade(case["regex"], final) if final else {g["name"]: False for g in case["regex"]}
    return {"final": final, "error": error, "score": sum(grades.values()) / len(grades), "graders": grades,
            "turns": sum(m["role"] == "assistant" for m in messages), "secs": round(time.time() - started, 1),
            "calls": calls, "reads": reads}


def load_case(name: str) -> dict:
    path = REPO / "evals" / name / "case.yaml"
    if not path.is_file():
        sys.exit(f"no case {name!r}")
    case = yaml.safe_load(path.read_text(encoding="utf-8"))
    case["regex"] = [g for g in case["graders"] if g["type"] == "regex"]
    for g in case["regex"]:
        if g.get("match", "contains") not in ("contains", "not_contains") or set(g) & {"target", "weight"}:
            sys.exit(f"{name}: grader {g['name']} uses a regex option this script does not score")
    return case


def parse_args():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True, type=Path)
    which = p.add_mutually_exclusive_group(required=True)
    which.add_argument("--case", action="append", help="case name; repeat for more")
    which.add_argument("--all-regex", action="store_true", help="every case with a regex grader")
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--label", default="run")
    p.add_argument("--skill-dir", type=Path, default=REPO / "skills" / SKILL)
    p.add_argument("--base-url", default=os.environ.get("LOCAL_MODEL_BASE_URL", "http://localhost:1234"))
    p.add_argument("--no-instructions", action="store_true")
    p.add_argument("--max-turns", type=int, default=10)
    p.add_argument("--ctx-limit", type=int, default=96000, help="tokens; set just under the loaded context")
    a = p.parse_args()
    if a.max_turns < 1 or a.runs < 1:
        p.error("--max-turns and --runs must be at least 1")
    return a


def main() -> int:
    a = parse_args()
    if not shutil.which("node"):
        sys.exit("node is required: regex graders are JavaScript patterns")
    if a.all_regex:
        names = sorted(p.parent.name for p in (REPO / "evals").glob("*/case.yaml"))
        cases = {n: c for n in names if (c := load_case(n))["regex"]}
    else:
        cases = {n: load_case(n) for n in sorted(set(a.case))}
        for name, case in cases.items():
            if not case["regex"]:
                sys.exit(f"{name} has no regex grader; this script scores only those")
    desc = skill_description(a.skill_dir)
    settings = {"model": a.model, "instructions": not a.no_instructions, "skill_dir": str(a.skill_dir.resolve()),
                "max_turns": a.max_turns, "ctx_limit": a.ctx_limit}
    a.out.mkdir(parents=True, exist_ok=True)
    failed = 0
    for n in range(1, a.runs + 1):
        for name, case in cases.items():
            path = a.out / f"{name}-{a.label}-r{n}.json"
            if path.exists():
                written = json.loads(path.read_text(encoding="utf-8"))
                if {k: written.get(k) for k in settings} != settings:
                    sys.exit(f"{path} was written with other settings; use another --label or --out")
                continue
            try:
                result = run_case(a, case, desc)
            except EndpointError as e:
                failed += 1
                print(f"{time.strftime('%T')} FAILED {path.name}: {e}", flush=True)
                continue
            result.update(case=name, label=a.label, run=n, **settings)
            path.write_text(json.dumps(result, indent=1), encoding="utf-8")
            print(f"{time.strftime('%T')} {path.name} score={result['score']:.2f} turns={result['turns']} "
                  f"secs={result['secs']} reads={result['reads']} {result['error'] or ''}", flush=True)
    if failed:
        print(f"{failed} run(s) failed at the endpoint and were not written", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
