/** Client-side chat / Explore turn traces (mirrors server chat.turn). */

import type { ChatResponse } from "@/lib/api";
import type { ChartBarMode } from "@/lib/data-source";
import type { UiSlice } from "@/lib/scope";

const STORAGE_KEY = "supplymate.chatTurnLog";
const MAX_STORED = 40;

export type ClientTurnTrace = {
  event: "ui.chat.turn";
  ts: string;
  message: string;
  serverTrace: Record<string, unknown> | null;
  chartMode: ChartBarMode;
  slice: {
    cats: string[];
    health: string[];
    coverage: string | null;
    suppliers: string[];
    nameTokens: string[];
    outOfStockOnly: boolean;
    subcategories: string[];
  };
  answerPreview: string;
};

function sliceSnapshot(slice: UiSlice) {
  return {
    cats: [...slice.cats],
    health: [...slice.health],
    coverage: slice.coverage,
    suppliers: [...slice.suppliers],
    nameTokens: [...slice.nameTokens],
    outOfStockOnly: slice.outOfStockOnly,
    subcategories: [...slice.subcategories],
  };
}

export function buildClientTurnTrace(opts: {
  message: string;
  res: ChatResponse;
  slice: UiSlice;
  chartMode: ChartBarMode;
}): ClientTurnTrace {
  return {
    event: "ui.chat.turn",
    ts: new Date().toISOString(),
    message: opts.message.slice(0, 240),
    serverTrace: (opts.res.trace as Record<string, unknown> | null | undefined) ?? null,
    chartMode: opts.chartMode,
    slice: sliceSnapshot(opts.slice),
    answerPreview: (opts.res.answer || "").slice(0, 280),
  };
}

export function emitClientTurnTrace(trace: ClientTurnTrace): void {
  // Always available in DevTools when diagnosing “el gráfico no cambió”.
  console.info("[SupplyMate turn]", trace);
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    const prev: ClientTurnTrace[] = raw ? (JSON.parse(raw) as ClientTurnTrace[]) : [];
    const next = [...prev, trace].slice(-MAX_STORED);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // private mode / quota — console is enough
  }
}

export function readClientTurnTraces(): ClientTurnTrace[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as ClientTurnTrace[]) : [];
  } catch {
    return [];
  }
}
