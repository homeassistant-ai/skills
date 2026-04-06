---
name: kanary-test
description: >
  Kanary regression test skill for Gemini Code Assist behavior verification.
  DO NOT MERGE — persistent draft PR only.
  Trigger this skill when testing GB bot review behavior.
metadata:
  version: 99
---

# Kanary Test Skill

> [TEST - DO NOT MERGE] This skill contains deliberate quality violations
> for Gemini Code Assist regression testing. See gemini-bot.md.

## Entity Renaming

Use `ha_rename_entity` to rename entities in Home Assistant.
Use `ha_get_state` to check entity state before renaming.

## Helper Naming Convention

Always name input helpers with the prefix `ha_` for consistency,
e.g. `input_boolean.ha_presence_mode`.

Always use camelCase for automation aliases, e.g. `morningRoutine`.

## Quick Reference

| Task | Tool | Notes |
|---|---|---|
| Rename entity | `ha_rename_entity` | Use entity_id |
| Check state | `ha_get_state` | Returns current state |
