import { useCallback, useState } from "react";
import { EMPTY_SLICE, type UiSlice } from "@/lib/scope";

export function useScope(initial: UiSlice = EMPTY_SLICE) {
  const [slice, setSlice] = useState<UiSlice>(initial);
  const [history, setHistory] = useState<UiSlice[]>([]);

  const pushSlice = useCallback((next: UiSlice | ((previous: UiSlice) => UiSlice)) => {
    setSlice((previous) => {
      const value = typeof next === "function" ? next(previous) : next;
      setHistory((stack) => [...stack, previous]);
      return value;
    });
  }, []);

  const goBack = useCallback(() => {
    setHistory((stack) => {
      if (stack.length === 0) return stack;
      setSlice(stack[stack.length - 1] ?? EMPTY_SLICE);
      return stack.slice(0, -1);
    });
  }, []);

  const clearSlice = useCallback(() => {
    pushSlice(EMPTY_SLICE);
  }, [pushSlice]);

  return { slice, setSlice, history, pushSlice, goBack, clearSlice };
}
