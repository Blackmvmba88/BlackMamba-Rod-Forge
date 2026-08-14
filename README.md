# BlackMamba Rod Forge

> **Divide. Construye. Evalúa. Corrige. Continúa.**

BlackMamba Rod Forge es un constructor autónomo orientado a piezas para transformar una referencia visual estilizada en una escena 3D organizada dentro de Blender.

El primer objetivo es un hot rod ilustrado. El objetivo real es más grande: construir una arquitectura capaz de **analizar una referencia, producir un grafo de piezas, planear tareas, ejecutar geometría, evaluar resultados, reparar fallos, persistir estado, aprender de resultados observados y continuar hasta terminar o encontrar un bloqueo real**.

## Principio rector

Rod Forge no es una macro larga de Blender.

Es un **loop de construcción con memoria de estado y experiencia**.

```text
Referencia visual
      ↓
Reference Analyzer
      ↓
Part Graph
      ↓
Task Planner
      ↓
Cognitive Hypothesis
      ↓
Executor (Dry Run / Blender)
      ↓
Preview Observation
      ↓
Critic
      ↓
Prediction Error + Experience
      ↓
Repair Engine
      ↓
State + Checkpoint
      ↓
Siguiente tarea viable
```

La regla operativa central es:

> **Mientras exista una tarea viable, el sistema continúa.**

La regla cognitiva es:

> **Una hipótesis no se convierte en conocimiento hasta que resultados observados la sostienen.**

## Estado del proyecto

Esta versión instala la columna vertebral del sistema:

- modelo de datos de tareas y proyecto,
- persistencia atómica de estado,
- grafo de dependencias,
- planificador determinista para el hot rod inicial,
- orquestador autónomo,
- ejecutor `dry-run`,
- ejecutor Blender con operaciones mínimas,
- crítico estructural,
- memoria episódica persistente,
- hipótesis y confianza basadas en experiencia,
- `shadow mode` cognitivo por defecto,
- previews Blender por tarea,
- comparación visual determinista de silueta y proporción,
- señal `improvement_score` para distinguir mejora, neutralidad o retroceso,
- motor de reparación y fallbacks,
- checkpoints,
- CLI,
- configuración YAML,
- pruebas,
- GitHub Actions.

El objetivo del MVP no es fingir que una sola imagen contiene todas las vistas técnicas. El sistema trabaja por **aproximación iterativa y verificable**: primero silueta y proporciones, después piezas principales, mecánica, detalle y materiales.

## Filosofía de modelado

1. **Silueta antes que detalle**.
2. **Piezas separadas y nombradas**.
3. **Dependencias explícitas**.
4. **Cada tarea produce evidencia**.
5. **Cada hito importante genera checkpoint**.
6. **Un fallo no crítico nunca tumba el proyecto**.
7. **Un bloqueo solo existe cuando ya no queda una estrategia útil**.
8. **Predicción y observación siempre permanecen separadas**.
9. **La experiencia puede influir en acción solo después de superar umbrales de evidencia**.

## Arquitectura

```text
src/rodforge/
├── schemas.py            # contrato de datos
├── reference_analyzer.py # descripción estructurada de la referencia
├── part_graph.py         # dependencias
├── task_planner.py       # creación de tareas
├── state_manager.py      # persistencia atómica
├── checkpointing.py      # snapshots recuperables
├── blender_executor.py   # dry-run + bpy + previews observables
├── visual_feedback.py    # silueta / proporción / referencia
├── cognition.py          # hipótesis / memoria / confianza / prediction error
├── critic.py             # validación estructural + métricas visuales
├── repair_engine.py      # reintento / fallback
├── orchestrator.py       # loop autónomo
└── cli.py                # entrada de usuario

blender/
├── startup.py
└── modeling/
    └── blockout.py
```

## Pipeline inicial del hot rod

El plan base divide el vehículo en capas:

### A. Blockout
- chasis
- cabina
- volumen del motor
- ejes y posición de ruedas

### B. Cuerpo
- techo
- paneles laterales
- cofre
- caja trasera

### C. Rodaje
- rueda delantera maestra
- rueda trasera maestra
- duplicados simétricos

### D. Frente
- parrilla
- soportes
- faros

### E. Motor
- bloque
- culatas
- admisión
- blower
- escapes

### F. Acabado
- materiales base
- pintura naranja
- metal expuesto
- desgaste
- preview

## Loop cognitivo visual

Cuando se ejecuta dentro de Blender con `visual_feedback` activo, Rod Forge observa el estado después de cada tarea.

```text
acción
  ↓
preview RGBA
  ↓
silhouette_score
proportion_score
reference_match
  ↓
comparación con observación anterior
  ↓
improvement_score
  ↓
memoria episódica
```

