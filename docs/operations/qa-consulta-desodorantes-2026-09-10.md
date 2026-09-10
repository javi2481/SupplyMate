# QA — consulta «qué desodorantes tengo que comprar?»

Fecha: 10 sep 2026. Superficie: Consulta de reposición (chat Lovable) + panel Explorar. No se cambió código en este informe.

Pregunta del operador: `que desodorantes tengo que comprar?`

Recorte resultante: **Desodorantes Corporales**. KPIs: 409 productos, 114 riesgo de quiebre, 0 falta de stock, 6.915 unidades a pedir.

## Veredicto

El chat **no responde la pregunta**. Entrega un wizard de recorte con markdown crudo, no un reporte de compra. El panel Explorar sí tiene los totales, pero el gráfico de categorías queda inutilizable: una sola barra a todo el ancho y el número de unidades ilegible.

## 1. Texto de salida del chat

### Lo que sale

```
_Paso 1 de 4 · Desodorantes Corporales_

**Entendí:** Desodorantes Corporales

Necesitás reponer aproximadamente:

- **Desodorantes Corporales** — **6915** unidades

Hay **409 SKUs** en este recorte. Para no mezclar grupos, ¿cuál querés analizar primero?
**Aerosol** · **Antitranspirante aerosol** · **Roll-on** · **Barra** · **Crema**
```

### Autopsia

| Línea en pantalla | Origen | Problema | Pri |
|-------------------|--------|----------|-----|
| `_Paso 1 de 4 · Desodorantes Corporales_` | `format_explore_answer` + `_progress()` | Wizard interno. El `_` se ve porque no hay markdown. | P0 |
| `**Entendí:** Desodorantes Corporales` | `ChatInterpretation.understood_labels` | Eco. El operador ya lo escribió. | P1 |
| 6.915 unidades, un solo renglón | `group_summaries_from_resolved` | Total de categoría. No dice qué SKU comprar. | P0 |
| «Hay 409 SKUs… ¿cuál querés analizar primero?» | `pick_next_question` · `multiple_subcategories` | Pregunta de funnel. Bloquea el ranking que ya está en `purchase_list`. | P0 |
| `**Aerosol** · **Roll-on** · …` | `guidance_options` incrustados en `answer` | Opciones como markdown. Los chips del composer ya existen. | P1 |

### Causas

1. **Render.** Python arma el `answer` con markdown (`**negrita**`, `_itálica_`). El chat Lovable pinta `message.text` en `frontend/src/routes/index.tsx` con `whitespace-pre-line` y sin parser. El operador ve asteriscos. Esa marca **no** viene de Streamlit en runtime: Streamlit ya no es la UI viva. Quedó el formato en el string de Python (`format_explore_answer`), pensado cuando `st.markdown` lo renderizaba.
2. **Producto.** La consulta cae en modo `explore`. `format_explore_answer` confirma recorte y pregunta el siguiente corte. El ranking de compra vive en `ChatResponse.purchase_list` y en la tabla del panel, no en la burbuja. La interpretación de «desodorantes» es por **reglas** (`interpret_query_rules`), no por el LLM.

### Qué debería decir el chat

Misma data del motor, otro texto:

1. Top N SKUs a pedir, con cantidad recomendada (`purchase_list`).
2. Total de unidades y SKUs del recorte, en una línea (dashboard + `group_summaries`).
3. Corte por formato (Aerosol, Roll-on, …) como chips, no como pregunta bloqueante.

Sacar: Paso 1 de 4, Entendí, asteriscos, y «para no mezclar grupos».

## 2. Gráfico «Unidades a reponer por categoría»

Captura: recorte ya filtrado a Desodorantes Corporales. Una barra rosa a todo el ancho del panel. Etiqueta `6.915 ud` encima, pegada a la barra, sin espacio, ilegible. Eje X: `Desodorantes …` (nombre cortado).

### Causas

El gráfico usa `chartUnitsByCategory(dash)` → `dashboard.by_category`. Con el recorte en **una** categoría hay **una** barra.

Recharts `BarChart` ocupa `width="100%"` y **no** define `barSize` / `maxBarSize`. Con un solo dato, la barra se estira al plot completo.

`LabelList` va en `position="top"` con `margin.top` de 24 px. El texto `nf.format(value) + " ud"` queda sobre el borde superior de la barra (se lee como `6.915ud`). El eje X recorta a 13 caracteres (`tickFormatter`).

El hint «Tocá una barra para ver esa categoría» no tiene sentido: el recorte **ya es** esa categoría. El KPI «Unidades a pedir · 6.915» duplica el mismo número. El desglose útil sería por **subcategoría** (Aerosol, Roll-on, Barra, Crema), que el motor de guidance ya conoce, pero `InventoryDashboard` no expone `by_subcategory`.

### Fixes de gráfico (propuestos, no aplicados)

| # | Cambio | Dónde | Efecto |
|---|--------|-------|--------|
| G1 | `maxBarSize` (~56–72 px) | `Bar` en `index.tsx` | Una barra no ocupa todo el ancho. |
| G2 | Más `margin.top` y/o offset del `LabelList`; espacio en `ud` | mismo `BarChart` | El número se lee. |
| G3 | No truncar el label si hay 1–2 barras | `tickFormatter` | Se lee «Desodorantes Corporales». |
| G4 | Con 1 categoría en scope: no graficar la misma categoría; o mostrar subcategorías | chart + dashboard | El gráfico deja de ser un KPI duplicado. |

## 3. Fixes de chat (propuestos, no aplicados)

| # | Cambio | Dónde | Efecto |
|---|--------|-------|--------|
| 1 | Dejar de pintar markdown. Texto plano o renderer real. | `explore_answer.py` y/o `index.tsx` | Se van `**` y `_`. |
| 2 | Respuesta = reporte de compra, no wizard. | `format_explore_answer` | La pregunta directa recibe SKUs y cantidades. |
| 3 | No incrustar opciones en el `answer`. | `explore_answer.py` | Los chips del composer alcanzan. |
| 4 | Sacar Entendí y Paso N de 4 del texto. | `explore_answer.py` | El chat deja de parecer un tutorial. |

## Archivos

- `app/agent/explore_answer.py` — copy de la burbuja
- `app/guidance/engine.py` — `pick_next_question`, `_progress`
- `frontend/src/routes/index.tsx` — burbuja (`message.text`) y `BarChart`
- `frontend/src/lib/data-source.ts` — `chartUnitsByCategory`
- `app/core/models.py` — `InventoryDashboard.by_category` (sin subcategorías)
