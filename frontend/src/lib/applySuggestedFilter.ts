/** Map a suggested-filter chip onto a UI command. Never send chat text. */

import { COVERAGE_ORDER, type CoverageBand, type HealthTag, type UiSlice } from "@/lib/scope";

export type SuggestedChip = {
  action: string;
  args: Record<string, string>;
  label: string;
};

export type ApplyResult =
  | { type: "slice"; slice: UiSlice }
  | { type: "open_sku"; productId: string }
  | { type: "draft_oc" }
  | { type: "noop" };

function union(list: string[], value: string): string[] {
  return list.includes(value) ? list : [...list, value];
}

function unionHealth(list: HealthTag[], value: HealthTag): HealthTag[] {
  return list.includes(value) ? list : [...list, value];
}

export function applySuggestedFilter(chip: SuggestedChip, slice: UiSlice): ApplyResult {
  const suppliers = slice.suppliers ?? [];
  switch (chip.action) {
    case "filter_category": {
      const category = chip.args["category"];
      if (!category) return { type: "noop" };
      return { type: "slice", slice: { ...slice, cats: union(slice.cats, category) } };
    }
    case "filter_coverage": {
      const band = chip.args["coverage_bucket"];
      if (!band || !(COVERAGE_ORDER as readonly string[]).includes(band)) return { type: "noop" };
      return { type: "slice", slice: { ...slice, coverage: band as CoverageBand } };
    }
    case "filter_health": {
      const bucket = chip.args["health_bucket"];
      const tag: HealthTag | null =
        bucket === "stockout_risk"
          ? "riesgo_quiebre"
          : bucket === "overstock"
            ? "sobrestock"
            : null;
      if (!tag) return { type: "noop" };
      return { type: "slice", slice: { ...slice, health: unionHealth(slice.health, tag) } };
    }
    case "filter_supplier": {
      const supplier = chip.args["supplier"];
      if (!supplier) return { type: "noop" };
      return { type: "slice", slice: { ...slice, suppliers: union(suppliers, supplier) } };
    }
    case "open_sku": {
      const productId = chip.args["product_id"];
      if (!productId) return { type: "noop" };
      return { type: "open_sku", productId };
    }
    case "draft_oc":
      return { type: "draft_oc" };
    default:
      return { type: "noop" };
  }
}
