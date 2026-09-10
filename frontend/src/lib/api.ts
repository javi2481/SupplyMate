/** SupplyMate FastAPI client — real catalog / replenishment data. */

export const API_URL = (
  (import.meta.env["VITE_SUPPLYMATE_API_URL"] as string | undefined) ??
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

export type ApiHealthBucket = "stockout_risk" | "understock" | "overstock" | "healthy";

export type AnalyticalScopePayload = {
  categories?: string[];
  subcategories?: string[];
  coverage_buckets?: string[];
  health_buckets?: string[];
  suppliers?: string[];
  name_tokens?: string[];
  highlight_product_id?: string;
  out_of_stock_only?: boolean;
  horizon_days?: number;
};

export type PurchaseListItem = {
  product_id: string;
  barcode: string;
  product_name: string;
  supplier: string;
  category: string;
  subcategory: string;
  current_stock: number;
  reorder_point: number | null;
  below_reorder_point: boolean;
  average_daily_demand: number;
  days_of_supply: number | null;
  health_bucket: string;
  recommended_quantity: number;
  operational_priority: string;
  purchase_cost: number | null;
  estimated_purchase_value: number | null;
};

export type InventoryDashboard = {
  skus: number;
  stockout_risk: number;
  understock: number;
  overstock: number;
  healthy: number;
  avg_coverage: number | null;
  estimated_purchase_value: number | null;
  recommended_units?: number;
  purchase_skus?: number;
  out_of_stock?: number;
  by_category: { category: string; recommended_quantity: number; sku_count: number }[];
};

export type SuggestedFilter = {
  action: string;
  args: Record<string, string>;
  label: string;
};

export type ReplenishmentSlice = {
  scope: AnalyticalScopePayload;
  evidence: string;
  dashboard: InventoryDashboard;
  purchase_list: PurchaseListItem[];
  suggested_filters: SuggestedFilter[];
};

export type ReplenishmentCalculation = {
  product_id: string;
  average_daily_demand: number;
  demand_horizon: number;
  demand_lead_time: number;
  stock_target: number;
  current_stock: number;
  recommended_quantity: number;
  horizon_days: number;
  history_days: number;
  lead_time_days: number;
  safety_stock: number;
};

export type ReplenishmentRecommendation = {
  product_id: string;
  product_name: string;
  recommended_quantity: number;
  calculation: ReplenishmentCalculation;
  context: {
    product_name: string;
    current_stock: number;
    units_sold_30d: number;
    average_daily_demand: number;
  };
};

export type ChatResponse = {
  answer: string;
  mode: string;
  product_id: string;
  product_name: string;
  recommended_quantity: number;
  calculation: ReplenishmentCalculation | null;
  purchase_list: PurchaseListItem[];
  dashboard: InventoryDashboard | null;
  scope: AnalyticalScopePayload | null;
  horizon_days?: number;
};

/** Query params matching FastAPI `_scope_dependency` (+ limit). */
export type ScopeQuery = {
  category?: string[] | undefined;
  subcategory?: string[] | undefined;
  coverage_bucket?: string[] | undefined;
  health_bucket?: string[] | undefined;
  supplier?: string[] | undefined;
  name_token?: string[] | undefined;
  highlight_product_id?: string | undefined;
  out_of_stock?: boolean | undefined;
  limit?: number | undefined;
  horizon_days?: number | undefined;
};

export function toSearchParams(scope: ScopeQuery): URLSearchParams {
  const params = new URLSearchParams();
  for (const cat of scope.category ?? []) params.append("category", cat);
  for (const sub of scope.subcategory ?? []) params.append("subcategory", sub);
  for (const cov of scope.coverage_bucket ?? []) params.append("coverage_bucket", cov);
  for (const health of scope.health_bucket ?? []) params.append("health_bucket", health);
  for (const supplier of scope.supplier ?? []) params.append("supplier", supplier);
  for (const token of scope.name_token ?? []) params.append("name_token", token);
  if (scope.highlight_product_id) {
    params.set("highlight_product_id", scope.highlight_product_id);
  }
  if (scope.out_of_stock) {
    params.set("out_of_stock", "true");
  }
  if (scope.horizon_days != null && scope.horizon_days > 0) {
    params.set("horizon_days", String(scope.horizon_days));
  }
  params.set("limit", String(scope.limit ?? 50));
  return params;
}

export class HttpError extends Error {
  status: number;
  constructor(status: number, path: string, detail: string) {
    super(`${status} ${path}: ${detail.slice(0, 200)}`);
    this.name = "HttpError";
    this.status = status;
  }
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new HttpError(res.status, path, detail);
  }
  return res.json() as Promise<T>;
}

export function fetchSlice(scope: ScopeQuery = {}): Promise<ReplenishmentSlice> {
  const qs = toSearchParams(scope).toString();
  return getJson<ReplenishmentSlice>(`/replenishment/slice?${qs}`);
}

export function fetchReplenishment(productId: string): Promise<ReplenishmentRecommendation> {
  return getJson<ReplenishmentRecommendation>(
    `/products/${encodeURIComponent(productId)}/replenishment`,
  );
}

export function postChat(
  message: string,
  scope?: AnalyticalScopePayload | null,
): Promise<ChatResponse> {
  return getJson<ChatResponse>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, scope: scope ?? null }),
  });
}

export function purchaseListCsvUrl(scope: ScopeQuery = {}): string {
  const qs = toSearchParams({ ...scope, limit: scope.limit ?? 100 }).toString();
  return `${API_URL}/replenishment/purchase-list.csv?${qs}`;
}

export function scopeQueryToPayload(query: ScopeQuery): AnalyticalScopePayload {
  const payload: AnalyticalScopePayload = {};
  if (query.category?.length) payload.categories = query.category;
  if (query.subcategory?.length) payload.subcategories = query.subcategory;
  if (query.coverage_bucket?.length) payload.coverage_buckets = query.coverage_bucket;
  if (query.health_bucket?.length) payload.health_buckets = query.health_bucket;
  if (query.supplier?.length) payload.suppliers = query.supplier;
  if (query.name_token?.length) payload.name_tokens = query.name_token;
  if (query.highlight_product_id) payload.highlight_product_id = query.highlight_product_id;
  if (query.out_of_stock) payload.out_of_stock_only = true;
  if (query.horizon_days != null && query.horizon_days > 0) {
    payload.horizon_days = query.horizon_days;
  }
  return payload;
}
