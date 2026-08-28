# Vehicle Profiles — Hot Rod + Combi

Rod Forge now separates **vehicle intelligence** from **vehicle identity**.

The same orchestration, checkpoints, cognitive memory, repair loop and Blender executor can serve multiple vehicles, while each vehicle keeps its own silhouette families, reference asset and task graph.

## Registered profiles

### `hotrod`

- Project: `blackmamba_hotrod`
- Reference asset: `hotrod.blend`
- Blueprint envelope: **2.710 × 1.710 × 1.260 m**
- Identity: chopped 1930s pickup hot rod
- Critical visual traits:
  - exposed V8
  - blower / intake
  - tall vertical grille
  - small front wheels
  - oversized rear wheels
  - exposed side exhaust
  - low chopped cabin

The blueprint envelope remains authoritative for proportion validation.

### `combi`

- Project: `blackmamba_combi`
- Reference asset: `COMBI_TOPOLOGIA_PRO.blend`
- Identity: stylized Type-2-like microbus / Combi
- Current mode: **topology first, reference driven**
- Critical visual traits:
  - long flat chassis floor
  - cab-forward front cabin
  - tall boxy body shell
  - upright windshield
  - side-window rhythm
  - sliding-door seam
  - front/rear bumpers
  - round headlights
  - compact mirrors

The Combi profile deliberately does not hard-code a real-world vehicle dimension envelope yet. Its final dimensions should be measured from `COMBI_TOPOLOGIA_PRO.blend` and then promoted into the profile as the authoritative envelope.

## Why geometry families are isolated

Hot Rod cognition must never choose a van silhouette strategy simply because both tasks are called `body_shell`.

The geometry families are therefore split:

- Hot Rod: `chassis`, `cabin`, `body`
- Combi: `van_chassis`, `van_cabin`, `van_body`
- Shared low-level family: `wheel`

Each family still exposes at least two materially different construction methods so the cognitive repair/probe loop has a real alternative rather than a renamed copy.

## Planner entry points

```python
from rodforge.task_planner import build_vehicle_plan

hotrod = build_vehicle_plan("hotrod")
combi = build_vehicle_plan("combi")

# aliases are accepted
combi_again = build_vehicle_plan("van")
```

Compatibility is preserved through:

```python
from rodforge.task_planner import build_hotrod_plan, build_combi_plan
```

## Combi task graph

1. chassis floor
2. cab-forward cabin
3. front wheels
4. rear wheels
5. body shell
6. front face
7. windshield
8. side windows
9. sliding door
10. bumpers
11. headlights
12. mirrors
13. secondary details
14. materials
15. preview

The ordering intentionally stabilizes the primary silhouette before openings, trim and decoration.

## Next implementation step

The next geometry step is to make wheel placement and body openings profile-aware inside `BlenderExecutor`, then measure the Combi `.blend` envelope and use that measurement as validation evidence. After that, the existing multi-reference curriculum can compare learning across the Hot Rod and Combi without allowing silhouette strategies to leak between profiles.
