import { describe, expect, it } from "vitest";
import type { InventoryDashboard } from "@/lib/api";
import { EMPTY_SLICE, type UiSlice } from "@/lib/scope";
import { HORIZON_DAYS } from "@/lib/supplymate";
import {
  BUY_QUERY,
  NO_REPLENISH_GREETING,
  SEED_GREETING,
  chipRecorteNote,
  consultGreeting,
  hasReplenishment,
  primaryConsultQuery,
  sliceHasFilters,
  sliceLabels,
} from "@/lib/scope-label";

function slice(partial: Partial<UiSlice>): UiSlice {
  return { ...EMPTY_SLICE, ...partial };
}

function dash(partial: Partial<InventoryDashboard> = {}): InventoryDashboard {
  return {
    skus: 10,
    stockout_risk: 0,
    understock: 0,
    overstock: 0,
    healthy: 10,
    avg_coverage: 7,
    estimated_purchase_value: 0,
    recommended_units: 0,
    by_category: [],
    ...partial,
  };
}

describe("sliceLabels", () => {
  it("falls back to Inventario on empty recorte", () => {
    expect(sliceLabels(EMPTY_SLICE)).toEqual(["Inventario"]);
  });

  it("includes buyOnly and non-default horizon", () => {
    expect(sliceLabels(slice({ buyOnly: true }), 30)).toEqual(["A comprar", "Horizonte 30 días"]);
  });

  it("uppercases lowercase name tokens and shows health labels", () => {
    expect(
      sliceLabels(
        slice({
          cats: ["Cosmetica"],
          health: ["riesgo_quiebre"],
          nameTokens: ["rexona"],
          subcategories: ["Desodorantes"],
          highlightProductId: "6033436",
        }),
      ),
    ).toEqual(["Cosmetica", "Desodorantes", "Riesgo de quiebre", "REXONA", "SKU 6033436"]);
  });

  it("does not add horizon when it matches the default", () => {
    expect(sliceLabels(slice({ cats: ["Cabello"] }), HORIZON_DAYS)).toEqual(["Cabello"]);
  });
});

describe("sliceHasFilters", () => {
  it("is false for empty slice", () => {
    expect(sliceHasFilters(EMPTY_SLICE)).toBe(false);
  });

  it("is true for buyOnly or taxonomy", () => {
    expect(sliceHasFilters(slice({ buyOnly: true }))).toBe(true);
    expect(sliceHasFilters(slice({ cats: ["X"] }))).toBe(true);
  });
});

describe("primaryConsultQuery / hasReplenishment", () => {
  it("offers BUY_QUERY when the dashboard has units to order", () => {
    const withUnits = dash({ recommended_units: 120 });
    expect(hasReplenishment(withUnits)).toBe(true);
    expect(primaryConsultQuery(EMPTY_SLICE, withUnits)).toBe(BUY_QUERY);
    expect(consultGreeting(withUnits)).toBe(SEED_GREETING);
  });

  it("hides BUY_QUERY when recommended_units is 0 (any health/coverage shape)", () => {
    const emptyUnits = dash({ recommended_units: 0, overstock: 50, skus: 50 });
    expect(hasReplenishment(emptyUnits)).toBe(false);
    expect(primaryConsultQuery(slice({ health: ["sobrestock"] }), emptyUnits)).toBeNull();
    expect(primaryConsultQuery(slice({ coverage: "0–3 días" }), emptyUnits)).toBeNull();
    expect(consultGreeting(emptyUnits)).toBe(NO_REPLENISH_GREETING);
  });

  it("treats a missing dashboard as no replenishment", () => {
    expect(hasReplenishment(null)).toBe(false);
    expect(primaryConsultQuery(EMPTY_SLICE, undefined)).toBeNull();
  });
});

describe("chipRecorteNote", () => {
  it("names the recorte without claiming empty when dash is unknown", () => {
    expect(chipRecorteNote(slice({ health: ["sobrestock"] }), null)).toBe("Recorte: Sobrestock.");
  });

  it("names the recorte and notes empty replenishment", () => {
    expect(chipRecorteNote(slice({ health: ["sobrestock"] }), dash({ recommended_units: 0 }))).toBe(
      "Recorte: Sobrestock.\nNo hay unidades a reponer.",
    );
  });

  it("names the recorte without the empty line when units remain", () => {
    expect(chipRecorteNote(slice({ cats: ["Fragancias"] }), dash({ recommended_units: 900 }))).toBe(
      "Recorte: Fragancias.",
    );
  });
});
