# Design: natural-query-interpretation

## Tesis de producto

> El usuario no debe conocer la estructura interna del sistema. Se expresa en lenguaje natural y SupplyMate transforma esa expresión en un **espacio analítico navegable**.

La secuencia objetivo:

```text
lenguaje natural
    → interpretación (intención + referencias + filtros)
    → resolución contra catálogo (Python)
    → cálculo determinístico (Python)
    → dashboard + resumen
    → exploración (clicks / chips / breadcrumb)
    → acción (OC / CSV)
```

**No** es: lenguaje → LLM → SQL → DB.

**Sí** es: lenguaje → estructura acotada → dominio → Python → `ReplenishmentSlice`.

---

## Principios

| # | Regla |
|---|--------|
| P1 | **LLM interpreta; Python determina.** El LLM extrae intención y referencias en lenguaje del usuario. Nunca asigna categorías del catálogo ni cantidades. |
| P2 | **Cardinalidad del catálogo desambigua.** 1 SKU → `EXACT`; N SKUs coherentes → `GROUP`; varias interpretaciones → `AMBIGUOUS`. |
| P3 | **La pregunta inicializa el scope.** El chat no solo devuelve texto: abre el panel con el alcance correcto. |
| P4 | **Confirmar solo con baja confianza.** Alta confianza → dashboard directo + «Entendí: …». |
| P5 | **Reutilizar infra existente.** `AnalyticalScope`, `ReplenishmentSlice`, `InteractionEvent`, panel Streamlit. |
| P6 | **Sin NL→SQL.** No exponer `category`, `health_bucket`, etc. al usuario. |

---

## Mapeo PLN → SupplyMate

Referencia: `docs/03 PLN - Conceptos y técnicas de procesamiento.pdf`.

| Concepto PLN | Rol en SupplyMate | Implementación |
|--------------|-------------------|----------------|
| **Pragmática** (intención del hablante) | Intención de negocio | `BusinessIntent`: replenishment, inventory_risk, sales_ranking, single_sku |
| **Extracción de información / NER** | Referencias del usuario | `Reference { text, kind }` — dominio: `product_group`, `sku_hint`, `filter_hint` |
| **Desambiguación semántica** | Grupo vs SKU vs ambiguo | `resolve_references()` contra catálogo |
| **Normalización + stop words** | Preprocesamiento | Reutilizar `_normalize()`; stopwords de consulta («cuántos», «debo», «comprar») |
| **Morfología** (jabones → jabón) | Matching grupal | Token + stem **validado por cardinalidad** en catálogo, no stemming ciego |
| **QA acotado** | Chat de reposición | Respuesta estructurada + dashboard, no párrafo libre |

**No priorizar:** sentimiento, topic modeling (LDA), traducción, resumen automático, pipeline SpaCy/NLTK completo, embeddings.

---

## Estado actual vs objetivo

### Hoy (`app/agent/runner.py`)

```text
match_rule_intent (4 etiquetas)
    → purchase_list | sales_categories | single_product | unknown
resolve_from_message → un product_id o error 404
```

Problemas:

1. `single_product` se usa para «cuántos jabones…» (grupo, no SKU).
2. `resolve_product_id` con empate ambiguo devuelve `None` → «No encontré ese producto».
3. `ChatResponse` no incluye `scope` ni interpretación.
4. Streamlit en `mode=list` hace `_set_scope(reset())` — ignora la pregunta.

### Objetivo

```text
interpret_query(message) → QueryInterpretation
resolve_references(interpretation) → ResolutionResult
build_scope(resolution) → AnalyticalScope
replenishment_slice(scope) → ReplenishmentSlice  # ya existe
format_explore_answer(...) → texto determinístico
ChatResponse(scope, interpretation, group_summaries, dashboard, ...)
```

---

## Modelos de datos

### `BusinessIntent`

```python
BusinessIntent = Literal[
    "replenishment",      # qué comprar / reponer / cantidades
    "inventory_risk",     # quiebre, falta, riesgo sobre un alcance
    "sales_ranking",      # categorías más vendidas (existente)
    "single_sku",         # un producto concreto
    "unknown",
]
```

Ortogonal a **cuántas referencias** hay (0, 1, N).

