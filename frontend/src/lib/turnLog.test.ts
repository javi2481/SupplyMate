import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { buildClientTurnTrace, emitClientTurnTrace, readClientTurnTraces } from "@/lib/turnLog";
import type { ChatResponse } from "@/lib/api";
import { EMPTY_SLICE } from "@/lib/scope";

function stubSessionStorage() {
  const store = new Map<string, string>();
  const mock = {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => {
      store.clear();
    },
    key: (index: number) => [...store.keys()][index] ?? null,
    get length() {
      return store.size;
    },
  };
  vi.stubGlobal("sessionStorage", mock);
  return mock;
}

describe("turnLog", () => {
  beforeEach(() => {
    stubSessionStorage();
    sessionStorage.clear();
    vi.spyOn(console, "info").mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("builds a client trace with server trace and chart mode", () => {
    const res = {
      answer: "ok",
      mode: "explore",
      product_id: "",
      product_name: "",
      recommended_quantity: 0,
      calculation: null,
      purchase_list: [],
      dashboard: null,
      scope: null,
      trace: { event: "chat.turn", route: "explore", chart_hint: "sku" },
    } as ChatResponse;
    const trace = buildClientTurnTrace({
      message: "críticos con cobertura",
      res,
      slice: { ...EMPTY_SLICE, health: ["riesgo_quiebre"], coverage: "0–3 días" },
      chartMode: "sku",
    });
    expect(trace.event).toBe("ui.chat.turn");
    expect(trace.chartMode).toBe("sku");
    expect(trace.serverTrace?.["route"]).toBe("explore");
    emitClientTurnTrace(trace);
    expect(readClientTurnTraces()).toHaveLength(1);
  });
});
