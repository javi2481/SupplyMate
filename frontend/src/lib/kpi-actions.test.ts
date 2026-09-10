import { describe, expect, it } from "vitest";
import { EMPTY_SLICE, type UiSlice } from "@/lib/scope";
import { toggleBuyOnly, toggleHealthTag } from "@/lib/kpi-actions";

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
