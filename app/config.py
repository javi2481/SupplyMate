from pathlib import Path
import os

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = Path(os.getenv("SUPPLYMATE_DATA_DIR", ROOT_DIR / "data"))

# Prefer Groq free tier; OpenAI remains optional fallback.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

PRODUCTS_CSV = DATA_DIR / "products.csv"
INVENTORY_CSV = DATA_DIR / "inventory.csv"
SALES_SUMMARY_CSV = DATA_DIR / "sales_summary.csv"
SALES_HISTORY_CSV = DATA_DIR / "sales_history.csv"  # legacy / test fixtures
PRICES_CSV = DATA_DIR / "prices.csv"
REPLENISHMENT_PARAMS_CSV = DATA_DIR / "replenishment_params.csv"

# Optional raw dump; runtime prefers resource CSVs under DATA_DIR.
_catalog_env = os.getenv("SUPPLYMATE_CATALOG_XLSX", "")
CATALOG_XLSX = Path(_catalog_env) if _catalog_env.strip() else None

API_BASE_URL = os.getenv("SUPPLYMATE_API_URL", "http://127.0.0.1:8000")
