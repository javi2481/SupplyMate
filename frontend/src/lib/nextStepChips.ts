/** Next-step chips ranking helper (tests). Live Explore uses slice suggested_filters. */

import { coverageBandFromDays, COVERAGE_ORDER, type CoverageBand, type HealthTag } from "@/lib/scope";
import type { Calc } from "@/lib/supplymate";
import type { SuggestedChip } from "@/lib/applySuggestedFilter";
import type { ChartBarMode } from "@/lib/data-source";

export type ChipSlice = {
  cats: string[];
  health: HealthTag[];
  coverage: CoverageBand | null;
  suppliers: string[];
};

export type { SuggestedChip };

const MAX_CHIPS = 6;

/**
 * Drop category/coverage chips when the Explore chart already answers that dimension.
 * Keep action chips (draft_oc, open_sku, health, supplier, …).
 */
export function filterChipsCoveredByCharts(
  chips: SuggestedChip[],
  chartMode: ChartBarMode,
): SuggestedChip[] {
  const hasCategoryChart = chartMode === "category" || chartMode === "subcategory";
  const hasCoverageChart = chartMode === "category" || chartMode === "subcategory";
  return chips.filter((chip) => {
    if (chip.action === "filter_category" && hasCategoryChart) return false;
    if (chip.action === "filter_coverage" && hasCoverageChart) return false;
    return true;
  });
}

function unionPush(list: SuggestedChip[], chip: SuggestedChip | null): void {
  if (!chip) return;
  const key = `${chip.action}:${JSON.stringify(Object.entries(chip.args).sort())}`;
  if (list.some((c) => `${c.action}:${JSON.stringify(Object.entries(c.args).sort())}` === key)) return;
  if (list.length >= MAX_CHIPS) return;
  list.push(chip);
}

export function mockNextStepChips(rows: Calc[], slice: ChipSlice): SuggestedChip[] {
  const out: SuggestedChip[] = [];
  const activeCats = new Set(slice.cats);
  const activeHealth = new Set(slice.health);
  const activeSuppliers = new Set(slice.suppliers);
  const activeCoverage = slice.coverage;

  const catQty = new Map<string, number>();
  for (const row of rows) {
    const cat = row.sku.category;
    catQty.set(cat, (catQty.get(cat) ?? 0) + row.recommended_quantity);
  }
  const unusedCats = [...catQty.entries()]
    .filter(([cat]) => !activeCats.has(cat))
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([cat]) => cat);
  for (const cat of unusedCats.slice(0, 2)) {
    unionPush(out, {
      action: "filter_category",
      args: { category: cat },
      label: `¿Qué hay en ${cat}?`,
    });
  }

  const bandCounts = new Map<CoverageBand, number>();
  for (const row of rows) {
    const band = coverageBandFromDays(row.coverage_days);
    if (!band) continue;
    bandCounts.set(band, (bandCounts.get(band) ?? 0) + 1);
  }
  const preferred = bandCounts.get("0–3 días") ? "0–3 días" : undefined;
  let coveragePick: CoverageBand | undefined;
  if (preferred && preferred !== activeCoverage) coveragePick = preferred;
  else {
    for (const band of COVERAGE_ORDER) {
      if ((bandCounts.get(band) ?? 0) <= 0 || band === activeCoverage) continue;
      coveragePick = band;
      break;
    }
  }
  if (coveragePick) {
    unionPush(out, {
      action: "filter_coverage",
      args: { coverage_bucket: coveragePick },
      label: `¿Cobertura ${coveragePick}?`,
    });
  }

  const hasStockout = rows.some((row) => row.health.includes("riesgo_quiebre"));
  const hasOverstock = rows.some((row) => row.health.includes("sobrestock"));
  if (hasStockout && !activeHealth.has("riesgo_quiebre")) {
    unionPush(out, {
      action: "filter_health",
      args: { health_bucket: "stockout_risk" },
      label: "¿Riesgo de quiebre?",
    });
  }
  if (hasOverstock && !activeHealth.has("sobrestock")) {
    unionPush(out, {
      action: "filter_health",
      args: { health_bucket: "overstock" },
      label: "¿Hay sobrestock?",
    });
  }

  const supplierCounts = new Map<string, number>();
  for (const row of rows) {
    const supplier = row.sku.supplier?.trim();
    if (!supplier) continue;
    supplierCounts.set(supplier, (supplierCounts.get(supplier) ?? 0) + 1);
  }
  const topSupplier = [...supplierCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0];
  if (topSupplier && !activeSuppliers.has(topSupplier)) {
    unionPush(out, {
      action: "filter_supplier",
      args: { supplier: topSupplier },
      label: `¿Qué pide ${topSupplier}?`,
    });
  }

  const topSku = [...rows].sort((a, b) => b.recommended_quantity - a.recommended_quantity)[0];
  if (topSku) {
    unionPush(out, {
      action: "open_sku",
      args: { product_id: topSku.sku.product_id },
      label: `¿Cuánto pedir de ${topSku.sku.product_name.slice(0, 32)}?`,
    });
  }

  if (rows.some((row) => row.recommended_quantity > 0)) {
    unionPush(out, { action: "draft_oc", args: {}, label: "¿Armar la OC?" });
  }

  return out;
}
