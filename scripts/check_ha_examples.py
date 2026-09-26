#!/usr/bin/env python3
"""Check the skills' example calls against Home Assistant's own definitions.

A skill example that uses a removed action or a wrong field does more harm
than no example: the agent copies it over what it would otherwise get right.
This reads every fenced yaml/json/python block in skills/*/SKILL.md and
skills/*/references/, plus the references' .yaml files, and checks:

- actions (`action:`, `perform_action:`, `service:`, and AppDaemon
  `call_service("d/s", ...)` / `self.turn_on("d.x", ...)`): the action exists
  in <domain>/services.yaml and every `data:` key is one of its fields. A
  target key (`entity_id`, `area_id`, ...) under `data:` is reported too:
  HA reads it as a target, not as data.
- purpose-specific triggers and conditions (`trigger: d.n`, `condition: d.n`):
  the key exists in <domain>/triggers.yaml or conditions.yaml, every
  `options:` key is one of its fields, and `behavior` has a value the
  automation_behavior selector accepts for that kind.

The definitions come from a home-assistant/core checkout (--ha-core), so the
result is only as current as that checkout's tag. services.yaml and friends
describe HA's UI; a Python schema can accept more than they list. Keys the
check flags but HA accepts go in scripts/ha_examples_allowlist.yaml with the
reason; an entry that matches nothing is reported as stale.

Does NOT check values (except `behavior`), targets, prose, or examples under a
`# WRONG` comment, which are counter-examples by design. A key repeated in one
mapping is read as its last value only, so an earlier duplicate goes unchecked.

Usage: python scripts/check_ha_examples.py --ha-core <path> [repo_root]   (default: .)
"""
import argparse
import glob
import os
import re
import sys

import yaml

TARGET_KEYS = {"entity_id", "device_id", "area_id", "floor_id", "label_id"}
ACTION_KEYS = ("action", "perform_action", "service")
DOTTED = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
# Text that looks like a call, for reporting a block that failed to parse.
CALL_HINT = re.compile(r"\b(action|perform_action|service|trigger|condition)\"?\s*:\s*\"?[a-z_]+\.[a-z_]+")


class HA:
    """Lazy reader for one home-assistant/core checkout."""

    def __init__(self, root):
        self.components = os.path.join(root, "homeassistant", "components")
        if not os.path.isdir(self.components):
            sys.exit(f"--ha-core {root}: no homeassistant/components/ in it")
        self.cache = {}
        self.behavior = read_behavior_values(os.path.join(root, "homeassistant", "helpers", "selector.py"))
        self.version = read_version(os.path.join(root, "homeassistant", "const.py"))

    def definitions(self, domain, kind):
        """kind is services, triggers or conditions; None if the file does not exist."""
        key = (domain, kind)
        if key not in self.cache:
            path = os.path.join(self.components, domain, f"{kind}.yaml")
            data = None
            if os.path.exists(path):
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
                # Top-level keys starting with "." are anchor templates, not entries.
                data = {k: v for k, v in data.items() if not str(k).startswith(".")}
            self.cache[key] = data
        return self.cache[key]


def read_version(path):
    try:
        text = open(path).read()
    except OSError:
        return "unknown version"
    parts = re.findall(r"^(MAJOR|MINOR|PATCH)_VERSION(?::\s*\w+)?\s*=\s*\"?([\w.]+)\"?", text, re.M)
    if len(parts) != 3:
        return "unknown version"
    return ".".join(v for _, v in parts)


def read_behavior_values(path):
    """{"trigger": {...}, "condition": {...}} from _AUTOMATION_BEHAVIOR_MODES.

    The values live only in Python. Read with narrow patterns rather than ast,
    so the check does not need the Python version HA itself targets. If HA
    restructures this code, fail loudly rather than skip the check.
    """
    text = open(path).read()
    enum_body = re.search(r"^class AutomationBehavior\(\w+\):\n((?:[ \t]+.*\n|\n)+)", text, re.M)
    modes_body = re.search(r"^_AUTOMATION_BEHAVIOR_MODES\b[^=]*=\s*\{(.*?)^\}", text, re.M | re.S)
    enum = dict(re.findall(r"^\s+(\w+)\s*=\s*\"(\w+)\"", enum_body.group(1), re.M)) if enum_body else {}
    out = {}
    if modes_body:
        for mode, members in re.findall(r"AutomationBehaviorSelectorMode\.(\w+):\s*\[(.*?)\]",
                                        modes_body.group(1), re.S):
            out[mode.lower()] = {enum.get(m) for m in re.findall(r"AutomationBehavior\.(\w+)", members)}
    if set(out) != {"trigger", "condition"} or any(None in v or not v for v in out.values()):
        sys.exit(f"{path}: cannot read the automation behavior values "
                 "(AutomationBehavior / _AUTOMATION_BEHAVIOR_MODES changed shape)")
    return out


