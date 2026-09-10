# Spec: chat-threads

## ADDED Requirements

### Thread model

- MUST represent a thread as an id, title, `updated_at`, `pinned` flag, and a snapshot of UI session fields
- Snapshot MUST include: `messages`, `analytical_scope`, `panel_mode`, `frozen_scope`, `live_list_active`, `slice_data`, `analyze_data`, `interaction_events`, `root_skus`, `root_question`, `highlight_calc`, `guidance`
- Snapshot MUST NOT include CSV bytes
- Thread helpers MUST be Streamlit-free and MUST NOT call HTTP or LLM

### Title

- GIVEN a non-empty scope (not only the default “Inventario” label)
  WHEN deriving the thread title
  THEN MUST use `compact_scope_line(scope)`
- GIVEN empty/default scope AND at least one user message
  WHEN deriving the title
  THEN MUST use the first user message, truncated to 48 characters
- GIVEN empty scope AND no user messages
  THEN title MUST be “Nuevo chat”

### Nuevo chat

- GIVEN the current session has messages or a live list
  WHEN the operator clicks **Nuevo chat**
  THEN MUST persist the current thread (create or update) AND reset to conversational home (no live panel)
- GIVEN home with no messages and no live list
  WHEN clicking **Nuevo chat**
  THEN MUST remain on home without duplicating an empty thread

### Restore

- GIVEN a persisted thread
  WHEN the operator selects it
  THEN MUST load that snapshot into session state, including scope and panel mode, before the next render
- GIVEN the restored `panel_mode` is `commit`
  THEN MUST keep `frozen_scope` as stored; MUST NOT clear it as a side effect of switching threads
- ui-v2 `chat_would_unfreeze` MUST still apply to chat turns inside a restored commit thread

### Pin

- MUST allow pin and unpin of an existing thread
- Pinned threads MUST appear under **Fijados** and MUST NOT be duplicated in **Historial de chats**
- GIVEN zero pinned threads
  WHEN rendering Fijados
  THEN MUST still show the section heading and a single empty caption (no fake rows)

### Historial

- Unpinned threads MUST list under **Historial de chats**, newest `updated_at` first, grouped by calendar day labels: Hoy, Ayer, then `YYYY-MM-DD`
- Store MUST cap unpinned history at 50 threads (drop oldest unpinned). Pinned threads MUST NOT be dropped by the cap

### Persistence

- MUST write the thread index to a local JSON file whose path is injectable in tests
- MUST autosave the active thread after a chat turn or scope mutation that already triggers a rerun
- GIVEN a corrupt or missing file
  WHEN loading
  THEN MUST start with an empty index (no crash)
