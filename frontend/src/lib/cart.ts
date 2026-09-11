/** Thread-scoped purchase cart. Quantities come from Python purchase_list only. */

import { rowFromPurchaseItem } from "@/lib/adapter";
import type { ChatResponse, PurchaseListItem } from "@/lib/api";
import { calcFromApiRow } from "@/lib/ops-row";
import { nf, type Calc } from "@/lib/supplymate";

export type CartRelation = "new_query" | "refinement";

export type CartLine = {
  product_id: string;
  product_name: string;
  recommended_quantity: number;
  category?: string;
  supplier?: string;
  barcode?: string;
  estimated_purchase_value?: number;
};

export type CartTotals = {
  lines: number;
  units: number;
  value: number;
};

const PURCHASE_CART_MODES = new Set(["explore", "list", "single"]);

export function emptyCart(): CartLine[] {
  return [];
}

export function cartTotals(cart: CartLine[]): CartTotals {
  return {
    lines: cart.length,
    units: cart.reduce((sum, line) => sum + line.recommended_quantity, 0),
    value: cart.reduce((sum, line) => sum + (line.estimated_purchase_value ?? 0), 0),
  };
}

export function cartLinesFromPurchaseItems(items: PurchaseListItem[]): CartLine[] {
  return items.map((item) => ({
    product_id: item.product_id,
    product_name: item.product_name,
    recommended_quantity: item.recommended_quantity,
    category: item.category || undefined,
    supplier: item.supplier || undefined,
    barcode: item.barcode || undefined,
    estimated_purchase_value: item.estimated_purchase_value ?? undefined,
  }));
}

export function cartRelationFromChat(res: Pick<ChatResponse, "trace">): CartRelation {
  const trace = res.trace;
  if (trace && typeof trace === "object") {
    if (trace["relation"] === "refinement") return "refinement";
    const interp = trace["interpretation"];
    if (interp && typeof interp === "object" && interp !== null && "relation" in interp) {
      if ((interp as { relation?: unknown }).relation === "refinement") return "refinement";
    }
  }
  return "new_query";
}

export function shouldAddPurchaseToCart(
  res: Pick<ChatResponse, "mode" | "purchase_list">,
): boolean {
  const mode = (res.mode ?? "").toLowerCase();
  if (!PURCHASE_CART_MODES.has(mode)) return false;
  return (res.purchase_list?.length ?? 0) > 0;
}

export function mergeCart(cart: CartLine[], items: CartLine[], relation: CartRelation): CartLine[] {
  if (items.length === 0) return cart;
  const incoming = items.filter((item) => item.product_id);
  if (incoming.length === 0) return cart;
  const base = relation === "refinement" ? dropRefinedGroup(cart, incoming) : cart;
  return maxMerge(base, incoming);
}

export function applyPurchaseToCart(
  cart: CartLine[],
  res: Pick<ChatResponse, "mode" | "purchase_list" | "trace">,
): CartLine[] {
  if (!shouldAddPurchaseToCart(res)) return cart;
  return mergeCart(cart, cartLinesFromPurchaseItems(res.purchase_list ?? []), cartRelationFromChat(res));
}

export function cartFooterText(cart: CartLine[]): string {
  const { lines, units } = cartTotals(cart);
  if (lines === 0) return "";
  return `En el pedido: ${nf.format(lines)} líneas · ${nf.format(units)} u.`;
}

export function csvTextFromCart(cart: CartLine[]): string {
  const header = "product_id,product_name,category,supplier,recommended_quantity,estimated_purchase_value";
  const rows = cart.map((line) =>
    [
      csvCell(line.product_id),
      csvCell(line.product_name),
      csvCell(line.category ?? ""),
      csvCell(line.supplier ?? ""),
      csvCell(String(line.recommended_quantity)),
      csvCell(line.estimated_purchase_value == null ? "" : String(line.estimated_purchase_value)),
    ].join(","),
  );
  return [header, ...rows].join("\n");
}

export function downloadCartCsv(cart: CartLine[], filename = "pedido.csv"): void {
  if (typeof document === "undefined") return;
  const blob = new Blob([csvTextFromCart(cart)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function calcFromCartLine(line: CartLine): Calc {
  return {
    sku: {
      barcode: line.barcode || line.product_id,
      product_id: line.product_id,
      product_name: line.product_name,
      category: line.category ?? "",
      supplier: line.supplier ?? "",
      stock: 0,
      sales_30: 0,
      lead_time_days: 0,
      safety_stock: 0,
      list_price: 0,
    },
    avg_daily: 0,
    demand_horizon: 0,
    demand_lead: 0,
    stock_target: 0,
    recommended_quantity: line.recommended_quantity,
    coverage_days: 999,
    health: [],
    priority: "Baja",
    estimated_purchase_value: line.estimated_purchase_value ?? 0,
  };
}

export function resolvePoRows(
  cart: CartLine[],
  focusPurchaseList: PurchaseListItem[],
  fallbackRows: Calc[],
): Calc[] {
  if (cart.length > 0) return cart.map(calcFromCartLine);
  if (focusPurchaseList.length > 0) {
    return focusPurchaseList.map((item) => calcFromApiRow(rowFromPurchaseItem(item)));
  }
  return fallbackRows;
}

export function cartCategoryLabels(cart: CartLine[]): string[] {
  const cats: string[] = [];
  for (const line of cart) {
    const cat = line.category?.trim();
    if (cat && !cats.includes(cat)) cats.push(cat);
  }
  return cats.length > 0 ? cats : ["Pedido del chat"];
}

function dropRefinedGroup(cart: CartLine[], incoming: CartLine[]): CartLine[] {
  const ids = new Set(incoming.map((item) => item.product_id));
  const cats = new Set(
    incoming.map((item) => item.category).filter((cat): cat is string => Boolean(cat)),
  );
  return cart.filter((line) => {
    if (ids.has(line.product_id)) return false;
    if (line.category && cats.has(line.category)) return false;
    return true;
  });
}

function maxMerge(cart: CartLine[], incoming: CartLine[]): CartLine[] {
  const byId = new Map(cart.map((line) => [line.product_id, line]));
  for (const item of incoming) {
    const prev = byId.get(item.product_id);
    if (!prev || item.recommended_quantity > prev.recommended_quantity) {
      byId.set(item.product_id, prev ? { ...prev, ...item, recommended_quantity: item.recommended_quantity } : item);
    }
  }
  return [...byId.values()];
}

function csvCell(value: string): string {
  if (/[",\n\r]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}
