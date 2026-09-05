# Delta for scope

## ADDED Requirements

### Requirement: Session scope history

The UI layer MUST be able to push, pop, and clear a list of `AnalyticalScope` snapshots without mutating AnalyticalScope fields. Push MUST be idempotent when the new dump equals the current top. Push MUST enforce a maximum length of 20 by dropping the oldest entry. Loading history from persisted JSON MUST validate each entry; invalid entries MUST be discarded without raising.

#### Scenario: push then pop restores prior scope

- GIVEN an empty history and current scope S0
- WHEN push(S0) then scope becomes S1 then pop
- THEN the restored scope MUST equal S0
- AND the remaining history MUST be empty

#### Scenario: push is idempotent at top

- GIVEN history whose top dump equals scope S
- WHEN push(S) is called
- THEN history length MUST be unchanged

#### Scenario: cap drops oldest

- GIVEN a history of 20 scopes
- WHEN a distinct 21st scope is pushed
- THEN length MUST remain 20
- AND the oldest entry MUST be gone
