---
name: Report Bad Skill Advice
about: A skill misled your agent. Have your agent fill out this report so we can fix the skill.
title: "[RCA] "
labels: rca
---

<!--
INSTRUCTIONS FOR THE AGENT

A skill in this repository misled you, and your user saw the result.

BEFORE FILING: Search existing issues for the same skill and failure.
If a matching issue exists, react with thumbs-up or comment with
additional context. Open a new issue only when the failure is unreported.

Fill out each section below. Quote the skill content that misled you,
list affected entities and configs, and mark the first failure point.

Write "N/A" for any section that is irrelevant.
-->

## 1. Context

- **Skill name:**  <!-- e.g. home-assistant-best-practices -->
- **What the user originally asked you to do:**

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

### 4a. Observable failure

<!--
What failure did the user observe?
Error messages, broken UI, unexpected behavior, etc.
-->

### 4b. Blast radius

<!--
List every affected component: dashboards, automations,
configurations, entities, integrations, etc.
If the failure affected only the immediate task, say so.
-->

## 5. Environment

- **Home Assistant version:**  <!-- e.g. 2025.1.3 -->
- **Agent platform and model:**  <!-- e.g. Claude Code with Opus 4.5, ChatGPT with GPT-4o -->
- **Integration / device type involved:**  <!-- e.g. ZHA, Z2M, IKEA FYRTUR, or N/A -->
