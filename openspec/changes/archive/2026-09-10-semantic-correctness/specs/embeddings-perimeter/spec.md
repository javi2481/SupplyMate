# Spec: embeddings-perimeter

## Requirements

### No semantic resolve

- GIVEN the runtime catalog
  WHEN `resolve_product_id` or `resolve_from_message` runs
  THEN resolution MUST use exact id/barcode and lexical matching only
  AND MUST NOT import `sentence_transformers`

### Declared UI chart dep

- GIVEN `pyproject.toml` dependencies
  THEN `altair` MUST be listed
  AND `sentence-transformers` and `numpy` MUST NOT be listed as project dependencies
