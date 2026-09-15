/** Visual projection: PurchaseListItem → table row. No replenishment math. */

import type { PurchaseListItem, ReplenishmentRecommendation } from "@/lib/api";

export type OperationalPriority = "critical" | "high" | "normal";

/** Matches app.services.analytics.metrics.PRIORITY_LABELS */
export const PRIORITY_LABELS: Record<OperationalPriority, string> = {
  critical: "Crítica",
  high: "Alta",
  normal: "Normal",
};

/** Matches app.services.analytics.metrics.BUCKET_LABELS */
export const HEALTH_BUCKET_LABEL = {
  stockout_risk: "Riesgo de quiebre",
  understock: "Falta de stock",
  overstock: "Sobrestock",
  healthy: "Saludable",
} as const;

export type HealthChipId =
  "riesgo_quiebre" | "sin_stock" | "sobrestock" | "falta_stock" | "saludable";

export type HealthChip = { id: HealthChipId; label: string };

export type SkuListRow = {
  product_id: string;
  barcode: string;
  product_name: string;
  category: string;
  supplier: string;
  stock: number;
  sales_30: number;
  recommended_quantity: number;
  coverage_days: number | null;
  priority: OperationalPriority;
  priority_label: string;
  health: HealthChip[];
  estimated_purchase_value: number;
  avg_daily: number;
};

export function normalizePriority(op: string): OperationalPriority {
  if (op === "critical" || op === "high" || op === "normal") return op;
  return "normal";
}

export function priorityLabel(op: string): string {
  return PRIORITY_LABELS[normalizePriority(op)];
}

export function healthTagsFromItem(item: PurchaseListItem): HealthChip[] {
  const chips: HealthChip[] = [];
  if (item.current_stock === 0) {
    chips.push({ id: "sin_stock", label: HEALTH_BUCKET_LABEL.understock });
  }
  switch (item.health_bucket) {
    case "stockout_risk":
      chips.push({ id: "riesgo_quiebre", label: HEALTH_BUCKET_LABEL.stockout_risk });
      break;
    case "understock":
      if (item.current_stock !== 0) {
        chips.push({ id: "falta_stock", label: HEALTH_BUCKET_LABEL.understock });
      }
      break;
    case "overstock":
      chips.push({ id: "sobrestock", label: HEALTH_BUCKET_LABEL.overstock });
      break;
    case "healthy":
      if (chips.length === 0) chips.push({ id: "saludable", label: HEALTH_BUCKET_LABEL.healthy });
      break;
    default:
      break;
  }
  return chips;
}

export function toSkuListRow(item: PurchaseListItem) {
  const row = rowFromPurchaseItem(item);
  return {
    ...row,
    current_stock: row.stock,
    days_of_supply: row.coverage_days,
    operational_priority: row.priority,
    health_label:
      item.health_bucket in HEALTH_BUCKET_LABEL
        ? HEALTH_BUCKET_LABEL[item.health_bucket as keyof typeof HEALTH_BUCKET_LABEL]
        : item.health_bucket,
  };
}

export function rowFromPurchaseItem(item: PurchaseListItem): SkuListRow {
  const priority = normalizePriority(item.operational_priority);
  const avg = item.average_daily_demand || 0;
  return {
    product_id: item.product_id,
    barcode: item.barcode || item.product_id,
    product_name: item.product_name,
    category: item.category,
    supplier: item.supplier,
    stock: item.current_stock,
    sales_30: Math.round(avg * 30),
    recommended_quantity: item.recommended_quantity,
    coverage_days: item.days_of_supply,
    priority,
    priority_label: PRIORITY_LABELS[priority],
    health: healthTagsFromItem(item),
    estimated_purchase_value: item.estimated_purchase_value ?? 0,
    avg_daily: avg,
  };
}

/** Enrich row with SKU detail from GET /products/{id}/replenishment (drawer only). */
export type SkuDetailFacts = {
  demand_horizon: number;
  demand_lead: number;
  stock_target: number;
  lead_time_days: number;
  safety_stock: number;
  avg_daily: number;
  recommended_quantity: number;
  stock: number;
  sales_30: number;
};

export function factsFromRecommendation(rec: ReplenishmentRecommendation): SkuDetailFacts {
  const c = rec.calculation;
  return {
    demand_horizon: c.demand_horizon,
    demand_lead: c.demand_lead_time,
    stock_target: c.stock_target,
    lead_time_days: c.lead_time_days,
    safety_stock: c.safety_stock,
    avg_daily: c.average_daily_demand,
    recommended_quantity: rec.recommended_quantity,
    stock: c.current_stock,
    sales_30: rec.context.units_sold_30d || Math.round(c.average_daily_demand * 30),
  };
}
