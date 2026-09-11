import { describe, expect, it } from "vitest";
import type { ChatResponse, PurchaseListItem } from "@/lib/api";
import {
  applyPurchaseToCart,
  cartCategoryLabels,
  cartFooterText,
  cartLinesFromPurchaseItems,
  cartRelationFromChat,
  cartTotals,
  csvTextFromCart,
  emptyCart,
  mergeCart,
  resolvePoRows,
  shouldAddPurchaseToCart,
  type CartLine,
} from "@/lib/cart";
import type { Calc } from "@/lib/supplymate";

function line(partial: Partial<CartLine> & Pick<CartLine, "product_id">): CartLine {
  return {
    product_name: partial.product_name ?? partial.product_id,
    recommended_quantity: partial.recommended_quantity ?? 1,
    ...partial,
  };
}

function purchaseItem(partial: Partial<PurchaseListItem> & Pick<PurchaseListItem, "product_id">): PurchaseListItem {
  return {
    barcode: partial.barcode ?? partial.product_id,
    product_name: partial.product_name ?? partial.product_id,
    supplier: partial.supplier ?? "Prov",
    category: partial.category ?? "Cat",
    subcategory: partial.subcategory ?? "",
    current_stock: 0,
    reorder_point: null,
    below_reorder_point: true,
    average_daily_demand: 1,
    days_of_supply: 0,
    health_bucket: "stockout_risk",
    recommended_quantity: partial.recommended_quantity ?? 4,
    operational_priority: "high",
    purchase_cost: null,
    estimated_purchase_value: partial.estimated_purchase_value ?? 100,
    ...partial,
  };
}

function chat(overrides: Partial<ChatResponse> = {}): ChatResponse {
  return {
    answer: "ok",
    mode: "explore",
    product_id: "",
    product_name: "",
    recommended_quantity: 0,
    calculation: null,
    purchase_list: [],
    dashboard: null,
    scope: null,
    ...overrides,
  };
}

describe("emptyCart / cartTotals", () => {
  it("starts empty with zero totals", () => {
    const cart = emptyCart();
    expect(cart).toEqual([]);
    expect(cartTotals(cart)).toEqual({ lines: 0, units: 0, value: 0 });
  });

  it("counts distinct lines, units, and estimated value", () => {
    const cart = [
      line({ product_id: "A", recommended_quantity: 10, estimated_purchase_value: 40 }),
      line({ product_id: "B", recommended_quantity: 5, estimated_purchase_value: 15 }),
    ];
    expect(cartTotals(cart)).toEqual({ lines: 2, units: 15, value: 55 });
  });
});

describe("mergeCart new_query", () => {
  it("adds a new SKU without touching other lines", () => {
    const cart = [line({ product_id: "A", category: "Pañales", recommended_quantity: 10 })];
    const next = mergeCart(
      cart,
      [line({ product_id: "B", category: "Shampoo", recommended_quantity: 3 })],
      "new_query",
    );
    expect(next.map((row) => row.product_id)).toEqual(["A", "B"]);
    expect(next.find((row) => row.product_id === "A")?.recommended_quantity).toBe(10);
    expect(next.find((row) => row.product_id === "B")?.recommended_quantity).toBe(3);
  });

  it("keeps max recommended_quantity for the same product_id and never sums", () => {
    const cart = [line({ product_id: "A", recommended_quantity: 10, estimated_purchase_value: 100 })];
    const lower = mergeCart(cart, [line({ product_id: "A", recommended_quantity: 7, estimated_purchase_value: 70 })], "new_query");
    expect(lower).toHaveLength(1);
    expect(lower[0]?.recommended_quantity).toBe(10);
    expect(lower[0]?.estimated_purchase_value).toBe(100);

    const higher = mergeCart(cart, [line({ product_id: "A", recommended_quantity: 15, estimated_purchase_value: 150 })], "new_query");
    expect(higher).toHaveLength(1);
    expect(higher[0]?.recommended_quantity).toBe(15);
    expect(higher[0]?.estimated_purchase_value).toBe(150);
  });
});

