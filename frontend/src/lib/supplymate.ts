import type { PurchaseListItem, ReplenishmentRecommendation } from "@/lib/api";

export const HORIZON_DAYS = 7;

/** UI filter chips (map to API health_bucket where possible). */
export type HealthTag = "riesgo_quiebre" | "sin_stock" | "sobrestock" | "cobertura_baja";

export const HEALTH_LABEL: Record<HealthTag, string> = {
  riesgo_quiebre: "Riesgo de quiebre",
  sin_stock: "Sin stock",
  sobrestock: "Sobrestock",
  cobertura_baja: "Cobertura baja",
};

/** API health_bucket → UI tags */
export function healthTagsFromApi(bucket: string, stock: number): HealthTag[] {
  const tags: HealthTag[] = [];
  if (stock === 0) tags.push("sin_stock");
  if (bucket === "stockout_risk") tags.push("riesgo_quiebre");
  if (bucket === "overstock") tags.push("sobrestock");
  if (bucket === "understock") tags.push("cobertura_baja");
  return tags;
}

export function apiHealthFromUi(tags: HealthTag[]): string[] {
  const out: string[] = [];
  if (tags.includes("riesgo_quiebre")) out.push("stockout_risk");
  if (tags.includes("sobrestock")) out.push("overstock");
  if (tags.includes("cobertura_baja")) out.push("understock");
  // sin_stock is filtered client-side (no dedicated API bucket)
  return out;
}

export type Priority = "Alta" | "Media" | "Baja";

export function priorityFromApi(op: string): Priority {
  if (op === "critical" || op === "high") return "Alta";
  if (op === "normal") return "Media";
  return "Baja";
}

/** Row shape used by the dark ops table / drawer. */
export type Calc = {
  product_id: string;
  barcode: string;
  product_name: string;
  category: string;
  supplier: string;
  stock: number;
  sales_30: number;
  recommended_quantity: number;
  coverage_days: number;
  health: HealthTag[];
  priority: Priority;
  estimated_purchase_value: number;
  avg_daily: number;
  demand_horizon: number;
  demand_lead: number;
  stock_target: number;
  lead_time_days: number;
  safety_stock: number;
};

export function rowFromPurchaseItem(item: PurchaseListItem): Calc {
  const avg = item.average_daily_demand || 0;
  const coverage =
    item.days_of_supply != null
      ? item.days_of_supply
      : avg > 0
        ? item.current_stock / avg
        : 999;
  return {
    product_id: item.product_id,
    barcode: item.barcode || item.product_id,
    product_name: item.product_name,
    category: item.category,
    supplier: item.supplier,
    stock: item.current_stock,
    sales_30: Math.round(avg * 30),
    recommended_quantity: item.recommended_quantity,
    coverage_days: coverage,
    health: healthTagsFromApi(item.health_bucket, item.current_stock),
    priority: priorityFromApi(item.operational_priority),
    estimated_purchase_value: item.estimated_purchase_value ?? 0,
    avg_daily: avg,
    demand_horizon: avg * HORIZON_DAYS,
    demand_lead: 0,
    stock_target: 0,
    lead_time_days: 0,
    safety_stock: 0,
  };
}

export function enrichWithRecommendation(row: Calc, rec: ReplenishmentRecommendation): Calc {
  const c = rec.calculation;
  return {
    ...row,
    avg_daily: c.average_daily_demand,
    demand_horizon: c.demand_horizon,
    demand_lead: c.demand_lead_time,
    stock_target: c.stock_target,
    lead_time_days: c.lead_time_days,
    safety_stock: c.safety_stock,
    recommended_quantity: rec.recommended_quantity,
    stock: c.current_stock,
    sales_30: rec.context.units_sold_30d || Math.round(c.average_daily_demand * 30),
  };
}

export const nf = new Intl.NumberFormat("es-AR");
export const money = (v: number) =>
  new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  }).format(v);
export const dec = (v: number) => v.toFixed(2).replace(".", ",");
