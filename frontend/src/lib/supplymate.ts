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

/** Canonical filter tags — re-export from scope (single source of truth). */
export type { HealthTag } from "@/lib/scope";
import type { HealthTag } from "@/lib/scope";

export const HEALTH_LABEL: Record<HealthTag, string> = {
  riesgo_quiebre: "Riesgo de quiebre",
  sin_stock: "Falta de stock",
  sobrestock: "Sobrestock",
};

/** Health chips shown in the UI. Coverage is a separate filter, not a health state. */
export const HEALTH_FILTERS: HealthTag[] = ["riesgo_quiebre", "sin_stock", "sobrestock"];

/** Operator-facing priority wording. The engine values do not change. */
export const PRIORITY_LABEL: Record<"Alta" | "Media" | "Baja", string> = {
  Alta: "Crítica",
  Media: "Alta",
  Baja: "Normal",
};

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

export const nf = new Intl.NumberFormat("es-AR");
export const money = (v: number) =>
  new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(v);
export const dec = (v: number) => v.toFixed(2).replace(".", ",");
