# Delta for visual-shell

## MODIFIED Requirements

### Requirement: Explore chart encoding

Explore category lollipop and coverage histogram MUST use a single brand-blue encoding. They MUST NOT use an orangered scheme or per-bar coverage-palette colors. Selected category rows MUST be visually stronger than unselected rows via stroke width and/or point size in addition to opacity, while remaining brand blue. Coverage histogram MAY show numeric `sku_count` labels without changing bar color encoding.
(Previously: brand blue only; no selected stroke/size or histogram labels.)

#### Scenario: explore charts use brand blue

- GIVEN live Explore category and coverage charts
- WHEN encodings are inspected
- THEN both MUST use one brand-blue scale
- AND MUST NOT use orangered or coverage-palette per-bar colors

#### Scenario: selected lollipop is stronger

- GIVEN category rows with selected_values set
- WHEN the lollipop encoding is inspected
- THEN selected rows MUST differ from unselected in stroke and/or point size as well as opacity
- AND color MUST remain brand blue