describe("mergeCart refinement", () => {
  it("drops cart lines that share a category with the new items, then adds the new subset", () => {
    const cart = [
      line({ product_id: "P1", category: "Pañales", recommended_quantity: 10 }),
      line({ product_id: "P2", category: "Pañales", recommended_quantity: 8 }),
      line({ product_id: "S1", category: "Shampoo", recommended_quantity: 5 }),
    ];
    const next = mergeCart(
      cart,
      [
        line({ product_id: "P1", category: "Pañales", recommended_quantity: 4 }),
        line({ product_id: "P3", category: "Pañales", recommended_quantity: 2 }),
      ],
      "refinement",
    );
    expect(next.map((row) => row.product_id).sort()).toEqual(["P1", "P3", "S1"]);
    expect(next.find((row) => row.product_id === "P1")?.recommended_quantity).toBe(4);
    expect(next.find((row) => row.product_id === "P2")).toBeUndefined();
    expect(next.find((row) => row.product_id === "S1")?.recommended_quantity).toBe(5);
  });

  it("still replaces by product_id when incoming lines have no category", () => {
    const cart = [line({ product_id: "A", category: "X", recommended_quantity: 9 })];
    const next = mergeCart(cart, [line({ product_id: "A", recommended_quantity: 3 })], "refinement");
    expect(next).toEqual([line({ product_id: "A", recommended_quantity: 3 })]);
  });
});

describe("sales / empty purchase_list no-op", () => {
  it("does not add when purchase_list is empty", () => {
    const cart = [line({ product_id: "A", recommended_quantity: 2 })];
    expect(shouldAddPurchaseToCart(chat({ mode: "explore", purchase_list: [] }))).toBe(false);
    expect(applyPurchaseToCart(cart, chat({ mode: "explore", purchase_list: [] }))).toEqual(cart);
  });

  it("does not add sales or disambiguation turns even with a non-empty list", () => {
    const cart = [line({ product_id: "A", recommended_quantity: 2 })];
    const items = [purchaseItem({ product_id: "B", recommended_quantity: 9 })];
    expect(shouldAddPurchaseToCart(chat({ mode: "sales", purchase_list: items }))).toBe(false);
    expect(applyPurchaseToCart(cart, chat({ mode: "sales", purchase_list: items }))).toEqual(cart);
    expect(shouldAddPurchaseToCart(chat({ mode: "disambiguation", purchase_list: items }))).toBe(false);
  });

  it("adds explore/list purchase turns and reads refinement from the server trace", () => {
    const items = [purchaseItem({ product_id: "B", category: "Jabones", recommended_quantity: 6 })];
    expect(shouldAddPurchaseToCart(chat({ mode: "list", purchase_list: items }))).toBe(true);
    const added = applyPurchaseToCart(emptyCart(), chat({ mode: "explore", purchase_list: items }));
    expect(added).toHaveLength(1);
    expect(added[0]?.product_id).toBe("B");
    expect(added[0]?.recommended_quantity).toBe(6);

    const trace = { interpretation: { relation: "refinement" } };
    expect(cartRelationFromChat(chat({ trace }))).toBe("refinement");
    expect(cartRelationFromChat(chat({}))).toBe("new_query");
  });
});

describe("cartLinesFromPurchaseItems", () => {
  it("copies Python qty and identity fields without inventing numbers", () => {
    const fromApi = cartLinesFromPurchaseItems([
      purchaseItem({
        product_id: "SKU-9",
        product_name: "Jabón",
        category: "Jabones",
        supplier: "Sur",
        recommended_quantity: 12,
        estimated_purchase_value: 240,
        barcode: "779",
      }),
    ]);
    expect(fromApi).toEqual([
      {
        product_id: "SKU-9",
        product_name: "Jabón",
        recommended_quantity: 12,
        category: "Jabones",
        supplier: "Sur",
        barcode: "779",
        estimated_purchase_value: 240,
      },
    ]);
  });
});

