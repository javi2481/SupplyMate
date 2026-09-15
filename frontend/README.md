# SupplyMate frontend (Vite)

UI operativa: chat + **Explorar** + **Revisar OC**. El chrome presenta; Python decide cantidades (`calculate_replenishment`). Scaffold inicial vía Lovable; la superficie de producto es esta app.

Con `VITE_SUPPLYMATE_API_URL` y FastAPI arriba, el estado es **Motor listo** (catálogo real de `/data`). Si no se pueden cargar los datos, el chrome dice **Sin catálogo** y no inventa SKUs.

## Run locally

API en `http://127.0.0.1:8000` (o `8001` si `8000` está ocupado), luego:

```bash
cd frontend
cp .env.example .env
# Edit VITE_SUPPLYMATE_API_URL if the API is not on :8000
npm install
npm run dev -- --host 127.0.0.1 --port 8080
```

Abrí **http://127.0.0.1:8080**.

```bash
npm test
```

## Product notes

- Panel owner: `GET /replenishment/slice` for the active scope (`panelFromSources`).
- Cart: operator adds lines; Review PO edits qty; export opens a **column picker** (default barcode + order quantity).
