import { describe, expect, it } from "vitest";
import { toSearchParams } from "@/lib/api";
import * as scope from "@/lib/scope";
import {
  COVERAGE_ORDER,
  EMPTY_SLICE,
  coverageBandFromDays,
  inCoverageBand,
  scopePayloadToUiSlice,
  sliceToScopeQuery,
} from "@/lib/scope";

describe("COVERAGE_ORDER", () => {
  it("matches the five backend bands with an en-dash", () => {
    expect(COVERAGE_ORDER).toEqual(["0–3 días", "3–7 días", "7–14 días", "14–30 días", "30+ días"]);
    expect(COVERAGE_ORDER[0]).toContain("\u2013");
    expect(COVERAGE_ORDER[0]).not.toContain("-");
  });
});

describe("coverageBandFromDays", () => {
  it("uses the same edges as dashboard.py", () => {
    expect(coverageBandFromDays(0)).toBe("0–3 días");
    expect(coverageBandFromDays(2.9)).toBe("0–3 días");
    expect(coverageBandFromDays(3)).toBe("3–7 días");
    expect(coverageBandFromDays(7)).toBe("7–14 días");
    expect(coverageBandFromDays(14)).toBe("14–30 días");
    expect(coverageBandFromDays(30)).toBe("30+ días");
  });

  it("inCoverageBand matches those edges", () => {
    expect(inCoverageBand(14, "14–30 días")).toBe(true);
    expect(inCoverageBand(29.9, "14–30 días")).toBe(true);
    expect(inCoverageBand(30, "14–30 días")).toBe(false);
    expect(inCoverageBand(30, "30+ días")).toBe(true);
  });
});

describe("no Lovable 14+ bridge", () => {
  it("does not export a 14+ mapping onto two backend bands", () => {
    expect(scope).not.toHaveProperty("LOVABLE_COVERAGE_TO_API");
    expect(scope).not.toHaveProperty("lovableSliceToScopeQuery");
  });
});

describe("sliceToScopeQuery", () => {
  it("serializes category, coverage, and health onto ScopeQuery", () => {
    const scope = sliceToScopeQuery({
      ...EMPTY_SLICE,
      cats: ["Pañales"],
      health: ["riesgo_quiebre"],
      coverage: "0–3 días",
    });
    expect(scope.category).toEqual(["Pañales"]);
    expect(scope.coverage_bucket).toEqual(["0–3 días"]);
    expect(scope.health_bucket).toEqual(["stockout_risk"]);
  });

  it("sends one coverage_bucket for 14–30 días", () => {
    const query = sliceToScopeQuery({
      ...EMPTY_SLICE,
      coverage: "14–30 días",
    });
    expect(query.coverage_bucket).toEqual(["14–30 días"]);
  });

  it("sends one coverage_bucket for 30+ días", () => {
    const query = sliceToScopeQuery({
      ...EMPTY_SLICE,
      coverage: "30+ días",
    });
    expect(query.coverage_bucket).toEqual(["30+ días"]);
  });

  it("does not send sin_stock as a health_bucket", () => {
    const scope = sliceToScopeQuery({
      ...EMPTY_SLICE,
      health: ["sin_stock", "sobrestock"],
      outOfStockOnly: true,
    });
    expect(scope.health_bucket).toEqual(["overstock"]);
    expect(scope.out_of_stock).toBe(true);
    expect(scope.coverage_bucket).toBeUndefined();
  });

  it("sends out_of_stock when the Falta de stock chip is active", () => {
    const query = sliceToScopeQuery({
      ...EMPTY_SLICE,
      health: ["sin_stock"],
      outOfStockOnly: true,
    });
    expect(query.out_of_stock).toBe(true);
    expect(query.health_bucket).toBeUndefined();
  });

  it("maps API scope payload back to UI slice", () => {
    const next = scopePayloadToUiSlice(
      {
        categories: ["Nutrición"],
        health_buckets: ["stockout_risk"],
        coverage_buckets: ["0–3 días"],
      },
      {
        ...EMPTY_SLICE,
        buyOnly: true,
      },
    );
    expect(next.cats).toEqual(["Nutrición"]);
    expect(next.health).toEqual(["riesgo_quiebre"]);
    expect(next.coverage).toBe("0–3 días");
    expect(next.buyOnly).toBe(true);
  });

  it("replace: empty categories clear a leftover category", () => {
    const next = scopePayloadToUiSlice(
      { health_buckets: ["stockout_risk"] },
      { ...EMPTY_SLICE, cats: ["Cuidado"], health: ["sobrestock"] },
    );
    expect(next.cats).toEqual([]);
    expect(next.health).toEqual(["riesgo_quiebre"]);
  });

  it("maps out_of_stock_only, name_tokens, and subcategories onto the query", () => {
    const next = scopePayloadToUiSlice({
      out_of_stock_only: true,
      name_tokens: ["serum"],
      subcategories: ["Ampollas"],
    });
    expect(next.outOfStockOnly).toBe(true);
    expect(next.health).toContain("sin_stock");
    expect(next.nameTokens).toEqual(["serum"]);
    expect(next.subcategories).toEqual(["Ampollas"]);
    const query = sliceToScopeQuery(next);
    expect(query.out_of_stock).toBe(true);
    expect(query.name_token).toEqual(["serum"]);
    expect(query.subcategory).toEqual(["Ampollas"]);
  });

  it("round-trips suppliers onto ScopeQuery.supplier", () => {
    const query = sliceToScopeQuery({
      ...EMPTY_SLICE,
      suppliers: ["Higiene Sur"],
    });
    expect(query.supplier).toEqual(["Higiene Sur"]);
    const params = toSearchParams(query);
    expect(params.getAll("supplier")).toEqual(["Higiene Sur"]);
  });
});

describe("toSearchParams", () => {
  it("includes coverage_bucket with the canonical en-dash label", () => {
    const params = toSearchParams({ coverage_bucket: ["0–3 días"] });
    expect(params.getAll("coverage_bucket")).toEqual(["0–3 días"]);
    expect(params.toString()).not.toContain("0-3");
  });

  it("ANDs category and health_bucket across axes", () => {
    const params = toSearchParams({
      category: ["Pañales"],
      health_bucket: ["stockout_risk"],
      subcategory: ["Talle M"],
      supplier: ["Higiene Sur"],
      name_token: ["pañal"],
      highlight_product_id: "P-7211045",
    });
    expect(params.getAll("category")).toEqual(["Pañales"]);
    expect(params.getAll("health_bucket")).toEqual(["stockout_risk"]);
    expect(params.getAll("subcategory")).toEqual(["Talle M"]);
    expect(params.getAll("supplier")).toEqual(["Higiene Sur"]);
    expect(params.getAll("name_token")).toEqual(["pañal"]);
    expect(params.get("highlight_product_id")).toBe("P-7211045");
  });
});
