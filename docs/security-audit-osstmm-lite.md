# Auditoría OSSTMM lite — Sección C (Internet)

Aplicación: SupplyMate API + Streamlit local.

## C — Seguridad en tecnologías de Internet

| Ítem | Estado | Evidencia |
|------|--------|-----------|
| Control de acceso a endpoints | Parcial — API abierta en MVP local | [`tests/test_security.py`](../tests/test_security.py) rate limit `/chat` |
| Validación de entradas | OK | max_length chat; scope params 422 |
| Headers de seguridad | OK | `X-Content-Type-Options`, `X-Frame-Options` |
| Errores sin fuga en producción | OK | `SafeErrorMiddleware` + `SUPPLYMATE_ENV=production` |
| Testeo app web (smoke) | OK | [`scripts/smoke_api.sh`](../scripts/smoke_api.sh) |
| Logging / monitoreo | Parcial — sin SIEM | logs uvicorn estándar |
| Política de dependencias | Documentada | [`docs/security-deps.md`](security-deps.md) |
| Denegación de servicio | Parcial | rate limit `/chat` only |

## Fuera de alcance (OSSTMM D–F)

Comunicaciones PBX/modem, wireless, físico.

## Próximos pasos (producción)

- Autenticación API
- HTTPS reverse proxy
- Secretos fuera de `.env` en servidor
