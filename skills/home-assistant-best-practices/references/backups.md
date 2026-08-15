# Backups and Recovery

**Three different things get called a "backup" in Home Assistant work.** This file covers the first two, and only the first is a Home Assistant feature:

1. A **full instance backup** — the archive Home Assistant creates at *Settings → System → Backups*, which is also the surface for restoring and deleting one.
2. **Object rollback** — not an HA feature but a workflow: fetch an object's current definition *before* editing it, then write that definition back through the same config API to undo. One object, no restart.
3. The **pre-edit file copy** a managed YAML write takes — a different mechanism entirely, covered in `references/yaml-only-integrations.md`.

**Restoring a backup, deleting a backup, and upgrading Core are irreversible and require explicit user confirmation before you act — every time, including when a backup already exists.** A backup lowers recovery risk; it does not authorize the action.

## Table of Contents
1. [Which Recovery Path](#which-recovery-path)
2. [When a Full Backup Earns Its Cost](#when-a-full-backup-earns-its-cost)
3. [What a Full Backup Contains](#what-a-full-backup-contains)
4. [Restoring: Consequences and Verification](#restoring-consequences-and-verification)
5. [Deleting Backups](#deleting-backups)
6. [Common Pitfalls](#common-pitfalls)

---

## Which Recovery Path

| Situation | What to do |
|-----------|------------|
| One automation / script / scene / dashboard / helper edit went wrong | **Roll the object back** — write its previous definition back through the config API. No restart, nothing else touched. Fetching before writing is what makes this possible; see `references/safe-refactoring.md#universal-workflow`. |
| Several objects were edited in one session | **Roll each object back**, one at a time. Still no restart. |
| A device, entity, or area was deleted from the registry | **Restore a full backup.** Registry state — IDs, area/label assignments, and the references other config held to them — cannot be recovered by writing a definition back. |
| An integration or config entry was removed | **Restore a full backup.** Its entities went with it. |
| An App update or removal broke something | **Restore a full backup partially** — that App and its data only. |
| A Core or Operating System upgrade broke the instance | **Restore a full backup.** |
| The instance no longer boots | **Restore a full backup** through the Supervisor / onboarding restore flow. |

Prefer the narrowest path that can fix the fault. Object rollback is scoped to one object, needs no restart, and cannot lose unrelated work.

**Partial restore is a narrower restore, not a rollback.** HA's partial restore (`hassio.restore_partial`) picks which parts of an existing backup to put back — Home Assistant settings, specific Apps, and folders. Including Home Assistant settings restarts HA. That is a different mechanism from writing one object's definition back through the config API, which restarts nothing.

## When a Full Backup Earns Its Cost

The test is reversibility, not how risky something feels: **back up before an operation you cannot undo by writing the old value back.**

**Irreversible — take the backup first, and confirm the operation with the user:**
- Deleting a device, entity, or area from the registry.
- Removing an integration or config entry.
- Removing an App, or a major App version jump.
- Core / Operating System upgrades.
- Restoring a *different* backup — a restore is itself destructive of current state.
- Bulk operations across many objects whose before-state was not captured.
- Editing a Config-Entry integration whose fields have no post-setup API write path — see `references/safe-refactoring.md#config-entry-data--blind-spots-for-entity-registry-renames`.

**Reversible — a backup is usually redundant:**
- Editing an automation / script / scene / dashboard / helper whose current definition was fetched first. Writing that definition back *is* the undo.
- Renaming a friendly name, changing an icon, moving an entity between areas.
- A service call whose inverse you can name and target identically — `light.turn_on` ↔ `light.turn_off` on the same entity.

**Neither list — treat as irreversible until you have checked:** a service call with no inverse (`vacuum.send_command`, any `*.press`, `notify.*`); anything that drives a physical mechanism (locks, covers, valves, garage doors); and anything whose effect leaves Home Assistant, since a sent notification or fired webhook cannot be recalled. "It's just a service call" is not a reversibility argument — the inverse depends on the service and the target.

Two things this test depends on:

- **Timing is the whole point.** A backup taken *after* the destructive step captures the damage. It must precede the operation.
- **An existing schedule does not substitute.** On an instance with nightly automatic backups, the newest one can be almost a day stale — fine for reversible edits, not for an irreversible operation about to run now.

## What a Full Backup Contains

Backup contents are **selected per backup**, so what a given archive holds is a property of that archive, not of Home Assistant:

- **Home Assistant settings** — the config directory: `.storage` registries, YAML configuration, and the stored automations, scripts, scenes, dashboards, and helpers.
- **The recorder database — included by default.** `include_database` defaults to true, so history and long-term statistics normally *are* in the backup and *do* come back on restore. The exceptions are a backup created with that option switched off, and a recorder pointed at an external database, which lives outside the backup entirely. Check the archive before telling a user their history will or won't return.
- **Apps**, individually selectable, with their data directories.
- **Folders**, individually selectable: `share`, `addons/local`, `ssl`, `media`.

Nothing else on the host is included, and a restore overwrites only the parts a given backup actually contains.

**Encryption and secrets.** Backups are password-protected by default, and restoring one requires its encryption key — the key issued in the backup emergency kit when HA sets up encrypted backups. **An archive without its key is not a recovery point**, so verify the user has the emergency kit before treating a backup as a fallback. A backup downloaded through the UI is decrypted on the way out, and that copy carries `.storage` in cleartext — credentials, long-lived tokens, API keys. Protect the archive and the emergency kit as separate secrets, and never move either anywhere the user has not chosen.

## Restoring: Consequences and Verification

- **Confirm before restoring.** Naming which changes will be lost is part of the ask.
- A **full restore** reverts every included part to its state at backup time and restarts HA. Unrelated work done in that window is gone.
- A **partial restore** narrows the blast radius; prefer it whenever the fault is localised. Including Home Assistant settings still restarts HA.
- An **object rollback** through the config API restarts nothing and touches one object.

After any restore, verify rather than assume:
- Entities are available, not `unavailable` — a restored config entry whose credentials expired comes back broken.
- The error log is clean of startup failures.
- Cloud-backed integrations may need re-authentication; a restore replays a token that may have been rotated since.
- Objects that were disabled when the backup was taken come back disabled.

## Deleting Backups

Be precise about what Home Assistant protects here, because it is less than it looks:

- The **retention cleanup** that enforces a backup schedule will not delete the last remaining backup for a backup location.
- A **direct delete of one specific backup** — the operation performed when a user asks for a particular backup to be removed — has **no such guard**, and there is no minimum-age protection anywhere. Delete the only recovery point and Home Assistant will carry it out.

So on this operation the caution has to come from whoever is driving, not from the platform:

- **Confirm the specific backup with the user before deleting it** — name which one and how old it is.
- **Leave at least one recent, usable recovery point.** Usable includes having its encryption key available.
- **Delete oldest first** when clearing several.

Storage pressure is not the only legitimate reason to delete. A credential compromise can make the archive itself the liability; a privacy or retention requirement can mandate removal; and a user can simply ask. None of those removes the confirmation step or the keep-one-recovery-point guidance.

## Common Pitfalls

- **Backing up after the destructive step.** The archive now contains the damage.
- **Using a full restore to undo one config edit.** It reverts every unrelated change since, and restarts HA.
- **Assuming a direct backup delete is guarded.** It isn't — only the scheduled retention cleanup keeps a last backup.
- **Treating an archive without its encryption key as a recovery point.** It cannot be restored.
- **Treating a UI-downloaded backup as an ordinary file.** It is decrypted, and it holds cleartext credentials and tokens.
- **Claiming history will or won't come back without checking.** The recorder database is included by default, but per-backup selection and external databases both change the answer.
- **Calling a service "reversible" without naming its inverse.**
- **Treating a backup as a substitute for fetching the current definition before an edit.** Fetching is cheaper, object-scoped, and needs no restart to undo.
- **Keeping backups only on the instance they back up.** One disk or host failure takes the instance and its recovery points together.
- **Acting on an irreversible operation because a backup exists.** The backup is the safety net, not the authorization — the user's confirmation is.
