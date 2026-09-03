# Spec: visual-shell

## ADDED Requirements

### Design tokens

- The UI MUST define visual-shell tokens for sidebar background, panel background, primary accent, destructive CTA, borders, and muted text in one central theme module
- The UI SHOULD use a single imported sans-serif font for the polished shell when Streamlit permits it

#### Scenario: central theme tokens drive shell styling

- **GIVEN** the app renders the polished shell
- **WHEN** theme CSS is injected
- **THEN** the sidebar, header, KPI cards, chart cards, and composer MUST reuse central tokens instead of per-widget inline color literals

### Hero header

- The live workspace MUST render a hero-style header with the product name, tagline, and current mode state
- The header MUST NOT repeat the scope line that already belongs to the Explore panel

#### Scenario: header shows product identity and mode

- **GIVEN** the app has a live or restored workspace
- **WHEN** the header renders
- **THEN** the visible content MUST include `SupplyMate`, the product tagline, and the current mode label

### KPI cards

- Live Explore MUST keep the existing 4 KPI metrics from `ui-v2`
- Each live Explore KPI card MAY include semantic icon metadata, but MUST NOT change the underlying metric values or ordering

#### Scenario: explore KPI cards stay functionally identical

- **GIVEN** a live Explore dashboard with KPI data
- **WHEN** KPI cards render
- **THEN** the labels MUST remain `Productos`, `Falta de stock`, `Riesgo de quiebre`, and `Cobertura prom.` in that order

### Chart cards

- The category and coverage charts MUST render inside card-style containers with a title area and content area
- Wrapping charts in cards MUST NOT change selection behavior in Explore mode

#### Scenario: chart wrappers preserve interaction

- **GIVEN** a live Explore dashboard with category and coverage data
- **WHEN** charts render inside chart-card containers
- **THEN** category and coverage selection MUST continue to add scope filters exactly as before

### Composer shell

- The sticky chat composer MUST render within `st.bottom`
- The polished shell MAY add decorative affordances such as a clip icon, but MUST NOT introduce real attachment behavior in this change

#### Scenario: composer remains the live input entrypoint

- **GIVEN** the operator is on the main page
- **WHEN** the app renders the input area
- **THEN** the sticky composer MUST still use the existing chat input behavior and placeholder

### Chat bubble polish

- The shell MAY restyle `st.chat_message` containers to resemble the mockup more closely
- Restyling MUST NOT alter message ordering or hide assistant content

#### Scenario: bubble styling preserves content

- **GIVEN** user and assistant messages exist in history
- **WHEN** chat containers receive shell styling
- **THEN** all message content MUST remain visible in the original order
