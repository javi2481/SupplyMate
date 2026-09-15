import { useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Check,
  ChevronRight,
  Search,
  ShoppingCart,
  X,
} from "lucide-react";
import { tableScopeCaption } from "@/lib/data-source";
import { clampOrderQuantity } from "@/lib/cart";
import { HEALTH_LABEL, nf, type Calc } from "@/lib/supplymate";
import { HealthChips, visibleHealth } from "@/components/HealthChips";

type SortKey = "product" | "stock" | "sales" | "order" | "health";
type SortDirection = "asc" | "desc";

function normalizeSearch(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
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
      current[j] = Math.min(
        (current[j - 1] ?? 0) + 1,
        (previous[j] ?? 0) + 1,
        (previous[j - 1] ?? 0) + (a[i - 1] === b[j - 1] ? 0 : 1),
      );
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
  return normalizeSearch(
    [row.sku.product_name, row.sku.barcode, row.sku.category, row.sku.supplier].join(" "),
  ).split(" ");
}

function SortIcon({
  column,
  active,
  direction,
}: {
  column: SortKey;
  active: SortKey;
  direction: SortDirection;
}) {
  if (column !== active) return <ArrowUpDown className="h-3 w-3 opacity-55" />;
  return direction === "asc" ? (
    <ArrowUp className="h-3 w-3 text-ops-accent" />
  ) : (
    <ArrowDown className="h-3 w-3 text-ops-accent" />
  );
}

