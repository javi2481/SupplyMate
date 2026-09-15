import { describe, expect, it } from "vitest";
import type { PurchaseListItem } from "@/lib/api";
import {
  addFocusToCart,
  addLineToCart,
  cartCategoryLabels,
  cartFooterText,
  cartLinesFromPurchaseItems,
  cartSourceFromCalc,
  cartTotals,
  csvTextFromCart,
  emptyCart,
  focusHasPurchase,
  hydrateCart,
  hydrateCartLine,
  normalizeCartCsvColumns,
  removeCartLine,
  resolvePoRows,
  setOrderQuantity,
  type CartLine,
} from "@/lib/cart";
import type { Calc } from "@/lib/supplymate";

function line(partial: Partial<CartLine> & Pick<CartLine, "product_id">): CartLine {
  const suggested = partial.suggested_quantity ?? 1;
  return {
    product_name: partial.product_name ?? partial.product_id,
    suggested_quantity: suggested,
    order_quantity: partial.order_quantity ?? suggested,
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

describe("hydrateCartLine / hydrateCart", () => {
  it("maps legacy recommended_quantity into suggested and order", () => {
    expect(hydrateCartLine({ product_id: "A", product_name: "A", recommended_quantity: 20 })).toEqual({
      product_id: "A",
      product_name: "A",
      suggested_quantity: 20,
      order_quantity: 20,
    });
  });

  it("keeps an existing edited order_quantity when hydrating", () => {
    const cart = hydrateCart([
      { product_id: "A", suggested_quantity: 20, order_quantity: 50, product_name: "A" },
    ]);
    expect(cart[0]?.order_quantity).toBe(50);
    expect(cart[0]?.suggested_quantity).toBe(20);
  });
});

describe("emptyCart / cartTotals", () => {
  it("starts empty with zero totals", () => {
    expect(emptyCart()).toEqual([]);
    expect(cartTotals(emptyCart())).toEqual({ lines: 0, units: 0, value: 0 });
  });

  it("counts lines, order units, and value scaled from suggested", () => {
    const cart = [
      line({ product_id: "A", suggested_quantity: 10, order_quantity: 20, estimated_purchase_value: 40 }),
      line({ product_id: "B", suggested_quantity: 5, order_quantity: 5, estimated_purchase_value: 15 }),
    ];
    expect(cartTotals(cart)).toEqual({ lines: 2, units: 25, value: 95 });
  });
});

describe("addFocusToCart", () => {
  it("adds focus SKUs without touching other lines", () => {
    const cart = [line({ product_id: "A", category: "Pañales", suggested_quantity: 10 })];
    const next = addFocusToCart(cart, [
      purchaseItem({ product_id: "B", category: "Shampoo", recommended_quantity: 3, estimated_purchase_value: 30 }),
    ]);
    expect(next.map((row) => row.product_id)).toEqual(["A", "B"]);
    expect(next.find((row) => row.product_id === "B")?.order_quantity).toBe(3);
    expect(next.find((row) => row.product_id === "B")?.suggested_quantity).toBe(3);
  });

  it("keeps max suggested for the same product_id and never sums", () => {
    const cart = [line({ product_id: "A", suggested_quantity: 10, order_quantity: 10, estimated_purchase_value: 100 })];
    const lower = addFocusToCart(cart, [
      purchaseItem({ product_id: "A", recommended_quantity: 7, estimated_purchase_value: 70 }),
    ]);
    expect(lower).toHaveLength(1);
    expect(lower[0]?.suggested_quantity).toBe(10);
    expect(lower[0]?.order_quantity).toBe(10);

    const higher = addFocusToCart(cart, [
      purchaseItem({ product_id: "A", recommended_quantity: 15, estimated_purchase_value: 150 }),
    ]);
    expect(higher[0]?.suggested_quantity).toBe(15);
    expect(higher[0]?.order_quantity).toBe(15);
    expect(higher[0]?.estimated_purchase_value).toBe(150);
  });

  it("does not overwrite an edited order_quantity on re-add", () => {
    const cart = [line({ product_id: "A", suggested_quantity: 20, order_quantity: 50, estimated_purchase_value: 200 })];
    const next = addFocusToCart(cart, [
      purchaseItem({ product_id: "A", recommended_quantity: 25, estimated_purchase_value: 250 }),
    ]);
    expect(next[0]?.suggested_quantity).toBe(25);
    expect(next[0]?.order_quantity).toBe(50);
  });

  it("does not drop sibling category lines (no refinement drop)", () => {
    const cart = [
      line({ product_id: "P1", category: "Pañales", suggested_quantity: 10 }),
      line({ product_id: "P2", category: "Pañales", suggested_quantity: 8 }),
      line({ product_id: "S1", category: "Shampoo", suggested_quantity: 5 }),
    ];
    const next = addFocusToCart(cart, [
      purchaseItem({ product_id: "P1", category: "Pañales", recommended_quantity: 4 }),
      purchaseItem({ product_id: "P3", category: "Pañales", recommended_quantity: 2 }),
    ]);
    expect(next.map((row) => row.product_id).sort()).toEqual(["P1", "P2", "P3", "S1"]);
  });

  it("no-ops on empty focus or zero qty", () => {
    const cart = [line({ product_id: "A", suggested_quantity: 2 })];
    expect(addFocusToCart(cart, [])).toEqual(cart);
    expect(addFocusToCart(cart, [purchaseItem({ product_id: "B", recommended_quantity: 0 })])).toEqual(cart);
    expect(focusHasPurchase([])).toBe(false);
    expect(focusHasPurchase([purchaseItem({ product_id: "B", recommended_quantity: 3 })])).toBe(true);
  });
});

describe("addLineToCart", () => {
  const source = {
    product_id: "A",
    product_name: "Jabón",
    suggested_quantity: 20,
    category: "Jabones",
    supplier: "Sur",
    barcode: "779",
    estimated_purchase_value: 200,
  };

  it("no-ops on empty, zero, or invalid qty", () => {
    const cart = emptyCart();
    expect(addLineToCart(cart, source, "")).toEqual(cart);
    expect(addLineToCart(cart, source, 0)).toEqual(cart);
    expect(addLineToCart(cart, source, 1.5)).toEqual(cart);
    expect(addLineToCart(cart, source, "nope")).toEqual(cart);
  });

  it("adds a line with typed order qty and python suggested", () => {
    const next = addLineToCart(emptyCart(), source, 50);
    expect(next).toHaveLength(1);
    expect(next[0]).toMatchObject({
      product_id: "A",
      order_quantity: 50,
      suggested_quantity: 20,
      category: "Jabones",
    });
  });

  it("upserts order_quantity when the SKU is already in the cart", () => {
    const cart = addLineToCart(emptyCart(), source, 50);
    const next = addLineToCart(cart, { ...source, suggested_quantity: 25 }, 80);
    expect(next).toHaveLength(1);
    expect(next[0]?.order_quantity).toBe(80);
    expect(next[0]?.suggested_quantity).toBe(25);
  });

  it("builds source metadata from a Calc row", () => {
    const row: Calc = {
      sku: {
        barcode: "779",
        product_id: "A",
        product_name: "Jabón",
        category: "Jabones",
        supplier: "Sur",
        stock: 1,
        sales_30: 10,
        lead_time_days: 3,
        safety_stock: 0,
        list_price: 0,
      },
      avg_daily: 1,
      demand_horizon: 1,
      demand_lead: 1,
      stock_target: 1,
      recommended_quantity: 20,
      coverage_days: 2,
      health: [],
      priority: "Alta",
      estimated_purchase_value: 200,
    };
    expect(cartSourceFromCalc(row).suggested_quantity).toBe(20);
    expect(addLineToCart(emptyCart(), cartSourceFromCalc(row), 12)[0]?.order_quantity).toBe(12);
  });
});

describe("setOrderQuantity / removeCartLine", () => {
  it("sets a valid integer order qty and rejects garbage", () => {
    const cart = [line({ product_id: "A", suggested_quantity: 20, order_quantity: 20 })];
    expect(setOrderQuantity(cart, "A", 50)[0]?.order_quantity).toBe(50);
    expect(setOrderQuantity(cart, "A", 0)).toEqual(cart);
    expect(setOrderQuantity(cart, "A", 1.5)).toEqual(cart);
    expect(setOrderQuantity(cart, "A", "nope")).toEqual(cart);
  });

  it("removes a line by product_id", () => {
    const cart = [
      line({ product_id: "A", suggested_quantity: 2 }),
      line({ product_id: "B", suggested_quantity: 3 }),
    ];
    expect(removeCartLine(cart, "A").map((row) => row.product_id)).toEqual(["B"]);
  });
});

describe("cartLinesFromPurchaseItems", () => {
  it("copies Python qty into suggested and order", () => {
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
        suggested_quantity: 12,
        order_quantity: 12,
        category: "Jabones",
        supplier: "Sur",
        barcode: "779",
        estimated_purchase_value: 240,
      },
    ]);
  });
});

