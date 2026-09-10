import { describe, expect, it } from "vitest";
import { completeTurn, type ChatMsg, type PendingTurn } from "@/lib/chatTurn";

const pending: PendingTurn = {
  threadId: "t1",
  userText: "que tengo que comprar para los proximos 45 dias",
  userMsgId: 100,
  thinkingId: 101,
};

describe("completeTurn", () => {
  it("replaces thinking with assistant and keeps user", () => {
    const messages: ChatMsg[] = [
      { id: 1, role: "assistant", text: "hola" },
      { id: 100, role: "user", text: pending.userText },
      { id: 101, role: "thinking", text: "Pensando…" },
    ];
    const next = completeTurn(messages, pending, "lista ok");
    expect(next.map((m) => m.role)).toEqual(["assistant", "user", "assistant"]);
    expect(next[1].text).toBe(pending.userText);
    expect(next[2].text).toBe("lista ok");
  });

  it("reinserts user when thread was reset to seed", () => {
    const seedOnly: ChatMsg[] = [{ id: 1, role: "assistant", text: "Listo para revisar…" }];
    const next = completeTurn(seedOnly, pending, "respuesta 45d");
    expect(next.some((m) => m.role === "user" && m.text === pending.userText)).toBe(true);
    expect(next.at(-1)?.role).toBe("assistant");
    expect(next.at(-1)?.text).toBe("respuesta 45d");
  });
});
