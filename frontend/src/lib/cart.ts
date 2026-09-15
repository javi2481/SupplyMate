/** Thread-scoped purchase cart. Chat suggests; operator adds and decides qty. */

import { rowFromPurchaseItem } from "@/lib/adapter";
import type { PurchaseListItem } from "@/lib/api";
import { calcFromApiRow } from "@/lib/ops-row";
import { nf, type Calc } from "@/lib/supplymate";

export const MAX_ORDER_QUANTITY = 1_000_000;

export type CartLine = {
  product_id: string;
  product_name: string;
  suggested_quantity: number;
  order_quantity: number;
  category?: string;
  supplier?: string;
  barcode?: string;
  /** Estimated value at suggested_quantity; totals scale by order/suggested. */
  estimated_purchase_value?: number;
};

/** Legacy persisted shape (chat-cart-oc auto-accumulate era). */
export type LegacyCartLine = Partial<CartLine> & {
  product_id: string;
  recommended_quantity?: number;
};

export type CartTotals = {
  lines: number;
  units: number;
  value: number;
};

export function emptyCart(): CartLine[] {
  return [];
}

export function hydrateCartLine(raw: LegacyCartLine): CartLine {
  const suggested = Math.max(1, Math.floor(Number(raw.suggested_quantity ?? raw.recommended_quantity ?? 1)) || 1);
  const orderRaw = raw.order_quantity ?? suggested;
  const order = clampOrderQuantity(orderRaw) ?? suggested;
  return {
    product_id: raw.product_id,
    product_name: raw.product_name ?? raw.product_id,
    suggested_quantity: suggested,
    order_quantity: order,
    category: raw.category || undefined,
    supplier: raw.supplier || undefined,
    barcode: raw.barcode || undefined,
    estimated_purchase_value: raw.estimated_purchase_value ?? undefined,
  };
}

export function hydrateCart(raw: LegacyCartLine[] | undefined | null): CartLine[] {
  if (!raw?.length) return emptyCart();
  return raw.filter((line) => line.product_id).map(hydrateCartLine);
}

export function clampOrderQuantity(value: unknown): number | null {
  if (typeof value === "string" && value.trim() === "") return null;
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n) || !Number.isInteger(n) || n < 1 || n > MAX_ORDER_QUANTITY) return null;
  return n;
}

export function lineOrderValue(line: CartLine): number {
  const suggested = line.suggested_quantity;
  const value = line.estimated_purchase_value ?? 0;
  if (suggested <= 0) return value;
  return (value * line.order_quantity) / suggested;
}

export function cartTotals(cart: CartLine[]): CartTotals {
  return {
    lines: cart.length,
    units: cart.reduce((sum, line) => sum + line.order_quantity, 0),
    value: cart.reduce((sum, line) => sum + lineOrderValue(line), 0),
  };
}

export function cartLinesFromPurchaseItems(items: PurchaseListItem[]): CartLine[] {
  return items
    .filter((item) => item.product_id && item.recommended_quantity > 0)
    .map((item) =>
      hydrateCartLine({
        product_id: item.product_id,
        product_name: item.product_name,
        suggested_quantity: item.recommended_quantity,
        order_quantity: item.recommended_quantity,
        category: item.category || undefined,
        supplier: item.supplier || undefined,
        barcode: item.barcode || undefined,
        estimated_purchase_value: item.estimated_purchase_value ?? undefined,
      }),
    );
}

export function focusHasPurchase(items: PurchaseListItem[] | undefined | null): boolean {
  return (items ?? []).some((item) => Boolean(item.product_id) && item.recommended_quantity > 0);
}

/** Opt-in merge of current focus (legacy helper; UI path uses addLineToCart). */
export function addFocusToCart(cart: CartLine[], focusItems: PurchaseListItem[]): CartLine[] {
  const incoming = cartLinesFromPurchaseItems(focusItems);
  if (incoming.length === 0) return cart;
  return maxMergePreserveOrder(cart, incoming);
}

export type CartLineSource = {
  product_id: string;
  product_name: string;
  suggested_quantity: number;
  category?: string;
  supplier?: string;
  barcode?: string;
  estimated_purchase_value?: number;
};

