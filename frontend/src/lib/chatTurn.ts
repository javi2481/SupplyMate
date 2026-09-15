/** Chat turn helpers: keep pregunta → pensando → respuesta even if thread state resets. */

import type { InventoryDashboard, PurchaseListItem } from "@/lib/api";
import type { AppliedChatScope } from "@/lib/applyChatScope";
import { emptyCart, hydrateCart, type CartLine } from "@/lib/cart";
import { EMPTY_SLICE, type UiSlice } from "@/lib/scope";

export type { CartLine } from "@/lib/cart";

export type ChatMsg = {
  id: number;
  role: "user" | "assistant" | "thinking";
  text: string;
};

export type PendingTurn = {
  threadId: string;
  userText: string;
  userMsgId: number;
  thinkingId: number;
};

/** Recorte + panel that belong to one conversation, not to the whole app. */
export type ThreadPanel = {
  slice: UiSlice;
  history: UiSlice[];
  horizonDays: number;
  chatBoard: { dashboard: InventoryDashboard; purchaseList: PurchaseListItem[] } | null;
  /** True when Explore is showing a payload-replaced surface (sales/root dashboard, not a purchase recorte). */
  replacedSurface: boolean;
  /** Recorte sent as `previous` on the next /chat. Survives a local panel replacement. */
  conversationSlice: UiSlice;
  /** Accumulated purchase lines for this thread (independent of Explore focus). */
  cart: CartLine[];
};

export type ThreadState = {
  id: string;
  title: string;
  messages: ChatMsg[];
  slice?: UiSlice;
  history?: UiSlice[];
  horizonDays?: number;
  chatBoard?: ThreadPanel["chatBoard"];
  replacedSurface?: boolean;
  conversationSlice?: UiSlice;
  cart?: CartLine[];
};

export function emptyPanel(horizonDays: number): ThreadPanel {
  return {
    slice: EMPTY_SLICE,
    history: [],
    horizonDays,
    chatBoard: null,
    replacedSurface: false,
    conversationSlice: EMPTY_SLICE,
    cart: emptyCart(),
  };
}

export function panelOf(thread: ThreadState | undefined, fallback: ThreadPanel): ThreadPanel {
  if (!thread) return fallback;
  const slice = thread.slice ?? fallback.slice;
  return {
    slice,
    history: thread.history ?? fallback.history,
    horizonDays: thread.horizonDays ?? fallback.horizonDays,
    chatBoard: thread.chatBoard !== undefined ? thread.chatBoard : fallback.chatBoard,
    replacedSurface: thread.replacedSurface ?? fallback.replacedSurface,
    conversationSlice: thread.conversationSlice ?? slice,
    cart: hydrateCart(thread.cart ?? fallback.cart),
  };
}

export function withPanel(thread: ThreadState, panel: ThreadPanel): ThreadState {
  return { ...thread, ...panel };
}

/** Chat updates focus only; cart changes via explicit Agregar al pedido. */
export function panelAfterChat(
  current: ThreadPanel,
  applied: AppliedChatScope,
  horizonDays: number,
): ThreadPanel {
  const keepBoard = applied.chatBoard === "keep";
  return {
    slice: applied.slice,
    history: applied.pushHistory ? [...current.history, current.slice] : current.history,
    horizonDays,
    chatBoard: applied.chatBoard === "keep" ? current.chatBoard : applied.chatBoard,
    replacedSurface: keepBoard ? current.replacedSurface : applied.replacedSurface,
    conversationSlice: applied.conversationSlice,
    cart: current.cart,
  };
}

/** Persist the live panel on the outgoing thread, then restore the target thread's panel. */
export function switchThread(
  threads: ThreadState[],
  fromId: string,
  toId: string,
  live: ThreadPanel,
  fallback: ThreadPanel,
): { threads: ThreadState[]; panel: ThreadPanel } {
  if (fromId === toId) {
    return { threads, panel: live };
  }
  const nextThreads = threads.map((thread) =>
    thread.id === fromId ? withPanel(thread, live) : thread,
  );
  const target = nextThreads.find((thread) => thread.id === toId);
  return { threads: nextThreads, panel: panelOf(target, fallback) };
}

export function isSameTurn(current: PendingTurn | null, pending: PendingTurn): boolean {
  return current != null && current.thinkingId === pending.thinkingId;
}

