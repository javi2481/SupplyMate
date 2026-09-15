import { describe, expect, it } from "vitest";
import {
  completeTurn,
  emptyPanel,
  loadThreads,
  panelAfterChat,
  panelOf,
  saveThreads,
  stripThinkingMessages,
  switchThread,
  deleteThread,
  isSameTurn,
  withPanel,
  type ChatMsg,
  type PendingTurn,
  type ThreadPanel,
  type ThreadState,
} from "@/lib/chatTurn";
import type { AppliedChatScope } from "@/lib/applyChatScope";
import type { InventoryDashboard } from "@/lib/api";
import { EMPTY_SLICE } from "@/lib/scope";
import { emptyCart, hydrateCartLine, type CartLine } from "@/lib/cart";

const pending: PendingTurn = {
  threadId: "t1",
  userText: "que tengo que comprar para los proximos 45 dias",
  userMsgId: 100,
  thinkingId: 101,
};

const fallback = emptyPanel(7);

function panel(partial: Partial<ThreadPanel>): ThreadPanel {
  return { ...fallback, ...partial };
}

describe("isSameTurn", () => {
  it("does not treat a cancelled turn as current", () => {
    expect(isSameTurn(null, pending)).toBe(false);
    expect(isSameTurn({ ...pending, thinkingId: 999 }, pending)).toBe(false);
    expect(isSameTurn(pending, pending)).toBe(true);
  });
});

describe("completeTurn", () => {
  it("replaces thinking with assistant and keeps user", () => {
    const messages: ChatMsg[] = [
      { id: 1, role: "assistant", text: "hola" },
      { id: 100, role: "user", text: pending.userText },
      { id: 101, role: "thinking", text: "Pensando…" },
    ];
    const next = completeTurn(messages, pending, "lista ok");
    expect(next.map((m) => m.role)).toEqual(["assistant", "user", "assistant"]);
    expect(next[1]?.text).toBe(pending.userText);
    expect(next[2]?.text).toBe("lista ok");
  });

  it("reinserts user when thread was reset to seed", () => {
    const seedOnly: ChatMsg[] = [{ id: 1, role: "assistant", text: "Listo para revisar…" }];
    const next = completeTurn(seedOnly, pending, "respuesta 45d");
    expect(next.some((m) => m.role === "user" && m.text === pending.userText)).toBe(true);
    expect(next.at(-1)?.role).toBe("assistant");
    expect(next.at(-1)?.text).toBe("respuesta 45d");
  });
});

describe("stripThinkingMessages / loadThreads", () => {
  it("drops thinking bubbles from a message list", () => {
    const messages: ChatMsg[] = [
      { id: 1, role: "assistant", text: "hola" },
      { id: 2, role: "user", text: "comprar" },
      { id: 3, role: "thinking", text: "Pensando…" },
    ];
    expect(stripThinkingMessages(messages).map((m) => m.role)).toEqual(["assistant", "user"]);
  });

  it("loadThreads strips thinking so reload never shows Pensando…", () => {
    const seed: ThreadState[] = [
      { id: "t1", title: "seed", messages: [{ id: 1, role: "assistant", text: "hola" }] },
    ];
    sessionStorage.setItem(
      "supplymate.chat.threads.v1",
      JSON.stringify({
        activeId: "t1",
        threads: [
          {
            id: "t1",
            title: "hung",
            messages: [
              { id: 1, role: "user", text: "¿Qué productos debería comprar?" },
              { id: 2, role: "thinking", text: "Pensando…" },
            ],
          },
        ],
      }),
    );
    const { threads } = loadThreads(seed);
    expect(threads[0]?.messages.every((m) => m.role !== "thinking")).toBe(true);
    expect(threads[0]?.messages.map((m) => m.text)).toEqual(["¿Qué productos debería comprar?"]);
  });

  it("saveThreads persists without thinking bubbles", () => {
    saveThreads(
      [
        {
          id: "t1",
          title: "x",
          messages: [
            { id: 1, role: "user", text: "hola" },
            { id: 2, role: "thinking", text: "Pensando…" },
          ],
        },
      ],
      "t1",
    );
    const raw = JSON.parse(sessionStorage.getItem("supplymate.chat.threads.v1") ?? "{}") as {
      threads: ThreadState[];
    };
    expect(raw.threads[0]?.messages.map((m) => m.role)).toEqual(["user"]);
  });
});

