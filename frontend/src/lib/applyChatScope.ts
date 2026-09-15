/** Apply ChatResponse onto UiSlice. Python owns the recorte; the UI does not parse text. */

import type { ChatResponse, InventoryDashboard, PurchaseListItem } from "@/lib/api";
import { HttpError } from "@/lib/api";
import { EMPTY_SLICE, scopePayloadToUiSlice, type UiSlice } from "@/lib/scope";

export const COPY_CATALOG_LOAD_FAILED = "No pude cargar el catálogo. Intentá de nuevo en un momento.";
export const COPY_ASSISTANT_UNAVAILABLE = "El asistente no está disponible. Intentá de nuevo en un momento.";
export const COPY_CHAT_TIMEOUT = "La consulta tardó demasiado. Intentá de nuevo en un momento.";

const PRODUCT_NOT_FOUND_RE = /Product not found:\s*([^"}\n]+)/i;

export type ChatBoardSnapshot = {
  dashboard: InventoryDashboard;
  purchaseList: PurchaseListItem[];
};

export type AppliedChatScope = {
  slice: UiSlice;
  openProductId: string | null;
  chatBoard: ChatBoardSnapshot | null | "keep";
  replacedSurface: boolean;
  pushHistory: boolean;
  conversationSlice: UiSlice;
};

function isAbortError(error: unknown): boolean {
  if (error instanceof DOMException && (error.name === "TimeoutError" || error.name === "AbortError")) {
    return true;
  }
  if (error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError")) {
    return true;
  }
  return false;
}

export function chatFailureMessage(query: string, error: unknown): string {
  if (isAbortError(error)) {
    return COPY_CHAT_TIMEOUT;
  }
  if (error instanceof HttpError) {
    if (error.status === 404) {
      const fromDetail = PRODUCT_NOT_FOUND_RE.exec(error.message)?.[1]?.trim();
      const token = fromDetail || query.trim() || "ese producto";
      return `No encontré «${token}» en el catálogo.`;
    }
    if (error.status >= 500) {
      return COPY_ASSISTANT_UNAVAILABLE;
    }
  }
  return COPY_CATALOG_LOAD_FAILED;
}

function isRootScope(scope: ChatResponse["scope"]): boolean {
  if (scope == null) return true;
  return !(
    (scope.categories?.length ?? 0) ||
    (scope.subcategories?.length ?? 0) ||
    (scope.coverage_buckets?.length ?? 0) ||
    (scope.health_buckets?.length ?? 0) ||
    (scope.suppliers?.length ?? 0) ||
    (scope.name_tokens?.length ?? 0) ||
    Boolean(scope.out_of_stock_only) ||
    Boolean(scope.highlight_product_id?.trim())
  );
}

function boardFrom(res: ChatResponse): ChatBoardSnapshot | null {
  if (!res.dashboard) return null;
  return { dashboard: res.dashboard, purchaseList: res.purchase_list ?? [] };
}

function hasPurchaseList(res: ChatResponse): boolean {
  return (res.purchase_list?.length ?? 0) > 0;
}

/** Payload-shape rule: a dashboard with no recorte (null or empty root, no purchase list) replaces the panel. */
export function isReplacedChatSurface(res: ChatResponse): boolean {
  if (!res.dashboard) return false;
  if (res.scope == null) return true;
  return isRootScope(res.scope) && !hasPurchaseList(res);
}

export function applyChatScope(
  current: UiSlice,
  res: ChatResponse,
  conversationSlice: UiSlice = current,
): AppliedChatScope {
  const fromFields = res.product_id?.trim() || res.scope?.highlight_product_id?.trim() || "";
  const board = boardFrom(res);

  if (res.scope == null && !res.dashboard) {
    return {
      slice: current,
      openProductId: fromFields || null,
      chatBoard: "keep",
      replacedSurface: false,
      pushHistory: false,
      conversationSlice,
    };
  }

  if (isReplacedChatSurface(res)) {
    return {
      slice: EMPTY_SLICE,
      openProductId: fromFields || null,
      chatBoard: board,
      replacedSurface: true,
      pushHistory: false,
      conversationSlice,
    };
  }

  const mapped = scopePayloadToUiSlice(res.scope, { ...EMPTY_SLICE, buyOnly: current.buyOnly });
  const slice = { ...mapped, buyOnly: res.mode === "list" ? true : mapped.buyOnly };
  return {
    slice,
    openProductId: fromFields || mapped.highlightProductId || null,
    chatBoard: board,
    replacedSurface: false,
    pushHistory: true,
    conversationSlice: slice,
  };
}
