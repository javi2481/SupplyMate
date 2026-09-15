import { describe, expect, it } from "vitest";
import type { ChatResponse, InventoryDashboard, PurchaseListItem } from "@/lib/api";
import { HttpError } from "@/lib/api";
import {
  COPY_ASSISTANT_UNAVAILABLE,
  COPY_CATALOG_LOAD_FAILED,
  COPY_CHAT_TIMEOUT,
  applyChatScope,
  chatFailureMessage,
} from "@/lib/applyChatScope";
import { EMPTY_SLICE, type UiSlice } from "@/lib/scope";

const dirty: UiSlice = {
  ...EMPTY_SLICE,
  cats: ["Cuidado"],
  health: ["sobrestock"],
  buyOnly: false,
};

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

function dashboard(overrides: Partial<InventoryDashboard> = {}): InventoryDashboard {
  return {
    skus: 100,
    stockout_risk: 10,
    understock: 5,
    overstock: 5,
    healthy: 80,
    avg_coverage: 20,
    estimated_purchase_value: 99999,
    recommended_units: 17753,
    purchase_skus: 50,
    by_category: [{ category: "GrupoA", recommended_quantity: 10, sku_count: 2 }],
    ...overrides,
  };
}

function purchaseItem(): PurchaseListItem {
  return {
    product_id: "1",
    barcode: "",
    product_name: "A",
    supplier: "",
    category: "GrupoB",
    subcategory: "",
    current_stock: 0,
    reorder_point: null,
    below_reorder_point: true,
    average_daily_demand: 1,
    days_of_supply: null,
    health_bucket: "stockout_risk",
    recommended_quantity: 1,
    operational_priority: "high",
    purchase_cost: null,
    estimated_purchase_value: null,
  };
}

describe("applyChatScope", () => {
  it("replaces leftover category when Python only sends stockout_risk", () => {
    const result = applyChatScope(
      dirty,
      chat({
        scope: { health_buckets: ["stockout_risk"] },
      }),
    );
    expect(result.slice.cats).toEqual([]);
    expect(result.slice.health).toEqual(["riesgo_quiebre"]);
    expect(result.slice.buyOnly).toBe(false);
    expect(result.openProductId).toBeNull();
  });

  it("sets buyOnly when mode is list", () => {
    const result = applyChatScope(dirty, chat({ mode: "list", scope: {} }));
    expect(result.slice.buyOnly).toBe(true);
    expect(result.slice.cats).toEqual([]);
  });

  it("keeps the current slice when scope is null", () => {
    const result = applyChatScope(dirty, chat({ scope: null, product_id: "P-1" }));
    expect(result.slice).toEqual(dirty);
    expect(result.openProductId).toBe("P-1");
  });

  it("replaces leftover filters when dashboard is present without scope", () => {
    const snap = dashboard();
    const result = applyChatScope(
      dirty,
      chat({
        mode: "explore",
        scope: null,
        dashboard: snap,
      }),
    );
    expect(result.slice).toEqual(EMPTY_SLICE);
    expect(result.slice.cats).toEqual([]);
    expect(result.slice.health).toEqual([]);
    expect(result.slice.coverage).toBeNull();
    expect(result.slice.buyOnly).toBe(false);
    expect(result.chatBoard).toEqual({ dashboard: snap, purchaseList: [] });
    expect(result.replacedSurface).toBe(true);
    expect(result.pushHistory).toBe(false);
    expect(result.conversationSlice).toEqual(dirty);
  });

  it("replaces with the root recorte when scope is present but empty and there is no purchase list", () => {
    const snap = dashboard({ recommended_units: 3436798 });
    const result = applyChatScope(
      dirty,
      chat({
        scope: {
          categories: [],
          health_buckets: [],
          suppliers: [],
          name_tokens: [],
        },
        dashboard: snap,
        purchase_list: [],
      }),
    );
    expect(result.slice.cats).toEqual([]);
    expect(result.slice.health).toEqual([]);
    expect(result.replacedSurface).toBe(true);
    expect(result.conversationSlice).toEqual(dirty);
    expect(result.chatBoard).toEqual({ dashboard: snap, purchaseList: [] });
  });

  it("keeps the panel when scope and dashboard are both absent", () => {
    const result = applyChatScope(dirty, chat({ scope: null, dashboard: null }));
    expect(result.slice).toEqual(dirty);
    expect(result.chatBoard).toBe("keep");
    expect(result.pushHistory).toBe(false);
    expect(result.conversationSlice).toEqual(dirty);
  });

  it("keeps conversationSlice across a keep-panel turn after a replaced surface", () => {
    const first = applyChatScope(dirty, chat({ scope: null, dashboard: dashboard() }));
    const second = applyChatScope(
      first.slice,
      chat({ scope: null, dashboard: null, mode: "disambiguation" }),
      first.conversationSlice,
    );
    expect(second.slice).toEqual(EMPTY_SLICE);
    expect(second.chatBoard).toBe("keep");
    expect(second.conversationSlice).toEqual(dirty);
  });

  it("maps a present non-root scope over previous UI state", () => {
    const result = applyChatScope(
      dirty,
      chat({
        scope: { categories: ["GrupoB"], health_buckets: ["stockout_risk"] },
        dashboard: dashboard({ recommended_units: 12 }),
        purchase_list: [purchaseItem()],
      }),
    );
    expect(result.slice.cats).toEqual(["GrupoB"]);
    expect(result.slice.health).toEqual(["riesgo_quiebre"]);
    expect(result.replacedSurface).toBe(false);
    expect(result.pushHistory).toBe(true);
    expect(result.conversationSlice.cats).toEqual(["GrupoB"]);
    expect(result.chatBoard).not.toBe("keep");
    if (result.chatBoard === "keep" || result.chatBoard == null) {
      throw new Error("scoped turn must replace chatBoard from the response dashboard");
    }
    expect(result.chatBoard.dashboard.recommended_units).toBe(12);
  });

  it("list mode with a purchase list still toggles buyOnly and is not a replaced surface", () => {
    const items = [purchaseItem()];
    const snap = dashboard();
    const result = applyChatScope(
      dirty,
      chat({ mode: "list", scope: {}, dashboard: snap, purchase_list: items }),
    );
    expect(result.slice.buyOnly).toBe(true);
    expect(result.replacedSurface).toBe(false);
    expect(result.pushHistory).toBe(true);
    expect(result.conversationSlice.buyOnly).toBe(true);
    expect(result.chatBoard).toEqual({ dashboard: snap, purchaseList: items });
  });

  it("opens highlight_product_id from scope", () => {
    const result = applyChatScope(EMPTY_SLICE, chat({ scope: { highlight_product_id: "P-9" } }));
    expect(result.openProductId).toBe("P-9");
  });
});

