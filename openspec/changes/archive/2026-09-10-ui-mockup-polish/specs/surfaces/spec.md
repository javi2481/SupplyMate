# Spec: surfaces

## MODIFIED Requirements

### Main pane

- The current conversation MUST own a single live dashboard surface
- Previous explore/list turns in chat history MUST NOT render an additional static dashboard when a live dashboard is already shown for the active thread
- Previous explore/list turns MUST preserve their assistant text content in chat history
- The live panel MUST remain the only interactive dashboard surface for the active thread

#### Scenario: old dashboard copies are suppressed for the active live workspace

- **GIVEN** the thread has prior explore/list assistant messages and `live_list_active` is true
- **WHEN** the app renders history plus the live panel
- **THEN** previous turns MUST render message text only, and the dashboard widgets MUST render only in the live panel

### Summary bar

- The latest active explore/list answer SHOULD render a compact summary bar near the live conversation

#### Scenario: summary remains visible above evidence

- **GIVEN** the latest active response contains dashboard or purchase-list information
- **WHEN** the live conversation renders
- **THEN** the operator SHOULD see the compact risk/replenishment summary before the deeper evidence section
