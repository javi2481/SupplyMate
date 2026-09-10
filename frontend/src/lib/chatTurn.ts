/** Chat turn helpers: keep pregunta → pensando → respuesta even if thread state resets. */

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

export type ThreadState = {
  id: string;
  title: string;
  messages: ChatMsg[];
};

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
    const activeId =
      parsed.activeId && parsed.threads.some((t) => t.id === parsed.activeId)
        ? parsed.activeId
        : parsed.threads[0].id;
    return { threads: parsed.threads, activeId };
  } catch {
    return { threads: seed, activeId: seed[0]?.id ?? "t1" };
  }
}

export function saveThreads(threads: ThreadState[], activeId: string): void {
  if (typeof sessionStorage === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ threads, activeId }));
  } catch {
    /* ignore quota */
  }
}
