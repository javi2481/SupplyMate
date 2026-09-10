# Spec: llm-evals

## Requirements

### Golden intents

- GIVEN `tests/golden_intents.csv`
  WHEN pytest runs without marker `llm`
  THEN obvious rows MUST match `match_rule_intent`
  AND Groq MUST NOT be called
- GIVEN `RUN_LLM_EVALS=1` and `@pytest.mark.llm`
  THEN hard paraphrases MUST be classified by the live model

### Insight fixtures

- GIVEN a fixture insight with an integer not present in the slice payload (and > 2)
  WHEN `validate_insight` runs
  THEN it MUST report an orphan integer
- GIVEN a valid SKU and matching qty from the purchase list
  THEN `validate_insight` MUST accept it

### Explain fallback

- GIVEN `explain_agent` output contains an orphan integer
  WHEN `_run_single_product` finishes
  THEN the user-facing answer MUST be the deterministic calculation text
  AND MUST NOT keep the hallucinated number