function neighborAfterDelete(threads: ThreadState[], removeId: string): ThreadState | undefined {
  const idx = threads.findIndex((thread) => thread.id === removeId);
  const remaining = threads.filter((thread) => thread.id !== removeId);
  if (remaining.length === 0) return undefined;
  if (idx < 0) return remaining[0];
  return remaining[Math.min(idx, remaining.length - 1)];
}

/**
 * Remove a conversation and its recorte.
 * Deleting the last thread yields a blank one (never an empty list).
 * Deleting the active thread restores the neighbor's panel — not the deleted recorte.
 */
export function deleteThread(
  threads: ThreadState[],
  activeId: string,
  removeId: string,
  live: ThreadPanel,
  fallback: ThreadPanel,
  newBlank: () => ThreadState,
): { threads: ThreadState[]; activeId: string; panel: ThreadPanel; deletedActive: boolean } {
  if (!threads.some((thread) => thread.id === removeId)) {
    return { threads, activeId, panel: live, deletedActive: false };
  }

  const remaining = threads.filter((thread) => thread.id !== removeId);
  if (remaining.length === 0) {
    const blank = newBlank();
    return {
      threads: [blank],
      activeId: blank.id,
      panel: fallback,
      deletedActive: true,
    };
  }

  if (removeId !== activeId) {
    return { threads: remaining, activeId, panel: live, deletedActive: false };
  }

  const next = neighborAfterDelete(threads, removeId) ?? remaining[0];
  if (!next) {
    const blank = newBlank();
    return {
      threads: [blank],
      activeId: blank.id,
      panel: fallback,
      deletedActive: true,
    };
  }
  return {
    threads: remaining,
    activeId: next.id,
    panel: panelOf(next, fallback),
    deletedActive: true,
  };
}

const STORAGE_KEY = "supplymate.chat.threads.v1";

let msgSeq = 0;
export function nextMsgId(): number {
  msgSeq += 1;
  return Date.now() * 1000 + msgSeq;
}

/** Replace thinking with assistant; re-insert user if the thread lost it (HMR/remount). */
export function completeTurn(
  messages: ChatMsg[],
  pending: PendingTurn,
  assistantText: string,
): ChatMsg[] {
  const withoutThinking = messages.filter((m) => m.id !== pending.thinkingId);
  const hasUser = withoutThinking.some(
    (m) => m.id === pending.userMsgId || (m.role === "user" && m.text === pending.userText),
  );
  const base = hasUser
    ? withoutThinking
    : [
        ...withoutThinking,
        { id: pending.userMsgId, role: "user" as const, text: pending.userText },
      ];
  return [
    ...base,
    {
      id: pending.thinkingId,
      role: "assistant" as const,
      text: assistantText,
    },
  ];
}

/** Drop in-flight thinking bubbles so a reload never leaves "Pensando…" forever. */
export function stripThinkingMessages(messages: ChatMsg[]): ChatMsg[] {
  return messages.filter((message) => message.role !== "thinking");
}

function threadsWithoutThinking(threads: ThreadState[]): ThreadState[] {
  return threads.map((thread) => ({
    ...thread,
    messages: stripThinkingMessages(thread.messages),
  }));
}

export function loadThreads(seed: ThreadState[]): { threads: ThreadState[]; activeId: string } {
  if (typeof sessionStorage === "undefined") {
    return { threads: seed, activeId: seed[0]?.id ?? "t1" };
  }
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return { threads: seed, activeId: seed[0]?.id ?? "t1" };
    const parsed = JSON.parse(raw) as { threads?: ThreadState[]; activeId?: string };
    if (!Array.isArray(parsed.threads) || parsed.threads.length === 0) {
      return { threads: seed, activeId: seed[0]?.id ?? "t1" };
    }
    const threads = threadsWithoutThinking(parsed.threads);
    const first = threads[0];
    const activeId =
      parsed.activeId && threads.some((t) => t.id === parsed.activeId)
        ? parsed.activeId
        : (first?.id ?? seed[0]?.id ?? "t1");
    return { threads, activeId };
  } catch {
    return { threads: seed, activeId: seed[0]?.id ?? "t1" };
  }
}

export function saveThreads(threads: ThreadState[], activeId: string): void {
  if (typeof sessionStorage === "undefined") return;
  try {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ threads: threadsWithoutThinking(threads), activeId }),
    );
  } catch {
    /* ignore quota */
  }
}
