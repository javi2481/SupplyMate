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
  by_category: { category: string; recommended_quantity: number; sku_count: number }[];
};

export type ReplenishmentSlice = {
  scope: AnalyticalScopePayload;
  evidence: string;
  dashboard: InventoryDashboard;
  purchase_list: PurchaseListItem[];
  suggested_filters: { action: string; args: Record<string, string>; label: string }[];
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
};

export type ScopeQuery = {
  category?: string[] | undefined;
  health_bucket?: string[] | undefined;
  supplier?: string[] | undefined;
  limit?: number | undefined;
};

function toSearchParams(scope: ScopeQuery): URLSearchParams {
  const params = new URLSearchParams();
  for (const cat of scope.category ?? []) params.append("category", cat);
  for (const health of scope.health_bucket ?? []) params.append("health_bucket", health);
  for (const supplier of scope.supplier ?? []) params.append("supplier", supplier);
  params.set("limit", String(scope.limit ?? 50));
  return params;
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${path}: ${detail.slice(0, 200)}`);
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