/** Build cart source metadata from an Explore Calc row. */
export function cartSourceFromCalc(row: Calc): CartLineSource {
  const suggested = Math.max(0, Math.floor(row.recommended_quantity) || 0);
  return {
    product_id: row.sku.product_id,
    product_name: row.sku.product_name,
    suggested_quantity: suggested > 0 ? suggested : 1,
    category: row.sku.category || undefined,
    supplier: row.sku.supplier || undefined,
    barcode: row.sku.barcode || undefined,
    estimated_purchase_value:
      row.estimated_purchase_value > 0 ? row.estimated_purchase_value : undefined,
  };
}

/**
 * Confirm one SKU into the cart with the operator's typed qty.
 * Empty / 0 / invalid → no-op. Same product_id → upsert order_quantity.
 */
export function addLineToCart(
  cart: CartLine[],
  source: CartLineSource,
  orderQty: unknown,
): CartLine[] {
  if (!source.product_id) return cart;
  const qty = clampOrderQuantity(orderQty);
  if (qty == null) return cart;
  const suggested = Math.max(1, Math.floor(Number(source.suggested_quantity)) || 1);
  const nextLine: CartLine = {
    product_id: source.product_id,
    product_name: source.product_name || source.product_id,
    suggested_quantity: suggested,
    order_quantity: qty,
    category: source.category,
    supplier: source.supplier,
    barcode: source.barcode,
    estimated_purchase_value: source.estimated_purchase_value,
  };
  const idx = cart.findIndex((line) => line.product_id === source.product_id);
  if (idx < 0) return [...cart, nextLine];
  const copy = cart.slice();
  copy[idx] = nextLine;
  return copy;
}

export function setOrderQuantity(cart: CartLine[], productId: string, qty: unknown): CartLine[] {
  const nextQty = clampOrderQuantity(qty);
  if (nextQty == null) return cart;
  return cart.map((line) => (line.product_id === productId ? { ...line, order_quantity: nextQty } : line));
}

export function removeCartLine(cart: CartLine[], productId: string): CartLine[] {
  return cart.filter((line) => line.product_id !== productId);
}

export function cartFooterText(cart: CartLine[]): string {
  const { lines, units } = cartTotals(cart);
  if (lines === 0) return "";
  return `En el pedido: ${nf.format(lines)} líneas · ${nf.format(units)} u.`;
}

export function csvTextFromCart(cart: CartLine[]): string {
  const header =
    "product_id,product_name,category,supplier,order_quantity,suggested_quantity,estimated_purchase_value";
  const rows = cart.map((line) =>
    [
      csvCell(line.product_id),
      csvCell(line.product_name),
      csvCell(line.category ?? ""),
      csvCell(line.supplier ?? ""),
      csvCell(String(line.order_quantity)),
      csvCell(String(line.suggested_quantity)),
      csvCell(lineOrderValue(line) === 0 && line.estimated_purchase_value == null ? "" : String(lineOrderValue(line))),
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
    recommended_quantity: line.order_quantity,
    suggested_quantity: line.suggested_quantity,
    coverage_days: 999,
    health: [],
    priority: "Baja",
    estimated_purchase_value: lineOrderValue(line),
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

function wasEdited(line: CartLine): boolean {
  return line.order_quantity !== line.suggested_quantity;
}

function maxMergePreserveOrder(cart: CartLine[], incoming: CartLine[]): CartLine[] {
  const byId = new Map(cart.map((line) => [line.product_id, line]));
  for (const item of incoming) {
    const prev = byId.get(item.product_id);
    if (!prev) {
      byId.set(item.product_id, item);
      continue;
    }
    const suggested =
      item.suggested_quantity > prev.suggested_quantity ? item.suggested_quantity : prev.suggested_quantity;
    const winner = item.suggested_quantity >= prev.suggested_quantity ? item : prev;
    const edited = wasEdited(prev);
    byId.set(item.product_id, {
      ...prev,
      ...winner,
      suggested_quantity: suggested,
      order_quantity: edited ? prev.order_quantity : suggested,
      estimated_purchase_value: winner.estimated_purchase_value,
    });
  }
  return [...byId.values()];
}

function csvCell(value: string): string {
  if (/[",\n\r]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}