export function SkuTable({
  rows,
  recorteToBuy,
  onOpen,
  cartProductIds = [],
  onAddLine,
}: {
  rows: Calc[];
  recorteToBuy: number;
  onOpen: (row: Calc) => void;
  cartProductIds?: string[];
  onAddLine?: (row: Calc, qty: number) => void;
}) {
  const [query, setQuery] = useState("");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [rowHints, setRowHints] = useState<Record<string, string>>({});
  const [sort, setSort] = useState<{ key: SortKey; direction: SortDirection }>({
    key: "order",
    direction: "desc",
  });
  const inCart = useMemo(() => new Set(cartProductIds), [cartProductIds]);
  const normalizedQuery = normalizeSearch(query);
  const queryTokens = normalizedQuery.split(" ").filter(Boolean);

  const vocabulary = useMemo(() => {
    const entries = new Map<string, string>();
    rows.forEach((row) => {
      [row.sku.product_name, row.sku.supplier].forEach((label) => {
        normalizeSearch(label)
          .split(" ")
          .filter((word) => word.length > 2)
          .forEach((word) => {
            if (!entries.has(word)) entries.set(word, word.charAt(0).toUpperCase() + word.slice(1));
          });
      });
      normalizeSearch(row.sku.category)
        .split(" ")
        .filter((word) => word.length > 2)
        .forEach((word) => entries.set(word, row.sku.category));
    });
    return Array.from(entries, ([word, label]) => ({ word, label }));
  }, [rows]);

  const correction = useMemo(() => {
    const token = queryTokens[0];
    if (queryTokens.length !== 1 || !token || token.length < 4) return null;
    if (vocabulary.some((entry) => singular(entry.word) === singular(token))) return null;
    const match = vocabulary
      .map((entry) => ({ ...entry, distance: distance(singular(token), singular(entry.word)) }))
      .filter(
        (entry) =>
          entry.distance > 0 && entry.distance <= Math.max(1, Math.floor(token.length * 0.34)),
      )
      .sort((a, b) => a.distance - b.distance)[0];
    return match?.label ?? null;
  }, [queryTokens, vocabulary]);

  const displayedRows = useMemo(() => {
    const filtered =
      queryTokens.length === 0
        ? rows
        : rows.filter((row) => {
            const words = rowSearchWords(row);
            return queryTokens.every((token) => words.some((word) => fuzzyTokenMatch(token, word)));
          });
    const healthValue = (row: Calc) =>
      visibleHealth(row)
        .map((tag) => HEALTH_LABEL[tag])
        .join(" ") || "Saludable";
    const valueFor = (row: Calc): string | number => {
      if (sort.key === "product") return row.sku.product_name;
      if (sort.key === "stock") return row.sku.stock;
      if (sort.key === "sales") return row.sku.sales_30;
      if (sort.key === "order") return row.recommended_quantity;
      return healthValue(row);
    };
    return [...filtered].sort((a, b) => {
      const aValue = valueFor(a);
      const bValue = valueFor(b);
      const result =
        typeof aValue === "number" && typeof bValue === "number"
          ? aValue - bValue
          : String(aValue).localeCompare(String(bValue), "es");
      return sort.direction === "asc" ? result : -result;
    });
  }, [queryTokens, rows, sort]);

  function changeSort(key: SortKey) {
    setSort((current) =>
      current.key === key
        ? { key, direction: current.direction === "asc" ? "desc" : "asc" }
        : { key, direction: key === "product" || key === "health" ? "asc" : "desc" },
    );
  }

  function setDraft(productId: string, value: string) {
    // Digits only — text field (no number spinners); empty allowed while typing.
    const digits = value.replace(/\D/g, "");
    setDrafts((prev) => ({ ...prev, [productId]: digits }));
    setRowHints((prev) => {
      if (!prev[productId]) return prev;
      const next = { ...prev };
      delete next[productId];
      return next;
    });
  }

  function confirmRow(row: Calc) {
    if (!onAddLine) return;
    const productId = row.sku.product_id;
    const raw = drafts[productId] ?? "";
    const qty = clampOrderQuantity(raw === "" ? raw : Number(raw));
    if (qty == null) {
      setRowHints((prev) => ({ ...prev, [productId]: "Indicá una cantidad" }));
      return;
    }
    onAddLine(row, qty);
    // Keep the confirmed qty visible in A pedir (do not clear the field).
    setDrafts((prev) => ({ ...prev, [productId]: String(qty) }));
    setRowHints((prev) => {
      const next = { ...prev };
      delete next[productId];
      return next;
    });
  }

  const headers: { key: SortKey; label: string; align?: "right" }[] = [
    { key: "product", label: "SKU / Producto" },
    { key: "stock", label: "Stock", align: "right" },
    { key: "sales", label: "Ventas 30d", align: "right" },
    { key: "order", label: "A pedir", align: "right" },
    { key: "health", label: "Salud" },
  ];

  const caption = tableScopeCaption({
    displayed: displayedRows.length,
    pageRows: rows.length,
    recorteToBuy,
    searching: queryTokens.length > 0,
  });

  const colCount = onAddLine ? 7 : 6;

  return (
    <div>
      <div className="border-b border-ops-border bg-background px-4 py-3 lg:px-5">
        <div className="flex flex-wrap items-center gap-2">
          <label className="relative min-w-[220px] flex-1">
            <span className="sr-only">Buscar productos</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar producto, SKU, categoría o proveedor"
              className="h-9 w-full rounded-md border border-ops-border bg-ops-panel pl-9 pr-9 text-xs text-foreground outline-none placeholder:text-muted-foreground focus:border-ops-accent focus:ring-2 focus:ring-ops-focus"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery("")}
                aria-label="Limpiar búsqueda"
                tabIndex={-1}
                className="absolute right-1.5 top-1/2 grid h-6 w-6 -translate-y-1/2 place-items-center rounded text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </label>
          <span className="text-[11px] tabular-nums text-muted-foreground">
            {nf.format(caption.shown)} de {nf.format(caption.total)} {caption.noun}
          </span>
        </div>
        {correction && displayedRows.length > 0 && (
          <p className="mt-2 text-[11px] text-muted-foreground">
            Mostrando resultados relacionados con{" "}
            <button
              type="button"
              onClick={() => setQuery(correction)}
              className="font-semibold text-ops-accent outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ops-focus"
            >
              “{correction}”
            </button>
            .
          </p>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-xs">
          <thead className="sticky top-0 bg-ops-panel text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
            <tr>
              {headers.map((header, index) => (
                <th
                  key={header.key}
                  className={`${index === 0 ? "px-5" : "px-3"} py-3 ${header.align === "right" ? "text-right" : ""}`}
                >
                  <button
                    type="button"
                    onClick={() => changeSort(header.key)}
                    aria-label={`Ordenar por ${header.label}`}
                    tabIndex={-1}
                    className={`inline-flex items-center gap-1 outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus ${header.align === "right" ? "ml-auto" : ""}`}
                  >
                    {header.label}
                    <SortIcon column={header.key} active={sort.key} direction={sort.direction} />
                  </button>
                </th>
              ))}
              {onAddLine ? (
                <th className="w-10 px-3 py-3">
                  <span className="sr-only">Agregar al pedido</span>
                </th>
              ) : null}
              <th className="w-10 px-3 py-3">
                <span className="sr-only">Detalle</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ops-border">
            {displayedRows.map((row) => {
              const productId = row.sku.product_id;
              const draft = drafts[productId] ?? "";
              const hint = rowHints[productId];
              const suggested = row.recommended_quantity;
              return (
                <tr
                  key={row.sku.barcode || productId}
                  onClick={() => onOpen(row)}
                  className="cursor-pointer bg-background outline-none transition-colors hover:bg-ops-row focus-within:bg-ops-row"
                >
                  <td className="px-5 py-3">
                    <div className="font-medium text-foreground">{row.sku.product_name}</div>
                    <div className="mt-0.5 text-[10px] tabular-nums text-muted-foreground">
                      {row.sku.barcode} · {row.sku.category}
                    </div>
                    {inCart.has(productId) && (
                      <div className="mt-1 inline-flex items-center gap-1 text-[10px] font-semibold text-ops-ok">
                        <Check className="h-3 w-3" />
                        En el pedido
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums">{nf.format(row.sku.stock)}</td>
                  <td className="px-3 py-3 text-right tabular-nums text-muted-foreground">
                    {nf.format(row.sku.sales_30)}
                  </td>
                  <td
                    className="px-3 py-3 text-right"
                    onMouseDown={(event) => event.stopPropagation()}
                    onClick={(event) => event.stopPropagation()}
                  >
                    {onAddLine ? (
                      <div className="inline-flex flex-col items-end gap-0.5">
                        <div className="inline-flex items-center gap-1.5">
                          <label className="sr-only" htmlFor={`order-qty-${productId}`}>
                            Cantidad a pedir de {row.sku.product_name}
                          </label>
                          <input
                            id={`order-qty-${productId}`}
                            type="text"
                            inputMode="numeric"
                            autoComplete="off"
                            value={draft}
                            placeholder="—"
                            onMouseDown={(event) => event.stopPropagation()}
                            onClick={(event) => event.stopPropagation()}
                            onChange={(event) => setDraft(productId, event.target.value)}
                            onKeyDown={(event) => {
                              event.stopPropagation();
                              if (event.key === "Enter") {
                                event.preventDefault();
                                confirmRow(row);
                              }
                            }}
                            className="h-8 w-16 rounded-md border border-ops-border bg-ops-panel px-2 text-right text-xs font-semibold tabular-nums outline-none placeholder:text-muted-foreground focus:border-ops-accent focus:ring-2 focus:ring-ops-focus"
                          />
                          <button
                            type="button"
                            tabIndex={-1}
                            onClick={() => setDraft(productId, String(suggested))}
                            className="text-[10px] text-muted-foreground outline-none hover:text-ops-accent focus-visible:ring-2 focus-visible:ring-ops-focus"
                            title="Usar cantidad sugerida"
                          >
                            sug. {nf.format(suggested)}
                          </button>
                        </div>
                        {hint ? <span className="text-[10px] text-ops-warn">{hint}</span> : null}
                      </div>
                    ) : (
                      <span className="font-semibold tabular-nums text-ops-accent">
                        {nf.format(suggested)}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <HealthChips row={row} />
                  </td>
                  {onAddLine ? (
                    <td
                      className="px-3 py-3"
                      onMouseDown={(event) => event.stopPropagation()}
                      onClick={(event) => event.stopPropagation()}
                    >
                      <button
                        type="button"
                        aria-label={`Agregar ${row.sku.product_name} al pedido`}
                        onClick={() => confirmRow(row)}
                        className="grid h-8 w-8 place-items-center rounded-md border border-ops-accent/50 bg-ops-accent-soft text-ops-accent outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
                      >
                        <ShoppingCart className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  ) : null}
                  <td className="px-3 py-3">
                    <button
                      type="button"
                      tabIndex={-1}
                      aria-label={`Ver cálculo de ${row.sku.product_name}`}
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
              );
            })}
            {displayedRows.length === 0 && (
              <tr>
                <td colSpan={colCount} className="px-5 py-12 text-center text-muted-foreground">
                  {query ? (
                    <span>
                      No encontramos productos para “{query}”.{" "}
                      <button
                        type="button"
                        onClick={() => setQuery("")}
                        className="font-semibold text-ops-accent outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ops-focus"
                      >
                        Limpiar búsqueda
                      </button>
                    </span>
                  ) : (
                    "No hay productos en este recorte. Probá quitar un filtro."
                  )}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
