import { describe, expect, it } from "vitest";
import { rowFromPurchaseItem } from "@/lib/adapter";
import type { InventoryDashboard, PurchaseListItem } from "@/lib/api";
import {
  COPY_CATEGORIES_LOAD_FAILED,
  categoryNamesForUi,
  chartTickLabel,
  chartUnitsByCategory,
  csvExportLimit,
  dataSourceLabel,
  kpisFromDashboard,
  preferLiveApi,
  tableScopeCaption,
} from "@/lib/data-source";

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

  it("says Sin catálogo when data did not load, never Catálogo demo", () => {
    expect(dataSourceLabel(true)).toBe("Motor listo");
    expect(dataSourceLabel(false)).toBe("Sin catálogo");
    expect(dataSourceLabel(false)).not.toMatch(/demo|localhost|127\.0\.0\.1|API|motor caíd/i);
    expect(COPY_CATEGORIES_LOAD_FAILED).toBe(
      "No pude cargar las categorías. Intentá de nuevo en un momento.",
    );
    expect(COPY_CATEGORIES_LOAD_FAILED).not.toMatch(/motor|API|localhost/i);
  });

  it("csvExportLimit caps at 10000 and uses purchase_skus", () => {
    expect(csvExportLimit(5395)).toBe(5395);
    expect(csvExportLimit(50)).toBe(50);
    expect(csvExportLimit(50_000)).toBe(10_000);
  });

  it("does not show Lovable demo categories when the live dashboard is in use", () => {
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
    expect(categoryNamesForUi(dash)).toEqual(["Cuidado del Cabello", "Cosmetica"]);
    expect(categoryNamesForUi(null)).toEqual([]);
    expect(chartUnitsByCategory(dash)).toEqual([
      { category: "Cuidado del Cabello", units: 100 },
      { category: "Cosmetica", units: 80 },
    ]);
  });

  it("keeps full category names when there are few bars", () => {
    expect(chartTickLabel("Desodorantes Corporales", 1)).toBe("Desodorantes Corporales");
    expect(chartTickLabel("Desodorantes Corporales", 2)).toBe("Desodorantes Corporales");
    expect(chartTickLabel("Desodorantes Corporales", 5)).toBe("Desodorantes …");
  });

  it("prefers live API when a URL is set, ignoring the old mock flag", () => {
    expect(preferLiveApi({ VITE_SUPPLYMATE_API_URL: "http://127.0.0.1:8000" })).toBe(true);
    expect(preferLiveApi({ VITE_SUPPLYMATE_API_URL: "" })).toBe(false);
    expect(
      preferLiveApi({ VITE_SUPPLYMATE_API_URL: "http://127.0.0.1:8000", VITE_SUPPLYMATE_USE_MOCK: "1" }),
    ).toBe(true);
  });

  it("projects a purchase list item without a demo catalog", () => {
    const projected = rowFromPurchaseItem({
      product_id: "P-1",
      barcode: "100",
      product_name: "Serum",
      supplier: "Prov",
      category: "Cuidado",
      subcategory: "",
      current_stock: 4,
      reorder_point: null,
      below_reorder_point: false,
      average_daily_demand: 1,
      days_of_supply: 4,
      health_bucket: "stockout_risk",
      recommended_quantity: 12,
      operational_priority: "critical",
      purchase_cost: null,
      estimated_purchase_value: 1200,
    } satisfies PurchaseListItem);
    expect(projected.recommended_quantity).toBe(12);
  });
});
