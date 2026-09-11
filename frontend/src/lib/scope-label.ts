/** Compact recorte labels for Explore chrome. */

import { HEALTH_LABEL, HORIZON_DAYS } from "@/lib/supplymate";
import type { UiSlice } from "@/lib/scope";

function tokenLabel(token: string): string {
  return token === token.toLowerCase() ? token.toUpperCase() : token;
}

/** True when the slice has any taxonomy / filter dimension (excluding buyOnly/horizon). */
export function sliceHasFilters(slice: UiSlice): boolean {
  return Boolean(
    slice.cats.length ||
      slice.subcategories.length ||
      slice.coverage ||
      slice.health.length ||
      slice.suppliers.length ||
      slice.nameTokens.length ||
      slice.highlightProductId ||
      slice.outOfStockOnly ||
      slice.buyOnly,
  );
}

/**
 * Human labels for the active recorte.
 * Empty taxonomy → ["Inventario"] unless buyOnly/horizon already label the view.
 */
export function sliceLabels(slice: UiSlice, horizonDays = HORIZON_DAYS): string[] {
  const labels: string[] = [];
  if (slice.buyOnly) labels.push("A comprar");
  if (horizonDays !== HORIZON_DAYS) labels.push(`Horizonte ${horizonDays} días`);
  labels.push(...slice.cats);
  labels.push(...(slice.subcategories ?? []));
  labels.push(...(slice.suppliers ?? []));
  labels.push(...slice.health.map((tag) => HEALTH_LABEL[tag]));
  if (slice.coverage) labels.push(`Cobertura ${slice.coverage}`);
  labels.push(...(slice.nameTokens ?? []).map(tokenLabel));
  if (slice.highlightProductId) labels.push(`SKU ${slice.highlightProductId}`);
  if (labels.length === 0) return ["Inventario"];
  return labels;
}
