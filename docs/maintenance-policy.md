# Política de mantenimiento — SupplyMate

Basado en las Leyes de Lehman (Cap. III, Celi-Párraga et al., 2023).

## Tipos de mantenimiento

| Tipo | Ejemplo en SupplyMate |
|------|------------------------|
| **Correctivo** | Bug en CSV, regresión en scope |
| **Adaptativo** | Nuevo proveedor LLM, Python 3.x |
| **Perfectivo** | Refactor Streamlit sin cambiar UX |

## Mantenimiento preventivo (Ley #2)

Cada **3 changes SDD** completados, dedicar un mini-sprint **sin features nuevas**:

- Refactor de módulos con deuda (p. ej. `ui/streamlit_app.py`)
- Actualizar `traceability-matrix.md`
- Revisar umbrales de `tests/test_performance.py`

## Flujo de cambio

1. Abrir change SDD (`openspec/changes/<name>/`)
2. Completar `proposal.md` → specs → TDD → `verify-report.md`
3. Bugfixes: usar plantilla de issue + test de regresión obligatorio
4. Cambios grandes: completar `docs/change-request-template.md`

## Evolución vs servicio

- **Evolución:** nuevos changes (drill-down, analytics, etc.)
- **Servicio:** parches, deps, CI — cambios tácticos en código estable
- **Retiro:** descontinuar features fuera de scope (p. ej. BI aparte)

## Referencias

- [`openspec/changes/engineering-quality/traceability-matrix.md`](../openspec/changes/engineering-quality/traceability-matrix.md)
- [`docs/change-request-template.md`](change-request-template.md)
