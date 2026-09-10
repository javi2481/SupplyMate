/** UI recorte → FastAPI ScopeQuery. Coverage labels match dashboard.COVERAGE_ORDER. */

import type { AnalyticalScopePayload, ScopeQuery } from "@/lib/api";

/** Canonical coverage bands from app/services/analytics/dashboard.py COVERAGE_ORDER. */
export const COVERAGE_ORDER = [
  "0–3 días",
  "3–7 días",
  "7–14 días",
  "14–30 días",
  "30+ días",
] as const;

export type CoverageBand = (typeof COVERAGE_ORDER)[number];

export type HealthTag = "riesgo_quiebre" | "sin_stock" | "sobrestock";

export type UiSlice = {
  cats: string[];
  health: HealthTag[];
  coverage: CoverageBand | null;
  buyOnly: boolean;
  /** Client-only: stock === 0. Not sent as health_bucket. */
  outOfStockOnly: boolean;
  suppliers: string[];
  nameTokens: string[];
  subcategories: string[];
  highlightProductId: string;
};

export const EMPTY_SLICE: UiSlice = {
  cats: [],
  health: [],
  coverage: null,
  buyOnly: false,
  outOfStockOnly: false,
  suppliers: [],
  nameTokens: [],
  subcategories: [],
  highlightProductId: "",
};

const HEALTH_TO_API: Partial<Record<HealthTag, string>> = {
  riesgo_quiebre: "stockout_risk",
  sobrestock: "overstock",
};

/** Map UI health tags to API health_bucket values. `sin_stock` is never sent. */
export function healthTagsToApi(tags: HealthTag[]): string[] {
  const out: string[] = [];
  for (const tag of tags) {
    const bucket = HEALTH_TO_API[tag];
    if (bucket && !out.includes(bucket)) out.push(bucket);
  }
  return out;
}

export function sliceToScopeQuery(slice: UiSlice, limit = 50): ScopeQuery {
  const health_bucket = healthTagsToApi(slice.health);
  const query: ScopeQuery = { limit };
  if (slice.cats.length) query.category = slice.cats;
  if (health_bucket.length) query.health_bucket = health_bucket;
  if (slice.coverage) query.coverage_bucket = [slice.coverage];
  if (slice.outOfStockOnly) query.out_of_stock = true;
  if (slice.suppliers?.length) query.supplier = slice.suppliers;
  if (slice.nameTokens?.length) query.name_token = slice.nameTokens;
  if (slice.subcategories?.length) query.subcategory = slice.subcategories;
  if (slice.highlightProductId) query.highlight_product_id = slice.highlightProductId;
  return query;
}

export function coverageBandFromDays(days: number | null | undefined): CoverageBand | null {
  if (days == null || !Number.isFinite(days)) return null;
  if (days < 3) return "0–3 días";
  if (days < 7) return "3–7 días";
  if (days < 14) return "7–14 días";
  if (days < 30) return "14–30 días";
  return "30+ días";
}

export function inCoverageBand(days: number, band: CoverageBand): boolean {
  return coverageBandFromDays(days) === band;
}

const API_HEALTH_TO_UI: Record<string, HealthTag> = {
  stockout_risk: "riesgo_quiebre",
  overstock: "sobrestock",
};

/** Map chat/API scope onto UiSlice. Empty lists clear filters (replace, not merge). */
export function scopePayloadToUiSlice(
  payload: AnalyticalScopePayload | null | undefined,
  base: UiSlice = EMPTY_SLICE,
): UiSlice {
  if (!payload) return base;
  const health: HealthTag[] = [];
  for (const bucket of payload.health_buckets ?? []) {
    const tag = API_HEALTH_TO_UI[bucket];
    if (tag && !health.includes(tag)) health.push(tag);
  }
  const outOfStockOnly = Boolean(payload.out_of_stock_only);
  if (outOfStockOnly && !health.includes("sin_stock")) health.push("sin_stock");
  const coverageRaw = payload.coverage_buckets?.[0];
  const coverage =
    coverageRaw && (COVERAGE_ORDER as readonly string[]).includes(coverageRaw)
      ? (coverageRaw as CoverageBand)
      : null;
  return {
    ...EMPTY_SLICE,
    buyOnly: base.buyOnly,
    cats: [...(payload.categories ?? [])],
    health,
    coverage,
    outOfStockOnly,
    suppliers: [...(payload.suppliers ?? [])],
    nameTokens: [...(payload.name_tokens ?? [])],
    subcategories: [...(payload.subcategories ?? [])],
    highlightProductId: payload.highlight_product_id ?? "",
  };
}