describe("multi-turn cart scenario", () => {
  function purchaseItem(
    partial: Partial<PurchaseListItem> & Pick<PurchaseListItem, "product_id" | "category">,
  ): PurchaseListItem {
    return {
      barcode: partial.barcode ?? partial.product_id,
      product_name: partial.product_name ?? partial.product_id,
      supplier: partial.supplier ?? "Prov",
      subcategory: partial.subcategory ?? "",
      current_stock: 0,
      reorder_point: null,
      below_reorder_point: true,
      average_daily_demand: 1,
      days_of_supply: 0,
      health_bucket: "stockout_risk",
      recommended_quantity: partial.recommended_quantity ?? 4,
      operational_priority: "high",
      purchase_cost: null,
      estimated_purchase_value: partial.estimated_purchase_value ?? 100,
      ...partial,
    };
  }

  it("accumulates two categories, ignores sales, and keeps the other category on refinement", () => {
    let cart = emptyCart();

    cart = applyPurchaseToCart(
      cart,
      chat({
        mode: "explore",
        purchase_list: [
          purchaseItem({ product_id: "C1", category: "Cosmetica", product_name: "Crema", recommended_quantity: 6 }),
        ],
      }),
    );
    cart = applyPurchaseToCart(
      cart,
      chat({
        mode: "explore",
        purchase_list: [
          purchaseItem({ product_id: "S1", category: "Shampoo", product_name: "Shampoo", recommended_quantity: 4 }),
        ],
      }),
    );
    expect(cart.map((row) => row.product_id).sort()).toEqual(["C1", "S1"]);

    const beforeSales = cart;
    cart = applyPurchaseToCart(
      cart,
      chat({
        mode: "sales",
        purchase_list: [purchaseItem({ product_id: "X9", category: "Ventas", recommended_quantity: 99 })],
      }),
    );
    expect(cart).toEqual(beforeSales);

    cart = applyPurchaseToCart(
      cart,
      chat({
        mode: "explore",
        trace: { interpretation: { relation: "refinement" } },
        purchase_list: [
          purchaseItem({ product_id: "C2", category: "Cosmetica", product_name: "Serum", recommended_quantity: 2 }),
        ],
      }),
    );
    expect(cart.map((row) => row.product_id).sort()).toEqual(["C2", "S1"]);
    expect(cart.find((row) => row.product_id === "S1")?.recommended_quantity).toBe(4);
  });
});

describe("cartFooterText / csv / resolvePoRows", () => {
  it("hides the footer when the cart is empty and formats counts when it is not", () => {
    expect(cartFooterText(emptyCart())).toBe("");
    expect(cartFooterText([line({ product_id: "A", recommended_quantity: 10 }), line({ product_id: "B", recommended_quantity: 5 })])).toBe(
      "En el pedido: 2 líneas · 15 u.",
    );
  });

  it("labels the OC from distinct cart categories", () => {
    expect(
      cartCategoryLabels([
        line({ product_id: "A", category: "Pañales" }),
        line({ product_id: "B", category: "Pañales" }),
        line({ product_id: "C", category: "Shampoo" }),
      ]),
    ).toEqual(["Pañales", "Shampoo"]);
    expect(cartCategoryLabels([line({ product_id: "A" })])).toEqual(["Pedido del chat"]);
  });

  it("builds a CSV with cart identity and qty columns", () => {
    const csv = csvTextFromCart([
      line({
        product_id: "A",
        product_name: "Jabón, extra",
        category: "Jabones",
        supplier: "Sur",
        recommended_quantity: 3,
        estimated_purchase_value: 30,
      }),
    ]);
    expect(csv.split("\n")[0]).toBe(
      "product_id,product_name,category,supplier,recommended_quantity,estimated_purchase_value",
    );
    expect(csv).toContain("A,");
    expect(csv).toContain('"Jabón, extra"');
    expect(csv).toContain(",3,30");
  });

  it("prefers cart rows for OC, else the focus purchase list, else fallback rows", () => {
    const fallback: Calc[] = [
      {
        sku: {
          barcode: "x",
          product_id: "FALL",
          product_name: "Fallback",
          category: "Z",
          supplier: "Z",
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
        recommended_quantity: 99,
        coverage_days: 1,
        health: [],
        priority: "Baja",
        estimated_purchase_value: 1,
      },
    ];
    const cart = [line({ product_id: "C1", product_name: "Cart SKU", recommended_quantity: 8, category: "A" })];
    const fromCart = resolvePoRows(cart, [purchaseItem({ product_id: "F1", recommended_quantity: 1 })], fallback);
    expect(fromCart).toHaveLength(1);
    expect(fromCart[0]?.sku.product_id).toBe("C1");
    expect(fromCart[0]?.recommended_quantity).toBe(8);

    const fromFocus = resolvePoRows(
      emptyCart(),
      [purchaseItem({ product_id: "F1", product_name: "Focus", recommended_quantity: 7 })],
      fallback,
    );
    expect(fromFocus).toHaveLength(1);
    expect(fromFocus[0]?.sku.product_id).toBe("F1");
    expect(fromFocus[0]?.recommended_quantity).toBe(7);

    const fromFallback = resolvePoRows(emptyCart(), [], fallback);
    expect(fromFallback).toBe(fallback);
  });
});
