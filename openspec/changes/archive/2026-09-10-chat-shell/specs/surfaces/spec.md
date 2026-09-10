# Spec: surfaces

## MODIFIED Requirements

### Sidebar chrome

- Live sidebar MUST show, in this order: **Nuevo chat**, **Fijados**, **Historial de chats**
- The active thread MUST be visually distinct in the list
- Clicking a Fijados or Historial row MUST restore that thread’s workspace in the main pane
- **Limpiar chat** MUST NOT remain as a first-class sidebar action; Nuevo chat is the empty-home control
- Analyst toggle MAY remain at the bottom of the sidebar (settings, not navigation)
- Sidebar MUST NOT present catalog health ovals as filters (ui-v2)

### Main pane

- GIVEN a selected thread with `live_list_active`
  WHEN rendering
  THEN the main pane MUST be the ui-v2 Explore or Commit layout for that snapshot
- GIVEN home (no live list, no messages)
  WHEN rendering
  THEN MUST show the conversational home and MUST NOT show the live replenishment panel

### Navigation (unchanged from ui-v2 except reset entry)

- Compact scope line remains in the Explore panel
- Explore still has a **Limpiar** control that resets **scope inside the current thread** (does not delete the thread)
- Commit scope controls remain read-only
