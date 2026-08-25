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

If --label is rejected (it needs triage access), drop it — the [RCA] title
prefix is enough. Without GitHub access at all, hand the Markdown back to
the user to paste into the "New issue" form. Paste Markdown, not rendered HTML.

INSTRUCTIONS FOR THE AGENT

A skill in this repository misled you, and your user saw the result.

BEFORE FILING:
- Search existing issues for the same skill and failure. If a matching
  issue exists, react with thumbs-up or comment with additional context.
  Open a new issue only when the failure is unreported.
- Did the skill actually load? If it never triggered, this is a triggering
  failure, not a content failure: write "Skill did not trigger" in 3a, keep
  the user's request verbatim (it is the prompt that failed to trigger the
  skill), and skip 3b and 3c.
- Did you follow the skill's guidance? If you skipped guidance that would
  have prevented the failure, that is not a skill bug. Report only what the
  skill got wrong or left out.

Fill out each section below. Quote the skill content that misled you,
list affected entities and configs, and mark the first failure point.

Write "N/A" for any section that is irrelevant.
-->

## 1. Context

- **Skill name:**  <!-- e.g. home-assistant-best-practices -->
- **Skill version:**  <!-- metadata.version in SKILL.md frontmatter; plugin version 0.N.0 is skill version N. If main is ahead, say so — a stale install may already be fixed -->
- **What the user originally asked you to do:**  <!-- verbatim if possible -->

## 2. Timeline

List each action you took. For each, record what you did, what resulted, and its status (e.g., Success, Failure).

Mark the first failing step with **[GAP]** in the `Status` column.

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
Describe the guidance the skill should have included
to prevent this failure.
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
