import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# Ensure agent model construction works in unit tests without a real key.
os.environ.setdefault("LLM_PROVIDER", "groq")
if os.getenv("RUN_LLM_EVALS") != "1":
    os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("OPENAI_AGENTS_DISABLE_TRACING", "1")
os.environ.setdefault("SUPPLYMATE_ENV", "test")

# Tests use the same catalog as runtime: data/ (~13k SKUs).
_DATA = _ROOT / "data"
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
