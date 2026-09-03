# Matriz de compatibilidad

SupplyMate MVP — entorno objetivo de prueba manual.

## Navegador × SO (Streamlit :8501)

| | Windows 10/11 | macOS 14+ | Ubuntu 22.04+ |
|---|:---:|:---:|:---:|
| Chrome (últimas 2 versiones) | Sí | Sí | Sí |
| Edge (últimas 2 versiones) | Sí | — | — |
| Firefox (últimas 2 versiones) | Sí | Sí | Sí |

## API (:8000)

| Cliente | Soportado |
|---------|-----------|
| curl / httpx | Sí |
| Streamlit → FastAPI local | Sí |
| Docker Linux container | Sí (CI smoke) |

## No probado formalmente

- Safari iOS
- Resoluciones móviles (< 768px)
- Proxy corporativo con inspección TLS

## Regresión manual sugerida

Tras cambios en `ui/streamlit_app.py` o `ui/charts.py`, verificar UX-01 … UX-07 en [`docs/operations/beta-test-protocol.md`](beta-test-protocol.md).
