# Delta for visual-shell

## ADDED Requirements

### Requirement: Workspace width

The main workspace SHOULD be width-capped via Streamlit block-container CSS. The UI MUST NOT wrap widgets in an HTML workspace wrapper for width.

#### Scenario: width cap is CSS not HTML wrap

- GIVEN the shell CSS is injected
- WHEN the main pane renders
- THEN theme CSS MUST constrain block-container max-width
- AND markdown MUST NOT wrap workspace widgets in a width-only HTML shell

### Requirement: Explore chart encoding

Explore category lollipop and coverage histogram MUST use a single brand-blue encoding. They MUST NOT use an orangered scheme or per-bar coverage-palette colors. These encodings MUST NOT mutate health or coverage color maps.

#### Scenario: explore charts use brand blue

- GIVEN live Explore category and coverage charts
- WHEN encodings are inspected
- THEN both MUST use one brand-blue scale
- AND MUST NOT use orangered or coverage-palette per-bar colors

## MODIFIED Requirements

### Requirement: Hero header

The live workspace MUST render a compact mode header. Product identity MUST appear in the sidebar. The header MUST NOT dominate the main pane and MUST NOT repeat the Explore scope line.
(Previously: hero in main with product name, tagline, and mode.)

#### Scenario: header shows compact mode not identity

- GIVEN a live or restored workspace
- WHEN the header renders
- THEN the main pane MUST show the current mode label without a dominating product-name heading
- AND the sidebar MUST show the product name

### Requirement: Chart cards

Category and coverage charts MUST render inside a native Streamlit bordered container with title and content areas. Chart cards MUST NOT use split HTML open/close markdown wrappers. Card chrome MUST NOT change Explore selection behavior. AppTests MUST NOT treat a chart-card wrapper class string in markdown as success.
(Previously: unspecified card wrappers; later split HTML chart-card shells.)

#### Scenario: native cards preserve interaction

- GIVEN a live Explore dashboard with category and coverage data
- WHEN charts render inside bordered containers
- THEN category and coverage selection MUST add scope filters exactly as before
- AND markdown MUST NOT include a split chart-card wrapper class

#### Scenario: AppTest does not lock chart wrapper class

- GIVEN visual-shell AppTests run
- WHEN chart-card rendering is asserted
- THEN success MUST NOT require a chart-card wrapper class string in markdown

### Requirement: Composer shell

The sticky chat composer MUST stay in `st.bottom` and MUST use `st.chat_input` only. The composer MUST NOT render decorative composer-shell HTML. AppTests MUST NOT treat a composer-shell class string in markdown as success.
(Previously: `st.bottom` required; decorative clip/shell MAY.)

#### Scenario: composer is native chat input

- GIVEN the operator is on the main page
- WHEN the input area renders
- THEN a chat input MUST be present in the bottom region with the existing placeholder
- AND markdown MUST NOT include a decorative composer-shell class

#### Scenario: AppTest does not lock composer class

- GIVEN visual-shell AppTests run
- WHEN composer rendering is asserted
- THEN success MUST NOT require a composer-shell class string in markdown

### Requirement: Chat bubble polish

Each chat message MUST set an explicit avatar for user vs assistant. CSS `:has(data-testid)` MUST NOT distinguish user vs assistant layout. Restyling MUST NOT alter message ordering or hide assistant content.
(Previously: optional restyle; no avatar contract.)

#### Scenario: bubble styling preserves content

- GIVEN user and assistant messages exist in history
- WHEN chat containers render
- THEN all message content MUST remain visible in the original order

#### Scenario: avatars are explicit

- GIVEN a user message and an assistant message
- WHEN each chat message is created
- THEN each MUST include an explicit avatar
- AND layout MUST NOT depend on CSS `:has([data-testid])` for role distinction
