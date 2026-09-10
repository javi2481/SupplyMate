import { useQuery } from "@tanstack/react-query";
import { fetchSlice, type InventoryDashboard, type PurchaseListItem, type ScopeQuery, type SuggestedFilter } from "@/lib/api";
import { rowFromPurchaseItem, type SkuListRow } from "@/lib/adapter";
import { preferLiveApi } from "@/lib/data-source";

export type SliceQueryResult = {
  /** True when live FastAPI data is available. */
  online: boolean;
  loading: boolean;
  error: string | null;
  rows: SkuListRow[];
  dashboard: InventoryDashboard | null;
  purchaseList: PurchaseListItem[];
  suggestedFilters: SuggestedFilter[];
  refetch: () => void;
};

export function useSlice(scopeQuery: ScopeQuery, listLimit = 50): SliceQueryResult {
  const enabled = preferLiveApi();
  const query = useQuery({
    queryKey: ["slice", scopeQuery, listLimit],
    queryFn: () => fetchSlice({ ...scopeQuery, limit: scopeQuery.limit ?? listLimit }),
    enabled,
    retry: 1,
    staleTime: 30_000,
  });

  const failed = !enabled || (query.isError && !query.data);
  const purchaseList = query.data?.purchase_list ?? [];

  return {
    online: enabled && query.isSuccess,
    loading: enabled && (query.isLoading || query.isFetching),
    error: query.isError
      ? query.error instanceof Error
        ? query.error.message
        : String(query.error)
      : enabled
        ? null
        : "unavailable",
    rows: failed ? [] : purchaseList.map(rowFromPurchaseItem),
    dashboard: failed ? null : (query.data?.dashboard ?? null),
    purchaseList: failed ? [] : purchaseList,
    suggestedFilters: failed ? [] : (query.data?.suggested_filters ?? []),
    refetch: () => {
      void query.refetch();
    },
  };
}
