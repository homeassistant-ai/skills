# Backups and Recovery

Home Assistant has **two independent recovery layers with very different blast radii**: a *full instance backup* (a tarball of the config directory and add-ons — restoring it restarts HA and reverts everything changed since it was taken) and *config-level rollback* (re-applying one stored automation/script/scene/dashboard/helper definition — no restart, one object). Picking the wrong layer is the common failure: a full restore used to undo a single automation edit also discards every unrelated change made in between.

## Table of Contents
1. [Which Recovery Layer](#which-recovery-layer)
2. [When a Full Backup Earns Its Cost](#when-a-full-backup-earns-its-cost)
3. [What a Full Backup Contains](#what-a-full-backup-contains)
4. [Restoring: Consequences and Verification](#restoring-consequences-and-verification)
5. [Why Deleting Backups Is Guarded](#why-deleting-backups-is-guarded)
6. [Common Pitfalls](#common-pitfalls)

---

## Which Recovery Layer

| Situation | Layer |
|-----------|-------|
| One automation / script / scene / dashboard / helper edit went wrong | Config-level rollback — write the previous definition back. No restart. |
| Several config objects edited in one session went wrong | Config-level rollback, one object at a time. Still no restart. |
| A device, entity, or area was deleted from the registry | Full backup. Registry state (IDs, area/label assignments, and every reference other config held) is not recoverable from a config-level snapshot. |
| An integration / config entry was removed | Full backup. Its entities and their recorded history went with it. |
| An add-on update or removal broke something | Full backup, restored partially — the affected add-on only, where the restore flow allows it. |
| A Core or OS upgrade broke the instance | Full backup restore. |
| The instance no longer boots | Full backup restore through the Supervisor / onboarding restore flow. |

Prefer the narrowest layer that can fix the problem. Config-level rollback is object-scoped, needs no restart, and cannot lose unrelated work.

## When a Full Backup Earns Its Cost

The rule is reversibility, not risk-feel: **take a full backup before an operation you cannot undo by writing the old value back.**

**Irreversible — back up first:**
- Deleting a device, entity, or area from the registry.
- Removing an integration or config entry.
- Removing an add-on, or a major add-on version jump.
- Core / Operating System version upgrades.
- Restoring a *different* backup — a restore is itself destructive of current state.
- Bulk operations across many objects whose before-state was not captured.

**Reversible — a backup is usually redundant:**
- Editing an automation / script / scene / dashboard / helper whose current definition was fetched first. Writing that fetched definition back *is* the undo.
- Renaming a friendly name, changing an icon, moving an entity between areas.
- Toggling an entity or calling a service.

Two things this rule depends on:

- **Timing is the whole point.** A backup taken *after* the destructive step captures the damage. It must precede the operation, not follow it.
- **An existing backup schedule does not substitute.** On an instance with nightly automatic backups, the newest one can be almost a day stale — fine for reversible edits, not for an irreversible operation about to run now.

## What a Full Backup Contains

- The config directory: registries under `.storage`, YAML configuration, and the stored automations, scripts, scenes, dashboards, and helpers.
- Add-ons and their data directories. Add-on selection is often partial — check what a given backup actually included before relying on it.
- The recorder database is **optional and commonly excluded**, because it dominates the size. Excluded means long-term statistics and history do not come back on restore, even though every entity does.
- Nothing outside the config directory. Files elsewhere on the host are not in the backup.

Backups contain credentials, tokens, and API keys in cleartext inside `.storage`. Treat the tarball as a secret: encrypt it, and do not copy it anywhere the user has not chosen.

## Restoring: Consequences and Verification

- A **full restore reverts everything** changed since the backup was taken, then restarts HA. Name the changes that will be lost and confirm before restoring — the user often has unrelated work in that window.
- A **partial restore** (config only, or one add-on) narrows the blast radius. Prefer it whenever the fault is localised.
- A **config-level rollback** re-applies one definition through the normal write path; the object reloads and no restart happens.

After any restore, verify rather than assume:
- Entities are available, not `unavailable` — a restored config entry whose credentials expired comes back broken.
- The error log is clean of startup failures.
- Cloud-backed integrations may need re-authentication; a restore replays a token that has since been rotated.
- Objects that were disabled when the backup was taken come back disabled.

## Why Deleting Backups Is Guarded

Deleting backups is guarded because the point of a backup is to survive a mistake made by whoever is currently editing the instance — including an automated agent. Three properties follow:

- **The newest remaining backup is never a valid delete target.** It is the only guaranteed rollback for whatever just happened.
- **Scheduled / automatic backups belong to a retention policy.** Deleting them ad hoc silently breaks the guarantee the schedule was configured to provide.
- **A minimum-age floor protects the recent ones.** Breakage is usually noticed hours after the change that caused it, so a young backup may be the only snapshot predating the change under investigation.

Storage pressure is the legitimate reason to delete. When it applies: delete oldest-first, keep the newest and the most recent known-good, and confirm the specific target with the user.

## Common Pitfalls

- **Backing up after the destructive step.** The snapshot now contains the damage.
- **Using a full restore to undo one config edit.** Discards every unrelated change made since.
- **Expecting history back.** The recorder database is usually excluded; entities return, their statistics do not.
- **Deleting the newest backup to free space.** Removes the only recovery point for the change being investigated.
- **Treating a backup as a substitute for fetching the current definition before an edit.** Fetching is cheaper, object-scoped, and needs no restart to undo.
- **Keeping backups only on the instance they back up.** One disk or host failure takes the instance and its recovery points together. Copy them off-box.
