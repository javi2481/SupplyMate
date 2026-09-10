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

/**
 * Toggle a health KPI. `sin_stock` also drives outOfStockOnly.
 * Idempotent: clicking an active tag removes it.
 */
export function toggleHealthTag(slice: UiSlice, tag: HealthTag): UiSlice {
  if (!TOGGLE_HEALTH.includes(tag)) return slice;
  const health = toggleList(slice.health, tag);
  return { ...slice, health, outOfStockOnly: health.includes("sin_stock") };
}
