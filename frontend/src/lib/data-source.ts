import type { InventoryDashboard, PurchaseListItem } from "@/lib/api";
import type { CoverageBand, HealthTag } from "@/lib/scope";

export const COPY_CATEGORIES_LOAD_FAILED =
  "No pude cargar las categorías. Intentá de nuevo en un momento.";

/** Status chrome: live catalog vs not loaded. Never leak the API host. */
export function dataSourceLabel(live: boolean): "Motor listo" | "Sin catálogo" {
  return live ? "Motor listo" : "Sin catálogo";
}

/** Category chips/chart from the live dashboard only. */
export function categoryNamesForUi(dashboard: InventoryDashboard | null): string[] {
  return (dashboard?.by_category ?? []).map((bar) => bar.category);
}

export type ChartBarMode = "category" | "subcategory" | "sku";

export type ChartBar = {
  category: string;
  units: number;
  productId?: string;
};

/**
 * Recorte hints for Explore chart granularity.
 * Policy (general — never special-case a rubro/pregunta):
 * 1. Several categories with volume → bars by category
 * 2. One category, no list-shaped filters → bars by subcategory
 * 3. List-shaped filters (health, coverage, supplier, name token, sin stock)
 *    or an answer that is “qué comprar” under those filters → top SKUs
 */
export type ChartSliceHints = {
  health?: HealthTag[];
  coverage?: CoverageBand | null;
  suppliers?: string[];
  nameTokens?: string[];
  outOfStockOnly?: boolean;
  purchaseList?: PurchaseListItem[];
  /** Max bars when charting top SKUs. */
  skuLimit?: number;
};

/** Filters that shrink the answer to a purchase list, not a taxonomy map. */
export function isListShapedRecorte(hints?: ChartSliceHints | null): boolean {
  if (!hints) return false;
  return (
    (hints.health?.length ?? 0) > 0 ||
    Boolean(hints.coverage) ||
    (hints.suppliers?.length ?? 0) > 0 ||
    (hints.nameTokens?.length ?? 0) > 0 ||
    Boolean(hints.outOfStockOnly)
  );
}

/** @deprecated Use isListShapedRecorte — same meaning, kept for call-site clarity. */
export function hasTightOperationalFilters(hints?: ChartSliceHints | null): boolean {
  return isListShapedRecorte(hints);
}

export function chartBarMode(
  dashboard: InventoryDashboard | null,
  hints?: ChartSliceHints | null,
): ChartBarMode {
  const purchase = (hints?.purchaseList ?? []).filter((item) => item.recommended_quantity > 0);
  if (isListShapedRecorte(hints) && purchase.length > 0) return "sku";
  const cats = (dashboard?.by_category ?? []).filter((b) => b.recommended_quantity > 0);
  const subs = (dashboard?.by_subcategory ?? []).filter((b) => b.recommended_quantity > 0);
  if (cats.length <= 1 && subs.length > 0) return "subcategory";
  return "category";
}

/** Units chart follows recorte shape, not a specific NL question. */
export function chartUnitsByCategory(
  dashboard: InventoryDashboard | null,
  hints?: ChartSliceHints | null,
): ChartBar[] {
  const mode = chartBarMode(dashboard, hints);
  if (mode === "sku") {
    const limit = hints?.skuLimit ?? 8;
    return (hints?.purchaseList ?? [])
      .filter((item) => item.recommended_quantity > 0)
      .slice()
      .sort((a, b) => b.recommended_quantity - a.recommended_quantity)
      .slice(0, limit)
      .map((item) => ({
        category: item.product_name,
        units: item.recommended_quantity,
        productId: item.product_id,
      }));
  }
  const source =
    mode === "subcategory" ? (dashboard?.by_subcategory ?? []) : (dashboard?.by_category ?? []);
  const bars = source.map((item) => ({
    category: item.category,
    units: item.recommended_quantity,
  }));
  return bars.filter((item) => item.units > 0).sort((a, b) => b.units - a.units);
}

/** Axis label: full name when few bars; truncate when the chart is crowded. */
export function chartTickLabel(name: string, barCount: number, maxLen = 13): string {
  if (barCount <= 2 || name.length <= maxLen) return name;
  return `${name.slice(0, maxLen)}…`;
}

export function kpisFromDashboard(
  dashboard: InventoryDashboard | null,
  listUnits: number,
  listOutOfStock = 0,
): {
  skus: number;
  stockout: number;
  understock: number;
  out_of_stock: number;
  units: number;
  purchase_skus: number;
} {
  if (dashboard) {
    return {
      skus: dashboard.skus,
      stockout: dashboard.stockout_risk,
      understock: dashboard.understock,
      out_of_stock: dashboard.out_of_stock ?? listOutOfStock,
      units: dashboard.recommended_units ?? listUnits,
      purchase_skus: dashboard.purchase_skus ?? listUnits,
    };
  }
  return {
    skus: 0,
    stockout: 0,
    understock: 0,
    out_of_stock: listOutOfStock,
    units: listUnits,
    purchase_skus: listUnits,
  };
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

/** Fetch the live catalog when a base URL is configured. */
export function preferLiveApi(
  env: Record<string, string | undefined> = import.meta.env as Record<string, string | undefined>,
): boolean {
  return Boolean(env["VITE_SUPPLYMATE_API_URL"]?.trim());
}

export const CSV_EXPORT_MAX = 10_000;

export function csvExportLimit(purchaseSkus: number): number {
  return Math.min(Math.max(purchaseSkus, 1), CSV_EXPORT_MAX);
}