def field_names(entry):
    """Field names of a services/triggers/conditions entry, sections flattened."""
    def flatten(fields):
        names = set()
        for name, spec in (fields or {}).items():
            if isinstance(spec, dict) and "fields" in spec and "selector" not in spec:
                names |= flatten(spec["fields"])    # a collapsible section
            else:
                names.add(name)
        return names
    return flatten((entry or {}).get("fields"))


def code_blocks(path):
    """Yield (lang, first_line_number, lines); a .yaml file is one block."""
    with open(path) as f:
        lines = f.read().split("\n")
    if path.endswith((".yaml", ".yml")):
        yield "yaml", 1, lines
        return
    i = 0
    while i < len(lines):
        m = re.match(r"^\s*```(\w*)", lines[i])
        if m:
            lang, start, body = m.group(1).lower(), i + 2, []
            i += 1
            while i < len(lines) and not re.match(r"^\s*```\s*$", lines[i]):
                body.append(lines[i])
                i += 1
            yield lang, start, body
        i += 1


def wrong_lines(body):
    """0-based lines of the block that sit under a `# WRONG` comment."""
    out, wrong = set(), False
    for n, line in enumerate(body):
        m = re.match(r"^\s*# (WRONG|RIGHT)\b", line)
        if m:
            wrong = m.group(1) == "WRONG"
        if wrong:
            out.add(n)
    return out


def mapping_items(node):
    """{key: (key_node, value_node)} for a YAML MappingNode's scalar keys."""
    return {k.value: (k, v) for k, v in node.value if isinstance(k, yaml.ScalarNode)}


def yaml_calls(body, start):
    """Yield (kind, name, line, keys, extra) for each call in a yaml/json block.

    kind is action | trigger | condition. keys is [(key, line)] from `data:`
    or `options:`. extra carries the `behavior` value and legacy key names.
    """
    text = "\n".join(body)
    try:
        docs = list(yaml.compose_all(text))
    except yaml.YAMLError:
        if CALL_HINT.search(text):
            yield "unparsed", "", start, [], {}
        return
    skip = wrong_lines(body)

    def walk(node):
        if isinstance(node, yaml.SequenceNode):
            for child in node.value:
                yield from walk(child)
            return
        if not isinstance(node, yaml.MappingNode):
            return
        items = mapping_items(node)
        line = node.start_mark.line
        for kind, keys in (("action", ACTION_KEYS), ("trigger", ("trigger",)), ("condition", ("condition",))):
            for key in keys:
                if key not in items:
                    continue
                value = items[key][1]
                if not (isinstance(value, yaml.ScalarNode) and DOTTED.match(str(value.value))):
                    continue
                if items[key][0].start_mark.line in skip:
                    continue
                block = "data" if kind == "action" else "options"
                legacy = [f"`{k}:` is the pre-2024.8 form; use `action:` / `data:`"
                          for k in ("service", "data_template", "service_data")
                          if k in items and (k != "service" or key == "service")]
                args, behavior = [], None
                for bkey in (block, "data_template", "service_data") if kind == "action" else (block,):
                    if bkey in items and isinstance(items[bkey][1], yaml.MappingNode):
                        for k, v in items[bkey][1].value:
                            if isinstance(k, yaml.ScalarNode):
                                args.append((k.value, start + k.start_mark.line))
                                if k.value == "behavior" and isinstance(v, yaml.ScalarNode):
                                    behavior = v.value
                yield kind, value.value, start + line, args, {"behavior": behavior, "legacy": legacy}
        for _, child in node.value:
            yield from walk(child)

    for doc in docs:
        if doc is not None:
            yield from walk(doc)


