# Verify: Sidebar Recortes Nav

Date: 2026-09-04

## Automated

- `pytest tests/unit/ui/test_chat_threads.py tests/unit/ui/test_thread_rail_apptest.py tests/unit/ui/test_visual_shell_apptest.py -m "not llm"` → **42 passed**

## Browser (localhost:8501)

After Streamlit restart with refreshed labels:

- Section heading **Recientes** (not Historial de chats)
- Titles **Inventario general** (not Catálogo · 13125 SKUs)
- Subtitles **Todos los productos**
- Active row exposes **···** menu; no permanent foot **Fijar**
- Hoy / Ayer grouping preserved
- Workspace KPIs unchanged (13125 / 25 para reponer stay in main pane)

## Notes

- AppTest does not surface `st.popover` trigger labels; pin contract asserted via `rail-pin-active` key when active and absence when inactive.
- Live `~/.supplymate/threads.json` labels recalculate on `refresh_all_labels` / load; no migration required.
- `graphify update .` completed.