`improvement_score` está normalizado:

```text
< 0.5  empeoró
= 0.5  neutral
> 0.5  mejoró
```

El sistema inicia en `shadow` mode: aprende y genera expectativas, pero no cambia una estrategia solo porque "cree" que otra será mejor. La activación futura exige suficientes muestras, confianza y margen de mejora.

Detalles técnicos:

- `docs/COGNITION.md`
- `docs/VISUAL_FEEDBACK.md`

## Estados de tarea

```text
pending
ready
running
completed
failed
needs_repair
blocked
skipped
```

Cada tarea conserva:

- ID,
- objetivo,
- dependencias,
- estrategia,
- criterios de éxito,
- intentos,
- máximo de intentos,
- fallbacks,
- criticidad,
- evidencia,
- último error,
- metadatos cognitivos.

## Estrategias de reparación

Orden por defecto:

```text
retry_same
split_task
simplify_geometry
alternate_method
rebuild_from_checkpoint
```

El motor de reparación no decide a ciegas: registra qué se intentó y evita repetir infinitamente la misma ruta.

## Instalación local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Dry run

El dry-run prueba **el cerebro del sistema sin abrir Blender**.

```bash
rodforge run --config configs/project.yaml --executor dry-run
```

Esto permite validar planner, dependencias, estado, reintentos, checkpoints y memoria cognitiva antes de meter geometría real.

## Blender headless

Cuando Blender esté instalado y las dependencias Python estén disponibles para su runtime:

```bash
blender --background --python blender/startup.py -- \
  run --config configs/project.yaml --executor blender
```

Con `visual_feedback.render_every_task: true`, cada tarea produce una observación en:

```text
data/outputs/previews/
```

La memoria cognitiva vive en:

```text
data/outputs/cognition/experience.json
```

## Reanudar

```bash
rodforge resume --config configs/project.yaml
```

El estado se guarda en:

```text
data/outputs/state/project_state.json
```

Los checkpoints viven en:

```text
data/outputs/checkpoints/
```

## Definición de éxito del MVP

El MVP se considera vivo cuando puede:

1. crear un plan desde la referencia configurada,
2. ejecutar las tareas respetando dependencias,
3. registrar evidencia,
4. detectar un fallo,
5. aplicar una estrategia alternativa,
6. persistir el estado,
7. reanudar después de una interrupción,
8. producir un `.blend` inicial cuando corre dentro de Blender,
9. observar visualmente estados intermedios,
10. medir si una operación mejoró o empeoró respecto a la observación anterior,
11. conservar esa experiencia para futuras ejecuciones.

## Lo que NO hace todavía

- reconstrucción fotogramétrica,
- inferencia geométrica perfecta desde una sola vista,
- visión multimodal semántica avanzada,
- retopología final,
- UVs de producción,
- simulación física del vehículo,
- crítica neuronal de estilo o intención artística,
- decisión autónoma activa basada en experiencia por defecto.

Primero se vuelve **confiable el constructor y verificable el aprendizaje**.

## Roadmap

### Fase 1 — Cerebro operativo
- [x] contratos
- [x] planner
- [x] state manager
- [x] dependency graph
- [x] orchestrator
- [x] repair engine
- [x] dry-run executor
- [x] CLI

### Fase 2 — Blender MVP
- [x] primitives bridge
- [x] blockout operations
- [ ] guardar primer `.blend` verificado en ejecución Blender real
- [x] preview automatizado por tarea

### Fase 3 — Cognición observable
- [x] memoria episódica
- [x] hipótesis antes de acción
- [x] prediction error
- [x] shadow mode
- [x] silhouette score
- [x] proportion score
- [x] reference match
- [x] improvement score
- [ ] múltiples vistas canónicas
- [ ] estrategias geométricas alternativas reales para aprendizaje comparativo

### Fase 4 — Forma
- [ ] comparación de silueta multivista
- [ ] proporciones parametrizadas
- [ ] biblioteca de piezas

### Fase 5 — Estilo
- [ ] toon shading
- [ ] outline
- [ ] pintura y desgaste procedural
- [ ] críticos independientes de estilo/material

### Fase 6 — Gemelo creativo
- [ ] análisis multimodal
- [ ] variantes automáticas
- [ ] crítica visual iterativa avanzada
- [ ] reconstrucción por instrucciones
- [ ] activación cognitiva graduada basada en experiencia verificada

---

**BlackMamba Rod Forge** no se detiene porque aparezca un problema. Se detiene únicamente cuando el problema ya no tiene una ruta viable de resolución.

Y cuando imagina que algo mejorará, no se cree a sí mismo: **lo renderiza, lo mide y aprende del resultado.**