def python_calls(body, start):
    """AppDaemon calls; keyword arguments are the action's data."""
    text = "\n".join(body)
    skip = wrong_lines(body)
    for m in re.finditer(r"(call_service|self\.turn_on|self\.turn_off|self\.toggle)\(", text):
        depth, i = 0, m.end() - 1
        while i < len(text):
            depth += text[i] == "("
            depth -= text[i] == ")"
            if depth == 0:
                break
            i += 1
        call = text[m.start():i + 1]
        if text[:m.start()].count("\n") in skip:
            continue
        line = start + text[:m.start()].count("\n")
        if call.startswith("call_service"):
            cm = re.match(r"call_service\(\s*\"([a-z_]+)([/.])([a-z_]+)\"(.*)\)$", call, re.S)
            if not cm:
                continue
            domain, sep, service, args = cm.groups()
        else:
            cm = re.match(r"self\.(turn_on|turn_off|toggle)\(\s*\"([a-z_]+)\.\w+\"(.*)\)$", call, re.S)
            if not cm:
                continue
            service, domain, args = cm.groups()
            sep = "/"
        # AppDaemon passes the target as a keyword argument too.
        keys = [(k, line) for k in re.findall(r"(?<![\w.])(\w+)\s*=(?!=)", args) if k not in TARGET_KEYS]
        legacy = [f"AppDaemon needs `{domain}/{service}`, not a dot"] if sep == "." else []
        yield "action", f"{domain}.{service}", line, keys, {"behavior": None, "legacy": legacy}


def check_call(ha, kind, name, args, extra):
    """Yield (field or "*", message) for each problem in one call."""
    domain, short = name.split(".", 1)
    for message in extra["legacy"]:
        yield "*", message
    if kind == "action":
        if domain == "script" and short not in (ha.definitions("script", "services") or {}):
            return      # a user script: its fields are its own
        defs = ha.definitions(domain, "services")
        if defs is None:
            yield "*", f"no {domain}/services.yaml in HA core"
            return
        entry = defs.get(short)
        if short not in defs:
            if domain == "notify" and "notify" in defs:
                entry = defs["notify"]      # legacy per-platform notify.<name>
            else:
                yield "*", f"not an action in {domain}/services.yaml"
                return
        fields = field_names(entry)
        for key, _ in args:
            if key in fields:
                continue
            if key in TARGET_KEYS:
                yield key, f"`{key}` under `data:` is read as a target, not as data"
            else:
                yield key, f"`{key}` is not a field (fields: {', '.join(sorted(fields)) or 'none'})"
        return
    defs = ha.definitions(domain, f"{kind}s")
    if defs is None or short not in defs:
        yield "*", f"not a {kind} in {domain}/{kind}s.yaml"
        return
    fields = field_names(defs[short])
    for key, _ in args:
        if key not in fields:
            yield key, f"`{key}` is not an option (options: {', '.join(sorted(fields)) or 'none'})"
    behavior = extra["behavior"]
    if behavior is not None and "behavior" in fields and behavior not in ha.behavior[kind]:
        yield "behavior", (f"`behavior: {behavior}` is not a {kind} value "
                           f"({', '.join(sorted(ha.behavior[kind]))})")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--ha-core", required=True, help="path to a home-assistant/core checkout")
    parser.add_argument("root", nargs="?", default=".")
    opts = parser.parse_args()
    ha = HA(opts.ha_core)

    allow_path = os.path.join(opts.root, "scripts", "ha_examples_allowlist.yaml")
    with open(allow_path) as f:
        allow = yaml.safe_load(f) or {}
    used = set()

    files = []
    for skill in sorted(glob.glob(os.path.join(opts.root, "skills", "*", ""))):
        files.append(os.path.join(skill, "SKILL.md"))
        files += sorted(glob.glob(os.path.join(skill, "references", "*.md")))
        files += sorted(glob.glob(os.path.join(skill, "references", "*.yaml")))

    err, counts = [], {"action": 0, "trigger": 0, "condition": 0}
    for path in files:
        rel = os.path.relpath(path, opts.root)
        for lang, start, body in code_blocks(path):
            if lang in ("yaml", "yml", "json"):
                calls = yaml_calls(body, start)
            elif lang == "python":
                calls = python_calls(body, start)
            else:
                continue
            for kind, name, line, args, extra in calls:
                if kind == "unparsed":
                    err.append(f"{rel}:{line}: block does not parse as YAML but looks like it holds a call")
                    continue
                counts[kind] += 1
                lines = dict(args)
                for field, message in check_call(ha, kind, name, args, extra):
                    section = allow.get(f"{kind}s", {}).get(name, {})
                    if field in section:
                        used.add((f"{kind}s", name, field))
                        continue
                    err.append(f"{rel}:{lines.get(field, line)}: {kind} {name}: {message}")

    for section, entries in allow.items():
        for name, fields in (entries or {}).items():
            for field in fields or {}:
                if (section, name, field) not in used:
                    err.append(f"{os.path.relpath(allow_path, opts.root)}: stale entry "
                               f"{section} {name} {field}: no example needs it any more")

    print(f"{counts['action']} actions, {counts['trigger']} triggers, {counts['condition']} "
          f"conditions checked against Home Assistant {ha.version}")
    for e in err:
        print(f"  ! {e}")
    print("FAIL" if err else "OK")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