describe("switchThread", () => {
  const loreal = panel({
    slice: { ...EMPTY_SLICE, suppliers: ["LOREAL"] },
    horizonDays: 7,
  });
  const jabones90 = panel({
    slice: { ...EMPTY_SLICE, cats: ["Jabon de Tocador", "Shampoo"] },
    horizonDays: 90,
  });
  const threads: ThreadState[] = [
    { id: "a", title: "loreal", messages: [], ...loreal },
    { id: "b", title: "jabones 90d", messages: [], ...jabones90 },
  ];

  it("snapshots the live panel onto the outgoing thread and restores the target", () => {
    const live = panel({
      slice: { ...EMPTY_SLICE, cats: ["Jabon de Tocador"] },
      horizonDays: 90,
    });
    const result = switchThread(threads, "b", "a", live, fallback);
    expect(result.threads.find((t) => t.id === "b")?.horizonDays).toBe(90);
    expect(result.threads.find((t) => t.id === "b")?.slice?.cats).toEqual(["Jabon de Tocador"]);
    expect(result.panel.horizonDays).toBe(7);
    expect(result.panel.slice.suppliers).toEqual(["LOREAL"]);
  });

  it("uses empty fallback when the target thread has no saved recorte", () => {
    const bare: ThreadState[] = [
      { id: "a", title: "nuevo", messages: [] },
      { id: "b", title: "90d", messages: [], ...jabones90 },
    ];
    const result = switchThread(bare, "b", "a", jabones90, fallback);
    expect(result.panel).toEqual(fallback);
  });

  it("is a no-op when selecting the already active thread", () => {
    const result = switchThread(threads, "a", "a", loreal, fallback);
    expect(result.threads).toBe(threads);
    expect(result.panel).toBe(loreal);
  });
});

describe("panelOf", () => {
  it("fills missing recorte fields from the fallback", () => {
    expect(panelOf({ id: "t", title: "x", messages: [] }, fallback)).toEqual(fallback);
  });
});

describe("deleteThread", () => {
  const loreal = panel({
    slice: { ...EMPTY_SLICE, suppliers: ["LOREAL"] },
    horizonDays: 7,
  });
  const jabones90 = panel({
    slice: { ...EMPTY_SLICE, cats: ["Jabon de Tocador", "Shampoo"] },
    horizonDays: 90,
  });
  const threads: ThreadState[] = [
    { id: "a", title: "loreal", messages: [], ...loreal },
    { id: "b", title: "jabones 90d", messages: [], ...jabones90 },
    { id: "c", title: "pañales", messages: [] },
  ];
  const blank = (): ThreadState => ({ id: "blank", title: "Nueva conversación", messages: [] });

  it("drops an inactive thread without touching the live recorte", () => {
    const result = deleteThread(threads, "b", "a", jabones90, fallback, blank);
    expect(result.threads.map((t) => t.id)).toEqual(["b", "c"]);
    expect(result.activeId).toBe("b");
    expect(result.panel).toBe(jabones90);
    expect(result.deletedActive).toBe(false);
  });

  it("deleting the active thread restores the neighbor recorte, not the deleted one", () => {
    const result = deleteThread(threads, "a", "a", loreal, fallback, blank);
    expect(result.threads.map((t) => t.id)).toEqual(["b", "c"]);
    expect(result.activeId).toBe("b");
    expect(result.panel.horizonDays).toBe(90);
    expect(result.panel.slice.cats).toEqual(["Jabon de Tocador", "Shampoo"]);
    expect(result.deletedActive).toBe(true);
  });

  it("replaces the last thread with a blank chat and an empty panel", () => {
    const only: ThreadState[] = [{ id: "b", title: "90d", messages: [], ...jabones90 }];
    const result = deleteThread(only, "b", "b", jabones90, fallback, blank);
    expect(result.threads).toEqual([blank()]);
    expect(result.activeId).toBe("blank");
    expect(result.panel).toEqual(fallback);
    expect(result.deletedActive).toBe(true);
  });
});

