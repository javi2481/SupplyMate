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
};

export const EMPTY_SLICE: UiSlice = {
  cats: [],
  health: [],
  coverage: null,
  buyOnly: false,
  outOfStockOnly: false,
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

/** Lovable coverage chips → FastAPI coverage_bucket (14+ spans the last two backend bands). */
export const LOVABLE_COVERAGE_TO_API: Record<"0-3" | "3-7" | "7-14" | "14+", string[]> = {
  "0-3": ["0–3 días"],
  "3-7": ["3–7 días"],
  "7-14": ["7–14 días"],
  "14+": ["14–30 días", "30+ días"],
};

export function lovableSliceToScopeQuery(
  slice: {
    cats: string[];
    health: Array<"riesgo_quiebre" | "sin_stock" | "sobrestock" | "cobertura_baja">;
    coverage: "0-3" | "3-7" | "7-14" | "14+" | null;
    buyOnly: boolean;
  },
  limit = 50,
): ScopeQuery {
  const health_bucket = healthTagsToApi(
    slice.health.filter((tag): tag is HealthTag => tag !== "cobertura_baja"),
  );
  const query: ScopeQuery = { limit };
  if (slice.cats.length) query.category = slice.cats;
  if (health_bucket.length) query.health_bucket = health_bucket;
  if (slice.coverage) query.coverage_bucket = LOVABLE_COVERAGE_TO_API[slice.coverage];
  return query;
}

const API_HEALTH_TO_UI: Record<string, HealthTag> = {
  stockout_risk: "riesgo_quiebre",
  overstock: "sobrestock",
};

/** Map chat/API scope payload back onto the UI recorte (client filters preserved separately). */
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
  const coverageRaw = payload.coverage_buckets?.[0];
  const coverage =
    coverageRaw && (COVERAGE_ORDER as readonly string[]).includes(coverageRaw)
      ? (coverageRaw as CoverageBand)
      : null;
  return {
    ...base,
    cats: payload.categories?.length ? [...payload.categories] : base.cats,
    health: health.length ? health : base.health,
    coverage: coverage ?? base.coverage,
  };
}
