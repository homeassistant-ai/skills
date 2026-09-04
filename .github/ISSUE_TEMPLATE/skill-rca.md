---
name: Report Bad Skill Advice
about: A skill misled your agent. Have your agent fill out this report so we can fix the skill.
title: "[RCA] "
labels: rca
---

<!--
HOW TO FILE

For the user: give your agent this template and ask it to fill the report in —
it holds the full context of what went wrong. The raw file is at
https://raw.githubusercontent.com/homeassistant-ai/skills/main/.github/ISSUE_TEMPLATE/skill-rca.md

For the agent: write the report in Markdown, then either file it yourself:

  gh issue create --repo homeassistant-ai/skills \
    --title "[RCA] <skill>: <one-line failure>" \
    --body-file report.md --label rca

If --label is rejected (it needs triage access), either file through the
"New issue" web form — the template applies the label for you — or drop the
flag; the [RCA] title prefix is enough for triage. Without GitHub access at
all, hand the Markdown back to the user to paste into that form. Paste
Markdown, not rendered HTML.

INSTRUCTIONS FOR THE AGENT

A skill in this repository misled you, and your user saw the result.

BEFORE FILING:
- Do not re-run any step that changed the user's config. Decide from
  evidence you already have whether the failure is HA's or your tool's:
  compare the bytes your tool sent with what HA stored, read HA's own log
  line, check the state the entity actually holds. Corrupted text is
  usually the tool. A stale cache or an unapplied write can be either; the
  core file or docs page that produces the behaviour decides. If the
  evidence points at the tool, there is no skill gap: do not file. If you
  cannot tell, say so in 3b and file only if the skill's guidance would
  still have changed what you did.
- Did the skill actually load? If it never triggered, this is a triggering
  failure, not a content failure: write "Skill did not trigger" in 3a, keep
  the user's request verbatim apart from redactions (it is the prompt that
  failed to trigger the skill), and skip 3b and 3c.
- Did you follow the skill's guidance? If you skipped guidance that would
  have prevented the failure, that is not a skill bug. Report only what the
  skill got wrong or left out.
- Did your fix break a rule? A step you marked Success that does something
  the Critical Anti-Patterns table in the skill's SKILL.md forbids is a
  second failure, not a fix. The test is the path, not the tool: anything
  you wrote under .storage/, or any configuration.yaml edit for a
  UI-configured integration, counts. Mark that row Failure, and in 3c give
  the supported path or say you did not find one.
- One failure per report. If your timeline has two unrelated [GAP] rows,
  file two reports.
- Search existing issues for the same skill and failure. If a matching
  issue exists, react with thumbs-up or comment with additional context.
  Open a new issue only when the failure is unreported.
- Redact before filing: tokens, URLs, IP addresses, email addresses, names,
  and anything from the user's setup the public need not see — replace each
  with [REDACTED] and keep the wording otherwise. Show the user the finished
  report and get an explicit go-ahead before you file it.

Fill out each section below. Quote the skill content that misled you,
list affected entities and configs, and mark the first failure point.

Write "N/A" for any section that is irrelevant.
-->

## 1. Context

- **Skill name:**  <!-- e.g. home-assistant-best-practices -->
- **Skill version:**  <!-- metadata.version in SKILL.md frontmatter; plugin version 0.N.0 is skill version N. If main is ahead, say so — a stale install may already be fixed -->
- **What the user originally asked you to do:**  <!-- verbatim apart from redactions -->

## 2. Timeline

List each action you took. For each, record what you did, what resulted, and its status (e.g., Success, Failure).

Mark the first failing step with **[GAP]** in the `Status` column.

One change per row. If one step changed several things, keep them in one row and write "not attributed" in Result; do not split them and assign results you did not observe separately.

| Step | Action | Result | Status |
|------|--------|--------|-----|
| 1 | | | |
| 2 | | | |
| 3 | | | |

<!-- Add or remove rows as needed. -->

## 3. Root Cause

### 3a. What skill instruction did you follow?

<!--
Quote the SKILL.md passage or reference file section that guided
your actions. Include the file name and section heading.
If the skill offered no guidance for this scenario, write:
"No guidance found in the skill for this scenario."
If the skill never loaded, write "Skill did not trigger" and skip 3b and 3c.
-->

### 3b. What did that instruction cause you to do (or not do)?

<!--
Describe the action or omission that caused the failure,
and tie it to the skill content you quoted in 3a.
-->

### 3c. What should the skill have told you instead?

<!--
State the HA behaviour the skill should carry, not the fix that worked for
your setup. Each claim must cite the core file or docs page that shows the
behaviour; a claim you cannot cite is a hypothesis, so label it as one.
Hardware models, threshold values, and layout preferences do not go in the
skill unless the HA behaviour is specific to that integration
(CONTRIBUTING.md, Guiding Principles: skills apply to any HA installation).
If you cannot phrase it without them, it is not a skill gap: write
"No skill gap: instance-specific" here and tell the user before filing.
-->

## 4. Impact

<!--
How bad was it: what the user saw beyond the timeline (silent failures,
lost data, how long it went unnoticed) and every affected component:
dashboards, automations, configurations, entities, integrations, etc.
If the failure affected only the immediate task, say so.
-->

## 5. Environment

- **Home Assistant version and install type:**  <!-- e.g. 2026.8.1 on Home Assistant OS; or Container, Core, Supervised -->
- **Agent platform, model, and HA access:**  <!-- e.g. Claude Code with Opus 5 via an MCP server (name and version); Cursor with the REST API; Codex, files only -->
- **Integration / device type involved:**  <!-- e.g. ZHA, Z2M, IKEA FYRTUR, or N/A -->
