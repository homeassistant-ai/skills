# Scenes

A scene is a **saved snapshot of target entity states, applied atomically** — not a sequential script. Activating it pushes every listed entity toward its stored state at once (optionally with a transition). Use a scene to *restore a set of states*; use a script's `sequence` when you need ordered, conditional, or timed steps.

## Table of Contents
1. [Scene Config Shape](#scene-config-shape)
2. [Activating a Scene](#activating-a-scene)
3. [Snapshot + Restore (scene.create)](#snapshot--restore-scenecreate)
4. [Apply States Without Storing (scene.apply)](#apply-states-without-storing-sceneapply)
5. [Reloading Scenes](#reloading-scenes)

---

## Scene Config Shape

```yaml
scene:
  - name: Romantic            # required; `id:` optional but recommended (stable unique id)
    icon: "mdi:flower-tulip"  # optional
    entities:
      light.tv_back_light: "on"          # simple form: entity_id → state string
      light.ceiling:                      # object form: state + attributes
        state: "on"
        brightness: 200                   # 0–255
        color_temp_kelvin: 2700           # Kelvin — NOT color_temp/mireds (removed 2026.3)
      climate.living_room:
        state: "heat"
        temperature: 21
```

- `entities` is a dict mapping `entity_id` → a state string, or an object with `state` plus the entity's attributes.
- Light color attributes use `color_temp_kelvin` / `rgb_color` / `xy_color` / `hs_color`. The mireds-based `color_temp` (and `kelvin`/`min_mireds`/`max_mireds`) were removed in 2026.3.
- A scene only sets the attributes you list; unlisted entities/attributes are untouched.
- UI-created scenes live in `scenes.yaml` and snapshot the *current* state of each added entity at save time.

## Activating a Scene

```yaml
actions:
  - action: scene.turn_on
    target:
      entity_id: scene.romantic
    data:
      transition: 2.5      # optional, seconds
```

## Snapshot + Restore (scene.create)

Capture live states into a transient scene, then restore them later — the canonical "save current state, do something, put it back" pattern.

```yaml
# Capture current states (transient scene — discarded on a config/scene reload)
- action: scene.create
  data:
    scene_id: before_alert          # required; lowercase + underscores
    snapshot_entities:              # capture the CURRENT state of these
      - light.living_room
      - light.kitchen
    entities:                       # optionally also set explicit states
      light.porch:
        state: "on"
        brightness: 255
# ...later, restore exactly what was captured:
- action: scene.turn_on
  target:
    entity_id: scene.before_alert
```

`scene.create` requires at least one of `snapshot_entities` / `entities` (they combine). The created scene is temporary and lost on a config/scene reload.

## Apply States Without Storing (scene.apply)

Push a one-off set of states atomically, with no `scene.*` entity created.

```yaml
- action: scene.apply
  data:
    entities:                       # same shape as a scene's `entities`
      light.tv_back_light:
        state: "on"
        brightness: 100
      light.ceiling: "off"
    transition: 2.5                 # optional, seconds
```

## Reloading Scenes

After editing scene YAML, apply it without restarting:

```yaml
- action: scene.reload
```
