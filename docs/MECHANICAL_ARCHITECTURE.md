# Hot Rod #4 — Mechanical Architecture v1

This document translates the current Hot Rod #4 design conversation into an explicit engineering package that Rod Forge can treat as a source of truth.

The machine is intentionally split into **visual identity**, **mechanical architecture**, and **validated fabrication data**. The first two can be authored and iterated in Rod Forge today. The third requires engineering analysis and physical validation before any real-world build.

Authoritative parameters live in:

```text
configs/hotrod_mechanical_v1.yaml
```

## 1. Vehicle intent

Hot Rod #4 is a chopped 1930s-style pickup silhouette built around a modern mechanical package:

- 2710 × 1710 × 1260 mm design envelope,
- exposed longitudinal supercharged V8,
- front-mid engine placement,
- rear transaxle,
- independent suspension front and rear,
- inboard pushrod/rocker actuation as the preferred suspension package,
- removable front module and rear subframe,
- large rear-biased wheel package,
- mechanical components deliberately visible,
- telemetry integrated from the beginning.

The visual rule is simple: **it may look primitive and brutal, but its internal architecture is deliberate and modern.**

## 2. Front corner

### Wheel and hub

Canonical starting package:

- tire OD: 580 mm,
- tire width: 200 mm,
- rim: 17 in,
- 5-bolt hub,
- baseline PCD: 114.3 mm, retained as parametric,
- M12 × 1.5 studs,
- hub-centric location,
- nominal hub pilot: 67.0 mm.

The wheel must not depend on lug nuts for centering.

### Brake

Starting package:

- 330 mm two-piece ventilated rotor,
- 28–30 mm rotor thickness,
- 4-piston caliper.

Caliper envelope and wheel barrel clearance are validation gates, not assumptions.

### Suspension

Preferred architecture:

```text
upper wishbone
      \
       upright — hub — wheel
      /
lower wishbone ---- pushrod -> rocker -> inboard coilover
```

Initial targets:

- static camber: -0.5°,
- caster: 6–8°, target 7°,
- toe: approximately 0.05° in,
- KPI/SAI: 8–10°, target 9°,
- scrub radius: +10 to +25 mm,
- front roll-center height: 50–90 mm,
- motion ratio target: 0.75.

Track width is intentionally adjustable:

- fine adjustment: ±10 mm per side,
- coarse module concept: -25 / 0 / +25 mm per side.

### Steering

Rack-and-pinion steering is authoritative. Ackermann geometry is required and bump steer must be minimized through actual kinematic analysis.

## 3. Rear corner

### Wheel and hub

Canonical starting package:

- tire OD: 680 mm,
- tire width: 320 mm,
- rim: 20 in,
- three-piece deep-dish construction,
- 5-bolt hub,
- baseline PCD: 114.3 mm,
- alternate 120 mm retained only as a candidate,
- M14 × 1.5 studs,
- nominal hub pilot: 72.6 mm.

The rear wheel is intentionally larger and wider than the front to create the Hot Rod #4 stance without relying on arbitrary bodywork.

### Brake

Starting package:

- 355 × 28 mm ventilated rotor,
- 4-piston caliper,
- independent parking-brake mechanism or secondary caliper.

### Suspension

The rear is independent, not a conventional solid axle.

Preferred topology:

- upper wishbone,
- lower wishbone,
- adjustable toe link,
- upright,
- CV half-shaft,
- pushrod/rocker,
- inboard coilover.

Initial targets:

- static camber: -1.0° to -1.5°, target -1.25°,
- toe-in: 0.10° to 0.20° per side,
- anti-squat: 20–40%, target 30%,
- rear roll center above the front roll center,
- rear track slightly wider than front.

## 4. Powertrain

The V8 is positioned as far rearward as practical while preserving the front-engine Hot Rod visual language.

```text
front
  ↓
[V8 + blower]
      │
 torque tube / driveshaft
      │
[rear transaxle + LSD]
      │          │
   CV shaft   CV shaft
      │          │
   rear L     rear R
```

Authoritative concept:

