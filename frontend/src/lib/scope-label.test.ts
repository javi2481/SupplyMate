import { describe, expect, it } from "vitest";
import { EMPTY_SLICE, type UiSlice } from "@/lib/scope";
import { HORIZON_DAYS } from "@/lib/supplymate";
import { sliceHasFilters, sliceLabels } from "@/lib/scope-label";

function slice(partial: Partial<UiSlice>): UiSlice {
  return { ...EMPTY_SLICE, ...partial };
}

describe("sliceLabels", () => {
  it("falls back to Inventario on empty recorte", () => {
    expect(sliceLabels(EMPTY_SLICE)).toEqual(["Inventario"]);
  });

  it("includes buyOnly and non-default horizon", () => {
    expect(sliceLabels(slice({ buyOnly: true }), 30)).toEqual([
      "A comprar",
      "Horizonte 30 días",
    ]);
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
    ).toEqual([
      "Cosmetica",
      "Desodorantes",
      "Riesgo de quiebre",
      "REXONA",
      "SKU 6033436",
    ]);
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