describe("thread cart persistence", () => {
  const panales: CartLine[] = [
    hydrateCartLine({ product_id: "P1", product_name: "Pañal", recommended_quantity: 10, category: "Pañales" }),
  ];
  const shampoo: CartLine[] = [
    hydrateCartLine({ product_id: "S1", product_name: "Shampoo", recommended_quantity: 4, category: "Shampoo" }),
  ];

  it("emptyPanel and missing thread cart start empty", () => {
    expect(emptyPanel(7).cart).toEqual(emptyCart());
    expect(panelOf({ id: "t", title: "x", messages: [] }, fallback).cart).toEqual([]);
  });

  it("panelOf hydrates legacy recommended_quantity cart lines", () => {
    const legacy = panelOf(
      {
        id: "t",
        title: "x",
        messages: [],
        cart: [{ product_id: "A", product_name: "A", recommended_quantity: 12 } as unknown as CartLine],
      },
      fallback,
    );
    expect(legacy.cart[0]?.suggested_quantity).toBe(12);
    expect(legacy.cart[0]?.order_quantity).toBe(12);
  });

  it("switchThread snapshots live cart and restores the target thread cart", () => {
    const withPanales = panel({ cart: panales });
    const withShampoo = panel({ cart: shampoo });
    const threads: ThreadState[] = [
      { id: "a", title: "pañales", messages: [], ...withPanales },
      { id: "b", title: "shampoo", messages: [], ...withShampoo },
    ];
    const result = switchThread(threads, "b", "a", withShampoo, fallback);
    expect(result.threads.find((t) => t.id === "b")?.cart).toEqual(shampoo);
    expect(result.panel.cart).toEqual(panales);
  });

  it("deleting the last thread yields an empty cart", () => {
    const only: ThreadState[] = [{ id: "b", title: "90d", messages: [], ...panel({ cart: panales }) }];
    const result = deleteThread(only, "b", "b", panel({ cart: panales }), fallback, () => ({
      id: "blank",
      title: "Nueva conversación",
      messages: [],
    }));
    expect(result.panel.cart).toEqual([]);
  });

  it("panelAfterChat keeps the cart without auto-adding focus purchase lines", () => {
    const live = panel({ cart: panales });
    const applied: AppliedChatScope = {
      slice: EMPTY_SLICE,
      openProductId: null,
      chatBoard: {
        dashboard: {
          skus: 1,
          stockout_risk: 0,
          understock: 0,
          overstock: 0,
          healthy: 1,
          avg_coverage: 1,
          estimated_purchase_value: 0,
          by_category: [],
        },
        purchaseList: [
          {
            product_id: "NEW",
            product_name: "New",
            barcode: "NEW",
            supplier: "S",
            category: "X",
            subcategory: "",
            current_stock: 0,
            reorder_point: null,
            below_reorder_point: true,
            average_daily_demand: 1,
            days_of_supply: 0,
            health_bucket: "stockout_risk",
            recommended_quantity: 9,
            operational_priority: "high",
            purchase_cost: null,
            estimated_purchase_value: 9,
          },
        ],
      },
      replacedSurface: true,
      pushHistory: false,
      conversationSlice: live.slice,
    };
    expect(panelAfterChat(live, applied, 7).cart).toEqual(panales);
  });

  it("withPanel persists cart on the thread snapshot", () => {
    const thread: ThreadState = { id: "a", title: "x", messages: [] };
    const next = withPanel(thread, panel({ cart: panales }));
    expect(next.cart).toEqual(panales);
  });
});

describe("panelAfterChat", () => {
  const snap: InventoryDashboard = {
    skus: 8,
    stockout_risk: 1,
    understock: 0,
    overstock: 0,
    healthy: 7,
    avg_coverage: 12,
    estimated_purchase_value: 50,
    recommended_units: 17753,
    purchase_skus: 3,
    by_category: [],
  };
  const live = panel({
    slice: { ...EMPTY_SLICE, cats: ["GrupoA"], health: ["riesgo_quiebre"] },
    history: [EMPTY_SLICE],
    conversationSlice: { ...EMPTY_SLICE, cats: ["GrupoA"], health: ["riesgo_quiebre"] },
  });

  it("replaces chatBoard from applyChatScope and does not push a sales reset into history", () => {
    const applied: AppliedChatScope = {
      slice: EMPTY_SLICE,
      openProductId: null,
      chatBoard: { dashboard: snap, purchaseList: [] },
      replacedSurface: true,
      pushHistory: false,
      conversationSlice: live.slice,
    };
    const next = panelAfterChat(live, applied, 7);
    expect(next.slice).toEqual(EMPTY_SLICE);
    expect(next.history).toEqual(live.history);
    expect(next.chatBoard).toEqual({ dashboard: snap, purchaseList: [] });
    expect(next.replacedSurface).toBe(true);
    expect(next.conversationSlice.cats).toEqual(["GrupoA"]);
    expect(next.conversationSlice.health).toEqual(["riesgo_quiebre"]);
  });

  it("keeps the current chatBoard when applyChatScope says keep", () => {
    const withBoard = panel({ ...live, chatBoard: { dashboard: snap, purchaseList: [] }, replacedSurface: true });
    const applied: AppliedChatScope = {
      slice: withBoard.slice,
      openProductId: null,
      chatBoard: "keep",
      replacedSurface: false,
      pushHistory: false,
      conversationSlice: withBoard.conversationSlice,
    };
    const next = panelAfterChat(withBoard, applied, 7);
    expect(next.chatBoard).toEqual(withBoard.chatBoard);
    expect(next.replacedSurface).toBe(true);
    expect(next.slice).toEqual(withBoard.slice);
  });

  it("pushes history and records the mapped recorte when a scope owns the panel", () => {
    const mapped = { ...EMPTY_SLICE, cats: ["GrupoB"] };
    const applied: AppliedChatScope = {
      slice: mapped,
      openProductId: null,
      chatBoard: { dashboard: snap, purchaseList: [] },
      replacedSurface: false,
      pushHistory: true,
      conversationSlice: mapped,
    };
    const next = panelAfterChat(live, applied, 15);
    expect(next.horizonDays).toBe(15);
    expect(next.slice.cats).toEqual(["GrupoB"]);
    expect(next.history).toEqual([...live.history, live.slice]);
    expect(next.replacedSurface).toBe(false);
    expect(next.conversationSlice).toEqual(mapped);
  });
});
