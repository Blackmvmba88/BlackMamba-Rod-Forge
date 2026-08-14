# BlackMamba Rod Forge

> **Divide. Construye. Evalúa. Corrige. Continúa.**

BlackMamba Rod Forge es un constructor autónomo orientado a piezas para transformar una referencia visual estilizada en una escena 3D organizada dentro de Blender.

El primer objetivo es un hot rod ilustrado. El objetivo real es más grande: construir una arquitectura capaz de **analizar una referencia, producir un grafo de piezas, planear tareas, ejecutar geometría, evaluar resultados, reparar fallos, persistir estado y continuar hasta terminar o encontrar un bloqueo real**.

## Principio rector

Rod Forge no es una macro larga de Blender.

Es un **loop de construcción con memoria de estado**.

```text
Referencia visual
      ↓
Reference Analyzer
      ↓
Part Graph
      ↓
Task Planner
      ↓
Executor (Dry Run / Blender)
      ↓
Critic
      ↓
Repair Engine
      ↓
State + Checkpoint
      ↓
Siguiente tarea viable
```

La regla operativa central es:

> **Mientras exista una tarea viable, el sistema continúa.**

## Estado del proyecto

Esta versión inicial instala la columna vertebral del sistema:

- modelo de datos de tareas y proyecto,
- persistencia atómica de estado,
- grafo de dependencias,
- planificador determinista para el hot rod inicial,
- orquestador autónomo,
- ejecutor `dry-run`,
- ejecutor Blender con operaciones mínimas,
- crítico estructural,
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

## Arquitectura

```text
src/rodforge/
├── schemas.py            # contrato de datos
├── reference_analyzer.py # descripción estructurada de la referencia
├── part_graph.py         # dependencias
├── task_planner.py       # creación de tareas
├── state_manager.py      # persistencia atómica
├── checkpointing.py      # snapshots recuperables
├── blender_executor.py   # dry-run + bpy
├── critic.py             # validación
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
- último error.

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

Esto permite validar planner, dependencias, estado, reintentos y checkpoints antes de meter geometría real.

## Blender headless

Cuando Blender esté instalado y `bpy` disponible:

```bash
blender --background --python blender/startup.py -- \
  run --config configs/project.yaml --executor blender
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
8. producir un `.blend` inicial cuando corre dentro de Blender.

## Lo que NO hace todavía

- reconstrucción fotogramétrica,
- inferencia geométrica perfecta desde una sola vista,
- visión multimodal automática avanzada,
- retopología final,
- UVs de producción,
- simulación física del vehículo,
- validación visual neuronal.

Esas capacidades pertenecen a etapas posteriores. Primero se vuelve **confiable el constructor**.

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
- [ ] guardar primer `.blend` verificado
- [ ] preview automatizado

### Fase 3 — Forma
- [ ] comparación de silueta
- [ ] proporciones parametrizadas
- [ ] biblioteca de piezas

### Fase 4 — Estilo
- [ ] toon shading
- [ ] outline
- [ ] pintura y desgaste procedural

### Fase 5 — Gemelo creativo
- [ ] análisis multimodal
- [ ] variantes automáticas
- [ ] crítica visual iterativa
- [ ] reconstrucción por instrucciones

---

**BlackMamba Rod Forge** no se detiene porque aparezca un problema. Se detiene únicamente cuando el problema ya no tiene una ruta viable de resolución.
