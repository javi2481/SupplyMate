/** Lovable chart colors, plus a palette for live catalog categories. */

export const CATEGORY_COLOR: Record<string, string> = {
  Pañales: "var(--ops-chart-diapers)",
  Nutrición: "var(--ops-chart-nutrition)",
  Mamaderas: "var(--ops-chart-bottles)",
  Cuidado: "var(--ops-chart-care)",
  Farmacia: "var(--ops-chart-pharmacy)",
};

export const CHART_PALETTE = [
  "var(--ops-chart-bottles)",
  "var(--ops-chart-diapers)",
  "var(--ops-chart-nutrition)",
  "var(--ops-chart-care)",
  "var(--ops-chart-pharmacy)",
  "oklch(0.72 0.14 200)",
  "oklch(0.76 0.16 45)",
  "oklch(0.68 0.15 285)",
] as const;

function hashName(name: string): number {
  let hash = 0;
  for (let i = 0; i < name.length; i += 1) {
    hash = (hash * 31 + name.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

export function categoryColor(name: string): string {
  const known = CATEGORY_COLOR[name];
  if (known) return known;
  const index = hashName(name) % CHART_PALETTE.length;
  return CHART_PALETTE[index] ?? CHART_PALETTE[0];
}