| Intención | Referencias | Superficie |
|-----------|-------------|------------|
| replenishment | 0 | Dashboard raíz |
| replenishment | 1 grupo | Dashboard filtrado + resumen 1 grupo |
| replenishment | N grupos | Dashboard comparativo + resumen N grupos |
| inventory_risk | 0..N | Dashboard + `health_buckets` iniciales |
| single_sku | 1 exact | Cálculo individual (flujo actual) |
| sales_ranking | — | Ranking ventas (flujo actual) |

### `Reference`

Lo que el LLM (o reglas) extrae del texto del usuario:

```python
class Reference(BaseModel):
    text: str = Field(max_length=80)   # "jabones", "shampoo", "6033436"
    kind: Literal["product_group", "sku_hint", "filter_hint"] = "product_group"
```

El LLM **no** emite `category: "Jabon de Tocador"`.

### `QueryInterpretation`

```python
class QueryInterpretation(BaseModel):
    intent: BusinessIntent
    references: list[Reference] = Field(default_factory=list, max_length=5)
    filter_hints: list[str] = Field(default_factory=list)  # "riesgo", "quiebre"
    confidence: Literal["high", "low"] = "high"
    source: Literal["rules", "llm", "hybrid"] = "rules"
```

### `ResolvedReference`

Salida de Python tras consultar el catálogo:

```python
class ResolvedReference(BaseModel):
    label: str              # "Jabones" — para UI
    user_text: str          # "jabones"
    match_kind: Literal["exact_sku", "group", "ambiguous", "unresolved"]
    product_id: str = ""    # solo exact_sku
    sku_ids: list[str] = Field(default_factory=list)  # grupo resuelto
    scope_dimension: Literal["category", "subcategory", "sku_set"] = "category"
    scope_value: str = ""   # nombre catálogo o id compuesto
    sku_count: int = 0
    recommended_quantity: int = 0
    confidence: Literal["high", "low"] = "high"
```

### `ResolutionResult`

```python
class ResolutionResult(BaseModel):
    interpretation: QueryInterpretation
    resolved: list[ResolvedReference]
    scope: AnalyticalScope
    disambiguation_options: list[str] = Field(default_factory=list)
    blocking: bool = False   # True → preguntar antes de abrir dashboard
```

### `GroupSummary`

Para el texto «Jabones 48 · Shampoo 31 · Total 79»:

```python
class GroupSummary(BaseModel):
    label: str
    recommended_quantity: int
    sku_count: int
```

### `ChatInterpretation` (respuesta al cliente)

```python
class ChatInterpretation(BaseModel):
    understood_labels: list[str] = Field(default_factory=list)
    confidence: Literal["high", "low"] = "high"
    disambiguation_question: str = ""
```

### Extensión de `ChatResponse`

```python
class ChatResponse(BaseModel):
    answer: str
    mode: str = "single"  # "single" | "list" | "sales" | "explore" | "disambiguation"
    scope: AnalyticalScope | None = None
    interpretation: ChatInterpretation | None = None
    group_summaries: list[GroupSummary] = Field(default_factory=list)
    # ... campos existentes ...
```

`mode="explore"` = abrir panel live con `scope` inicial (equivalente a list pero con alcance).

---

## Extensión de `AnalyticalScope`

Hoy solo filtra por `categories`, no `subcategories`. En el catálogo real:

| Referencia usuario | Nivel catálogo |
|--------------------|----------------|
| jabones | categoría `Jabon de Tocador` |
| shampoo | subcategoría `Shampoo` (padre `Cuidado del Cabello`) |

**Opción A (recomendada fase 1–2):** agregar `subcategories: list[str]` a `AnalyticalScope` y extender `filter_rows()`.

```python
class AnalyticalScope(BaseModel):
    categories: list[str] = Field(default_factory=list)
    subcategories: list[str] = Field(default_factory=list)  # nuevo
    coverage_buckets: list[str] = Field(default_factory=list)
    health_buckets: list[str] = Field(default_factory=list)
    suppliers: list[str] = Field(default_factory=list)
    highlight_product_id: str = ""
    query_groups: list[str] = Field(default_factory=list)  # opcional fase 2: ids de grupo lógico
```

Semántica multi-grupo «jabones y shampoo»:

- Resolver cada referencia a su dimensión (`category` o `subcategory`).
- Scope = OR dentro de la dimensión correspondiente; para **varias referencias de usuario** usar `query_groups` o unión de SKU sets.

**Opción B (fase 2 comparativa):** `ResolvedGroup` con `sku_ids[]` y dashboard `by_query_group` agregando por etiqueta de usuario, no por campo CSV.

Para fase 1, **un solo grupo** basta con `categories=[...]` o `subcategories=[...]`.

---

## Pipeline detallado

```text
POST /chat { message }
        │
        ▼
┌───────────────────────┐
│  preprocess(message)  │  normalize, strip purchase verbs
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  interpret_query()    │  rules fast-path → LLM if needed
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  resolve_references() │  catalog lookup, cardinality
└───────────┬───────────┘
            │
     blocking? ──yes──► ChatResponse mode=disambiguation
            │
            no
            ▼
┌───────────────────────┐
│  build_scope()        │  AnalyticalScope + filter_hints → health_buckets
└───────────┬───────────┘
            ▼
     intent == single_sku && exact?
            │
      yes ──┴── no
       │         │
       ▼         ▼
 _run_single   replenishment_slice(scope)
 _product()         │
       │            ▼
       │     format_explore_answer()
       │            │
       └────────────┴──► ChatResponse
```

### Módulos nuevos (propuesta)

| Módulo | Responsabilidad |
|--------|-----------------|
| `app/pipeline/query_interpretation.py` | Modelos Pydantic, `interpret_query()` |
| `app/pipeline/reference_resolver.py` | `resolve_references()`, matching catálogo |
| `app/scope_builder.py` | `build_scope()`, hints → `health_buckets` |
| `app/explore_answer.py` | Texto determinístico + `GroupSummary` |

Eliminar o fusionar el borrador `app/category_resolve.py` (incompleto) en `reference_resolver.py`.

---

## `interpret_query()`

### Fast path (sin LLM)

| Condición | Resultado |
|-----------|-----------|
| `is_purchase_list_query(msg)` y sin referencias detectables | `replenishment`, `references=[]` |
| `is_top_categories_query(msg)` | `sales_ranking` |
| `message_looks_like_sku(msg)` | `single_sku`, `sku_hint` |
| Patrón `cuant[oa]s? … compr\|ped\|repon` + sustantivos residuales | `replenishment` + `product_group` por token |
| `riesgo\|quiebre\|sin stock` sin SKU | `inventory_risk` |

### LLM path

Agente ligero (`SupplyMateQueryInterpreter`) con salida JSON validada:

```json
{
  "intent": "replenishment",
  "references": [
    { "text": "jabones", "kind": "product_group" },
    { "text": "shampoo", "kind": "product_group" }
  ],
  "filter_hints": [],
  "confidence": "high"
}
```

Instrucciones clave:

- Extraer sustantivos/rubros que el usuario nombra; no inventar SKUs.
- No emitir nombres internos de categoría del catálogo.
- `confidence: low` si el término es genérico («cuidado», «cosas de baño»).

Fallback si LLM no disponible: reglas + `unknown` o `replenishment` raíz según patrones.

---

## `resolve_references()`

Para cada `Reference`:

### 1. Código numérico (5+ dígitos)

→ `resolve_exact` en store → `exact_sku` si existe.

### 2. Texto libre

Buscar en catálogo (nombre, categoría, subcategoría, marca):

```python
def classify_match(query: str, candidates: list[ProductMaster]) -> MatchKind:
    if len(candidates) == 1:
        return EXACT_SKU
    if len(candidates) == 0:
        return UNRESOLVED
    # ¿Todos comparten misma categoría o subcategoría dominante?
    if dominant_category(candidates):
        return GROUP
    if dominant_subcategory(candidates):
        return GROUP
    return AMBIGUOUS
```

### 3. Normalización morfológica

- Tokenizar referencia («jabones»).
- Probar token y stem (`jabon`) contra nombres normalizados.
- **La decisión final usa cardinalidad**, no solo substring.

### 4. Empates

| Situación | Acción |
|-----------|--------|
| 2+ categorías distintas con score similar | `AMBIGUOUS`, `confidence=low`, opciones en `disambiguation_options` |
| Subcategoría clara (shampoo) | `scope_dimension=subcategory` |
| Categoría clara (jabones → Jabon de Tocador) | `scope_dimension=category` |

### Ejemplos con catálogo perfumería

| Entrada | Resolución esperada |
|---------|---------------------|
| `jabones` | GROUP → categoría `Jabon de Tocador`, ~100+ SKUs |
| `shampoo` | GROUP → subcategoría `Shampoo` |
| `6033436` | EXACT → SKU |
| `issue flowpack` | EXACT o GROUP según cardinalidad |
| `cuidado` | AMBIGUOUS → varias categorías |
| `Dove jabón 90g` | EXACT si 1 SKU; si no, GROUP o pedir precisión |

---

## `build_scope()`

```python
def build_scope(resolution: ResolutionResult) -> AnalyticalScope:
    scope = AnalyticalScope()
    for ref in resolution.resolved:
        if ref.match_kind != "group":
            continue
        if ref.scope_dimension == "category":
            scope = scope_svc.add(scope, "category", ref.scope_value)
        elif ref.scope_dimension == "subcategory":
            scope = scope_svc.add_subcategory(scope, ref.scope_value)  # nuevo
    for hint in resolution.interpretation.filter_hints:
        if hint in ("riesgo", "quiebre", "stockout"):
            scope = scope_svc.add(scope, "health_bucket", metrics.BUCKET_STOCKOUT_RISK)
    return scope
```

Multi-grupo: si hay 2+ grupos resueltos, unión de filtros (OR por dimensión) o `sku_set` explícito en fase 2.

---

## Respuesta al usuario

### Alta confianza — replenishment multi-grupo

```markdown
**Entendí:** Jabones · Shampoo

Necesitás reponer aproximadamente:

| Grupo | Unidades |
|-------|----------|
| Jabones | 48 |
| Shampoo | 31 |
| **Total** | **79** |

Usá el panel para explorar por grupo, riesgo o SKU.
```

Números: **suma de `recommended_quantity`** por `sku_ids` del grupo (Python).

### Baja confianza

```markdown
No estoy seguro de a qué te referís con **«cuidado»**. ¿Querés decir:

1. Cuidado del Cabello
2. Jabon de Tocador
3. Otra categoría — escribí el nombre completo
```

`mode=disambiguation`, sin abrir panel hasta respuesta.

### Single SKU

Flujo actual sin cambios (`mode=single`).

---

## Integración Streamlit

Cambio en handler de chat (`ui/streamlit_app.py`):

```python
if mode in ("list", "explore"):
    st.session_state.live_list_active = True
    st.session_state.root_question = prompt
    if data.get("scope"):
        _set_scope(AnalyticalScope.model_validate(data["scope"]))
    else:
        _set_scope(scope_svc.reset())
    _append_event(source="chat", action="add_filter", ...)  # opcional
    render_live_panel()
```

Mostrar chips «Entendí: Jabones · Shampoo» arriba del panel si `interpretation` viene en la respuesta.

Dashboard comparativo (fase 2): gráfico `by_query_group` además de `by_category` cuando `len(group_summaries) > 1`.

---

## Integración API

`POST /chat` sin cambio de contrato de entrada. Salida extendida con campos opcionales (`scope`, `interpretation`, `group_summaries`).

`GET /replenishment/slice` ya acepta filtros — el chat solo debe **sembrar** el mismo scope que los clicks.

---

## Clasificador actual: migración

`app/intents.py` / `intent_classifier.py` siguen para compatibilidad. Plan:

1. Introducir `BusinessIntent` en paralelo.
2. `run_supplymate()` usa `interpret_query()` primero.
3. Mapear legacy: `purchase_list` → `replenishment` + refs vacías.
4. Deprecar clasificador de 4 etiquetas cuando golden pase.

---

## Casos golden (CI)

Archivo: `tests/golden_query_interpretation.csv`

```csv
message,intent,references,confidence,expected_mode
¿Qué productos tengo que comprar?,replenishment,,high,explore
¿Cuántos jabones debo comprar?,replenishment,jabones,high,explore
¿Cuántos jabones y shampoo debo comprar?,replenishment,jabones|shampoo,high,explore
¿Cuánto pedir de 6033436?,single_sku,6033436,high,single
¿Qué jabones tienen riesgo?,inventory_risk,jabones,high,explore
¿Cuánto cuidado debo comprar?,replenishment,cuidado,low,disambiguation
```

