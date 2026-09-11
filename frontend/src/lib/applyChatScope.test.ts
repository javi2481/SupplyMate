import { describe, expect, it } from "vitest";
import type { ChatResponse } from "@/lib/api";
import { HttpError } from "@/lib/api";
import {
  COPY_ASSISTANT_UNAVAILABLE,
  COPY_CATALOG_LOAD_FAILED,
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

  it("opens highlight_product_id from scope", () => {
    const result = applyChatScope(
      EMPTY_SLICE,
      chat({ scope: { highlight_product_id: "P-9" } }),
    );
    expect(result.openProductId).toBe("P-9");
  });
});

describe("chatFailureMessage", () => {
  it("translates 404 into operator not-found copy", () => {
    expect(chatFailureMessage("SKU999", new HttpError(404, "/chat", "Product not found: SKU999"))).toBe(
      "No encontré «SKU999» en el catálogo.",
    );
    expect(chatFailureMessage("SKU999", new HttpError(404, "/chat", "Product not found: SKU999"))).not.toMatch(
      /Product not found|Pañales|Mamaderas/i,
    );
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
    expect(chatFailureMessage("quiebre", new HttpError(503, "/chat", "Assistant unavailable"))).toBe(
      COPY_ASSISTANT_UNAVAILABLE,
    );
    expect(chatFailureMessage("quiebre", new HttpError(500, "/chat", "Internal Server Error"))).toBe(
      COPY_ASSISTANT_UNAVAILABLE,
    );
    expect(COPY_ASSISTANT_UNAVAILABLE).not.toMatch(/motor|API|localhost|levantad|127\.0\.0\.1/i);
  });

  it("uses catalog load copy for other failures", () => {
    expect(chatFailureMessage("quiebre", new Error("Failed to fetch"))).toBe(COPY_CATALOG_LOAD_FAILED);
    expect(chatFailureMessage("quiebre", new HttpError(422, "/chat", "Unprocessable"))).toBe(
      COPY_CATALOG_LOAD_FAILED,
    );
    expect(COPY_CATALOG_LOAD_FAILED).not.toMatch(/motor|API|localhost|levantad/i);
  });
});