- longitudinal front-mid V8,
- exposed supercharger,
- three-intake blower visual signature,
- rear transaxle,
- LSD required,
- clutch-type and helical LSD retained as candidates,
- baseline final-drive target: 3.73,
- 3.55 and 3.91 retained for later gearing analysis.

The transaxle is primarily a mass-distribution and packaging decision, not a styling gimmick.

## 5. Mass distribution

Primary target:

```text
front 48% / rear 52%
```

Acceptable exploration window:

```text
47–49% front
51–53% rear
```

This target must be recomputed when actual engine, transaxle, fuel, cooling, battery, driver, body and frame masses exist.

## 6. Chassis

The chassis is a hybrid spaceframe with three major zones:

```text
[removable front module]
          ||
   [central safety cell]
          ||
 [removable rear subframe]
```

The front module carries the front suspension, steering, cooling support and front mechanical packaging.

The central structure carries the cockpit, driveline tunnel and primary load path.

The rear subframe carries the transaxle and rear suspension pickups.

Suspension pickups must be triangulated into the structural frame. Body panels are non-structural by default unless explicitly redesigned otherwise.

## 7. Telemetry from day one

The vehicle package reserves sensors for:

- wheel speed,
- suspension travel,
- steering angle,
- brake temperature,
- bearing temperature,
- body acceleration,
- derived dynamic camber,
- estimated wheel load,
- estimated tire slip.

This is not cosmetic telemetry. Rod Forge should eventually use this same parameter model to compare predicted geometry against measured behavior.

## 8. Modularity rule

A major design principle is that the car should tolerate controlled changes without redesigning the entire machine.

Examples:

- wheel removal through standard 5-lug hardware,
- wheel width and offset changes through multipiece rear rims,
- coarse/fine front track adjustment,
- replaceable front module,
- replaceable rear subframe,
- adjustable rear toe,
- serviceable brake rotors,
- changeable final drive and LSD strategy.

Every adjustable feature must have a defined range and a locking method. “Adjustable” must never mean “structurally vague.”

## 9. What is frozen vs provisional

### Frozen for v1 modeling

- overall envelope,
- 17 in / 580 × 200 front wheel package,
- 20 in / 680 × 320 rear wheel package,
- 5-lug architecture,
- independent double-wishbone suspension,
- pushrod/rocker preferred packaging,
- rack-and-pinion steering,
- front-mid V8,
- rear transaxle,
- modular front and rear structures,
- rear-biased mass target,
- exposed mechanical language.

### Provisional until validated

- exact PCD and hub pilot production dimensions,
- stud grade and final stud diameter,
- bearing selection,
- rotor/caliper production sizing,
- pickup-point coordinates,
- spring/damper rates,
- motion ratios after packaging,
- exact roll centers,
- anti-squat percentage,
- final drive,
- LSD type,
- track widths,
- real curb mass and CG height.

## 10. Required validation before fabrication

No value in this document should be treated as fabrication approval. A real vehicle requires at minimum:

1. suspension kinematic simulation through bump/rebound and steering,
2. bump-steer and Ackermann verification,
3. wheel/rotor/caliper clearance model,
4. hub, bearing and fastener load analysis,
5. brake torque and thermal sizing,
6. half-shaft/CV angle and torque analysis,
7. frame and suspension-pickup FEA,
8. tire load-rating verification,
9. steering-effort analysis,
10. cooling and driveline packaging,
11. roadworthiness, crash and regulatory review applicable to the build location.

## 11. Rod Forge implementation order

The planner should construct the mechanical package in this dependency order:

```text
chassis blockout
    ↓
front/rear wheel masters
    ↓
front hubs + brakes
rear hubs + brakes
    ↓
front uprights + wishbones + steering
rear uprights + wishbones + toe links
    ↓
pushrods + rockers + inboard dampers
    ↓
front-mid V8 package
    ↓
rear transaxle + differential + half-shafts
    ↓
central frame + modular subframes
    ↓
body shell fitted around validated mechanical envelopes
```

This is the key change in philosophy: **the body no longer invents the mechanics. The mechanics establish hard envelopes, and the body is fitted around them.**
