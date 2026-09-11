# Delta for llm-evals

Promotes the archived `llm-evals` concept
(`archive/2026-09-10-semantic-correctness/specs/llm-evals`) into a live
capability and extends it: the model MAY paraphrase contracts, and it MUST NOT
judge answers. The archived insight-validation and explain-fallback
requirements remain in force unchanged and are not restated here.

## ADDED Requirements

### Requirement: The model paraphrases inputs and never judges outputs

A live model MAY be used only to generate natural-language phrasings of a
contract's question. The pass/fail verdict MUST come from the Python oracle
defined by the `recorte-oracle` capability. No test MUST send an assistant
answer to a model for scoring, rating, ranking, or preference comparison, and
no assertion MUST depend on model-produced text about quality. A judge-shaped
call (answer in, verdict out) MUST NOT exist in the test suite.

#### Scenario: Paraphrase in, oracle decides

- **GIVEN** a generated contract with its axis expectations
- **WHEN** the model produces an alternative phrasing of the question
- **THEN** the phrasing MUST be fed to the same pipeline as the contract
- **AND** the verdict MUST come from the same Python assertions
- **AND** no model call MUST receive the assistant answer as input

#### Scenario: No judge call exists

- **GIVEN** the full test suite
- **WHEN** model call sites are inspected
- **THEN** every call MUST be classification or paraphrase generation
- **AND** none MUST return a score, grade, or verdict used in an assertion

### Requirement: Live evals are opt-in and excluded from CI

Live-model evals MUST carry `@pytest.mark.llm` and MUST skip unless
`RUN_LLM_EVALS=1` is set. The CI command MUST remain
`pytest -m "not performance and not llm"`, and that run MUST NOT call Groq or
require credentials. A missing key MUST cause a skip, never a failure, in the
default run.

#### Scenario: Default run never reaches the model

- **GIVEN** `RUN_LLM_EVALS` unset and no Groq key
- **WHEN** `pytest -m "not performance and not llm"` runs
- **THEN** every `llm`-marked test MUST be deselected
- **AND** the run MUST be green with zero outbound model requests

#### Scenario: Gated run samples paraphrases

- **GIVEN** `RUN_LLM_EVALS=1`, a Groq key, and `-m llm`
- **WHEN** the paraphrase eval runs
- **THEN** it MUST sample a subset of generated contracts
- **AND** each sampled contract MUST be evaluated by the Python oracle

### Requirement: Paraphrases reuse the contract's expectations unchanged

A paraphrased question MUST be asserted against the same expectations as the
contract it came from: the same resolved dimension, the same containment and
count relations, the same allowed surfaces and offers. The eval MUST NOT relax
expectations because the input was model-generated, and MUST NOT introduce a
second, prose-based expectation set.

#### Scenario: Same expectations for paraphrase and canonical form

- **GIVEN** a contract and a model paraphrase of its question
- **WHEN** both run through the pipeline
- **THEN** both MUST be asserted with the identical expectation object
- **AND** a divergence MUST be reported as a recorte failure naming the axis

### Requirement: Paraphrase failures reduce to deterministic regressions

When a paraphrase makes a contract fail, the failure MUST be reported as a
resolution or surface defect (which dimension won, which invariant broke), not
as a prose defect. The phrasing that exposed the defect SHOULD be captured as a
deterministic trap under `tests/golden/traps/` so the regression is reproducible
without a model.

#### Scenario: Gated finding becomes an offline trap

- **GIVEN** a gated paraphrase run that breaks the family-resolution invariant
- **WHEN** the finding is triaged
- **THEN** the report MUST name the broken invariant and the axis combination
- **AND** a trap reproducing it offline SHOULD be added
- **AND** the trap MUST assert the invariant, not the paraphrase wording

### Requirement: Intent goldens stay rules-first

Obvious intent rows MUST be classified by the deterministic rule router without
calling a model. Only hard paraphrases MAY require the live model, and only
under the `llm` marker with `RUN_LLM_EVALS=1`.

#### Scenario: Obvious rows never call the model

- **GIVEN** the committed intent golden rows
- **WHEN** pytest runs without the `llm` marker
- **THEN** obvious rows MUST match the rule router
- **AND** Groq MUST NOT be called

### Requirement: The golden corpora are frozen

The four existing golden CSVs are frozen: their row counts MUST NOT change in
this capability, and new coverage MUST land as generated contracts or as named
traps. Growing a golden CSV to encode a new behavior MUST NOT be used in place
of a shape assertion.

#### Scenario: New coverage does not grow the goldens

- **GIVEN** a newly discovered behavior to cover
- **WHEN** the test is added
- **THEN** it MUST be a generated contract or a trap entry
- **AND** the golden CSV row counts MUST stay unchanged
