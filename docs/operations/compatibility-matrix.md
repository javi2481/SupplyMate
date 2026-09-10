# Matriz de compatibilidad

SupplyMate MVP — entorno objetivo de prueba manual.

## Navegador × SO (Vite UI :8080)

| | Windows 10/11 | macOS 14+ | Ubuntu 22.04+ |
|---|:---:|:---:|:---:|
| Chrome (últimas 2 versiones) | Sí | Sí | Sí |
| Edge (últimas 2 versiones) | Sí | — | — |
| Firefox (últimas 2 versiones) | Sí | Sí | Sí |

## API (:8000)

| Cliente | Soportado |
|---------|-----------|
| curl / httpx | Sí |
| Vite frontend → FastAPI local | Sí |
| Docker Linux container | Sí (CI smoke) |

## No probado formalmente

- Safari iOS
- Resoluciones móviles (< 768px)
- Proxy corporativo con inspección TLS

## Regresión manual sugerida

Tras cambios en `frontend/src/routes/index.tsx` o libs de scope/chart, verificar el flujo Explorar / Armar OC en [`docs/operations/beta-test-protocol.md`](beta-test-protocol.md).
