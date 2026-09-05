# SupplyMate frontend (Lovable)

React + TanStack Start UI exported from Lovable (dark ops redesign), cableado a la API FastAPI local.

## Run locally

Necesitás la API en `http://127.0.0.1:8000` y luego:

```bash
# desde la raíz del repo
.\.venv\Scripts\uvicorn.exe app.api:app --reload --host 127.0.0.1 --port 8000

cd frontend
npm install
npm run dev
```

Abrí `http://127.0.0.1:5173`. La URL de la API se configura con `VITE_SUPPLYMATE_API_URL` (ver `.env.example`).

Preview en Lovable (mock / sin API local): https://id-preview--acb3278c-2dcc-4198-85eb-a5c7cf2daed6.lovable.app  
Editor: https://lovable.dev/projects/acb3278c-2dcc-4198-85eb-a5c7cf2daed6

Snapshot Lovable: `6bdd1387` (Aplicó rediseño dark tokens).

## Backend

- Cliente: `src/lib/api.ts` → `GET /replenishment/slice`, `POST /chat`, `GET /products/{id}/replenishment`, CSV de OC.
- FastAPI habilita CORS para los puertos Vite habituales (`5173`, `3000`, `4173`).
- La tabla muestra el top N del slice (default 50); los KPIs usan el `dashboard` del alcance completo (~13k SKUs).

## Streamlit backup

UI Streamlit congelada en `backup/streamlit-ui` (también en origin). Sigue en el working tree para tests hasta retirarla.
