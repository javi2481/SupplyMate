import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  BarChart3,
  Box,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Download,
  Loader2,
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
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  API_URL,
  fetchReplenishment,
  fetchSlice,
  postChat,
  purchaseListCsvUrl,
  type InventoryDashboard,
} from "@/lib/api";
import {
  HEALTH_LABEL,
  HORIZON_DAYS,
  apiHealthFromUi,
  dec,
  enrichWithRecommendation,
  money,
  nf,
  rowFromPurchaseItem,
  type Calc,
  type HealthTag,
} from "@/lib/supplymate";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "SupplyMate · Operación de reposición" },
      {
        name: "description",
        content: "Panel operativo para decidir cuánto comprar en los próximos 7 días.",
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
type Mode = "chat" | "explore" | "po";

const CHIPS = ["¿Qué productos debería comprar?", "¿Cuánto pedir de 6033436?", "Riesgo de quiebre"];
const HEALTH_FILTERS: HealthTag[] = ["riesgo_quiebre", "sin_stock", "sobrestock", "cobertura_baja"];
const BUY_QUERY = "¿Qué productos debería comprar?";
const LIST_LIMIT = 50;

const SEED: Thread[] = [
  {
    id: "t1",
    title: "Qué comprar esta semana",
    messages: [
      {
        id: 1,
        role: "assistant",
        text: `Listo para revisar la reposición de los próximos ${HORIZON_DAYS} días con el catálogo real. Las cantidades salen del motor FastAPI.`,
      },
    ],
  },
  { id: "t2", title: "Quiebres Pañales Talle M", messages: [] },
  { id: "t3", title: "Revisión sobrestock Nutrición", messages: [] },
];

const healthIcon: Record<HealthTag, typeof AlertTriangle> = {
  riesgo_quiebre: AlertTriangle,
  sin_stock: CircleAlert,
  sobrestock: Box,
  cobertura_baja: BarChart3,
};

function Index() {
  const [threads, setThreads] = useState<Thread[]>(SEED);
  const [activeId, setActiveId] = useState("t1");
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"explore" | "po">("explore");
  const [mobileView, setMobileView] = useState<Mode>("explore");
  const [health, setHealth] = useState<HealthTag[]>([]);
  const [cats, setCats] = useState<string[]>([]);
  const [recommendedOnly, setRecommendedOnly] = useState(false);
  const [open, setOpen] = useState<Calc | null>(null);
  const [scope, setScope] = useState<{ health: HealthTag[]; cats: string[]; recommendedOnly: boolean } | null>(null);
  const [railCollapsed, setRailCollapsed] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);

  const [rows, setRows] = useState<Calc[]>([]);
  const [dashboard, setDashboard] = useState<InventoryDashboard | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chatBusy, setChatBusy] = useState(false);
  const [online, setOnline] = useState(false);

  const active = threads.find((thread) => thread.id === activeId) ?? threads[0];

  const loadSlice = useCallback(async (healthTags: HealthTag[], categoryFilter: string[]) => {
    setLoading(true);
    setError(null);
    try {
      const slice = await fetchSlice({
        category: categoryFilter.length ? categoryFilter : undefined,
        health_bucket: apiHealthFromUi(healthTags).length
          ? apiHealthFromUi(healthTags)
          : undefined,
        limit: LIST_LIMIT,
      });
      setDashboard(slice.dashboard);
      setRows(slice.purchase_list.map(rowFromPurchaseItem));
      const fromDash = (slice.dashboard.by_category ?? []).map((c) => c.category).filter(Boolean);
      setCategories((prev) => {
        const merged = new Set([...prev, ...fromDash, ...categoryFilter]);
        return [...merged].sort((a, b) => a.localeCompare(b, "es"));
      });
      setOnline(true);
    } catch (err) {
      setOnline(false);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSlice(health, cats);
  }, [health, cats, loadSlice]);

  const displayRows = useMemo(() => {
    return rows.filter((row) => {
      if (recommendedOnly && row.recommended_quantity <= 0) return false;
      if (health.length === 0) return true;
      return health.some(
        (tag) => (tag === "sin_stock" && row.stock === 0) || row.health.includes(tag),
      );
    });
  }, [rows, health, recommendedOnly]);

  const poRows = useMemo(() => {
    const current = scope ?? { health, cats, recommendedOnly };
    return rows.filter((row) => {
      if (row.recommended_quantity <= 0) return false;
      if (current.recommendedOnly === false && current.health.length === 0 && current.cats.length === 0) {
        return true;
      }
      if (current.health.length > 0) {
        const ok =
          current.health.some((tag) => row.health.includes(tag)) ||
          (current.health.includes("sin_stock") && row.stock === 0);
        if (!ok) return false;
      }
      if (current.cats.length > 0 && !current.cats.includes(row.category)) return false;
      return true;
    });
  }, [scope, health, cats, recommendedOnly, rows]);

  const kpis = [
    {
      label: "Productos",
      value: nf.format(dashboard?.skus ?? displayRows.length),
      detail: recommendedOnly ? "con compra sugerida" : "en alcance API",
      icon: Box,
    },
    {
      label: "Riesgo de quiebre",
      value: nf.format(dashboard?.stockout_risk ?? displayRows.filter((r) => r.health.includes("riesgo_quiebre")).length),
      detail: "requieren atención",
      icon: AlertTriangle,
    },
    {
      label: "Sin stock / bajo",
      value: nf.format(dashboard?.understock ?? displayRows.filter((r) => r.stock === 0).length),
      detail: "understock en dashboard",
      icon: CircleAlert,
    },
    {
      label: "Unidades sugeridas",
      value: nf.format(displayRows.reduce((sum, row) => sum + row.recommended_quantity, 0)),
      detail: `top ${LIST_LIMIT} · ${HORIZON_DAYS} días`,
      icon: PackageCheck,
    },
  ];

  async function send(text: string) {
    const query = text.trim();
    if (!query || chatBusy) return;
    setInput("");
    const userId = Date.now();
    setThreads((previous) =>
      previous.map((thread) =>
        thread.id !== activeId
          ? thread
          : {
              ...thread,
              title: thread.messages.length === 0 ? query.slice(0, 34) : thread.title,
              messages: [...thread.messages, { id: userId, role: "user" as const, text: query }],
            },
      ),
    );
    setChatBusy(true);
    try {
      const res = await postChat(query, {
        categories: cats,
        health_buckets: apiHealthFromUi(health),
      });
      setThreads((previous) =>
        previous.map((thread) =>
          thread.id !== activeId
            ? thread
            : {
                ...thread,
                messages: [
                  ...thread.messages,
                  { id: Date.now() + 1, role: "assistant" as const, text: res.answer },
                ],
              },
        ),
      );
      if (res.purchase_list?.length) {
        setRows(res.purchase_list.map(rowFromPurchaseItem));
      }
      if (res.dashboard) setDashboard(res.dashboard);
      setOnline(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
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
                    text: `No pude consultar la API (${API_URL}). ${msg}`,
                  },
                ],
              },
        ),
      );
    } finally {
      setChatBusy(false);
    }
    if (query.toLowerCase() === BUY_QUERY.toLowerCase()) {
      setRecommendedOnly(true);
      setHealth([]);
      setCats([]);
    }
    setMode("explore");
    setMobileView("explore");
  }

  function newThread() {
    const id = `t${Date.now()}`;
    setThreads((previous) => [{ id, title: "Nueva conversación", messages: [] }, ...previous]);
    setActiveId(id);
    setMobileView("chat");
    setMobileMenu(false);
  }

  function exportCsv() {
    const current = scope ?? { health, cats, recommendedOnly };
    window.open(
      purchaseListCsvUrl({
        category: current.cats.length ? current.cats : undefined,
        health_bucket: apiHealthFromUi(current.health).length
          ? apiHealthFromUi(current.health)
          : undefined,
        limit: 100,
      }),
      "_blank",
    );
  }

  async function openDetail(row: Calc) {
    setOpen(row);
    try {
      const rec = await fetchReplenishment(row.product_id);
      setOpen(enrichWithRecommendation(row, rec));
    } catch {
      /* keep list row if detail fails */
    }
  }

  const units = poRows.reduce((sum, row) => sum + row.recommended_quantity, 0);
  const value = poRows.reduce((sum, row) => sum + row.estimated_purchase_value, 0);

  const rail = (
    <aside className={`${railCollapsed ? "w-[72px]" : "w-[72px] xl:w-[248px]"} flex h-full shrink-0 flex-col border-r border-ops-border bg-ops-panel transition-[width] duration-200`}>
      <div className="grid h-16 grid-cols-[minmax(0,1fr)_auto] items-center gap-2 border-b border-ops-border px-4">
        <div className="flex min-w-0 items-center gap-3">
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-ops-accent text-ops-accent-foreground"><Box className="h-4 w-4" /></div>
          {!railCollapsed && <div className="hidden min-w-0 xl:block"><div className="truncate font-display text-base font-semibold text-foreground">SupplyMate</div><div className="truncate text-[11px] text-muted-foreground">Reposición · 7 días</div></div>}
        </div>
        <button type="button" aria-label={railCollapsed ? "Expandir menú" : "Reducir menú"} onClick={() => setRailCollapsed((v) => !v)} className="hidden h-8 w-8 shrink-0 place-items-center rounded-md text-muted-foreground outline-none hover:bg-ops-row hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-accent md:grid">
          {railCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
      </div>
      <div className="p-3">
        <button type="button" onClick={newThread} className="flex h-9 w-full items-center justify-center gap-2 rounded-md bg-ops-accent px-3 text-xs font-semibold text-ops-accent-foreground outline-none hover:bg-ops-accent-hover focus-visible:ring-2 focus-visible:ring-ops-focus">
          <Plus className="h-4 w-4 shrink-0" />{!railCollapsed && <span className="hidden xl:inline">Nueva conversación</span>}
        </button>
      </div>
      <nav aria-label="Conversaciones" className="flex-1 overflow-y-auto px-3">
        {!railCollapsed && <div className="mb-2 hidden px-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground xl:block">Recientes</div>}
        <div className="space-y-1">
          {threads.map((thread) => (
            <button key={thread.id} type="button" title={thread.title} onClick={() => { setActiveId(thread.id); setMobileMenu(false); }} className={`flex h-10 w-full items-center gap-3 rounded-md px-3 text-left text-xs outline-none focus-visible:ring-2 focus-visible:ring-ops-accent ${thread.id === activeId ? "bg-ops-row text-foreground" : "text-muted-foreground hover:bg-ops-row hover:text-foreground"}`}>
              <MessageSquareText className={`h-4 w-4 shrink-0 ${thread.id === activeId ? "text-ops-accent" : ""}`} />
              {!railCollapsed && <span className="hidden truncate xl:inline">{thread.title}</span>}
            </button>
          ))}
        </div>
      </nav>
      <div className="border-t border-ops-border p-4">
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground"><CheckCircle2 className="h-4 w-4 shrink-0 text-ops-ok" />{!railCollapsed && <span className="hidden xl:inline">API {API_URL.replace("http://", "")}</span>}</div>
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
              <div className="min-w-0">
                <h1 className="truncate font-display text-lg font-semibold">SupplyMate · Operación</h1>
                <p className="truncate text-[11px] text-muted-foreground">
                  Catálogo real · {nf.format(dashboard?.skus ?? 0)} SKUs · top {LIST_LIMIT} · horizonte {HORIZON_DAYS} días
                </p>
              </div>
            </div>
            <div className={`flex shrink-0 items-center gap-2 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase ${online ? "border-ops-ok/30 bg-ops-ok-soft text-ops-ok" : "border-ops-danger/40 bg-ops-danger/10 text-ops-danger"}`}>
              <span className={`h-1.5 w-1.5 rounded-full ${online ? "bg-ops-ok" : "bg-ops-danger"}`} />
              {online ? "API en línea" : "API offline"}
            </div>
          </header>

          <div className="grid h-12 shrink-0 grid-cols-3 border-b border-ops-border bg-ops-panel md:hidden">
            {(["chat", "explore", "po"] as Mode[]).map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => {
                  setMobileView(item);
                  if (item !== "chat") {
                    setMode(item);
                    if (item === "po") setScope({ health, cats, recommendedOnly });
                  }
                }}
                className={`border-b-2 text-xs font-semibold outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ops-accent ${mobileView === item ? "border-ops-accent text-foreground" : "border-transparent text-muted-foreground"}`}
              >
                {item === "chat" ? "Consulta" : item === "explore" ? "Explorar" : "Armar OC"}
              </button>
            ))}
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
                {active?.messages.length === 0 && <p className="text-sm text-muted-foreground">Escribí una consulta. Las cantidades vienen de FastAPI.</p>}
                {active?.messages.map((message) => (
                  <div key={message.id} className={`whitespace-pre-line rounded-lg px-3.5 py-3 leading-relaxed ${message.role === "user" ? "ml-auto max-w-[88%] border border-ops-accent/50 bg-ops-accent-soft" : "max-w-[94%] border border-ops-border bg-ops-panel"}`}>
                    {message.role === "assistant" && <div className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-ops-ok"><CheckCircle2 className="h-3.5 w-3.5" />SupplyMate</div>}{message.text}
                  </div>
                ))}
                {chatBusy && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" /> Consultando motor…
                  </div>
                )}
              </div>
              <div className="border-t border-ops-border bg-ops-panel p-4">
                <div className="mb-2 flex flex-wrap gap-1.5">{CHIPS.slice(1).map((chip) => <button key={chip} type="button" onClick={() => void send(chip)} className="rounded-md border border-ops-border bg-background px-2.5 py-1.5 text-[11px] text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus">{chip}</button>)}</div>
                <form onSubmit={(event) => { event.preventDefault(); void send(input); }} className="grid grid-cols-[minmax(0,1fr)_auto] gap-2">
                  <div className="relative min-w-0"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><input value={input} onChange={(event) => setInput(event.target.value)} aria-label="Consulta de reposición" placeholder="Escribí una consulta…" className="h-10 w-full rounded-md border border-ops-border bg-background pl-9 pr-3 text-sm outline-none placeholder:text-muted-foreground focus:border-ops-accent focus:ring-2 focus:ring-ops-focus" /></div>
                  <button type="submit" aria-label="Enviar consulta" disabled={chatBusy} className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-ops-accent text-ops-accent-foreground outline-none hover:bg-ops-accent-hover focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-50"><Send className="h-4 w-4" /></button>
                </form>
              </div>
            </section>

            <section className={`${mobileView !== "chat" ? "flex" : "hidden"} min-h-0 min-w-0 flex-col bg-background md:flex`}>
              <div className="hidden h-12 shrink-0 grid-cols-2 border-b border-ops-border bg-ops-panel md:grid">
                {(["explore", "po"] as const).map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => {
                      setMode(item);
                      if (item === "po") setScope({ health, cats, recommendedOnly });
                    }}
                    className={`border-b-2 text-xs font-semibold outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ops-accent ${mode === item ? "border-ops-accent text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
                  >
                    {item === "explore" ? "Explorar" : "Armar OC"}
                  </button>
                ))}
              </div>
              {mode === "po" ? (
                <PurchaseOrder rows={poRows} scope={scope} units={units} value={value} onExport={exportCsv} />
              ) : (
                <div className="min-h-0 flex-1 overflow-y-auto">
                  {error && (
                    <div className="border-b border-ops-danger/40 bg-ops-danger/10 px-4 py-3 text-xs text-ops-danger">
                      No se pudo cargar el slice: {error}. ¿Está corriendo la API en {API_URL}?
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-3 p-4 lg:grid-cols-4 lg:p-5">
                    {kpis.map((kpi) => (
                      <div key={kpi.label} className="rounded-lg border border-ops-border bg-ops-panel p-3.5">
                        <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-2">
                          <div className="truncate text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">{kpi.label}</div>
                          <kpi.icon className="h-4 w-4 shrink-0 text-ops-accent" />
                        </div>
                        <div className="mt-2 font-display text-2xl font-semibold tabular-nums">{loading ? "…" : kpi.value}</div>
                        <div className="mt-0.5 text-[11px] text-muted-foreground">{kpi.detail}</div>
                      </div>
                    ))}
                  </div>
                  <div className="border-y border-ops-border bg-ops-panel px-4 py-3 lg:px-5">
                    <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground"><SlidersHorizontal className="h-3.5 w-3.5" />Filtros</div>
                    <div className="flex flex-wrap gap-1.5">
                      <button type="button" onClick={() => setRecommendedOnly((v) => !v)} className={`rounded-full border px-2.5 py-1 text-[11px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-ops-focus ${recommendedOnly ? "border-ops-accent bg-ops-accent-soft text-ops-accent" : "border-ops-border text-muted-foreground hover:border-ops-accent"}`}><ShoppingCart className="mr-1 inline h-3 w-3" />A comprar</button>
                      {HEALTH_FILTERS.map((tag) => {
                        const Icon = healthIcon[tag];
                        return (
                          <button
                            key={tag}
                            type="button"
                            onClick={() =>
                              setHealth((previous) =>
                                previous.includes(tag) ? previous.filter((item) => item !== tag) : [...previous, tag],
                              )
                            }
                            className={`rounded-full border px-2.5 py-1 text-[11px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-ops-focus ${health.includes(tag) ? "border-ops-accent bg-ops-accent-soft text-foreground" : "border-ops-border text-muted-foreground hover:border-ops-accent"}`}
                          >
                            <Icon className="mr-1 inline h-3 w-3" />
                            {HEALTH_LABEL[tag]}
                          </button>
                        );
                      })}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {categories.slice(0, 12).map((category) => (
                        <button
                          key={category}
                          type="button"
                          onClick={() =>
                            setCats((previous) =>
                              previous.includes(category)
                                ? previous.filter((item) => item !== category)
                                : [...previous, category],
                            )
                          }
                          className={`rounded-md border px-2.5 py-1 text-[11px] outline-none focus-visible:ring-2 focus-visible:ring-ops-focus ${cats.includes(category) ? "border-ops-accent text-ops-accent" : "border-ops-border text-muted-foreground hover:border-ops-accent"}`}
                        >
                          {category}
                        </button>
                      ))}
                    </div>
                  </div>
                  {loading ? (
                    <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" /> Cargando slice real…
                    </div>
                  ) : (
                    <SkuTable rows={displayRows} onOpen={(row) => void openDetail(row)} />
                  )}
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

function SkuTable({ rows, onOpen }: { rows: Calc[]; onOpen: (row: Calc) => void }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-xs">
        <thead className="sticky top-0 bg-ops-panel text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
          <tr>
            <th className="px-5 py-3">SKU / Producto</th>
            <th className="px-3 py-3 text-right">Stock</th>
            <th className="px-3 py-3 text-right">V30d</th>
            <th className="px-3 py-3 text-right">A comprar</th>
            <th className="px-3 py-3">Prioridad</th>
            <th className="px-3 py-3">Salud</th>
            <th className="w-10 px-3 py-3"><span className="sr-only">Detalle</span></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-ops-border">
          {rows.map((row) => (
            <tr
              key={row.product_id}
              onClick={() => onOpen(row)}
              className="cursor-pointer bg-background outline-none hover:bg-ops-row focus-within:bg-ops-row"
            >
              <td className="px-5 py-3">
                <div className="font-medium text-foreground">{row.product_name}</div>
                <div className="mt-0.5 text-[10px] tabular-nums text-muted-foreground">
                  {row.barcode} · {row.category}
                </div>
              </td>
              <td className="px-3 py-3 text-right tabular-nums">{nf.format(row.stock)}</td>
              <td className="px-3 py-3 text-right tabular-nums text-muted-foreground">{nf.format(row.sales_30)}</td>
              <td className="px-3 py-3 text-right font-semibold tabular-nums text-ops-accent">{nf.format(row.recommended_quantity)}</td>
              <td className={`px-3 py-3 font-medium ${row.priority === "Alta" ? "text-ops-danger" : row.priority === "Media" ? "text-ops-warn" : "text-muted-foreground"}`}>
                {row.priority}
              </td>
              <td className="px-3 py-3">
                <div className="flex flex-wrap gap-1">
                  {row.health.length === 0 ? (
                    <span className="inline-flex items-center gap-1 rounded-full border border-ops-ok/40 bg-ops-ok-soft px-2 py-0.5 text-[10px] text-ops-ok">
                      <CheckCircle2 className="h-3 w-3" />OK
                    </span>
                  ) : (
                    row.health.map((tag) => {
                      const Icon = healthIcon[tag];
                      return (
                        <span key={tag} className="inline-flex items-center gap-1 rounded-full border border-ops-border bg-ops-panel px-2 py-0.5 text-[10px] text-muted-foreground">
                          <Icon className="h-3 w-3" />
                          {HEALTH_LABEL[tag]}
                        </span>
                      );
                    })
                  )}
                </div>
              </td>
              <td className="px-3 py-3">
                <button
                  type="button"
                  aria-label={`Ver cálculo de ${row.product_name}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    onOpen(row);
                  }}
                  className="grid h-7 w-7 place-items-center rounded-md text-muted-foreground outline-none hover:bg-ops-panel hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={7} className="px-5 py-12 text-center text-muted-foreground">
                No hay productos para estos filtros.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function PurchaseOrder({
  rows,
  scope,
  units,
  value,
  onExport,
}: {
  rows: Calc[];
  scope: { health: HealthTag[]; cats: string[]; recommendedOnly: boolean } | null;
  units: number;
  value: number;
  onExport: () => void;
}) {
  return (
    <div className="min-h-0 flex-1 overflow-y-auto p-4 lg:p-5">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
        <div className="min-w-0">
          <h2 className="truncate font-display text-lg font-semibold">Orden de compra</h2>
          <p className="text-xs text-muted-foreground">CSV desde FastAPI · alcance al entrar en esta vista.</p>
        </div>
        <button
          type="button"
          onClick={onExport}
          disabled={rows.length === 0}
          className="inline-flex h-9 shrink-0 items-center gap-2 rounded-md bg-ops-accent px-3 text-xs font-semibold text-ops-accent-foreground outline-none hover:bg-ops-accent-hover focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-40"
        >
          <Download className="h-4 w-4" />
          Exportar CSV
        </button>
      </div>
      <div className="mt-4 rounded-lg border border-ops-border bg-ops-panel p-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">Alcance congelado</div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {[...(scope?.health ?? []).map((tag) => HEALTH_LABEL[tag]), ...(scope?.cats ?? [])].map((label) => (
            <span key={label} className="rounded-full border border-ops-accent/50 bg-ops-accent-soft px-2 py-0.5 text-[11px] text-ops-accent">
              {label}
            </span>
          ))}
          {(scope?.health.length ?? 0) + (scope?.cats.length ?? 0) === 0 && (
            <span className="text-xs text-muted-foreground">Catálogo completo (top lista)</span>
          )}
        </div>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-3">
        {[["Productos", nf.format(rows.length)], ["Unidades", nf.format(units)], ["Valor estimado", money(value)]].map(
          ([label, amount]) => (
            <div key={label} className="rounded-lg border border-ops-border bg-ops-panel p-3">
              <div className="text-[10px] uppercase text-muted-foreground">{label}</div>
              <div className="mt-1 font-display text-lg font-semibold tabular-nums">{amount}</div>
            </div>
          ),
        )}
      </div>
      <div className="mt-4 overflow-hidden rounded-lg border border-ops-border">
        <table className="w-full text-xs">
          <thead className="bg-ops-panel text-left text-[10px] uppercase text-muted-foreground">
            <tr>
              <th className="px-3 py-2.5">Producto</th>
              <th className="px-3 py-2.5">Proveedor</th>
              <th className="px-3 py-2.5 text-right">Cantidad</th>
              <th className="px-3 py-2.5 text-right">Valor</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ops-border">
            {rows.map((row) => (
              <tr key={row.product_id} className="hover:bg-ops-row">
                <td className="px-3 py-3">
                  <div className="font-medium">{row.product_name}</div>
                  <div className="text-[10px] text-muted-foreground">{row.barcode}</div>
                </td>
                <td className="px-3 py-3 text-muted-foreground">{row.supplier}</td>
                <td className="px-3 py-3 text-right font-semibold tabular-nums">{nf.format(row.recommended_quantity)}</td>
                <td className="px-3 py-3 text-right tabular-nums">{money(row.estimated_purchase_value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SkuDrawer({ row, onClose }: { row: Calc; onClose: () => void }) {
  const facts = [
    ["Promedio diario", `${row.sales_30} / 30 ≈ ${dec(row.avg_daily)}`],
    [`Demanda a ${HORIZON_DAYS} días`, `${dec(row.avg_daily)} × ${HORIZON_DAYS} = ${dec(row.demand_horizon)}`],
    ["Demanda durante entrega", `${dec(row.avg_daily)} × ${row.lead_time_days} = ${dec(row.demand_lead)}`],
    ["Stock objetivo", `${dec(row.demand_horizon)} + ${dec(row.demand_lead)} + ${row.safety_stock} = ${dec(row.stock_target)}`],
    ["Cantidad recomendada", `máx. 0, ${dec(row.stock_target)} − ${row.stock} = ${nf.format(row.recommended_quantity)}`],
  ];
  return (
    <div className="fixed inset-0 z-[60] flex justify-end bg-ops-overlay" onClick={onClose}>
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={`Detalle de ${row.product_name}`}
        onClick={(event) => event.stopPropagation()}
        className="h-full w-full max-w-[460px] overflow-y-auto border-l border-ops-border bg-background p-5 shadow-2xl"
      >
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
          <div className="min-w-0">
            <div className="text-xs tabular-nums text-ops-accent">SKU {row.barcode}</div>
            <h2 className="mt-1 font-display text-xl font-semibold">{row.product_name}</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              {row.category} · {row.supplier}
            </p>
          </div>
          <button
            type="button"
            aria-label="Cerrar detalle"
            onClick={onClose}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-md text-muted-foreground outline-none hover:bg-ops-row hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3">
          {[
            ["A comprar", nf.format(row.recommended_quantity)],
            ["Prioridad", row.priority],
            ["Cobertura", `${dec(Math.min(row.coverage_days, 999))} d`],
            ["Valor estimado", money(row.estimated_purchase_value)],
          ].map(([label, amount]) => (
            <div key={label} className="rounded-lg border border-ops-border bg-ops-panel p-3">
              <div className="text-[10px] uppercase tracking-[0.08em] text-muted-foreground">{label}</div>
              <div className="mt-1 font-display text-lg font-semibold tabular-nums">{amount}</div>
            </div>
          ))}
        </div>
        <div className="mt-5 overflow-hidden rounded-lg border border-ops-border">
          <div className="border-b border-ops-border bg-ops-panel px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
            Cálculo del motor determinístico
          </div>
          <dl className="divide-y divide-ops-border">
            {facts.map(([label, formula]) => (
              <div key={label} className="grid grid-cols-[minmax(0,1fr)_auto] gap-4 px-4 py-3 text-xs">
                <dt className="min-w-0 text-muted-foreground">{label}</dt>
                <dd className="text-right tabular-nums text-foreground">{formula}</dd>
              </div>
            ))}
          </dl>
        </div>
      </aside>
    </div>
  );
}
