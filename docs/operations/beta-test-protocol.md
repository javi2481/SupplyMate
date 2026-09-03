# Protocolo de prueba beta — SupplyMate

Prueba de usuario estilo escenario (Kaner, citado en Cap. II §2.5).

## Participante

Operador de distribución / compras (conoce categorías y OC).

## Duración

30 minutos.

## Escenario narrativo

> Sos el responsable de compras. Abrís SupplyMate en http://localhost:8501. Querés saber qué comprar esta semana, recortar por categoría problemática, refinar por cobertura, exportar la OC de ese recorte y revisar un SKU puntual.

### Pasos

1. Preguntá: **¿Qué productos tengo que comprar?**
2. Verificá KPIs + gráficos + tabla en el panel.
3. Click en una **categoría** del lollipop → breadcrumb actualizado; tarjeta **Analista IA** (modo Explorar).
4. Click en un **chip** de cobertura sugerido.
5. Verificá que **Exportar OC** está deshabilitado en Explorar.
6. Pulsá **Listo — armar OC de este recorte** → badge **Armar OC**; resumen de confirmación.
7. **Exportar OC (N SKUs)** → abrir CSV y contar filas (= N).
8. Click en una fila SKU (en Explorar) → **Cómo se calculó**.
9. **Volver a explorar** → clicks habilitados de nuevo.
10. **Limpiar filtros** → volver al universo completo.

## Registro de hallazgos

| ID | Paso | Problema | Severidad (1–5) | Captura |
|----|------|----------|-----------------|---------|
| B1 | | | | |
| B2 | | | | |

## Criterio de éxito beta

- Completar el escenario sin ayuda del desarrollador
- CSV coherente con el recorte visible
- Cantidades iguales a las de la tabla

## Checklist UX automatizable (manual)

| ID | Ítem | OK |
|----|------|-----|
| UX-01 | Panel vivo con gráficos clickeables | |
| UX-02 | Historial de chat sin selección en gráficos | |
| UX-03 | Breadcrumb + Limpiar filtros | |
| UX-04 | Click gráfico → add al scope | |
| UX-05 | Chip → add al scope | |
| UX-06 | Exportar OC solo en modo Armar OC | |
| UX-07 | SKU → Cómo se calculó | |
| UX-08 | Analista IA coherente con tabla (Explorar) | |
| UX-09 | Prioridades sugeridas = SKUs visibles | |
| UX-10 | Toggle Analista IA off → evidence determinística | |
| UX-11 | Transición Explorar → Armar OC congela scope | |
| UX-12 | CSV filas = N del recorte congelado | |
| UX-13 | Volver a explorar rehabilita clicks | |
| UX-14 | Pregunta sugerida re-dispara chat | |

Completar en [`openspec/changes/interactive-drilldown/verify-report.md`](../openspec/changes/interactive-drilldown/verify-report.md).
