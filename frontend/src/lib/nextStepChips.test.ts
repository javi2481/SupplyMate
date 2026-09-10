import { describe, expect, it } from "vitest";
import type { Calc, Sku } from "@/lib/supplymate";
import { filterChipsCoveredByCharts, mockNextStepChips, type ChipSlice } from "@/lib/nextStepChips";

const EMPTY: ChipSlice = { cats: [], health: [], coverage: null, suppliers: [] };

function calc(partial: Partial<Sku> & Pick<Sku, "product_id" | "product_name" | "category">, extra?: Partial<Calc>): Calc {
  const sku: Sku = {
    barcode: partial.barcode ?? partial.product_id,
    supplier: "ProvX",
    stock: 10,
    sales_30: 90,
    lead_time_days: 4,
    safety_stock: 5,
    list_price: 100,
    ...partial,
  };
  const avg_daily = sku.sales_30 / 30;
  const coverage_days = avg_daily > 0 ? sku.stock / avg_daily : 999;
  const health: Calc["health"] = [];
  if (sku.stock === 0) health.push("sin_stock");
  if (coverage_days <= sku.lead_time_days) health.push("riesgo_quiebre");
  if (coverage_days > 60) health.push("sobrestock");
  return {
    sku,
    avg_daily,
    demand_horizon: avg_daily * 7,
    demand_lead: avg_daily * sku.lead_time_days,
    stock_target: 0,
    recommended_quantity: Math.max(0, Math.ceil(avg_daily * 11 + sku.safety_stock - sku.stock)),
    coverage_days,
    health,
    priority: sku.stock === 0 ? "Alta" : "Baja",
    estimated_purchase_value: 0,
    ...extra,
  };
}

describe("mockNextStepChips", () => {
  it("ranks unused categories then coverage, health, supplier; caps at 6; drops open_sku and draft_oc", () => {
    const rows: Calc[] = [
      calc({ product_id: "1", product_name: "Top", category: "A", supplier: "ProvX", stock: 0, sales_30: 600 }),
      calc({ product_id: "2", product_name: "B-item", category: "B", supplier: "ProvX", stock: 0, sales_30: 300 }),
      calc({ product_id: "3", product_name: "Over", category: "A", supplier: "ProvX", stock: 9000, sales_30: 30 }),
    ];
    const chips = mockNextStepChips(rows, EMPTY);
    expect(chips.length).toBeLessThanOrEqual(6);
    expect(chips.map((c) => c.action)).toEqual([
      "filter_category",
      "filter_category",
      "filter_coverage",
      "filter_health",
      "filter_health",
      "filter_supplier",
    ]);
    expect(chips[0]?.args.category).toBe("A");
    expect(chips[1]?.args.category).toBe("B");
    expect(chips.some((c) => c.action === "open_sku")).toBe(false);
    expect(chips.some((c) => c.action === "draft_oc")).toBe(false);
  });

  it("does not pad when only two slots apply", () => {
    const rows = [
      calc({ product_id: "1", product_name: "Only", category: "Cabello", stock: 40, sales_30: 210 }),
    ];
    const chips = mockNextStepChips(rows, EMPTY);
    expect(chips.length).toBeGreaterThanOrEqual(2);
    expect(chips.length).toBeLessThan(6);
    expect(chips.every((c) => c.label.length > 0)).toBe(true);
  });

  it("skips active category but still offers open_sku / draft_oc", () => {
    const rows = [
      calc({ product_id: "99", product_name: "Top SKU", category: "Cabello", stock: 0, sales_30: 400 }),
    ];
    const chips = mockNextStepChips(rows, {
      cats: ["Cabello"],
      health: ["riesgo_quiebre", "sobrestock"],
      coverage: "0–3 días",
      suppliers: ["ProvX"],
    });
    const actions = chips.map((c) => c.action);
    expect(actions).toContain("open_sku");
    expect(actions).toContain("draft_oc");
    expect(chips.some((c) => c.action === "filter_category")).toBe(false);
  });

  it("keeps recommended_quantity from the row fixture", () => {
    const row = calc({ product_id: "1", product_name: "Qty", category: "Cuidado", stock: 0, sales_30: 300 });
    const chips = mockNextStepChips([row], EMPTY);
    const skuChip = chips.find((c) => c.action === "open_sku");
    if (skuChip) {
      expect(skuChip.args.product_id).toBe("1");
    }
  });
});

describe("filterChipsCoveredByCharts", () => {
  const chips = [
    { action: "filter_category", args: { category: "Cabello" }, label: "Cabello" },
    { action: "filter_coverage", args: { coverage_bucket: "0–3 días" }, label: "0–3" },
    { action: "filter_health", args: { health_bucket: "stockout_risk" }, label: "Riesgo" },
    { action: "draft_oc", args: {}, label: "Armar OC" },
  ];

  it("drops category and coverage when chart is taxonomy-shaped", () => {
    const kept = filterChipsCoveredByCharts(chips, "category");
    expect(kept.map((c) => c.action)).toEqual(["filter_health", "draft_oc"]);
  });

  it("keeps all chips when chart is top SKUs", () => {
    expect(filterChipsCoveredByCharts(chips, "sku").map((c) => c.action)).toEqual([
      "filter_category",
      "filter_coverage",
      "filter_health",
      "draft_oc",
    ]);
  });
});