describe("chatFailureMessage", () => {
  it("translates 404 into operator not-found copy", () => {
    expect(
      chatFailureMessage("SKU999", new HttpError(404, "/chat", "Product not found: SKU999")),
    ).toBe("No encontré «SKU999» en el catálogo.");
    expect(
      chatFailureMessage("SKU999", new HttpError(404, "/chat", "Product not found: SKU999")),
    ).not.toMatch(/Product not found|Pañales|Mamaderas/i);
  });

  it("prefers Product not found token over the full user query", () => {
    expect(
      chatFailureMessage(
        "que me falta de unilever?",
        new HttpError(404, "/chat", "Product not found: unilever"),
      ),
    ).toBe("No encontré «unilever» en el catálogo.");
  });

  it("falls back to the query when detail has no token", () => {
    expect(chatFailureMessage("SKU999", new HttpError(404, "/chat", "Not found"))).toBe(
      "No encontré «SKU999» en el catálogo.",
    );
  });

  it("uses assistant-unavailable copy for server failures", () => {
    expect(
      chatFailureMessage("quiebre", new HttpError(503, "/chat", "Assistant unavailable")),
    ).toBe(COPY_ASSISTANT_UNAVAILABLE);
    expect(
      chatFailureMessage("quiebre", new HttpError(500, "/chat", "Internal Server Error")),
    ).toBe(COPY_ASSISTANT_UNAVAILABLE);
    expect(COPY_ASSISTANT_UNAVAILABLE).not.toMatch(/motor|API|localhost|levantad|127\.0\.0\.1/i);
  });

  it("uses catalog load copy for other failures", () => {
    expect(chatFailureMessage("quiebre", new Error("Failed to fetch"))).toBe(
      COPY_CATALOG_LOAD_FAILED,
    );
    expect(chatFailureMessage("quiebre", new HttpError(422, "/chat", "Unprocessable"))).toBe(
      COPY_CATALOG_LOAD_FAILED,
    );
    expect(COPY_CATALOG_LOAD_FAILED).not.toMatch(/motor|API|localhost|levantad/i);
  });

  it("uses timeout copy for AbortError / TimeoutError", () => {
    expect(chatFailureMessage("quiebre", new DOMException("Aborted", "AbortError"))).toBe(
      COPY_CHAT_TIMEOUT,
    );
    expect(chatFailureMessage("quiebre", new DOMException("Timed out", "TimeoutError"))).toBe(
      COPY_CHAT_TIMEOUT,
    );
    const named = new Error("signal timed out");
    named.name = "TimeoutError";
    expect(chatFailureMessage("quiebre", named)).toBe(COPY_CHAT_TIMEOUT);
  });
});
