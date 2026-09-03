"""Architecture constraints for the catalog layer."""

import inspect

import app.catalog.products as products


def test_products_module_has_no_sentence_transformers():
    source = inspect.getsource(products)
    assert "sentence_transformers" not in source
    assert "SEMANTIC_MAX_PRODUCTS" not in source
    assert "numpy" not in source
