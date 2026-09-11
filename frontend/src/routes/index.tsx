import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowLeft,
  Box,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Eraser,
  Menu,
  MessageSquareText,
  PackageCheck,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  Send,
  ShoppingCart,
  Loader2,
  SlidersHorizontal,
  Timer,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PurchaseOrder } from "@/components/PurchaseOrder";
import { SkuDrawer } from "@/components/SkuDrawer";
import { SkuTable } from "@/components/SkuTable";
import { useScope } from "@/hooks/use-scope";
import { useSlice } from "@/hooks/use-slice";
import {
  fetchReplenishment,
  postChat,
  purchaseListCsvUrl,
  scopeQueryToPayload,
  type InventoryDashboard,
  type PurchaseListItem,
} from "@/lib/api";
import { factsFromRecommendation, rowFromPurchaseItem } from "@/lib/adapter";
import { applyChatScope, chatFailureMessage } from "@/lib/applyChatScope";
import { buildClientTurnTrace, emitClientTurnTrace } from "@/lib/turnLog";
import { applySuggestedFilter, type SuggestedChip } from "@/lib/applySuggestedFilter";
import { categoryColor } from "@/lib/chart-colors";
import {
  completeTurn,
  loadThreads,
  nextMsgId,
  saveThreads,
  type PendingTurn,
} from "@/lib/chatTurn";
import {
  COPY_CATEGORIES_LOAD_FAILED,
  categoryNamesForUi,
  chartBarMode,
  chartTickLabel,
  chartUnitsByCategory,
  csvExportLimit,
  dataSourceLabel,
  kpisFromDashboard,
} from "@/lib/data-source";
import { toggleBuyOnly, toggleHealthTag } from "@/lib/kpi-actions";
import { calcFromApiRow } from "@/lib/ops-row";
import { filterChipsCoveredByCharts } from "@/lib/nextStepChips";
import { COVERAGE_ORDER, sliceToScopeQuery, type UiSlice } from "@/lib/scope";
import { sliceLabels } from "@/lib/scope-label";
import {
  HEALTH_FILTERS,
  HEALTH_LABEL,
  HORIZON_DAYS,
  nf,
  type Calc,
  type HealthTag,
} from "@/lib/supplymate";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "SupplyMate · Operación de reposición" },
      {
        name: "description",
        content: "Panel operativo para decidir cuánto pedir en los próximos 7 días.",
      },
      { property: "og:title", content: "SupplyMate · Operación de reposición" },
      {
        property: "og:description",
        content: "Recomendaciones de compra, alertas de stock y órdenes en un solo panel.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

type Msg = { id: number; role: "user" | "assistant" | "thinking"; text: string };
type Thread = { id: string; title: string; messages: Msg[] };
type MobileView = "chat" | "explore" | "po";

const BUY_QUERY = "¿Qué productos debería comprar?";

const SEED: Thread[] = [
  {
    id: "t1",
    title: "Qué comprar esta semana",
    messages: [
      {
        id: 1,
        role: "assistant",
        text: `Listo para revisar la reposición del recorte. Elegí una consulta rápida para comenzar: las cantidades salen del motor de cálculo.`,
      },
    ],
  },
];

const healthIcon: Record<HealthTag, typeof AlertTriangle> = {
  riesgo_quiebre: AlertTriangle,
  sin_stock: CircleAlert,
  sobrestock: Box,
};

function applyClientFilters(rows: Calc[], slice: UiSlice): Calc[] {
  const onlyOutOfStock =
    slice.health.includes("sin_stock") && slice.health.every((tag) => tag === "sin_stock");
  return rows.filter((row) => {
    if (slice.buyOnly && row.recommended_quantity <= 0) return false;
    if (onlyOutOfStock && row.sku.stock !== 0) return false;
    return true;
  });
}

function Index() {
  const boot = useMemo(() => loadThreads(SEED), []);
  const [threads, setThreads] = useState<Thread[]>(boot.threads);
  const [activeId, setActiveId] = useState(boot.activeId);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"explore" | "po">("explore");
  const [mobileView, setMobileView] = useState<MobileView>("explore");
  const { slice, history, pushSlice, goBack, clearSlice } = useScope();
  const [open, setOpen] = useState<Calc | null>(null);
  const [frozen, setFrozen] = useState<UiSlice | null>(null);
  const [railCollapsed, setRailCollapsed] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [chatBusy, setChatBusy] = useState(false);
  const [horizonDays, setHorizonDays] = useState(HORIZON_DAYS);
  const pendingTurn = useRef<PendingTurn | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  /** Panel snapshot from last /chat so KPIs/chart match the answer even if scope queryKey is unchanged. */
  const [chatBoard, setChatBoard] = useState<{
    dashboard: InventoryDashboard;
    purchaseList: PurchaseListItem[];
  } | null>(null);

  useEffect(() => {
    saveThreads(threads, activeId);
  }, [threads, activeId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [threads, activeId, chatBusy]);

  const scopeQuery = useMemo(
    () => ({ ...sliceToScopeQuery(slice, 50), horizon_days: horizonDays }),
    [slice, horizonDays],
  );
  const api = useSlice(scopeQuery, 50);
  const online = api.online;
  const statusLabel = dataSourceLabel(online);
  const statusLive = online;

  const dash = chatBoard?.dashboard ?? api.dashboard;
  const boardRows = chatBoard
    ? chatBoard.purchaseList.map(rowFromPurchaseItem)
    : api.rows;
  const categoryNames = useMemo(() => categoryNamesForUi(dash), [dash]);

  const active = threads.find((thread) => thread.id === activeId) ?? threads[0];
  const rows = useMemo(
    () => applyClientFilters(boardRows.map(calcFromApiRow), slice),
    [boardRows, slice],
  );
  const labels = sliceLabels(slice, horizonDays);

  function toggleList<T>(list: T[], item: T): T[] {
    return list.includes(item) ? list.filter((value) => value !== item) : [...list, item];
  }

  /** User-driven recorte changes drop the chat snapshot so /slice owns the panel again. */
  function mutateSlice(next: UiSlice | ((previous: UiSlice) => UiSlice)) {
    setChatBoard(null);
    pushSlice(next);
  }

  function toggleHealth(tag: "riesgo_quiebre" | "sin_stock" | "sobrestock") {
    mutateSlice((previous) => toggleHealthTag(previous, tag));
  }

  const listUnits = rows.reduce((sum, row) => sum + row.recommended_quantity, 0);
  const listOutOfStock = rows.filter((row) => row.sku.stock === 0).length;
  const kpisDash = kpisFromDashboard(dash, listUnits, listOutOfStock);
  const kpis = [
    {
      label: "Productos",
      value: nf.format(
        slice.buyOnly
          ? (dash?.purchase_skus ?? rows.length)
          : (dash?.skus ?? rows.length),
      ),
      detail: slice.buyOnly ? "a reponer" : "en este recorte",
      icon: Box,
      active: slice.buyOnly,
      onClick: () => mutateSlice((previous) => toggleBuyOnly(previous)),
    },
    {
      label: "Riesgo de quiebre",
      value: nf.format(
        dash?.stockout_risk ?? rows.filter((row) => row.health.includes("riesgo_quiebre")).length,
      ),
      detail: "requieren atención",
      icon: AlertTriangle,
      active: slice.health.includes("riesgo_quiebre"),
      onClick: () => toggleHealth("riesgo_quiebre"),
    },
    {
      label: "Falta de stock",
      value: nf.format(kpisDash.out_of_stock),
      detail: "reposición urgente",
      icon: CircleAlert,
      active: slice.health.includes("sin_stock"),
      onClick: () => toggleHealth("sin_stock"),
    },
    {
      label: "Unidades a pedir",
      value: nf.format(kpisDash.units),
      detail: `para ${horizonDays} días`,
      icon: PackageCheck,
      active: slice.buyOnly,
      onClick: () => mutateSlice((previous) => toggleBuyOnly(previous)),
    },
  ];

  const purchaseForChart = chatBoard?.purchaseList ?? api.purchaseList;
  const chartHints = useMemo(
    () => ({
      health: slice.health,
      coverage: slice.coverage,
      suppliers: slice.suppliers,
      nameTokens: slice.nameTokens,
      outOfStockOnly: slice.outOfStockOnly,
      purchaseList: purchaseForChart,
    }),
    [
      slice.health,
      slice.coverage,
      slice.suppliers,
      slice.nameTokens,
      slice.outOfStockOnly,
      purchaseForChart,
    ],
  );
  const chartData = useMemo(
    () => chartUnitsByCategory(dash, chartHints),
    [dash, chartHints],
  );
  const chartMode = useMemo(() => chartBarMode(dash, chartHints), [dash, chartHints]);
  const chartKey = `${chartMode}:${chartData.map((b) => `${b.productId ?? b.category}:${b.units}`).join("|")}`;

  const nextStepChips = useMemo(
    () =>
      filterChipsCoveredByCharts((api.suggestedFilters ?? []).slice(0, 6), chartMode),
    [api.suggestedFilters, chartMode],
  );

  const poRows = useMemo(() => {
    const scope: UiSlice = { ...(frozen ?? slice), buyOnly: true };
    return applyClientFilters(api.rows.map(calcFromApiRow), scope);
  }, [frozen, slice, api.rows]);
  const units = dash?.recommended_units ?? poRows.reduce((sum, row) => sum + row.recommended_quantity, 0);
  const value = dash?.estimated_purchase_value ?? poRows.reduce((sum, row) => sum + row.estimated_purchase_value, 0);
  const poSkuCount = dash?.purchase_skus ?? poRows.length;

  async function send(text: string) {
    const query = text.trim();
    if (!query || chatBusy) return;
    setInput("");

    const userMsgId = nextMsgId();
    const thinkingId = nextMsgId();
    const pending: PendingTurn = {
      threadId: activeId,
      userText: query,
      userMsgId,
      thinkingId,
    };
    pendingTurn.current = pending;
    setThreads((previous) =>
      previous.map((thread) =>
        thread.id !== activeId
          ? thread
          : {
              ...thread,
              title: thread.messages.length === 0 ? query.slice(0, 34) : thread.title,
              messages: [
                ...thread.messages,
                { id: userMsgId, role: "user" as const, text: query },
                {
                  id: thinkingId,
                  role: "thinking" as const,
                  text: "Pensando…",
                },
              ],
            },
      ),
    );
    setMode("explore");
    setMobileView("chat");
    setChatBusy(true);
    try {
      const res = await postChat(
        query,
        scopeQueryToPayload({ ...sliceToScopeQuery(slice), horizon_days: horizonDays }),
      );
      const applied = applyChatScope(slice, res);
      const nextHorizon =
        typeof res.horizon_days === "number" && res.horizon_days > 0
          ? res.horizon_days
          : horizonDays;
      setHorizonDays(nextHorizon);
      if (res.dashboard) {
        setChatBoard({
          dashboard: res.dashboard,
          purchaseList: res.purchase_list ?? [],
        });
      }
      if (res.scope != null) pushSlice(applied.slice);
      const uiChartMode = chartBarMode(res.dashboard, {
        health: applied.slice.health,
        coverage: applied.slice.coverage,
        suppliers: applied.slice.suppliers,
        nameTokens: applied.slice.nameTokens,
        outOfStockOnly: applied.slice.outOfStockOnly,
        purchaseList: res.purchase_list ?? [],
      });
      emitClientTurnTrace(
        buildClientTurnTrace({
          message: query,
          res,
          slice: applied.slice,
          chartMode: uiChartMode,
        }),
      );
      setThreads((previous) =>
        previous.map((thread) =>
          thread.id !== pending.threadId
            ? thread
            : {
                ...thread,
                messages: completeTurn(
                  thread.messages,
                  pending,
                  res.answer || "Sin respuesta del catálogo.",
                ),
              },
        ),
      );
      pendingTurn.current = null;
      setMobileView("chat");
      window.setTimeout(() => setMobileView("explore"), 1200);
      if (applied.openProductId) {
        const fromRes = res.purchase_list.find((item) => item.product_id === applied.openProductId);
        const row = fromRes
          ? calcFromApiRow(rowFromPurchaseItem(fromRes))
          : findRowForProduct(applied.openProductId);
        if (row) void openDetail(row);
      }
    } catch (error) {
      const pendingErr = pendingTurn.current ?? pending;
      setThreads((previous) =>
        previous.map((thread) =>
          thread.id !== pendingErr.threadId
            ? thread
            : {
                ...thread,
                messages: completeTurn(
                  thread.messages,
                  pendingErr,
                  chatFailureMessage(query, error),
                ),
              },
        ),
      );
      pendingTurn.current = null;
    } finally {
      setChatBusy(false);
    }
  }

  function newThread() {
    const id = `t${Date.now()}`;
    setThreads((previous) => [{ id, title: "Nueva conversación", messages: [] }, ...previous]);
    setActiveId(id);
    setChatBoard(null);
    setHorizonDays(HORIZON_DAYS);
    clearSlice();
    setFrozen(null);
    setMode("explore");
    setOpen(null);
    setMobileView("chat");
    setMobileMenu(false);
  }

  function openPo() {
    setFrozen(slice);
    setMode("po");
    setMobileView("po");
  }

  function backToExplore() {
    setFrozen(null);
    setMode("explore");
    setMobileView("explore");
  }

  function exportOrder() {
    if (!online) return;
    const purchaseSkus = dash?.purchase_skus ?? poRows.length;
    window.open(
      purchaseListCsvUrl(sliceToScopeQuery(frozen ?? slice, csvExportLimit(purchaseSkus))),
      "_blank",
    );
  }

  async function openDetail(row: Calc) {
    if (!online) {
      setOpen(row);
      return;
    }
    try {
      const rec = await fetchReplenishment(row.sku.product_id);
      const facts = factsFromRecommendation(rec);
      setOpen({
        ...row,
        avg_daily: facts.avg_daily,
        demand_horizon: facts.demand_horizon,
        demand_lead: facts.demand_lead,
        stock_target: facts.stock_target,
        recommended_quantity: facts.recommended_quantity,
        sku: {
          ...row.sku,
          stock: facts.stock,
          sales_30: facts.sales_30,
          lead_time_days: facts.lead_time_days,
          safety_stock: facts.safety_stock,
        },
      });
    } catch {
      setOpen(row);
    }
  }

  function findRowForProduct(productId: string): Calc | undefined {
    const fromRows = rows.find((row) => row.sku.product_id === productId);
    if (fromRows) return fromRows;
    const list = chatBoard?.purchaseList ?? api.purchaseList;
    const fromList = list.find((item) => item.product_id === productId);
    if (fromList) return calcFromApiRow(rowFromPurchaseItem(fromList));
    return undefined;
  }

  function applyChip(chip: SuggestedChip) {
    const result = applySuggestedFilter(chip, slice);
    if (result.type === "slice") {
      mutateSlice(result.slice);
      return;
    }
    if (result.type === "open_sku") {
      const row = findRowForProduct(result.productId);
      if (row) void openDetail(row);
      return;
    }
    if (result.type === "draft_oc") {
      openPo();
    }
  }

  function handleGoBack() {
    setChatBoard(null);
    goBack();
  }

  function handleClearSlice() {
    setChatBoard(null);
    setHorizonDays(HORIZON_DAYS);
    clearSlice();
  }

  const rail = (
    <aside className={`${railCollapsed ? "w-[72px]" : "w-[72px] xl:w-[248px]"} flex h-full shrink-0 flex-col border-r border-ops-border bg-ops-panel transition-[width] duration-200`}>
      <div className="grid h-16 grid-cols-[minmax(0,1fr)_auto] items-center gap-2 border-b border-ops-border px-4">
        <div className="flex min-w-0 items-center gap-3">
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-ops-accent text-ops-accent-foreground"><Box className="h-4 w-4" /></div>
          {!railCollapsed && <div className="hidden min-w-0 xl:block"><div className="truncate font-display text-base font-semibold text-foreground">SupplyMate</div><div className="truncate text-[11px] text-muted-foreground">Reposición · {horizonDays} días</div></div>}
        </div>
        <button type="button" aria-label={railCollapsed ? "Expandir menú" : "Reducir menú"} onClick={() => setRailCollapsed((value) => !value)} className="hidden h-8 w-8 shrink-0 place-items-center rounded-md text-muted-foreground outline-none hover:bg-ops-row hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-accent md:grid">
          {railCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
      </div>
      <div className="p-3">
        <button type="button" onClick={newThread} className="flex h-9 w-full items-center justify-center gap-2 rounded-md bg-ops-accent px-3 text-xs font-semibold text-ops-accent-foreground outline-none hover:bg-ops-accent-hover focus-visible:ring-2 focus-visible:ring-ops-focus">
          <Plus className="h-4 w-4 shrink-0" />{!railCollapsed && <span className="hidden xl:inline">Nueva conversación</span>}
        </button>
      </div>
      <nav aria-label="Conversaciones" className="flex-1 overflow-y-auto px-3">
        {!railCollapsed && <div className="mb-2 hidden px-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground xl:block">Ejemplos</div>}
        <div className="space-y-1">
          {threads.map((thread) => (
            <button key={thread.id} type="button" title={thread.title} onClick={() => { setActiveId(thread.id); setMobileMenu(false); setMobileView("chat"); }} className={`flex h-10 w-full items-center gap-3 rounded-md px-3 text-left text-xs outline-none focus-visible:ring-2 focus-visible:ring-ops-accent ${thread.id === activeId ? "bg-ops-row text-foreground" : "text-muted-foreground hover:bg-ops-row hover:text-foreground"}`}>
              <MessageSquareText className={`h-4 w-4 shrink-0 ${thread.id === activeId ? "text-ops-accent" : ""}`} />
              {!railCollapsed && (
                <span className="hidden min-w-0 flex-1 items-center gap-2 xl:flex">
                  <span className="truncate">{thread.title}</span>
                </span>
              )}
            </button>
          ))}
        </div>
      </nav>
      <div className="border-t border-ops-border p-4">
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground"><CheckCircle2 className={`h-4 w-4 shrink-0 ${statusLive ? "text-ops-ok" : "text-ops-warn"}`} />{!railCollapsed && <span className="hidden xl:inline">{statusLabel}</span>}</div>
      </div>
    </aside>
  );

  return (
    <div className="h-dvh w-full overflow-hidden bg-background font-sans text-[13px] text-foreground">
      <div className="flex h-full w-full">
        <div className="hidden md:block">{rail}</div>
        {mobileMenu && <div className="fixed inset-0 z-50 md:hidden"><button aria-label="Cerrar menú" className="absolute inset-0 bg-ops-overlay" onClick={() => setMobileMenu(false)} /><div className="relative h-full w-[268px]">{rail}</div></div>}

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="grid h-16 shrink-0 grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-ops-border bg-ops-panel px-4 md:px-5">
            <div className="flex min-w-0 items-center gap-3">
              <button type="button" aria-label="Abrir menú" onClick={() => setMobileMenu(true)} className="grid h-9 w-9 shrink-0 place-items-center rounded-md text-muted-foreground outline-none hover:bg-ops-row focus-visible:ring-2 focus-visible:ring-ops-accent md:hidden"><Menu className="h-5 w-5" /></button>
              <div className="min-w-0"><h1 className="truncate font-display text-lg font-semibold">SupplyMate · Operación de reposición</h1><p className="truncate text-[11px] text-muted-foreground">Próximos {horizonDays} días · este recorte</p></div>
            </div>
            <div className={`flex shrink-0 items-center gap-2 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase ${statusLive ? "border-ops-ok/30 bg-ops-ok-soft text-ops-ok" : "border-ops-warn/40 bg-ops-warn/10 text-ops-warn"}`}><span className={`h-1.5 w-1.5 rounded-full ${statusLive ? "bg-ops-ok" : "bg-ops-warn"}`} />{statusLabel}</div>
          </header>

          <div className="grid h-12 shrink-0 grid-cols-3 border-b border-ops-border bg-ops-panel md:hidden">
            {(["chat", "explore", "po"] as MobileView[]).map((item) => <button key={item} type="button" onClick={() => { if (item === "po") { openPo(); return; } setMobileView(item); if (item === "explore") { setMode("explore"); setFrozen(null); } }} className={`border-b-2 text-xs font-semibold outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ops-accent ${mobileView === item ? "border-ops-accent text-foreground" : "border-transparent text-muted-foreground"}`}>{item === "chat" ? "Consulta" : item === "explore" ? "Explorar" : "Revisar OC"}</button>)}
          </div>

          <div className="grid min-h-0 flex-1 md:grid-cols-[minmax(280px,38%)_minmax(420px,62%)] xl:grid-cols-[minmax(340px,34%)_minmax(560px,66%)]">
            <section className={`${mobileView === "chat" ? "flex" : "hidden"} min-h-0 flex-col border-r border-ops-border bg-background md:flex`}>
              <div className="border-b border-ops-border p-4 md:p-5">
                <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground"><MessageSquareText className="h-4 w-4 text-ops-accent" />Consulta de reposición</div>
                <button type="button" onClick={() => void send(BUY_QUERY)} disabled={chatBusy} className="grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-lg border border-ops-accent/60 bg-ops-accent-soft p-4 text-left outline-none hover:border-ops-accent focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-50">
                  <span className="min-w-0 font-display text-base font-semibold text-foreground">{BUY_QUERY}</span><ChevronRight className="h-5 w-5 shrink-0 text-ops-accent" />
                </button>
              </div>
              <div className="flex-1 space-y-3 overflow-y-auto p-4 md:p-5">
                {active?.messages.length === 0 && <p className="text-sm text-muted-foreground">Escribí una consulta sobre reposición. Las cantidades siempre provienen del motor de cálculo.</p>}
                {active?.messages.map((message) => (
                  <div
                    key={message.id}
                    className={`whitespace-pre-line rounded-lg px-3.5 py-3 leading-relaxed ${
                      message.role === "user"
                        ? "ml-auto max-w-[88%] border border-ops-accent/50 bg-ops-accent-soft"
                        : "max-w-[94%] border border-ops-border bg-ops-panel"
                    }`}
                  >
                    {message.role === "thinking" ? (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 shrink-0 animate-spin text-ops-accent" aria-hidden />
                        <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-ops-accent">
                          Pensando
                        </span>
                        <span aria-live="polite">{message.text}</span>
                      </div>
                    ) : (
                      <>
                        {message.role === "user" && (
                          <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-ops-accent">
                            Vos
                          </div>
                        )}
                        {message.role === "assistant" && (
                          <div className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-ops-ok">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            SupplyMate
                          </div>
                        )}
                        {message.text}
                      </>
                    )}
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
              <div className="border-t border-ops-border bg-ops-panel p-4">
                {labels.length > 0 && <p className="mb-2 text-[11px] text-muted-foreground">Recorte actual: <span className="text-foreground">{labels.join(" · ")}</span></p>}
                {nextStepChips.length > 0 && (
                  <div className="mb-2 grid grid-cols-3 gap-1.5">
                    {nextStepChips.map((chip) => (
                      <button
                        key={`${chip.action}:${JSON.stringify(chip.args)}`}
                        type="button"
                        title={chip.label}
                        onClick={() => applyChip(chip)}
                        className="truncate rounded-md border border-ops-border bg-background px-2.5 py-1.5 text-[11px] text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
                      >
                        {chip.label}
                      </button>
                    ))}
                  </div>
                )}
                <form onSubmit={(event) => { event.preventDefault(); void send(input); }} className="grid grid-cols-[minmax(0,1fr)_auto] gap-2">
                  <div className="relative min-w-0"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><input value={input} onChange={(event) => setInput(event.target.value)} aria-label="Consulta de reposición" placeholder="Escribí una consulta…" className="h-10 w-full rounded-md border border-ops-border bg-background pl-9 pr-3 text-sm outline-none placeholder:text-muted-foreground focus:border-ops-accent focus:ring-2 focus:ring-ops-focus" /></div>
                  <button type="submit" aria-label="Enviar consulta" disabled={chatBusy} className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-ops-accent text-ops-accent-foreground outline-none hover:bg-ops-accent-hover focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-50"><Send className="h-4 w-4" /></button>
                </form>
              </div>
            </section>

            <section className={`${mobileView !== "chat" ? "flex" : "hidden"} min-h-0 min-w-0 flex-col bg-background md:flex`}>
              <div className="hidden h-12 shrink-0 grid-cols-2 border-b border-ops-border bg-ops-panel md:grid">
                <button type="button" onClick={backToExplore} className={`border-b-2 text-xs font-semibold outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ops-accent ${mode === "explore" ? "border-ops-accent text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Explorar</button>
                <button type="button" onClick={openPo} className={`border-b-2 text-xs font-semibold outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ops-accent ${mode === "po" ? "border-ops-accent text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Revisar OC</button>
              </div>

              {mode === "po" ? (
                <PurchaseOrder rows={poRows} labels={sliceLabels(frozen ?? slice, horizonDays)} units={units} value={value} skuCount={poSkuCount} onExport={exportOrder} onBack={backToExplore} />
              ) : (
                <div className="min-h-0 flex-1 overflow-y-auto">
                  <div className="flex flex-wrap items-center gap-2 border-b border-ops-border bg-ops-panel px-4 py-2.5 lg:px-5">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">Recorte</span>
                    <span className="min-w-0 truncate text-xs text-foreground">{labels.length > 0 ? labels.join(" · ") : "Inventario completo"}</span>
                    <div className="ml-auto flex items-center gap-1.5">
                      <button type="button" onClick={handleGoBack} disabled={history.length === 0} className="inline-flex h-7 items-center gap-1 rounded-md border border-ops-border px-2 text-[11px] text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-40"><ArrowLeft className="h-3.5 w-3.5" />Volver</button>
                      <button type="button" onClick={handleClearSlice} disabled={labels.length === 0 && !chatBoard} className="inline-flex h-7 items-center gap-1 rounded-md border border-ops-border px-2 text-[11px] text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-40"><Eraser className="h-3.5 w-3.5" />Limpiar</button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 p-4 lg:grid-cols-4 lg:p-5">
                    {kpis.map((kpi) => (
                      <button key={kpi.label} type="button" onClick={kpi.onClick} aria-pressed={kpi.active} className={`rounded-lg border p-3.5 text-left outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ops-focus ${kpi.active ? "border-ops-accent bg-ops-accent-soft" : "border-ops-border bg-ops-panel hover:border-ops-accent"}`}>
                        <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-2"><div className="truncate text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">{kpi.label}</div><kpi.icon className="h-4 w-4 shrink-0 text-ops-accent" /></div>
                        <div className="mt-2 font-display text-2xl font-semibold tabular-nums">{kpi.value}</div>
                        <div className="mt-0.5 text-[11px] text-muted-foreground">{kpi.detail}</div>
                      </button>
                    ))}
                  </div>

                  <div className="border-y border-ops-border bg-ops-panel px-4 py-4 lg:px-5">
                    <div className="mb-3 flex items-center justify-between gap-2">
                      <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                        {chartMode === "sku"
                          ? "Top productos a reponer"
                          : chartMode === "subcategory"
                            ? "Unidades a reponer por subcategoría"
                            : "Unidades a reponer por categoría"}
                      </div>
                      {chartData.length > 1 && (
                        <div className="text-[11px] text-muted-foreground">
                          {chartMode === "sku"
                            ? "Tocá una barra para abrir el producto"
                            : chartMode === "subcategory"
                              ? "Tocá una barra para ver esa subcategoría"
                              : "Tocá una barra para ver esa categoría"}
                        </div>
                      )}
                    </div>
                    {api.error && chartData.length === 0 ? (
                      <p className="py-6 text-center text-xs text-muted-foreground">{COPY_CATEGORIES_LOAD_FAILED}</p>
                    ) : api.loading && chartData.length === 0 ? (
                      <p className="py-6 text-center text-xs text-muted-foreground">Cargando categorías del catálogo…</p>
                    ) : chartData.length === 0 ? (
                      <p className="py-6 text-center text-xs text-muted-foreground">No hay unidades a reponer en este recorte.</p>
                    ) : (
                      <div className="h-[210px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart key={chartKey} data={chartData} margin={{ top: 40, right: 8, bottom: 28, left: 0 }}>
                            <CartesianGrid stroke="var(--ops-border)" vertical={false} />
                            <XAxis
                              dataKey="category"
                              tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
                              tickLine={false}
                              axisLine={{ stroke: "var(--ops-border)" }}
                              interval={0}
                              tickFormatter={(value: string) =>
                                chartTickLabel(value, chartData.length, chartMode === "sku" ? 10 : 13)
                              }
                            />
                            <YAxis tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} tickLine={false} axisLine={false} width={44} />
                            <Tooltip cursor={{ fill: "var(--ops-row)" }} contentStyle={{ background: "var(--ops-panel)", border: "1px solid var(--ops-border)", borderRadius: 8, fontSize: 12, color: "var(--foreground)" }} formatter={(item: number) => [nf.format(item), "Unidades"]} />
                            <Bar
                              dataKey="units"
                              maxBarSize={64}
                              radius={[4, 4, 0, 0]}
                              cursor="pointer"
                              isAnimationActive={false}
                              onClick={(bar: { category?: string; productId?: string }) => {
                                if (chartMode === "sku") {
                                  const productId =
                                    bar.productId ||
                                    chartData.find((item) => item.category === bar.category)?.productId;
                                  if (!productId) return;
                                  const row = findRowForProduct(productId);
                                  if (row) void openDetail(row);
                                  return;
                                }
                                if (!bar.category) return;
                                if (chartMode === "subcategory") {
                                  mutateSlice((previous) => ({
                                    ...previous,
                                    subcategories: [bar.category as string],
                                  }));
                                  return;
                                }
                                mutateSlice((previous) => ({ ...previous, cats: [bar.category as string] }));
                              }}
                            >
                              {chartData.map((item) => {
                                const active =
                                  chartMode === "sku"
                                    ? slice.highlightProductId === item.productId
                                    : chartMode === "subcategory"
                                      ? slice.subcategories.includes(item.category)
                                      : slice.cats.includes(item.category);
                                const dimmed =
                                  chartMode === "sku"
                                    ? Boolean(slice.highlightProductId) && !active
                                    : chartMode === "subcategory"
                                      ? slice.subcategories.length > 0 && !active
                                      : slice.cats.length > 0 && !active;
                                return (
                                  <Cell
                                    key={item.productId ?? item.category}
                                    fill={categoryColor(item.productId ?? item.category)}
                                    stroke={active ? "var(--foreground)" : "transparent"}
                                    strokeWidth={active ? 2 : 0}
                                    fillOpacity={dimmed ? 0.45 : 1}
                                  />
                                );
                              })}
                              <LabelList
                                dataKey="units"
                                position="top"
                                offset={8}
                                formatter={(value: number) => `${nf.format(value)} ud`}
                                fill="var(--foreground)"
                                fontSize={11}
                                fontWeight={600}
                              />
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>

                  <div className="border-b border-ops-border bg-ops-panel px-4 py-3 lg:px-5">
                    <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground"><SlidersHorizontal className="h-3.5 w-3.5" />Filtros</div>
                    <div className="flex flex-wrap gap-1.5">
                      <button type="button" onClick={() => mutateSlice((previous) => ({ ...previous, buyOnly: !previous.buyOnly }))} className={`rounded-full border px-2.5 py-1 text-[11px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-ops-focus ${slice.buyOnly ? "border-ops-accent bg-ops-accent-soft text-ops-accent" : "border-ops-border text-muted-foreground hover:border-ops-accent"}`}><ShoppingCart className="mr-1 inline h-3 w-3" />A comprar</button>
                      {HEALTH_FILTERS.map((tag) => {
                        const Icon = healthIcon[tag];
                        const healthTag = tag as "riesgo_quiebre" | "sin_stock" | "sobrestock";
                        return (
                          <button
                            key={tag}
                            type="button"
                            onClick={() => toggleHealth(healthTag)}
                            className={`rounded-full border px-2.5 py-1 text-[11px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-ops-focus ${slice.health.includes(healthTag) ? "border-ops-accent bg-ops-accent-soft text-foreground" : "border-ops-border text-muted-foreground hover:border-ops-accent"}`}
                          >
                            <Icon className="mr-1 inline h-3 w-3" />
                            {HEALTH_LABEL[tag]}
                          </button>
                        );
                      })}
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-1.5">
                      <span className="mr-1 text-[10px] uppercase tracking-[0.08em] text-muted-foreground">Cobertura</span>
                      {COVERAGE_ORDER.map((band) => <button key={band} type="button" onClick={() => mutateSlice((previous) => ({ ...previous, coverage: previous.coverage === band ? null : band }))} className={`rounded-full border px-2.5 py-1 text-[11px] outline-none focus-visible:ring-2 focus-visible:ring-ops-focus ${slice.coverage === band ? "border-ops-accent bg-ops-accent-soft text-ops-accent" : "border-ops-border text-muted-foreground hover:border-ops-accent"}`}><Timer className="mr-1 inline h-3 w-3" />{band}</button>)}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5">{categoryNames.map((category) => <button key={category} type="button" onClick={() => mutateSlice((previous) => ({ ...previous, cats: toggleList(previous.cats, category) }))} className={`rounded-md border px-2.5 py-1 text-[11px] outline-none focus-visible:ring-2 focus-visible:ring-ops-focus ${slice.cats.includes(category) ? "border-ops-accent text-ops-accent" : "border-ops-border text-muted-foreground hover:border-ops-accent"}`}>{category}</button>)}</div>
                  </div>

                  <SkuTable rows={rows} recorteToBuy={dash?.purchase_skus ?? rows.length} onOpen={(row) => void openDetail(row)} />
                </div>
              )}
            </section>
          </div>
        </div>
      </div>

      {open && <SkuDrawer row={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
