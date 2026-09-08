# SupplyMate frontend (Lovable)

Snapshot Lovable `44cf812b` (recorte navegable, gráfico por categoría con colores, copy de producto). El chrome no se rediseña: la UI presenta; Python decide cantidades (`calculate_replenishment`).

Con `VITE_SUPPLYMATE_API_URL` y FastAPI arriba, el estado es **Motor listo** (catálogo real). Si la API no responde, cae a **Catálogo demo**. Nunca muestra localhost ni la URL de la API.

Preview Lovable: https://id-preview--acb3278c-2dcc-4198-85eb-a5c7cf2daed6.lovable.app

## Run locally

API en `http://127.0.0.1:8000`, luego:

```bash
cd frontend
npm install
npm run dev
```

Abrí `http://127.0.0.1:5173` (o el puerto que imprima Vite; a veces 5174). Copiá `frontend/.env.example` a `frontend/.env`.

```bash
npm test
```
