import os
from pathlib import Path

# Ensure agent model construction works in unit tests without a real key.
os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("OPENAI_AGENTS_DISABLE_TRACING", "1")

# Tests use the same catalog as runtime: data/ (~13k SKUs).
_DATA = Path(__file__).resolve().parent.parent / "data"
os.environ["SUPPLYMATE_CATALOG_XLSX"] = ""
os.environ["SUPPLYMATE_DATA_DIR"] = str(_DATA)

from app import config  # noqa: E402
from app.products import clear_product_caches  # noqa: E402

config.CATALOG_XLSX = None
config.DATA_DIR = _DATA
config.PRODUCTS_CSV = _DATA / "products.csv"
config.INVENTORY_CSV = _DATA / "inventory.csv"
config.SALES_SUMMARY_CSV = _DATA / "sales_summary.csv"
config.SALES_HISTORY_CSV = _DATA / "sales_history.csv"
config.PRICES_CSV = _DATA / "prices.csv"
config.REPLENISHMENT_PARAMS_CSV = _DATA / "replenishment_params.csv"
clear_product_caches()
