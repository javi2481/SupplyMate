import { describe, expect, it } from "vitest";
import { toSearchParams } from "@/lib/api";
import { COVERAGE_ORDER, coverageBandFromDays, scopePayloadToUiSlice, sliceToScopeQuery } from "@/lib/scope";

describe("COVERAGE_ORDER", () => {
  it("matches the five backend bands with an en-dash", () => {
    expect(COVERAGE_ORDER).toEqual([
      "0–3 días",
      "3–7 días",
      "7–14 días",
      "14–30 días",
      "30+ días",
    ]);
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
});

describe("sliceToScopeQuery", () => {
  it("serializes category, coverage, and health onto ScopeQuery", () => {
    const scope = sliceToScopeQuery({
      cats: ["Pañales"],
      health: ["riesgo_quiebre"],
      coverage: "0–3 días",
      buyOnly: false,
      outOfStockOnly: false,
    });
    expect(scope.category).toEqual(["Pañales"]);
    expect(scope.coverage_bucket).toEqual(["0–3 días"]);
    expect(scope.health_bucket).toEqual(["stockout_risk"]);
  });

  it("does not send sin_stock as a health_bucket", () => {
    const scope = sliceToScopeQuery({
      cats: [],
      health: ["sin_stock", "sobrestock"],
      coverage: null,
      buyOnly: false,
      outOfStockOnly: true,
    });
    expect(scope.health_bucket).toEqual(["overstock"]);
    expect(scope.coverage_bucket).toBeUndefined();
  });

  it("maps API scope payload back to UI slice", () => {
    const next = scopePayloadToUiSlice(
      {
        categories: ["Nutrición"],
        health_buckets: ["stockout_risk"],
        coverage_buckets: ["0–3 días"],
      },
      {
        cats: [],
        health: [],
        coverage: null,
        buyOnly: true,
        outOfStockOnly: false,
      },
    );
    expect(next.cats).toEqual(["Nutrición"]);
    expect(next.health).toEqual(["riesgo_quiebre"]);
    expect(next.coverage).toBe("0–3 días");
    expect(next.buyOnly).toBe(true);
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
