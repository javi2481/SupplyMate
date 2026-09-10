import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  ArrowUpDown,
  Box,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Download,
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
  SlidersHorizontal,
  Timer,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useScope } from "@/hooks/use-scope";
import { useSlice } from "@/hooks/use-slice";
import {
  fetchReplenishment,
  postChat,
  purchaseListCsvUrl,
  scopeQueryToPayload,
} from "@/lib/api";
import { factsFromRecommendation, rowFromPurchaseItem } from "@/lib/adapter";
import { applyChatScope, chatFailureMessage } from "@/lib/applyChatScope";
import { applySuggestedFilter, type SuggestedChip } from "@/lib/applySuggestedFilter";
import { categoryColor } from "@/lib/chart-colors";
import {
  COPY_CATEGORIES_LOAD_FAILED,
  categoryNamesForUi,
  chartTickLabel,
  chartUnitsByCategory,
  csvExportLimit,
  dataSourceLabel,
  kpisFromDashboard,
  tableScopeCaption,
} from "@/lib/data-source";
import { calcFromApiRow } from "@/lib/ops-row";
import { COVERAGE_ORDER, sliceToScopeQuery, type UiSlice } from "@/lib/scope";
import {
  HEALTH_FILTERS,
  HEALTH_LABEL,
  HORIZON_DAYS,
  PRIORITY_LABEL,
  dec,
  money,
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

type Msg = { id: number; role: "user" | "assistant"; text: string };
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
        text: `Listo para revisar la reposición de los próximos ${HORIZON_DAYS} días. Elegí una consulta rápida para comenzar: las cantidades salen del motor de cálculo.`,
      },
    ],
  },
];

const healthIcon: Record<HealthTag, typeof AlertTriangle> = {
  riesgo_quiebre: AlertTriangle,
  sin_stock: CircleAlert,
  sobrestock: Box,
  cobertura_baja: Timer,
};

function visibleHealth(row: Calc): HealthTag[] {
  return row.health.filter((tag) => HEALTH_FILTERS.includes(tag));
}

