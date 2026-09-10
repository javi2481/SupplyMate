/** Apply ChatResponse onto UiSlice. Python owns the recorte; the UI does not parse text. */

import type { ChatResponse } from "@/lib/api";
import { HttpError } from "@/lib/api";
import { EMPTY_SLICE, scopePayloadToUiSlice, type UiSlice } from "@/lib/scope";

export const COPY_CATALOG_LOAD_FAILED = "No pude cargar el catálogo. Intentá de nuevo en un momento.";

export function chatFailureMessage(query: string, error: unknown): string {
  if (error instanceof HttpError && error.status === 404) {
    return `No encontré «${query}» en el catálogo.`;
  }
  return COPY_CATALOG_LOAD_FAILED;
}

export function applyChatScope(
  current: UiSlice,
  res: ChatResponse,
): { slice: UiSlice; openProductId: string | null } {
  const fromFields = res.product_id?.trim() || res.scope?.highlight_product_id?.trim() || "";
  if (res.scope == null) {
    return { slice: current, openProductId: fromFields || null };
  }
  const mapped = scopePayloadToUiSlice(res.scope, { ...EMPTY_SLICE, buyOnly: current.buyOnly });
  return {
    slice: { ...mapped, buyOnly: res.mode === "list" ? true : mapped.buyOnly },
    openProductId: fromFields || mapped.highlightProductId || null,
  };
}
