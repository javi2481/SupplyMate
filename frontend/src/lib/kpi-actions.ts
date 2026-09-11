/** Pure Explore KPI → slice mutations (Lovable toggle semantics). */

import type { HealthTag, UiSlice } from "@/lib/scope";

const TOGGLE_HEALTH: readonly HealthTag[] = ["riesgo_quiebre", "sin_stock", "sobrestock"];

function toggleList<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((value) => value !== item) : [...list, item];
}

/** Toggle buy-only flag (Productos / Unidades KPIs). */
export function toggleBuyOnly(slice: UiSlice): UiSlice {
  return { ...slice, buyOnly: !slice.buyOnly };
}

/** Toggle a health KPI. `sin_stock` also drives outOfStockOnly.
 * Idempotent: clicking an active tag removes it.
 */
export function toggleHealthTag(slice: UiSlice, tag: HealthTag): UiSlice {
  if (!TOGGLE_HEALTH.includes(tag)) return slice;
  const health = toggleList(slice.health, tag);
  return { ...slice, health, outOfStockOnly: health.includes("sin_stock") };
}

export type ExploreKpiKind = "products" | "stockout_risk" | "out_of_stock" | "units_to_order";

const EXPLORE_KPI_KINDS: readonly ExploreKpiKind[] = [
  "products",
  "stockout_risk",
  "out_of_stock",
  "units_to_order",
];

const REPLACED_SURFACE_KPI_KINDS: readonly ExploreKpiKind[] = [
  "products",
  "stockout_risk",
  "out_of_stock",
];

/** Purchase KPI row (Unidades a pedir) stays off a payload-replaced surface. */
export function visibleExploreKpiKinds(replacedSurface: boolean): readonly ExploreKpiKind[] {
  return replacedSurface ? REPLACED_SURFACE_KPI_KINDS : EXPLORE_KPI_KINDS;
}

export function purchaseActionsAllowed(replacedSurface: boolean): boolean {
  return !replacedSurface;
}

export type PurchaseKpiTotals = {
  recommendedUnits: number;
  estimatedValue: number | null;
  purchaseSkus: number;
};

/** Stale recorte purchase counters must not leak onto a replaced surface. */
export function purchaseKpiTotals(
  replacedSurface: boolean,
  totals: PurchaseKpiTotals,
): PurchaseKpiTotals | null {
  if (replacedSurface) return null;
  return totals;
}
