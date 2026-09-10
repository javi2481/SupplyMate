# Design: Sidebar Recortes Nav

## Goal

Sidebar answers only “¿en qué recorte estaba?”. Main pane keeps metrics.

## Label contract

1. Title = `compact_scope_line` when scope is not Inventario.
2. Inventario with catalog/slice → title `Inventario general`, subtitle `Todos los productos`.
3. Inventario empty → first non-boilerplate user message, else `DEFAULT_TITLE` (`Nuevo chat`).
4. Filtered scope subtitle = `N para reponer` if `purchase_list` non-empty, else empty. Never `SKUs` or catalog totals.
5. Same UTC day + same title+subtitle → replace subtitle with first non-boilerplate question when available.
6. Groups: Hoy, Ayer, Esta semana (Mon–Sun UTC excluding Hoy/Ayer), then `YYYY-MM-DD`.

## Rail chrome

- Keep `st.container(border=is_active)` as native hook.
- CSS: no hard box; `rgba(255,255,255,.06)`, radius 8px, left accent bar.
- Pin: `st.popover("···")` only on active row; one action Fijar/Quitar.
- `RailAction` and `_handle_sidebar` stay unchanged.

## Settled

- No threads.json migration.
- Search stays title+subtitle, accent-insensitive.
- Won’t-fix: search input color, IA toggle color, avatars, rename/delete.
