import { useQuery } from "@tanstack/react-query";
import { fetchSlice, type InventoryDashboard, type PurchaseListItem, type ScopeQuery } from "@/lib/api";
import { rowFromPurchaseItem, type SkuListRow } from "@/lib/adapter";
import { preferLiveApi } from "@/lib/data-source";

export type SliceQueryResult = {
  /** True when live FastAPI data is available. */
  online: boolean;
  /** True when we should render the demo catalog. */
  useMock: boolean;
  loading: boolean;
  error: string | null;
  rows: SkuListRow[];
  dashboard: InventoryDashboard | null;
  purchaseList: PurchaseListItem[];
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

  const useMock = !enabled || (query.isError && !query.data);
  const purchaseList = query.data?.purchase_list ?? [];

  return {
    online: enabled && query.isSuccess,
    useMock,
    loading: enabled && (query.isLoading || query.isFetching),
    error: query.isError
      ? query.error instanceof Error
        ? query.error.message
        : String(query.error)
      : null,
    rows: useMock ? [] : purchaseList.map(rowFromPurchaseItem),
    dashboard: useMock ? null : (query.data?.dashboard ?? null),
    purchaseList: useMock ? [] : purchaseList,
    refetch: () => {
      void query.refetch();
    },
  };
}
