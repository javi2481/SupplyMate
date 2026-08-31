# Plantilla — solicitud de cambio

## 1. Resumen

- **Solicitante:**
- **Fecha:**
- **Tipo:** correctivo | adaptativo | perfectivo | evolución

## 2. Motivación

¿Qué problema de negocio o técnico resuelve?

## 3. Impacto en el sistema

| Área | Impacto esperado |
|------|------------------|
| API | |
| Streamlit | |
| Catálogo CSV | |
| Agente LLM | |
| Tests | |

## 4. Riesgos

- Regresión en fórmula de reabastecimiento
- Desalineación CSV vs panel
- Costo LLM / latencia

## 5. Plan de pruebas

- [ ] Tests unitarios nuevos/actualizados
- [ ] `pytest` verde sin LLM en vivo
- [ ] Smoke `scripts/smoke_api.ps1`
- [ ] Checklist UX si aplica

## 6. Decisión

- [ ] Aprobado para SDD change
- [ ] Rechazado — motivo:
