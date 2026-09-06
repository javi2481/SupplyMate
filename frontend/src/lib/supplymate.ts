export type Sku = {
  barcode: string;
  product_id: string;
  product_name: string;
  category: string;
  supplier: string;
  stock: number;
  sales_30: number;
  lead_time_days: number;
  safety_stock: number;
  list_price: number;
};

export const HORIZON_DAYS = 7;

export const CATALOG: Sku[] = [
  { barcode: "6033436", product_id: "P-6033436", product_name: "Mamadera anticólico 260 ml", category: "Mamaderas", supplier: "Distribuidora Andina", stock: 80, sales_30: 600, lead_time_days: 4, safety_stock: 33, list_price: 4890 },
  { barcode: "8141600", product_id: "P-8141600", product_name: "Pañales Talle G x 50", category: "Pañales", supplier: "Higiene Sur", stock: 200, sales_30: 90, lead_time_days: 5, safety_stock: 10, list_price: 12500 },
  { barcode: "7211045", product_id: "P-7211045", product_name: "Pañales Talle M x 60", category: "Pañales", supplier: "Higiene Sur", stock: 0, sales_30: 420, lead_time_days: 6, safety_stock: 40, list_price: 13400 },
  { barcode: "5590112", product_id: "P-5590112", product_name: "Toallitas húmedas x 80", category: "Cuidado", supplier: "Higiene Sur", stock: 145, sales_30: 300, lead_time_days: 3, safety_stock: 25, list_price: 2390 },
  { barcode: "4402987", product_id: "P-4402987", product_name: "Tetina silicona flujo medio x2", category: "Mamaderas", supplier: "Distribuidora Andina", stock: 34, sales_30: 210, lead_time_days: 5, safety_stock: 18, list_price: 3150 },
  { barcode: "9087563", product_id: "P-9087563", product_name: "Crema para pañalitis 100 g", category: "Cuidado", supplier: "Farma Central", stock: 0, sales_30: 150, lead_time_days: 7, safety_stock: 20, list_price: 5600 },
  { barcode: "3320874", product_id: "P-3320874", product_name: "Shampoo bebé sin lágrimas 400 ml", category: "Cuidado", supplier: "Farma Central", stock: 260, sales_30: 120, lead_time_days: 4, safety_stock: 12, list_price: 4100 },
  { barcode: "6712390", product_id: "P-6712390", product_name: "Chupete ortodóncico 0-6 m", category: "Mamaderas", supplier: "Puericultura Norte", stock: 58, sales_30: 180, lead_time_days: 4, safety_stock: 15, list_price: 2750 },
  { barcode: "2298431", product_id: "P-2298431", product_name: "Leche de fórmula etapa 1 800 g", category: "Nutrición", supplier: "Nutrilac SA", stock: 96, sales_30: 540, lead_time_days: 6, safety_stock: 45, list_price: 18900 },
  { barcode: "2298432", product_id: "P-2298432", product_name: "Leche de fórmula etapa 2 800 g", category: "Nutrición", supplier: "Nutrilac SA", stock: 310, sales_30: 240, lead_time_days: 6, safety_stock: 30, list_price: 18400 },
  { barcode: "8845102", product_id: "P-8845102", product_name: "Termómetro digital infrarrojo", category: "Farmacia", supplier: "Farma Central", stock: 12, sales_30: 60, lead_time_days: 8, safety_stock: 8, list_price: 21500 },
  { barcode: "7756308", product_id: "P-7756308", product_name: "Suero fisiológico ampollas x20", category: "Farmacia", supplier: "Farma Central", stock: 74, sales_30: 330, lead_time_days: 3, safety_stock: 22, list_price: 3300 },
];

export type HealthTag = "riesgo_quiebre" | "sin_stock" | "sobrestock" | "cobertura_baja";

export const HEALTH_LABEL: Record<HealthTag, string> = {
  riesgo_quiebre: "Riesgo de quiebre",
  sin_stock: "Falta de stock",
  sobrestock: "Sobrestock",
  cobertura_baja: "Cobertura baja",
};

/** Health chips shown in the UI. Coverage is a separate filter, not a health state. */
export const HEALTH_FILTERS: HealthTag[] = ["riesgo_quiebre", "sin_stock", "sobrestock"];

/** Operator-facing priority wording. The engine values do not change. */
export const PRIORITY_LABEL: Record<"Alta" | "Media" | "Baja", string> = {
  Alta: "Crítica",
  Media: "Alta",
  Baja: "Normal",
};

export type CoverageBand = "0-3" | "3-7" | "7-14" | "14+";

export const COVERAGE_BANDS: { id: CoverageBand; label: string; min: number; max: number }[] = [
  { id: "0-3", label: "0–3 días", min: 0, max: 3 },
  { id: "3-7", label: "3–7 días", min: 3, max: 7 },
  { id: "7-14", label: "7–14 días", min: 7, max: 14 },
  { id: "14+", label: "14+ días", min: 14, max: Infinity },
];

export function inBand(coverage: number, band: CoverageBand): boolean {
  const found = COVERAGE_BANDS.find((item) => item.id === band);
  if (!found) return true;
  return coverage >= found.min && coverage < found.max;
}

export type Calc = {
  sku: Sku;
  avg_daily: number;
  demand_horizon: number;
  demand_lead: number;
  stock_target: number;
  recommended_quantity: number;
  coverage_days: number;
  health: HealthTag[];
  priority: "Alta" | "Media" | "Baja";
  estimated_purchase_value: number;
};

export function compute(sku: Sku): Calc {
  const avg_daily = sku.sales_30 / 30;
  const demand_horizon = avg_daily * HORIZON_DAYS;
  const demand_lead = avg_daily * sku.lead_time_days;
  const stock_target = demand_horizon + demand_lead + sku.safety_stock;
  const recommended_quantity = Math.max(0, Math.ceil(stock_target - sku.stock));
  const coverage_days = avg_daily > 0 ? sku.stock / avg_daily : 999;

  const health: HealthTag[] = [];
  if (sku.stock === 0) health.push("sin_stock");
  if (coverage_days <= sku.lead_time_days) health.push("riesgo_quiebre");
  if (coverage_days < 14 && sku.stock > 0) health.push("cobertura_baja");
  if (coverage_days > 60) health.push("sobrestock");

  const priority: Calc["priority"] =
    sku.stock === 0 || coverage_days <= sku.lead_time_days
      ? "Alta"
      : coverage_days < 14
        ? "Media"
        : "Baja";

  return {
    sku,
    avg_daily,
    demand_horizon,
    demand_lead,
    stock_target,
    recommended_quantity,
    coverage_days,
    health,
    priority,
    estimated_purchase_value: recommended_quantity * sku.list_price,
  };
}

export const ROWS: Calc[] = CATALOG.map(compute);

export const CATEGORIES = Array.from(new Set(CATALOG.map((s) => s.category)));

export const nf = new Intl.NumberFormat("es-AR");
export const money = (v: number) =>
  new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(v);
export const dec = (v: number) => v.toFixed(2).replace(".", ",");

export function csvFor(rows: Calc[]): string {
  const head = "barcode,product_id,product_name,supplier,recommended_quantity,operational_priority,estimated_purchase_value";
  const body = rows.map((r) =>
    [
      r.sku.barcode,
      r.sku.product_id,
      `"${r.sku.product_name}"`,
      `"${r.sku.supplier}"`,
      r.recommended_quantity,
      r.priority,
      r.estimated_purchase_value,
    ].join(","),
  );
  return [head, ...body].join("\n");
}

/** Deterministic narration: the engine computes, the chat only quotes it. */
export function answerFor(text: string, rows: Calc[]): string {
  const q = text.toLowerCase();
  const code = text.match(/\d{5,}/)?.[0];

  if (code) {
    const r = ROWS.find((x) => x.sku.barcode === code);
    if (!r) return `No encuentro el SKU ${code} en el catálogo cargado.`;
    return `SKU ${code} · ${r.sku.product_name}\nCantidad recomendada del motor: ${nf.format(r.recommended_quantity)} unidades (prioridad ${r.priority}).\nStock ${nf.format(r.sku.stock)} · ventas 30d ${nf.format(r.sku.sales_30)} · lead time ${r.sku.lead_time_days} días · safety stock ${nf.format(r.sku.safety_stock)}.\nAbrí la fila en Explorar para ver el detalle del cálculo.`;
  }

  if (q.includes("quiebre") || q.includes("riesgo")) {
    const risk = ROWS.filter((r) => r.health.includes("riesgo_quiebre") || r.health.includes("sin_stock"));
    return `Hay ${risk.length} SKUs con riesgo de quiebre o sin stock:\n${risk
      .slice(0, 6)
      .map((r) => `· ${r.sku.barcode} ${r.sku.product_name} — pedir ${nf.format(r.recommended_quantity)} u.`)
      .join("\n")}\nTodas las cantidades salen del motor determinístico, no de una estimación.`;
  }

  const toBuy = rows.filter((r) => r.recommended_quantity > 0);
  const units = toBuy.reduce((a, r) => a + r.recommended_quantity, 0);
  return `Para los próximos ${HORIZON_DAYS} días el motor recomienda comprar ${toBuy.length} SKUs por ${nf.format(units)} unidades.\nPrioridad Alta: ${toBuy
    .filter((r) => r.priority === "Alta")
    .slice(0, 4)
    .map((r) => `${r.sku.barcode} (${nf.format(r.recommended_quantity)} u.)`)
    .join(", ")}.\nEl panel Explorar tiene el detalle; yo solo narro el resultado del cálculo.`;
}
