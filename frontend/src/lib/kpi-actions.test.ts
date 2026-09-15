import { describe, expect, it } from "vitest";
import { EMPTY_SLICE, type UiSlice } from "@/lib/scope";
import {
  toggleBuyOnly,
  toggleHealthTag,
  purchaseActionsAllowed,
  purchaseKpiTotals,
  visibleExploreKpiKinds,
} from "@/lib/kpi-actions";

function slice(partial: Partial<UiSlice>): UiSlice {
  return { ...EMPTY_SLICE, ...partial };
}

describe("toggleBuyOnly", () => {
  it("flips buyOnly", () => {
    expect(toggleBuyOnly(EMPTY_SLICE).buyOnly).toBe(true);
    expect(toggleBuyOnly(slice({ buyOnly: true })).buyOnly).toBe(false);
  });
});

describe("toggleHealthTag", () => {
  it("adds health idempotently and removes on second click", () => {
    const once = toggleHealthTag(EMPTY_SLICE, "riesgo_quiebre");
    expect(once.health).toEqual(["riesgo_quiebre"]);
    expect(toggleHealthTag(once, "riesgo_quiebre").health).toEqual([]);
  });

  it("keeps sin_stock in sync with outOfStockOnly", () => {
    const on = toggleHealthTag(EMPTY_SLICE, "sin_stock");
    expect(on.outOfStockOnly).toBe(true);
    expect(toggleHealthTag(on, "sin_stock").outOfStockOnly).toBe(false);
  });

  it("ignores unknown tags by returning the same dimensions", () => {
    const base = slice({ cats: ["X"] });
    expect(toggleHealthTag(base, "riesgo_quiebre" as never).cats).toEqual(["X"]);
  });
});

describe("replaced-surface purchase KPIs", () => {
  it("hides the purchase KPI row under a replaced surface", () => {
    expect(visibleExploreKpiKinds(true)).toEqual(["products", "stockout_risk", "out_of_stock"]);
    expect(visibleExploreKpiKinds(true)).not.toContain("units_to_order");
    expect(visibleExploreKpiKinds(false)).toEqual([
      "products",
      "stockout_risk",
      "out_of_stock",
      "units_to_order",
    ]);
  });

  it("does not expose stale recommended_units or purchase value under a replaced surface", () => {
    const stale = { recommendedUnits: 17753, estimatedValue: 99999, purchaseSkus: 50 };
    expect(purchaseKpiTotals(true, stale)).toBeNull();
    expect(purchaseKpiTotals(false, stale)).toEqual(stale);
  });

  it("does not offer recorte purchase actions for the prior slice", () => {
    expect(purchaseActionsAllowed(true)).toBe(false);
    expect(purchaseActionsAllowed(false)).toBe(true);
  });
});
