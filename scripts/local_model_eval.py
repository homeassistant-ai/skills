#!/usr/bin/env python3
"""Run eval cases against a local model the way ha-mcp serves the skill.

`claude plugin eval` runs cases through Claude Code, whose system prompt and
tool set dominate a small model's context. Local-model users more often reach
the skill through an MCP client (Open WebUI, for example) talking to ha-mcp,
which hands the skill out through one tool. This script imitates that path
against any OpenAI-compatible chat endpoint (LM Studio, llama.cpp, Ollama).

The model gets:
- as the system prompt, ha-mcp's server instructions (skip with
  --no-instructions: not every client forwards them);
- one tool, ha_get_skill_guide, in one of two shapes (--tool):
  - legacy (default): ha-mcp at commit af9b054a. No args lists the skills,
    `skill` lists the files, `skill` + `file` returns a file.
  - single-file: ha-mcp branch feat/skill-guide-single-arg. No args returns
    SKILL.md; `file` returns that file; any other path is refused.

Tool description, instructions and response texts are copied from ha-mcp
src/ha_mcp/server.py for each shape. Re-copy them when that file changes. An
MCP tool error reaches the model as text; here it is a JSON object with
`error` and `suggestions`.

There are no Home Assistant tools, so the config must be in the final answer.
Only the case's regex graders are scored, compiled with node as the harness
does; llm and tool_used graders are skipped, so a case's score here is not
comparable with `claude plugin eval`.

Each run is written to <out>/<case>-<label>-r<n>.json with the tool calls,
files read, final answer and grader results. An existing file is skipped, so a
stopped batch resumes. A run that fails on the endpoint is not written.

Usage:
  python scripts/local_model_eval.py --model <model> --out <dir> \
      --case <case> [--case <case> ...] [--runs 3] [--label <label>] \
      [--skill-dir <dir>] [--base-url http://localhost:1234] \
      [--tool legacy|single-file] [--no-instructions] [--max-turns 10] [--ctx-limit 96000]
  --all-regex instead of --case runs every case that has a regex grader.
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

# Texts from ha-mcp server.py, shared by both tool shapes.
USE_BEFORE = (
    "Use BEFORE: creating or editing automations, scripts, scenes, "
    "helpers, or dashboards; writing triggers, conditions, actions, "
    "wait_template, or service calls; renaming entities or migrating "
    "device_id to entity_id; calling ha_config_set_automation, "
    "ha_config_set_script, ha_config_set_helper, ha_config_set_dashboard, "
    "or ha_set_entity."
)
ALIASES = (
    "Replaces (and supersedes) the prior tools: ha_list_resources, "
    "ha_read_resource, and ha_get_skill_home_assistant_best_practices. "
    "If you were going to call any of those, call this instead."
)
BPS_HINT = (
    "You now have this best-practice reference in your context. "
    "Pass `MandatoryBPS=false` on subsequent write-tool calls in this "
    "session (ha_config_set_automation / _script / _scene / _helper / "
    "_dashboard / _yaml) to avoid re-receiving the canonical reference "
    "files inline."
)


def frontmatter_description(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1])["description"].strip()


def server_instructions(desc: str, shape: str) -> str:
    if shape == "legacy":
        fallback = (
            f"If for any reason you cannot access MCP resources, use the {TOOL} "
            "tool as a fallback."
        )
    else:
        fallback = (
            f"If for any reason you cannot access MCP resources, call {TOOL}() with no "
            "arguments as a fallback: it returns SKILL.md, then pass file='<path>' for a "
            "reference file."
        )
    access = (
        "Read the skill via MCP resources (resources/read with the "
        "skill:// URI) — if you can read these instructions, you "
        f"should be able to access resources as well. {fallback} "
        "If you can access resources normally, do "
        "not waste time or tokens on that tool."
    )
    header = (
        "IMPORTANT: This server provides best-practice skills that MUST "
        "be consulted before performing matching actions. "
        "Read the SKILL.md for the matching skill "
        "— it contains a Reference Files table that maps tasks to "
        "specific reference files. You MUST read the referenced files "
        "that match your current task before proceeding. "
        "Do NOT load all reference files upfront "
        "— only the ones the table directs you to.\n\n"
        f"How to access: {access}\n"
    )
    return header + f"\n### Skill: {SKILL} (skill://{SKILL}/SKILL.md)\n{desc}"


def tool_schema(desc: str, shape: str) -> dict:
    block = f"### {SKILL} (skill://{SKILL}/SKILL.md)\n{desc}\n\n{USE_BEFORE}\n\n{ALIASES}"
    if shape == "legacy":
        description = (
            "Get bundled Home Assistant best-practice skill guides. "
            "CALL THIS FIRST before performing matching actions.\n\n"
            "Three modes (progressive disclosure):\n"
            "- No args: list bundled skills with their trigger conditions.\n"
            "- skill arg: list reference files for that skill.\n"
            "- skill + file args: read the file content.\n\n"
            "Bundled skills:\n\n" + block
        )
        params = {"type": "object", "properties": {
            "skill": {"type": "string", "description": "Skill name from the no-args listing (e.g., 'home-assistant-best-practices')."},
            "file": {"type": "string", "description": "Reference file path within the skill, relative to the skill directory (e.g., 'SKILL.md' or 'references/automation-patterns.md'). Requires skill to be set."},
        }}
    else:
        description = (
            "Get the bundled Home Assistant best-practices skill. "
            "CALL THIS FIRST before performing matching actions.\n\n"
            "Call with no arguments to read SKILL.md: the workflow, the common mistakes, "
            "and a table that says which reference file to read for each task. Then call "
            "again with file='<path>' (e.g. 'references/automation-patterns.md') for only "
            "the files that table points to.\n\n" + block
        )
        params = {"type": "object", "additionalProperties": False, "properties": {
            "file": {"type": "string", "default": "SKILL.md",
                     "description": "Path of the file to read, exactly as SKILL.md links it (e.g. 'references/automation-patterns.md'). Omit to read SKILL.md."},
        }}
    return {"type": "function", "function": {"name": TOOL, "description": description, "parameters": params}}


def skill_files(skill_dir: Path) -> list:
    return sorted(f.relative_to(skill_dir).as_posix() for f in skill_dir.rglob("*") if f.is_file())


def run_tool(skill_dir: Path, desc: str, args: dict, shape: str) -> dict:
    if shape == "single-file":
        extra = set(args) - {"file"}
        if extra:
            return {"error": f"Unexpected argument(s): {', '.join(sorted(extra))}."}
        file = args.get("file") or "SKILL.md"
        files = skill_files(skill_dir)
        if file not in files:
            return {"error": f"Unknown file {file!r} in skill {SKILL!r}.",
                    "suggestions": [f"Pass one of these paths exactly as written: {', '.join(files)}",
                                    f"Call {TOOL}() with no arguments to read SKILL.md, whose table says which file to read."]}
        content = (skill_dir / file).read_text(encoding="utf-8")
        uri = f"skill://{SKILL}/{file}"
        if file == "SKILL.md":
            return {"success": True, "file": file, "uri": uri, "content": content,
                    "how_to_use": (f"Call {TOOL}(file='<path>') for the reference files the table above "
                                   "points to for your task, using the path exactly as linked (e.g. "
                                   "'references/automation-patterns.md'). Read only those; do not load every file.")}
        return {"skill_content_hint": BPS_HINT, "success": True, "file": file, "uri": uri, "content": content}

    skill, file = args.get("skill"), args.get("file")
    if not skill:
        return {"success": True,
                "skills": [{"skill": SKILL, "uri": f"skill://{SKILL}/SKILL.md", "description": desc}],
                "how_to_use": (f"Call {TOOL}(skill='<name>') to list a skill's reference files, then "
                               f"{TOOL}(skill='<name>', file='<path>') to read content. Resource-capable "
                               "clients can also read skill:// URIs via resources/read.")}
    if skill != SKILL:
        return {"success": False, "error": f"Unknown skill {skill!r}."}
    if not file:
        return {"success": True, "skill": skill, "uri": f"skill://{skill}/SKILL.md",
                "files": [{"name": n, "uri": f"skill://{skill}/{n}"} for n in skill_files(skill_dir)],
                "how_to_use": (f"Call {TOOL}(skill={skill!r}, file='<name>') to read a specific file. "
                               "Start with SKILL.md for the decision workflow.")}
    target = (skill_dir / file).resolve()
    if not target.is_relative_to(skill_dir.resolve()) or not target.is_file():
        return {"success": False, "error": f"File {file!r} not found in skill {skill!r}."}
    return {"skill_content_hint": BPS_HINT, "success": True, "skill": skill, "file": file,
            "uri": f"skill://{skill}/{file}", "content": target.read_text(encoding="utf-8")}


def chat(base_url: str, model: str, messages: list, tools: list) -> dict:
    body = json.dumps({"model": model, "messages": messages, "tools": tools, "stream": False}).encode()
    req = urllib.request.Request(base_url.rstrip("/") + "/v1/chat/completions", data=body,
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=1500) as r:
        return json.loads(r.read())


def grade(case: dict, text: str) -> dict:
    regex = [g for g in case["graders"] if g["type"] == "regex"]
    q = [[g["pattern"], g.get("flags", ""), text] for g in regex]
    node = ("const q=JSON.parse(require('fs').readFileSync(0,'utf8'));"
            "process.stdout.write(JSON.stringify(q.map(([p,f,t])=>new RegExp(p,f).test(t))))")
    res = json.loads(subprocess.run(["node", "-e", node], input=json.dumps(q),
                                    capture_output=True, text=True, check=True).stdout)
    return {g["name"]: (m if g.get("match", "contains") == "contains" else not m) for g, m in zip(regex, res)}


def one_run(a, case: dict, desc: str) -> dict:
    tools = [tool_schema(desc, a.tool)]
    messages = [] if a.no_instructions else [{"role": "system", "content": server_instructions(desc, a.tool)}]
    messages.append({"role": "user", "content": case["execution"]["prompt"]})
    calls, reads, ratio, error, final = [], [], 4.0, None, ""
    t0 = time.time()
    for turn in range(1, a.max_turns + 1):
        # Refuse a prompt that would overflow the loaded context: some servers
        # crash instead of returning an error. Chars per token is learned from
        # the prompt_tokens each response reports.
        size = len(json.dumps(messages)) + len(json.dumps(tools))
        if size / ratio > a.ctx_limit:
            error = f"context overflow: estimated {int(size / ratio)} tokens, limit {a.ctx_limit}"
            break
        try:
            resp = chat(a.base_url, a.model, messages, tools)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            detail = e.read().decode()[:300] if isinstance(e, urllib.error.HTTPError) else str(e)
            error = f"api error: {detail}"
            break
        pt = (resp.get("usage") or {}).get("prompt_tokens")
        if pt and pt > 1000:
            ratio = size / pt
        msg = resp["choices"][0]["message"]
        tcs = msg.get("tool_calls") or []
        messages.append({k: v for k, v in msg.items() if k in ("role", "content", "tool_calls")})
        if not tcs:
            final = msg.get("content") or ""
            break
        for tc in tcs:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {"_raw": tc["function"].get("arguments")}
            calls.append({"name": fn, "args": args})
            if fn == TOOL and isinstance(args, dict) and "_raw" not in args:
                out = run_tool(a.skill_dir, desc, args, a.tool)
                read = args.get("file") or ("SKILL.md" if a.tool == "single-file" else None)
                if read and "error" not in out:
                    reads.append(read)
            else:
                out = {"success": False, "error": f"Unknown tool {fn!r} or bad arguments."}
            messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": json.dumps(out)})
    else:
        error = f"reached maximum number of turns ({a.max_turns})"
    g = grade(case, final) if final else {x["name"]: False for x in case["graders"] if x["type"] == "regex"}
    return {"final": final, "error": error, "turns": turn, "secs": round(time.time() - t0, 1),
            "calls": calls, "reads": reads, "graders": g,
            "score": sum(g.values()) / len(g) if g else None}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--case", action="append", default=[])
    p.add_argument("--all-regex", action="store_true", help="every case with a regex grader")
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--label", default="run")
    p.add_argument("--skill-dir", type=Path, default=REPO / "skills" / SKILL)
    p.add_argument("--base-url", default=os.environ.get("LOCAL_MODEL_BASE_URL", "http://localhost:1234"))
    p.add_argument("--tool", choices=["legacy", "single-file"], default="legacy",
                   help="ha_get_skill_guide shape: legacy (af9b054a) or single-file")
    p.add_argument("--no-instructions", action="store_true")
    p.add_argument("--max-turns", type=int, default=10)
    p.add_argument("--ctx-limit", type=int, default=96000, help="tokens; set just under the loaded context")
    a = p.parse_args()
    if not shutil.which("node"):
        sys.exit("node is required: regex graders are JavaScript patterns")
    cases = sorted(a.case)
    if a.all_regex:
        cases = sorted(c.parent.name for c in (REPO / "evals").glob("*/case.yaml")
                       if any(g["type"] == "regex" for g in yaml.safe_load(c.read_text())["graders"]))
    if not cases:
        sys.exit("give --case at least once, or --all-regex")
    desc = frontmatter_description(a.skill_dir)
    a.out.mkdir(parents=True, exist_ok=True)
    for n in range(1, a.runs + 1):
        for name in cases:
            path = a.out / f"{name}-{a.label}-r{n}.json"
            if path.exists() and path.stat().st_size:
                continue
            case = yaml.safe_load((REPO / "evals" / name / "case.yaml").read_text())
            r = one_run(a, case, desc)
            r.update({"case": name, "label": a.label, "run": n, "model": a.model,
                      "instructions": not a.no_instructions, "tool": a.tool})
            if r["error"] and r["error"].startswith("api error"):
                print(f"{time.strftime('%T')} FAILED {path.name}: {r['error'][:160]}", flush=True)
                continue
            path.write_text(json.dumps(r, indent=1))
            print(f"{time.strftime('%T')} {path.name} score={r['score']:.2f} turns={r['turns']} "
                  f"secs={r['secs']} reads={r['reads']} {r['error'] or ''}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
