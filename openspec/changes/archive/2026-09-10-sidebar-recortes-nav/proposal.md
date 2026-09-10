# Proposal: Sidebar Recortes Nav

## Intent

La rail ya tiene la estructura correcta (+ Nuevo recorte, buscar, Fijados, historial),
pero todavía habla de “chats” y muestra métricas de catálogo (`Catálogo · N SKUs`,
`N SKUs · M para reponer`). La sidebar debe ser navegación de recortes, no un
resumen de datos. El workspace ya responde “qué está pasando”.

## Scope

### In Scope

- Copy: `Recientes`, vacío `Sin recortes recientes`, menú `···`
- Labels: `Inventario general` / `Todos los productos`; subtítulo `N para reponer`
  sin la palabra SKU; sin `Catálogo ·`
- Grupos: Hoy / Ayer / Esta semana (lunes–domingo UTC) / `YYYY-MM-DD`
- Disambiguar clones mismo día UTC con la primera pregunta no boilerplate
- Pin via `st.popover` en el recorte activo; sacar Fijar/Quitar del pie
- Restyle CSS del container activo (fondo sutil + línea azul); sin wrappers HTML
- Delta OpenSpec `chat-threads`; TDD unit + AppTest

### Out of Scope

- FastAPI, `app/core`, workspace/KPIs/charts/composer
- `ThreadStore.search` architecture (solo cambian los strings indexados)
- `DEFAULT_TITLE` interno (`"Nuevo chat"`)
- Hover en todas las filas; Renombrar/Eliminar
- Input de búsqueda blanco; toggle Lectura con IA; avatares
- Migración de `threads.json` (labels se recalculan al cargar)

## Capabilities

### Modified Capabilities

- `chat-threads`: sección Recientes; labels sin SKUs/Catálogo; pin via menú activo;
  agrupado con Esta semana; `DEFAULT_TITLE` sigue `"Nuevo chat"`

## Approach

Presentación + generadores de título/subtítulo + CSS. No reescribir store de
búsqueda ni el handler de pin/unpin en `streamlit_app.py`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `ui/composition/copy.py` | Modified | Recientes, HISTORY_EMPTY, THREAD_MENU |
| `ui/threads/store.py` | Modified | title/subtitle/group_history/dedupe |
| `ui/threads/rail.py` | Modified | popover activo; sin Fijar al pie |
| `ui/theme.py` | Modified | chrome del container activo |
| `tests/unit/ui/test_chat_threads.py` | Modified | labels, Esta semana, clones, search |
| `tests/unit/ui/test_thread_rail_apptest.py` | Modified | Recientes, menú, sin Fijar permanente |
