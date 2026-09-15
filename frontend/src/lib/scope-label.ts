/** Compact recorte labels for Explore chrome. */

import type { InventoryDashboard } from "@/lib/api";
import { HEALTH_LABEL, HORIZON_DAYS } from "@/lib/supplymate";
import type { UiSlice } from "@/lib/scope";

export const BUY_QUERY = "¿Qué productos debería comprar?";

export const SEED_GREETING =
  "Listo para revisar la reposición del recorte. Elegí una consulta rápida para comenzar: las cantidades salen del motor de cálculo.";

export const NO_REPLENISH_GREETING =
  "Este recorte no tiene unidades a reponer. Usá los filtros o cambiá el recorte.";

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

/** True when the dashboard recommends buying units for this recorte. */
export function hasReplenishment(dash: InventoryDashboard | null | undefined): boolean {
  return (dash?.recommended_units ?? 0) > 0;
}

/**
 * Primary quick-consult CTA for the chat header.
 * Policy on the recorte shape (units to order), never a hardcoded category name.
 */
export function primaryConsultQuery(
  _slice: UiSlice,
  dash: InventoryDashboard | null | undefined,
): string | null {
  if (!hasReplenishment(dash)) return null;
  return BUY_QUERY;
}

/** Local assistant note after a filter chip (no /chat). */
export function chipRecorteNote(
  slice: UiSlice,
  dash: InventoryDashboard | null | undefined,
  horizonDays = HORIZON_DAYS,
): string {
  const labels = sliceLabels(slice, horizonDays).join(" · ");
  // Missing dash → labels only (avoid claiming "0 a reponer" for the wrong recorte).
  if (dash == null) {
    return `Recorte: ${labels}.`;
  }
  if (!hasReplenishment(dash)) {
    return `Recorte: ${labels}.\nNo hay unidades a reponer.`;
  }
  return `Recorte: ${labels}.`;
}

/** Seed / empty-chat greeting for the active recorte. */
export function consultGreeting(dash: InventoryDashboard | null | undefined): string {
  return hasReplenishment(dash) ? SEED_GREETING : NO_REPLENISH_GREETING;
}
