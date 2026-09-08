import type { InventoryDashboard } from "@/lib/api";

/** Offline fallback: never leak API host into status copy. */
export function dataSourceLabel(online: boolean): "Motor listo" | "Catálogo demo" {
  return online ? "Motor listo" : "Catálogo demo";
}

/** Category chips/chart: live dashboard names, never Lovable demo names while the API is in use. */
export function categoryNamesForUi(
  useMock: boolean,
  dashboard: InventoryDashboard | null,
  mockCategories: string[],
): string[] {
  if (useMock) return mockCategories;
  return (dashboard?.by_category ?? []).map((bar) => bar.category);
}

export function chartUnitsByCategory(
  useMock: boolean,
  dashboard: InventoryDashboard | null,
  mockBars: { category: string; units: number }[],
): { category: string; units: number }[] {
  const bars = useMock
    ? mockBars
    : (dashboard?.by_category ?? []).map((item) => ({
        category: item.category,
        units: item.recommended_quantity,
      }));
  return bars.filter((item) => item.units > 0).sort((a, b) => b.units - a.units);
}

export function kpisFromDashboard(
  dashboard: InventoryDashboard | null,
  listUnits: number,
): { skus: number; stockout: number; understock: number; units: number; purchase_skus: number } {
  if (dashboard) {
    return {
      skus: dashboard.skus,
      stockout: dashboard.stockout_risk,
      understock: dashboard.understock,
      units: dashboard.recommended_units ?? listUnits,
      purchase_skus: dashboard.purchase_skus ?? listUnits,
    };
  }
  return { skus: 0, stockout: 0, understock: 0, units: listUnits, purchase_skus: listUnits };
}

export function tableScopeCaption(opts: {
  displayed: number;
  pageRows: number;
  recorteToBuy: number | null;
  searching: boolean;
}): { shown: number; total: number; noun: "productos" | "a reponer" } {
  if (opts.searching) {
    return { shown: opts.displayed, total: opts.pageRows, noun: "productos" };
  }
  if (opts.recorteToBuy != null && opts.recorteToBuy > opts.pageRows) {
    return { shown: opts.pageRows, total: opts.recorteToBuy, noun: "a reponer" };
  }
  return { shown: opts.pageRows, total: opts.pageRows, noun: "productos" };
}

/** Prefer live API when a base URL is configured and mock is not forced. */
export function preferLiveApi(
  env: Record<string, string | undefined> = import.meta.env as Record<string, string | undefined>,
): boolean {
  const flag = env["VITE_SUPPLYMATE_USE_MOCK"];
  if (flag === "1" || flag === "true") return false;
  return Boolean(env["VITE_SUPPLYMATE_API_URL"]?.trim());
}
