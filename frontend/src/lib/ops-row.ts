/** Bridge SkuListRow (API) → Calc shape used by table/drawer (display only). */

import type { HealthChipId, SkuListRow } from "@/lib/adapter";
import type { HealthTag } from "@/lib/scope";
import type { Calc, Sku } from "@/lib/supplymate";

const HEALTH_TAG_IDS: readonly HealthTag[] = ["riesgo_quiebre", "sin_stock", "sobrestock"];

function isFilterHealthTag(id: HealthChipId): id is HealthTag {
  return (HEALTH_TAG_IDS as readonly string[]).includes(id);
}

export function calcFromApiRow(row: SkuListRow): Calc {
  const sku: Sku = {
    barcode: row.barcode,
    product_id: row.product_id,
    product_name: row.product_name,
    category: row.category,
    supplier: row.supplier,
    stock: row.stock,
    sales_30: row.sales_30,
    lead_time_days: 0,
    safety_stock: 0,
    list_price: 0,
  };
  const health = row.health.map((chip) => chip.id).filter(isFilterHealthTag);

  const priority: Calc["priority"] =
    row.priority === "critical" ? "Alta" : row.priority === "high" ? "Media" : "Baja";

  return {
    sku,
    avg_daily: row.avg_daily,
    demand_horizon: 0,
    demand_lead: 0,
    stock_target: 0,
    recommended_quantity: row.recommended_quantity,
    coverage_days: row.coverage_days ?? 999,
    health,
    priority,
    estimated_purchase_value: row.estimated_purchase_value,
  };
}
