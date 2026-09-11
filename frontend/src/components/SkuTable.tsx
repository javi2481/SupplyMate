import { useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronRight,
  Search,
  X,
} from "lucide-react";
import { tableScopeCaption } from "@/lib/data-source";
import { HEALTH_LABEL, dec, nf, type Calc } from "@/lib/supplymate";
import { HealthChips, PriorityCell, visibleHealth } from "@/components/HealthChips";

type SortKey = "product" | "stock" | "sales" | "coverage" | "order" | "priority" | "health";
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
}: {
  rows: Calc[];
  recorteToBuy: number;
  onOpen: (row: Calc) => void;
}) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<{ key: SortKey; direction: SortDirection }>({
    key: "order",
    direction: "desc",
  });
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
      .filter((entry) => entry.distance > 0 && entry.distance <= Math.max(1, Math.floor(token.length * 0.34)))
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
    const priorityRank = { Alta: 3, Media: 2, Baja: 1 } as const;
    const healthValue = (row: Calc) =>
      visibleHealth(row)
        .map((tag) => HEALTH_LABEL[tag])
        .join(" ") || "Saludable";
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
        <table className="w-full min-w-[760px] text-left text-xs">
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
                    className={`inline-flex items-center gap-1 outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus ${header.align === "right" ? "ml-auto" : ""}`}
                  >
                    {header.label}
                    <SortIcon column={header.key} active={sort.key} direction={sort.direction} />
                  </button>
                </th>
              ))}
              <th className="w-10 px-3 py-3">
                <span className="sr-only">Detalle</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ops-border">
            {displayedRows.map((row) => (
              <tr
                key={row.sku.barcode}
                onClick={() => onOpen(row)}
                className="cursor-pointer bg-background outline-none transition-colors hover:bg-ops-row focus-within:bg-ops-row"
              >
                <td className="px-5 py-3">
                  <div className="font-medium text-foreground">{row.sku.product_name}</div>
                  <div className="mt-0.5 text-[10px] tabular-nums text-muted-foreground">
                    {row.sku.barcode} · {row.sku.category}
                  </div>
                </td>
                <td className="px-3 py-3 text-right tabular-nums">{nf.format(row.sku.stock)}</td>
                <td className="px-3 py-3 text-right tabular-nums text-muted-foreground">
                  {nf.format(row.sku.sales_30)}
                </td>
                <td className="px-3 py-3 text-right tabular-nums text-muted-foreground">
                  {row.coverage_days >= 999 ? "sin venta" : `${dec(row.coverage_days)} d`}
                </td>
                <td className="px-3 py-3 text-right font-semibold tabular-nums text-ops-accent">
                  {nf.format(row.recommended_quantity)}
                </td>
                <td className="px-3 py-3">
                  <PriorityCell row={row} />
                </td>
                <td className="px-3 py-3">
                  <HealthChips row={row} />
                </td>
                <td className="px-3 py-3">
                  <button
                    type="button"
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
            ))}
            {displayedRows.length === 0 && (
              <tr>
                <td colSpan={8} className="px-5 py-12 text-center text-muted-foreground">
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