Archivo: `tests/golden_reference_resolution.csv`

```csv
reference,match_kind,scope_dimension,scope_value_contains
jabones,group,category,Jabon
shampoo,group,subcategory,Shampoo
6033436,exact_sku,,
cuidado,ambiguous,,
```

Tests de resolución: **sin LLM**, solo Python + catálogo fixture.

---

## Fases de implementación

### Fase 1 — Un grupo, replenishment (MVP del cambio)

- [ ] Modelos `QueryInterpretation`, `ResolvedReference`, extensión `ChatResponse`
- [ ] `interpret_query()` reglas + LLM JSON
- [ ] `resolve_references()` para un `product_group`
- [ ] `build_scope()` con `categories` / `subcategories`
- [ ] `run_supplymate()` ruta explore antes de `single_product`
- [ ] Streamlit: aplicar `scope` desde chat
- [ ] Golden tests resolución
- [ ] Caso: «¿Cuántos jabones debo comprar?» → 200, dashboard filtrado

### Fase 2 — Multi-grupo comparativo

- [ ] Varias referencias en un mensaje
- [ ] `GroupSummary` + texto total
- [ ] `by_query_group` en dashboard o agregación en respuesta
- [ ] Caso: «jabones y shampoo»

### Fase 3 — inventory_risk sobre grupos

- [ ] `filter_hints` → `health_buckets`
- [ ] Caso: «¿Qué jabones tienen riesgo?»

### Fase 4 — Desambiguación conversacional

- [ ] `mode=disambiguation`
- [ ] UI opciones clicables
- [ ] Sin confirmación en alta confianza

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| LLM inventa referencias | Validar contra tokens del mensaje original |
| Subcategoría vs categoría inconsistente | `scope_dimension` explícito en resolución |
| Multi-grupo con OR demasiado amplio | Fase 2: `sku_set` por grupo |
| Regresión en SKU único | Golden `6033436`, `47 street aura`; single path intacto |
| Panel resetea scope | Test E2E Streamlit o contrato API + manual QA |

---

## Non-goals (recordatorio)

- NL→SQL, lenguaje de filtros visible
- Embeddings / búsqueda semántica de productos
- Pipeline NLP genérico completo (SpaCy como requisito)
- Memoria conversacional multi-turn (fase 1)
- Confirmación obligatoria en cada mensaje

---

## Diagrama de experiencia objetivo

```text
Usuario: ¿Cuántos jabones y shampoo debo comprar?
                    │
                    ▼
        Entendí: Jabones · Shampoo
        Jabones  48 u. │ Shampoo  31 u. │ Total 79 u.
                    │
                    ▼
            [ Dashboard exploración ]
         KPIs · Cobertura · Riesgo · Prioridad
         [Jabones] [Shampoo] [Riesgo de quiebre]
                    │
          click Jabones
                    ▼
         Breadcrumb: Inventario › Jabones
                    │
          click Riesgo
                    ▼
         Inventario › Jabones › Riesgo
                    │
          click SKU
                    ▼
         Cómo se calculó → Armar OC → CSV
```

---

## Referencias en el repo

| Artefacto | Relación |
|-----------|----------|
| `openspec/changes/interactive-drilldown/design.md` | `AnalyticalScope`, slice, panel |
| `openspec/changes/llm-drilldown-insights/design.md` | LLM solo narrativa en analyze |
| `openspec/changes/semantic-correctness/` | Python calcula qty; sin embeddings |
| `app/agent/runner.py` | Router actual a reemplazar/extend |
| `app/products.py` | Resolución SKU a acotar a `exact_sku` |
| `docs/03 PLN - Conceptos y técnicas de procesamiento.pdf` | Marco PLN |

---

## Decisión abierta (resolver en implementación)

**Multi-grupo con categoría + subcategoría:** ¿OR en `filter_rows` entre `categories` y `subcategories`, o lista explícita de `sku_ids` por mensaje?

- Fase 1: un solo grupo → sin decisión.
- Fase 2: prototipar con datos reales «jabones + shampoo» y medir si OR por dimensión alcanza o hace falta `sku_set`.
