import { describe, expect, it } from "vitest";
import { rowFromPurchaseItem } from "@/lib/adapter";
import type { InventoryDashboard, PurchaseListItem } from "@/lib/api";
import {
  categoryNamesForUi,
  chartUnitsByCategory,
  csvExportLimit,
  dataSourceLabel,
  kpisFromDashboard,
  preferLiveApi,
  tableScopeCaption,
} from "@/lib/data-source";
import { ROWS } from "@/lib/supplymate";

describe("slice data source helpers", () => {
  it("uses dashboard KPIs from JSON when present", () => {
    const dash: InventoryDashboard = {
      skus: 13125,
      stockout_risk: 400,
      understock: 200,
      overstock: 100,
      healthy: 12000,
      avg_coverage: 20,
      estimated_purchase_value: 1,
      recommended_units: 17753,
      purchase_skus: 1059,
      out_of_stock: 88,
      by_category: [],
    };
    const kpis = kpisFromDashboard(dash, 5);
    expect(kpis.skus).toBe(13125);
    expect(kpis.stockout).toBe(400);
    expect(kpis.understock).toBe(200);
    expect(kpis.out_of_stock).toBe(88);
    expect(kpis.units).toBe(17753);
    expect(kpis.purchase_skus).toBe(1059);
  });

  it("falls back to the list sum when the dashboard has no recorte totals", () => {
    const dash: InventoryDashboard = {
      skus: 10,
      stockout_risk: 1,
      understock: 1,
      overstock: 0,
      healthy: 8,
      avg_coverage: 20,
      estimated_purchase_value: 1,
      by_category: [],
    };
    expect(kpisFromDashboard(dash, 42).units).toBe(42);
    expect(kpisFromDashboard(null, 42).units).toBe(42);
    expect(kpisFromDashboard(null, 42).purchase_skus).toBe(42);
    expect(kpisFromDashboard(null, 42, 3).out_of_stock).toBe(3);
  });

  it("table caption uses purchase_skus when the page is truncated", () => {
    expect(tableScopeCaption({ displayed: 50, pageRows: 50, recorteToBuy: 1059, searching: false })).toEqual({
      shown: 50,
      total: 1059,
      noun: "a reponer",
    });
    expect(tableScopeCaption({ displayed: 12, pageRows: 50, recorteToBuy: 1059, searching: true })).toEqual({
      shown: 12,
      total: 50,
      noun: "productos",
    });
  });

  it("shows Catálogo demo only when mock is active", () => {
    expect(dataSourceLabel(true)).toBe("Catálogo demo");
    expect(dataSourceLabel(true)).not.toMatch(/localhost|127\.0\.0\.1|API/i);
    expect(dataSourceLabel(false)).toBe("Motor listo");
  });

  it("csvExportLimit caps at 10000 and uses purchase_skus", () => {
    expect(csvExportLimit(5395)).toBe(5395);
    expect(csvExportLimit(50)).toBe(50);
    expect(csvExportLimit(50_000)).toBe(10_000);
  });

  it("does not show Lovable demo categories when the live dashboard is in use", () => {
    const mock = ["Mamaderas", "Pañales", "Nutrición", "Cuidado", "Farmacia"];
    const dash: InventoryDashboard = {
      skus: 13125,
      stockout_risk: 1,
      understock: 1,
      overstock: 1,
      healthy: 1,
      avg_coverage: 20,
      estimated_purchase_value: 1,
      by_category: [
        { category: "Cuidado del Cabello", recommended_quantity: 100, sku_count: 10 },
        { category: "Cosmetica", recommended_quantity: 80, sku_count: 8 },
      ],
    };
    expect(categoryNamesForUi(false, dash, mock)).toEqual(["Cuidado del Cabello", "Cosmetica"]);
    expect(categoryNamesForUi(false, null, mock)).toEqual([]);
    expect(categoryNamesForUi(true, dash, mock)).toEqual(mock);
    expect(chartUnitsByCategory(false, dash, mock.map((category) => ({ category, units: 1 })))).toEqual([
      { category: "Cuidado del Cabello", units: 100 },
      { category: "Cosmetica", units: 80 },
    ]);
  });

  it("prefers live API only when a URL is set and mock is off", () => {
    expect(preferLiveApi({ VITE_SUPPLYMATE_API_URL: "http://127.0.0.1:8000" })).toBe(true);
    expect(preferLiveApi({ VITE_SUPPLYMATE_API_URL: "" })).toBe(false);
    expect(
      preferLiveApi({ VITE_SUPPLYMATE_API_URL: "http://127.0.0.1:8000", VITE_SUPPLYMATE_USE_MOCK: "1" }),
    ).toBe(false);
  });

  it("mock rows remain available as fallback catalog", () => {
    expect(ROWS.length).toBeGreaterThan(0);
    const projected = rowFromPurchaseItem({
      product_id: ROWS[0]!.sku.product_id,
      barcode: ROWS[0]!.sku.barcode,
      product_name: ROWS[0]!.sku.product_name,
      supplier: ROWS[0]!.sku.supplier,
      category: ROWS[0]!.sku.category,
      subcategory: "",
      current_stock: ROWS[0]!.sku.stock,
      reorder_point: null,
      below_reorder_point: false,
      average_daily_demand: ROWS[0]!.avg_daily,
      days_of_supply: ROWS[0]!.coverage_days,
      health_bucket: "stockout_risk",
      recommended_quantity: ROWS[0]!.recommended_quantity,
      operational_priority: "critical",
      purchase_cost: null,
      estimated_purchase_value: ROWS[0]!.estimated_purchase_value,
    } satisfies PurchaseListItem);
    expect(projected.recommended_quantity).toBe(ROWS[0]!.recommended_quantity);
  });
});