function sliceLabels(slice: UiSlice): string[] {
  const labels: string[] = [];
  if (slice.buyOnly) labels.push("A comprar");
  labels.push(...slice.cats);
  labels.push(...(slice.suppliers ?? []));
  labels.push(...slice.health.map((tag) => HEALTH_LABEL[tag]));
  if (slice.coverage) {
    labels.push(`Cobertura ${slice.coverage}`);
  }
  return labels;
}

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
  const [threads, setThreads] = useState<Thread[]>(SEED);
  const [activeId, setActiveId] = useState("t1");
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"explore" | "po">("explore");
  const [mobileView, setMobileView] = useState<MobileView>("explore");
  const { slice, history, pushSlice, goBack, clearSlice } = useScope();
  const [open, setOpen] = useState<Calc | null>(null);
  const [frozen, setFrozen] = useState<UiSlice | null>(null);
  const [railCollapsed, setRailCollapsed] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [chatBusy, setChatBusy] = useState(false);

  const scopeQuery = useMemo(() => sliceToScopeQuery(slice, 50), [slice]);
  const api = useSlice(scopeQuery, 50);
  const online = api.online;
  const statusLabel = dataSourceLabel(online);
  const statusLive = online;

  const categoryNames = useMemo(() => categoryNamesForUi(api.dashboard), [api.dashboard]);

  const active = threads.find((thread) => thread.id === activeId) ?? threads[0];
  const rows = useMemo(
    () => applyClientFilters(api.rows.map(calcFromApiRow), slice),
    [api.rows, slice],
  );
  const labels = sliceLabels(slice);

  const nextStepChips = useMemo(
    () => (api.suggestedFilters ?? []).slice(0, 6),
    [api.suggestedFilters],
  );

  function toggleList<T>(list: T[], item: T): T[] {
    return list.includes(item) ? list.filter((value) => value !== item) : [...list, item];
  }

  function toggleHealth(tag: "riesgo_quiebre" | "sin_stock" | "sobrestock") {
    pushSlice((previous) => {
      const health = toggleList(previous.health, tag);
      return { ...previous, health, outOfStockOnly: health.includes("sin_stock") };
    });
  }

  const dash = api.dashboard;
  const listUnits = rows.reduce((sum, row) => sum + row.recommended_quantity, 0);
  const listOutOfStock = rows.filter((row) => row.sku.stock === 0).length;
  const kpisDash = kpisFromDashboard(dash, listUnits, listOutOfStock);
  const kpis = [
    {
      label: "Productos",
      value: nf.format(dash?.skus ?? rows.length),
      detail: "en este recorte",
      icon: Box,
      active: slice.buyOnly,
      onClick: () => pushSlice((previous) => ({ ...previous, buyOnly: !previous.buyOnly })),
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
      detail: `para ${HORIZON_DAYS} días`,
      icon: PackageCheck,
      active: slice.buyOnly,
      onClick: () => pushSlice((previous) => ({ ...previous, buyOnly: !previous.buyOnly })),
    },
  ];

  const chartData = useMemo(() => chartUnitsByCategory(dash), [dash]);

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

    setThreads((previous) =>
      previous.map((thread) =>
        thread.id !== activeId
          ? thread
          : {
              ...thread,
              title: thread.messages.length === 0 ? query.slice(0, 34) : thread.title,
              messages: [...thread.messages, { id: Date.now(), role: "user" as const, text: query }],
            },
      ),
    );
    setMode("explore");
    setMobileView("explore");

    setChatBusy(true);
    try {
      const res = await postChat(query, scopeQueryToPayload(sliceToScopeQuery(slice)));
      const applied = applyChatScope(slice, res);
      if (res.scope != null) pushSlice(applied.slice);
      setThreads((previous) =>
        previous.map((thread) =>
          thread.id !== activeId
            ? thread
            : {
                ...thread,
                messages: [
                  ...thread.messages,
                  {
                    id: Date.now() + 1,
                    role: "assistant" as const,
                    text: res.answer || "Sin respuesta del catálogo.",
                  },
                ],
              },
        ),
      );
      if (applied.openProductId) {
        const fromRes = res.purchase_list.find((item) => item.product_id === applied.openProductId);
        const row = fromRes
          ? calcFromApiRow(rowFromPurchaseItem(fromRes))
          : findRowForProduct(applied.openProductId);
        if (row) void openDetail(row);
      }
    } catch (error) {
      setThreads((previous) =>
        previous.map((thread) =>
          thread.id !== activeId
            ? thread
            : {
                ...thread,
                messages: [
                  ...thread.messages,
                  {
                    id: Date.now() + 1,
                    role: "assistant" as const,
                    text: chatFailureMessage(query, error),
                  },
                ],
              },
        ),
      );
    } finally {
      setChatBusy(false);
    }
  }

  function newThread() {
    const id = `t${Date.now()}`;
    setThreads((previous) => [{ id, title: "Nueva conversación", messages: [] }, ...previous]);
    setActiveId(id);
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
    const fromList = api.purchaseList.find((item) => item.product_id === productId);
    if (fromList) return calcFromApiRow(rowFromPurchaseItem(fromList));
    return undefined;
  }

  function applyChip(chip: SuggestedChip) {
    const result = applySuggestedFilter(chip, slice);
    if (result.type === "slice") {
      pushSlice(result.slice);
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

  const rail = (
    <aside className={`${railCollapsed ? "w-[72px]" : "w-[72px] xl:w-[248px]"} flex h-full shrink-0 flex-col border-r border-ops-border bg-ops-panel transition-[width] duration-200`}>
      <div className="grid h-16 grid-cols-[minmax(0,1fr)_auto] items-center gap-2 border-b border-ops-border px-4">
        <div className="flex min-w-0 items-center gap-3">
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-ops-accent text-ops-accent-foreground"><Box className="h-4 w-4" /></div>
          {!railCollapsed && <div className="hidden min-w-0 xl:block"><div className="truncate font-display text-base font-semibold text-foreground">SupplyMate</div><div className="truncate text-[11px] text-muted-foreground">Reposición · 7 días</div></div>}
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
              <div className="min-w-0"><h1 className="truncate font-display text-lg font-semibold">SupplyMate · Operación de reposición</h1><p className="truncate text-[11px] text-muted-foreground">Próximos {HORIZON_DAYS} días · este recorte</p></div>
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
                <button type="button" onClick={() => void send(BUY_QUERY)} className="grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-lg border border-ops-accent/60 bg-ops-accent-soft p-4 text-left outline-none hover:border-ops-accent focus-visible:ring-2 focus-visible:ring-ops-focus">
                  <span className="min-w-0 font-display text-base font-semibold text-foreground">{BUY_QUERY}</span><ChevronRight className="h-5 w-5 shrink-0 text-ops-accent" />
                </button>
              </div>
              <div className="flex-1 space-y-3 overflow-y-auto p-4 md:p-5">
                {active?.messages.length === 0 && <p className="text-sm text-muted-foreground">Escribí una consulta sobre reposición. Las cantidades siempre provienen del motor de cálculo.</p>}
                {active?.messages.map((message) => (
                  <div key={message.id} className={`whitespace-pre-line rounded-lg px-3.5 py-3 leading-relaxed ${message.role === "user" ? "ml-auto max-w-[88%] border border-ops-accent/50 bg-ops-accent-soft" : "max-w-[94%] border border-ops-border bg-ops-panel"}`}>
                    {message.role === "assistant" && <div className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-ops-ok"><CheckCircle2 className="h-3.5 w-3.5" />SupplyMate</div>}{message.text}
                  </div>
                ))}
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
                <PurchaseOrder rows={poRows} labels={sliceLabels(frozen ?? slice)} units={units} value={value} skuCount={poSkuCount} onExport={exportOrder} onBack={backToExplore} />
              ) : (
                <div className="min-h-0 flex-1 overflow-y-auto">
                  <div className="flex flex-wrap items-center gap-2 border-b border-ops-border bg-ops-panel px-4 py-2.5 lg:px-5">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">Recorte</span>
                    <span className="min-w-0 truncate text-xs text-foreground">{labels.length > 0 ? labels.join(" · ") : "Inventario completo"}</span>
                    <div className="ml-auto flex items-center gap-1.5">
                      <button type="button" onClick={goBack} disabled={history.length === 0} className="inline-flex h-7 items-center gap-1 rounded-md border border-ops-border px-2 text-[11px] text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-40"><ArrowLeft className="h-3.5 w-3.5" />Volver</button>
                      <button type="button" onClick={clearSlice} disabled={labels.length === 0} className="inline-flex h-7 items-center gap-1 rounded-md border border-ops-border px-2 text-[11px] text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-40"><Eraser className="h-3.5 w-3.5" />Limpiar</button>
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
                      <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">Unidades a reponer por categoría</div>
                      {chartData.length > 1 && (
                        <div className="text-[11px] text-muted-foreground">Tocá una barra para ver esa categoría</div>
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
                          <BarChart data={chartData} margin={{ top: 40, right: 8, bottom: 28, left: 0 }}>
                            <CartesianGrid stroke="var(--ops-border)" vertical={false} />
                            <XAxis
                              dataKey="category"
                              tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
                              tickLine={false}
                              axisLine={{ stroke: "var(--ops-border)" }}
                              interval={0}
                              tickFormatter={(value: string) => chartTickLabel(value, chartData.length)}
                            />
                            <YAxis tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} tickLine={false} axisLine={false} width={44} />
                            <Tooltip cursor={{ fill: "var(--ops-row)" }} contentStyle={{ background: "var(--ops-panel)", border: "1px solid var(--ops-border)", borderRadius: 8, fontSize: 12, color: "var(--foreground)" }} formatter={(item: number) => [nf.format(item), "Unidades"]} />
                            <Bar
                              dataKey="units"
                              maxBarSize={64}
                              radius={[4, 4, 0, 0]}
                              cursor="pointer"
                              isAnimationActive={false}
                              onClick={(bar: { category?: string }) => bar.category && pushSlice((previous) => ({ ...previous, cats: [bar.category as string] }))}
                            >
                              {chartData.map((item) => <Cell key={item.category} fill={categoryColor(item.category)} stroke={slice.cats.includes(item.category) ? "var(--foreground)" : "transparent"} strokeWidth={slice.cats.includes(item.category) ? 2 : 0} fillOpacity={slice.cats.length === 0 || slice.cats.includes(item.category) ? 1 : 0.45} />)}
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
                      <button type="button" onClick={() => pushSlice((previous) => ({ ...previous, buyOnly: !previous.buyOnly }))} className={`rounded-full border px-2.5 py-1 text-[11px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-ops-focus ${slice.buyOnly ? "border-ops-accent bg-ops-accent-soft text-ops-accent" : "border-ops-border text-muted-foreground hover:border-ops-accent"}`}><ShoppingCart className="mr-1 inline h-3 w-3" />A comprar</button>
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
                      {COVERAGE_ORDER.map((band) => <button key={band} type="button" onClick={() => pushSlice((previous) => ({ ...previous, coverage: previous.coverage === band ? null : band }))} className={`rounded-full border px-2.5 py-1 text-[11px] outline-none focus-visible:ring-2 focus-visible:ring-ops-focus ${slice.coverage === band ? "border-ops-accent bg-ops-accent-soft text-ops-accent" : "border-ops-border text-muted-foreground hover:border-ops-accent"}`}><Timer className="mr-1 inline h-3 w-3" />{band}</button>)}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5">{categoryNames.map((category) => <button key={category} type="button" onClick={() => pushSlice((previous) => ({ ...previous, cats: toggleList(previous.cats, category) }))} className={`rounded-md border px-2.5 py-1 text-[11px] outline-none focus-visible:ring-2 focus-visible:ring-ops-focus ${slice.cats.includes(category) ? "border-ops-accent text-ops-accent" : "border-ops-border text-muted-foreground hover:border-ops-accent"}`}>{category}</button>)}</div>
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

function PriorityCell({ row }: { row: Calc }) {
  const label = PRIORITY_LABEL[row.priority];
  const tone = row.priority === "Alta" ? "text-ops-danger" : row.priority === "Media" ? "text-ops-warn" : "text-muted-foreground";
  return <span className={`font-medium ${tone}`}>{label}</span>;
}

function HealthChips({ row }: { row: Calc }) {
  const tags = visibleHealth(row);
  if (tags.length === 0) {
    return <span className="inline-flex items-center gap-1 rounded-full border border-ops-ok/40 bg-ops-ok-soft px-2 py-0.5 text-[10px] text-ops-ok"><CheckCircle2 className="h-3 w-3" />Saludable</span>;
  }
  return (
    <div className="flex flex-wrap gap-1">
      {tags.map((tag) => {
        const Icon = healthIcon[tag];
        return <span key={tag} className="inline-flex items-center gap-1 rounded-full border border-ops-border bg-ops-panel px-2 py-0.5 text-[10px] text-muted-foreground"><Icon className="h-3 w-3" />{HEALTH_LABEL[tag]}</span>;
      })}
    </div>
  );
}

type SortKey = "product" | "stock" | "sales" | "coverage" | "order" | "priority" | "health";
type SortDirection = "asc" | "desc";

function normalizeSearch(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function singular(value: string): string {
  if (value.length > 5 && value.endsWith("es")) return value.slice(0, -2);
  if (value.length > 4 && value.endsWith("s")) return value.slice(0, -1);
  return value;
}

function distance(a: string, b: string): number {
  const previous = Array.from({ length: b.length + 1 }, (_, index) => index);
  for (let i = 1; i <= a.length; i += 1) {
    const current = [i];
    for (let j = 1; j <= b.length; j += 1) {
      current[j] = Math.min((current[j - 1] ?? 0) + 1, (previous[j] ?? 0) + 1, (previous[j - 1] ?? 0) + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    previous.splice(0, previous.length, ...current);
  }
  return previous[b.length] ?? a.length;
}

function fuzzyTokenMatch(query: string, candidate: string): boolean {
  const q = singular(query);
  const c = singular(candidate);
  if (c.includes(q) || q.includes(c)) return true;
  return distance(q, c) <= Math.max(1, Math.floor(Math.max(q.length, c.length) * 0.3));
}

function rowSearchWords(row: Calc): string[] {
  return normalizeSearch([row.sku.product_name, row.sku.barcode, row.sku.category, row.sku.supplier].join(" ")).split(" ");
}

function SortIcon({ column, active, direction }: { column: SortKey; active: SortKey; direction: SortDirection }) {
  if (column !== active) return <ArrowUpDown className="h-3 w-3 opacity-55" />;
  return direction === "asc" ? <ArrowUp className="h-3 w-3 text-ops-accent" /> : <ArrowDown className="h-3 w-3 text-ops-accent" />;
}

function SkuTable({ rows, recorteToBuy, onOpen }: { rows: Calc[]; recorteToBuy: number; onOpen: (row: Calc) => void }) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<{ key: SortKey; direction: SortDirection }>({ key: "order", direction: "desc" });
  const normalizedQuery = normalizeSearch(query);
  const queryTokens = normalizedQuery.split(" ").filter(Boolean);

  const vocabulary = useMemo(() => {
    const entries = new Map<string, string>();
    rows.forEach((row) => {
      [row.sku.product_name, row.sku.supplier].forEach((label) => {
        normalizeSearch(label).split(" ").filter((word) => word.length > 2).forEach((word) => {
          if (!entries.has(word)) entries.set(word, word.charAt(0).toUpperCase() + word.slice(1));
        });
      });
      normalizeSearch(row.sku.category).split(" ").filter((word) => word.length > 2).forEach((word) => entries.set(word, row.sku.category));
    });
    return Array.from(entries, ([word, label]) => ({ word, label }));
  }, [rows]);

  const correction = useMemo(() => {
    const token = queryTokens[0];
    if (queryTokens.length !== 1 || !token || token.length < 4) return null;
    if (vocabulary.some((entry) => singular(entry.word) === singular(token))) return null;
    const match = vocabulary
      .map((entry) => ({ ...entry, distance: distance(singular(token), singular(entry.word)) }))
      .filter((entry) => entry.distance > 0 && entry.distance <= Math.max(1, Math.floor(token.length * 0.34)))
      .sort((a, b) => a.distance - b.distance)[0];
    return match?.label ?? null;
  }, [queryTokens, vocabulary]);

  const displayedRows = useMemo(() => {
    const filtered = queryTokens.length === 0 ? rows : rows.filter((row) => {
      const words = rowSearchWords(row);
      return queryTokens.every((token) => words.some((word) => fuzzyTokenMatch(token, word)));
    });
    const priorityRank = { Alta: 3, Media: 2, Baja: 1 } as const;
    const healthValue = (row: Calc) => visibleHealth(row).map((tag) => HEALTH_LABEL[tag]).join(" ") || "Saludable";
    const valueFor = (row: Calc): string | number => {
      if (sort.key === "product") return row.sku.product_name;
      if (sort.key === "stock") return row.sku.stock;
      if (sort.key === "sales") return row.sku.sales_30;
      if (sort.key === "coverage") return row.coverage_days;
      if (sort.key === "order") return row.recommended_quantity;
      if (sort.key === "priority") return priorityRank[row.priority];
      return healthValue(row);
    };
    return [...filtered].sort((a, b) => {
      const aValue = valueFor(a);
      const bValue = valueFor(b);
      const result = typeof aValue === "number" && typeof bValue === "number" ? aValue - bValue : String(aValue).localeCompare(String(bValue), "es");
      return sort.direction === "asc" ? result : -result;
    });
  }, [queryTokens, rows, sort]);

  function changeSort(key: SortKey) {
    setSort((current) => current.key === key ? { key, direction: current.direction === "asc" ? "desc" : "asc" } : { key, direction: key === "product" || key === "health" ? "asc" : "desc" });
  }

  const headers: { key: SortKey; label: string; align?: "right" }[] = [
    { key: "product", label: "SKU / Producto" },
    { key: "stock", label: "Stock", align: "right" },
    { key: "sales", label: "Ventas 30d", align: "right" },
    { key: "coverage", label: "Cobertura", align: "right" },
    { key: "order", label: "A pedir", align: "right" },
    { key: "priority", label: "Prioridad" },
    { key: "health", label: "Salud" },
  ];

  const caption = tableScopeCaption({
    displayed: displayedRows.length,
    pageRows: rows.length,
    recorteToBuy,
    searching: queryTokens.length > 0,
  });

  return (
    <div>
      <div className="border-b border-ops-border bg-background px-4 py-3 lg:px-5">
        <div className="flex flex-wrap items-center gap-2">
          <label className="relative min-w-[220px] flex-1">
            <span className="sr-only">Buscar productos</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar producto, SKU, categoría o proveedor" className="h-9 w-full rounded-md border border-ops-border bg-ops-panel pl-9 pr-9 text-xs text-foreground outline-none placeholder:text-muted-foreground focus:border-ops-accent focus:ring-2 focus:ring-ops-focus" />
            {query && <button type="button" onClick={() => setQuery("")} aria-label="Limpiar búsqueda" className="absolute right-1.5 top-1/2 grid h-6 w-6 -translate-y-1/2 place-items-center rounded text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"><X className="h-3.5 w-3.5" /></button>}
          </label>
          <span className="text-[11px] tabular-nums text-muted-foreground">{nf.format(caption.shown)} de {nf.format(caption.total)} {caption.noun}</span>
        </div>
        {correction && displayedRows.length > 0 && <p className="mt-2 text-[11px] text-muted-foreground">Mostrando resultados relacionados con <button type="button" onClick={() => setQuery(correction)} className="font-semibold text-ops-accent outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ops-focus">“{correction}”</button>.</p>}
      </div>
      <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] text-left text-xs">
        <thead className="sticky top-0 bg-ops-panel text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
          <tr>
            {headers.map((header, index) => <th key={header.key} className={`${index === 0 ? "px-5" : "px-3"} py-3 ${header.align === "right" ? "text-right" : ""}`}><button type="button" onClick={() => changeSort(header.key)} aria-label={`Ordenar por ${header.label}`} className={`inline-flex items-center gap-1 outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus ${header.align === "right" ? "ml-auto" : ""}`}>{header.label}<SortIcon column={header.key} active={sort.key} direction={sort.direction} /></button></th>)}
            <th className="w-10 px-3 py-3"><span className="sr-only">Detalle</span></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-ops-border">
          {displayedRows.map((row) => (
            <tr key={row.sku.barcode} onClick={() => onOpen(row)} className="cursor-pointer bg-background outline-none transition-colors hover:bg-ops-row focus-within:bg-ops-row">
              <td className="px-5 py-3"><div className="font-medium text-foreground">{row.sku.product_name}</div><div className="mt-0.5 text-[10px] tabular-nums text-muted-foreground">{row.sku.barcode} · {row.sku.category}</div></td>
              <td className="px-3 py-3 text-right tabular-nums">{nf.format(row.sku.stock)}</td>
              <td className="px-3 py-3 text-right tabular-nums text-muted-foreground">{nf.format(row.sku.sales_30)}</td>
              <td className="px-3 py-3 text-right tabular-nums text-muted-foreground">{row.coverage_days >= 999 ? "sin venta" : `${dec(row.coverage_days)} d`}</td>
              <td className="px-3 py-3 text-right font-semibold tabular-nums text-ops-accent">{nf.format(row.recommended_quantity)}</td>
              <td className="px-3 py-3"><PriorityCell row={row} /></td>
              <td className="px-3 py-3"><HealthChips row={row} /></td>
              <td className="px-3 py-3"><button type="button" aria-label={`Ver cálculo de ${row.sku.product_name}`} onClick={(event) => { event.stopPropagation(); onOpen(row); }} className="grid h-7 w-7 place-items-center rounded-md text-muted-foreground outline-none hover:bg-ops-panel hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"><ChevronRight className="h-4 w-4" /></button></td>
            </tr>
          ))}
          {displayedRows.length === 0 && <tr><td colSpan={8} className="px-5 py-12 text-center text-muted-foreground">{query ? <span>No encontramos productos para “{query}”. <button type="button" onClick={() => setQuery("")} className="font-semibold text-ops-accent outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ops-focus">Limpiar búsqueda</button></span> : "No hay productos en este recorte. Probá quitar un filtro."}</td></tr>}
        </tbody>
      </table>
      </div>
    </div>
  );
}

function PurchaseOrder({ rows, labels, units, value, skuCount, onExport, onBack }: { rows: Calc[]; labels: string[]; units: number; value: number; skuCount: number; onExport: () => void; onBack: () => void }) {
  return (
    <div className="min-h-0 flex-1 overflow-y-auto p-4 lg:p-5">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
        <div className="min-w-0">
          <h2 className="truncate font-display text-lg font-semibold">Revisar orden de compra</h2>
          <p className="text-xs text-muted-foreground">El recorte queda congelado en esta vista.</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button type="button" onClick={onBack} className="inline-flex h-9 items-center gap-2 rounded-md border border-ops-border px-3 text-xs font-semibold text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"><ArrowLeft className="h-4 w-4" />Volver a Explorar</button>
          <button type="button" onClick={onExport} disabled={rows.length === 0} className="inline-flex h-9 items-center gap-2 rounded-md bg-ops-accent px-3 text-xs font-semibold text-ops-accent-foreground outline-none hover:bg-ops-accent-hover focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-40"><Download className="h-4 w-4" />Exportar orden</button>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-ops-border bg-ops-panel p-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">Recorte congelado</div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {labels.filter((label) => label !== "A comprar").map((label) => <span key={label} className="rounded-full border border-ops-accent/50 bg-ops-accent-soft px-2 py-0.5 text-[11px] text-ops-accent">{label}</span>)}
          {labels.filter((label) => label !== "A comprar").length === 0 && <span className="text-xs text-muted-foreground">Inventario completo</span>}
        </div>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-3">
        {[["Productos", nf.format(skuCount)], ["Unidades", nf.format(units)], ["Valor estimado", money(value)]].map(([label, amount]) => (
          <div key={label} className="rounded-lg border border-ops-border bg-ops-panel p-3"><div className="text-[10px] uppercase text-muted-foreground">{label}</div><div className="mt-1 font-display text-lg font-semibold tabular-nums">{amount}</div></div>
        ))}
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-ops-border">
        <table className="w-full text-xs">
          <thead className="bg-ops-panel text-left text-[10px] uppercase text-muted-foreground">
            <tr><th className="px-3 py-2.5">Producto</th><th className="px-3 py-2.5">Proveedor</th><th className="px-3 py-2.5 text-right">Cantidad</th><th className="px-3 py-2.5 text-right">Valor</th></tr>
          </thead>
          <tbody className="divide-y divide-ops-border">
            {rows.map((row) => (
              <tr key={row.sku.barcode} className="hover:bg-ops-row">
                <td className="px-3 py-3"><div className="font-medium">{row.sku.product_name}</div><div className="text-[10px] text-muted-foreground">{row.sku.barcode}</div></td>
                <td className="px-3 py-3 text-muted-foreground">{row.sku.supplier}</td>
                <td className="px-3 py-3 text-right font-semibold tabular-nums">{nf.format(row.recommended_quantity)}</td>
                <td className="px-3 py-3 text-right tabular-nums">{money(row.estimated_purchase_value)}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={4} className="px-3 py-10 text-center text-muted-foreground">No hay productos en este recorte. Probá quitar un filtro.</td></tr>}
          </tbody>
        </table>
      </div>
      {skuCount > rows.length && (
        <p className="mt-2 text-[11px] text-muted-foreground">
          La tabla muestra una muestra de {nf.format(rows.length)} SKUs. Exportar orden descarga hasta {nf.format(skuCount)} del recorte.
        </p>
      )}
    </div>
  );
}

function SkuDrawer({ row, onClose }: { row: Calc; onClose: () => void }) {
  const facts: [string, string][] = [
    ["Venta diaria promedio", `${nf.format(row.sku.sales_30)} vendidas en 30 días = ${dec(row.avg_daily)} por día`],
    [`Lo que se vende en ${HORIZON_DAYS} días`, `${dec(row.avg_daily)} × ${HORIZON_DAYS} = ${dec(row.demand_horizon)}`],
    ["Lo que se vende mientras llega", `${dec(row.avg_daily)} × ${row.sku.lead_time_days} días de entrega = ${dec(row.demand_lead)}`],
    ["Reserva de seguridad", nf.format(row.sku.safety_stock)],
    ["Stock objetivo", `${dec(row.demand_horizon)} + ${dec(row.demand_lead)} + ${nf.format(row.sku.safety_stock)} = ${dec(row.stock_target)}`],
    ["Menos lo que ya tenés", `${dec(row.stock_target)} − ${nf.format(row.sku.stock)} = ${nf.format(row.recommended_quantity)}`],
  ];

  return (
    <div className="fixed inset-0 z-[60] flex justify-end bg-ops-overlay" onClick={onClose}>
      <aside role="dialog" aria-modal="true" aria-label={`Detalle de ${row.sku.product_name}`} onClick={(event) => event.stopPropagation()} className="h-full w-full max-w-[460px] overflow-y-auto border-l border-ops-border bg-background p-5 shadow-2xl">
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
          <div className="min-w-0">
            <div className="text-xs tabular-nums text-ops-accent">SKU {row.sku.barcode}</div>
            <h2 className="mt-1 font-display text-xl font-semibold">{row.sku.product_name}</h2>
            <p className="mt-1 text-xs text-muted-foreground">{row.sku.category} · {row.sku.supplier}</p>
          </div>
          <button type="button" aria-label="Cerrar detalle" onClick={onClose} className="grid h-9 w-9 shrink-0 place-items-center rounded-md text-muted-foreground outline-none hover:bg-ops-row hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"><X className="h-5 w-5" /></button>
        </div>

        <div className="mt-5 rounded-lg border border-ops-accent/50 bg-ops-accent-soft p-4">
          <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">Cantidad a pedir</div>
          <div className="mt-1 font-display text-5xl font-semibold tabular-nums text-foreground">{nf.format(row.recommended_quantity)}</div>
          <div className="mt-1 text-xs text-muted-foreground">unidades para cubrir los próximos {HORIZON_DAYS} días</div>
        </div>

        <div className="mt-3 grid grid-cols-3 gap-3">
          {[["Prioridad", PRIORITY_LABEL[row.priority]], ["Cobertura", row.coverage_days >= 999 ? "sin venta" : `${dec(row.coverage_days)} d`], ["Valor estimado", money(row.estimated_purchase_value)]].map(([label, amount]) => (
            <div key={label} className="rounded-lg border border-ops-border bg-ops-panel p-3"><div className="text-[10px] uppercase tracking-[0.08em] text-muted-foreground">{label}</div><div className="mt-1 font-display text-base font-semibold tabular-nums">{amount}</div></div>
          ))}
        </div>

        <div className="mt-3"><HealthChips row={row} /></div>

        <div className="mt-5 overflow-hidden rounded-lg border border-ops-border">
          <div className="border-b border-ops-border bg-ops-panel px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">Cómo se llega a esa cantidad</div>
          <dl className="divide-y divide-ops-border">
            {facts.map(([label, formula]) => (
              <div key={label} className="grid grid-cols-[minmax(0,1fr)_auto] gap-4 px-4 py-3 text-xs"><dt className="min-w-0 text-muted-foreground">{label}</dt><dd className="text-right tabular-nums text-foreground">{formula}</dd></div>
            ))}
          </dl>
        </div>

        <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">
          La cobertura es el stock dividido por la venta diaria de los últimos 30 días, no una proyección. Las alertas de salud avisan cuándo mirar el producto; no suman unidades a la cantidad a pedir.
        </p>
      </aside>
    </div>
  );
}
