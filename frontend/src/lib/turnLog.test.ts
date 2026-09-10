import { describe, expect, it, vi, beforeEach } from "vitest";
import { buildClientTurnTrace, emitClientTurnTrace, readClientTurnTraces } from "@/lib/turnLog";
import type { ChatResponse } from "@/lib/api";
import { EMPTY_SLICE } from "@/lib/scope";

describe("turnLog", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.spyOn(console, "info").mockImplementation(() => undefined);
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
    expect(trace.serverTrace?.route).toBe("explore");
    emitClientTurnTrace(trace);
    expect(readClientTurnTraces()).toHaveLength(1);
  });
});
