# Protocolo de prueba beta — SupplyMate

Prueba de usuario estilo escenario (Kaner).

## Participante

Operador de distribución / compras (conoce categorías y OC).

## Duración

30 minutos.

## Escenario narrativo

> Sos el responsable de compras. Abrís SupplyMate en http://localhost:8080. Querés saber qué comprar esta semana, recortar por categoría problemática, agregar SKUs al pedido, exportar la OC eligiendo columnas y revisar un SKU puntual.

### Pasos

1. Preguntá: **¿Qué productos tengo que comprar?**
2. Verificá KPIs + gráficos + tabla en el panel (misma verdad que el label del recorte).
3. Click en una **categoría** del chart → breadcrumb actualizado; KPIs/tabla cambian.
4. Click en un **chip** de cobertura o salud sugerido → el panel se actualiza sin colgar el chat.
5. En la tabla, **Agregar al pedido** en 2–3 SKUs (el chat no arma el carrito solo).
6. Abrí **Revisar OC** → ajustá una cantidad → **Exportar y terminar**.
7. En el cartel de columnas, dejá **barcode + cantidad** (o agregá nombre) → confirmá → abrí el CSV.
8. Volvé a Explorar → click en una fila SKU → **Cómo se calculó**.
9. **Limpiar filtros** → volver al universo completo.

## Registro de hallazgos

| ID | Paso | Problema | Severidad (1–5) | Captura |
|----|------|----------|-----------------|---------|
| B1 | | | | |
| B2 | | | | |

## Criterio de éxito beta

- Completar el escenario sin ayuda del desarrollador
- CSV con las columnas elegidas y las cantidades de Revisar OC
- Label ≡ KPIs ≡ chart ≡ tabla después de cada click

## Checklist UX automatizable (manual)

| ID | Ítem | OK |
|----|------|-----|
| UX-01 | Panel vivo con gráficos clickeables | |
| UX-02 | Historial de chat sin selección en gráficos | |
| UX-03 | Breadcrumb + Limpiar filtros | |
| UX-04 | Click gráfico → add al scope | |
| UX-05 | Chip → add al scope (nota local, sin LLM) | |
| UX-06 | Exportar OC solo desde Revisar OC con carrito | |
| UX-07 | SKU → Cómo se calculó | |
| UX-08 | Analista / respuesta coherente con tabla (Explorar) | |
| UX-09 | Agregar al pedido no vacía el carrito previo | |
| UX-10 | Picker de columnas: default barcode + qty | |
| UX-11 | Tras exportar, carrito vacío y vuelta a Explorar | |
| UX-12 | CSV filas = líneas del pedido | |
| UX-13 | Pregunta sugerida re-dispara chat | |
| UX-14 | Ritual: mirar trace / chat-turns antes de culpar UI | |