describe("multi-turn opt-in scenario", () => {
  it("accumulates two categories only after addFocusToCart", () => {
    let cart = emptyCart();
    const cosmetics = [purchaseItem({ product_id: "C1", category: "Cosmetica", recommended_quantity: 6 })];
    const shampoo = [purchaseItem({ product_id: "S1", category: "Shampoo", recommended_quantity: 4 })];

    expect(cart).toEqual([]);
    cart = addFocusToCart(cart, cosmetics);
    cart = addFocusToCart(cart, shampoo);
    expect(cart.map((row) => row.product_id).sort()).toEqual(["C1", "S1"]);

    cart = setOrderQuantity(cart, "C1", 50);
    cart = addFocusToCart(cart, cosmetics);
    expect(cart.find((row) => row.product_id === "C1")?.order_quantity).toBe(50);
  });
});

describe("cartFooterText / csv / resolvePoRows", () => {
  it("hides the footer when the cart is empty and formats order units", () => {
    expect(cartFooterText(emptyCart())).toBe("");
    expect(
      cartFooterText([
        line({ product_id: "A", suggested_quantity: 10, order_quantity: 10 }),
        line({ product_id: "B", suggested_quantity: 5, order_quantity: 5 }),
      ]),
    ).toBe("En el pedido: 2 líneas · 15 u.");
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

  it("builds a CSV with order and suggested qty columns", () => {
    const csv = csvTextFromCart(
      [
        line({
          product_id: "A",
          product_name: "Jabón, extra",
          category: "Jabones",
          supplier: "Sur",
          suggested_quantity: 3,
          order_quantity: 50,
          estimated_purchase_value: 30,
        }),
      ],
      [
        "product_id",
        "product_name",
        "category",
        "supplier",
        "order_quantity",
        "suggested_quantity",
        "estimated_purchase_value",
      ],
    );
    expect(csv.split("\n")[0]).toBe(
      "order_quantity,product_id,product_name,category,supplier,suggested_quantity,estimated_purchase_value",
    );
    expect(csv).toContain('"Jabón, extra"');
    expect(csv.split("\n")[1]).toBe('50,A,"Jabón, extra",Jabones,Sur,3,500');
  });

  it("exports only the selected columns in picker order", () => {
    const csv = csvTextFromCart(
      [
        line({
          product_id: "A",
          product_name: "Jabón",
          barcode: "779123",
          order_quantity: 12,
          suggested_quantity: 10,
        }),
      ],
      ["barcode", "order_quantity"],
    );
    expect(csv).toBe("barcode,order_quantity\n779123,12");
  });

  it("falls back to barcode + qty when normalize gets an empty selection", () => {
    expect(normalizeCartCsvColumns([])).toEqual(["barcode", "order_quantity"]);
    expect(normalizeCartCsvColumns(["nope", "barcode"])).toEqual(["barcode"]);
  });

  it("prefers cart rows for OC using order_quantity", () => {
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
    const cart = [
      line({ product_id: "C1", product_name: "Cart SKU", suggested_quantity: 8, order_quantity: 50, category: "A" }),
    ];
    const fromCart = resolvePoRows(cart, [purchaseItem({ product_id: "F1", recommended_quantity: 1 })], fallback);
    expect(fromCart[0]?.sku.product_id).toBe("C1");
    expect(fromCart[0]?.recommended_quantity).toBe(50);
    expect(fromCart[0]?.suggested_quantity).toBe(8);

    const fromFocus = resolvePoRows(
      emptyCart(),
      [purchaseItem({ product_id: "F1", product_name: "Focus", recommended_quantity: 7 })],
      fallback,
    );
    expect(fromFocus[0]?.sku.product_id).toBe("F1");
    expect(fromFocus[0]?.recommended_quantity).toBe(7);

    expect(resolvePoRows(emptyCart(), [], fallback)).toBe(fallback);
  });
});
