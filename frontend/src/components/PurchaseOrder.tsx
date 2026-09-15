import { useEffect, useState } from "react";
import { ArrowLeft, Download, Trash2, X } from "lucide-react";
import {
  ALL_CART_CSV_COLUMNS,
  CART_CSV_COLUMN_DEFS,
  DEFAULT_CART_CSV_COLUMNS,
  loadCartCsvColumns,
  type CartCsvColumnId,
} from "@/lib/cart";
import { money, nf, type Calc } from "@/lib/supplymate";

export function PurchaseOrder({
  rows,
  labels,
  units,
  value,
  skuCount,
  onExportAndFinish,
  onBack,
  editable = false,
  onChangeQty,
  onRemoveLine,
}: {
  rows: Calc[];
  labels: string[];
  units: number;
  value: number;
  skuCount: number;
  onExportAndFinish: (columns: CartCsvColumnId[]) => void;
  onBack: () => void;
  editable?: boolean;
  onChangeQty?: (productId: string, qty: number) => void;
  onRemoveLine?: (productId: string) => void;
}) {
  const [exportOpen, setExportOpen] = useState(false);
  const [columns, setColumns] = useState<CartCsvColumnId[]>(DEFAULT_CART_CSV_COLUMNS);

  useEffect(() => {
    if (!exportOpen) return;
    setColumns(loadCartCsvColumns());
  }, [exportOpen]);

  function toggleColumn(id: CartCsvColumnId) {
    setColumns((prev) => (prev.includes(id) ? prev.filter((col) => col !== id) : [...prev, id]));
  }

  function confirmExport() {
    if (columns.length === 0) return;
    onExportAndFinish(columns);
    setExportOpen(false);
  }

  return (
    <div className="min-h-0 flex-1 overflow-y-auto p-4 lg:p-5">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
        <div className="min-w-0">
          <h2 className="truncate font-display text-lg font-semibold">Revisar orden de compra</h2>
          <p className="text-xs text-muted-foreground">
            {editable
              ? "Podés ajustar las cantidades antes de exportar y terminar."
              : "El recorte queda congelado en esta vista."}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex h-9 items-center gap-2 rounded-md border border-ops-border px-3 text-xs font-semibold text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver a Explorar
          </button>
          <button
            type="button"
            onClick={() => setExportOpen(true)}
            disabled={rows.length === 0}
            className="inline-flex h-9 items-center gap-2 rounded-md bg-ops-accent px-3 text-xs font-semibold text-ops-accent-foreground outline-none hover:bg-ops-accent-hover focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-40"
          >
            <Download className="h-4 w-4" />
            Exportar y terminar
          </button>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-ops-border bg-ops-panel p-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
          {editable ? "Pedido" : "Recorte congelado"}
        </div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {labels
            .filter((label) => label !== "A comprar")
            .map((label) => (
              <span
                key={label}
                className="rounded-full border border-ops-accent/50 bg-ops-accent-soft px-2 py-0.5 text-[11px] text-ops-accent"
              >
                {label}
              </span>
            ))}
          {labels.filter((label) => label !== "A comprar").length === 0 && (
            <span className="text-xs text-muted-foreground">Inventario completo</span>
          )}
        </div>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-3">
        {(
          [
            ["Productos", nf.format(skuCount)],
            ["Unidades", nf.format(units)],
            ["Valor estimado", money(value)],
          ] as const
        ).map(([label, amount]) => (
          <div key={label} className="rounded-lg border border-ops-border bg-ops-panel p-3">
            <div className="text-[10px] uppercase text-muted-foreground">{label}</div>
            <div className="mt-1 font-display text-lg font-semibold tabular-nums">{amount}</div>
          </div>
        ))}
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-ops-border">
        <table className="w-full text-xs">
          <thead className="bg-ops-panel text-left text-[10px] uppercase text-muted-foreground">
            <tr>
              <th className="px-3 py-2.5">Producto</th>
              <th className="px-3 py-2.5">Proveedor</th>
              <th className="px-3 py-2.5 text-right">Cantidad</th>
              <th className="px-3 py-2.5 text-right">Valor</th>
              {editable ? (
                <th className="px-3 py-2.5 text-right">
                  <span className="sr-only">Quitar</span>
                </th>
              ) : null}
            </tr>
          </thead>
          <tbody className="divide-y divide-ops-border">
            {rows.map((row) => {
              const productId = row.sku.product_id;
              const suggested = row.suggested_quantity;
              return (
                <tr key={row.sku.barcode || productId} className="hover:bg-ops-row">
                  <td className="px-3 py-3">
                    <div className="font-medium">{row.sku.product_name}</div>
                    <div className="text-[10px] text-muted-foreground">{row.sku.barcode}</div>
                  </td>
                  <td className="px-3 py-3 text-muted-foreground">{row.sku.supplier}</td>
                  <td className="px-3 py-3 text-right">
                    {editable && onChangeQty ? (
                      <div className="inline-flex flex-col items-end gap-0.5">
                        <label className="sr-only" htmlFor={`qty-${productId}`}>
                          Cantidad a pedir de {row.sku.product_name}
                        </label>
                        <input
                          id={`qty-${productId}`}
                          type="text"
                          inputMode="numeric"
                          autoComplete="off"
                          value={row.recommended_quantity}
                          onChange={(event) => {
                            const digits = event.target.value.replace(/\D/g, "");
                            if (digits === "") return;
                            const n = Number(digits);
                            if (Number.isInteger(n)) onChangeQty(productId, n);
                          }}
                          className="h-8 w-20 rounded-md border border-ops-border bg-background px-2 text-right text-xs font-semibold tabular-nums outline-none focus:border-ops-accent focus:ring-2 focus:ring-ops-focus"
                        />
                        {suggested != null && (
                          <span className="text-[10px] text-muted-foreground">
                            Sugerido: {nf.format(suggested)}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="font-semibold tabular-nums">
                        {nf.format(row.recommended_quantity)}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums">
                    {money(row.estimated_purchase_value)}
                  </td>
                  {editable ? (
                    <td className="px-3 py-3 text-right">
                      <button
                        type="button"
                        aria-label={`Quitar ${row.sku.product_name} del pedido`}
                        onClick={() => onRemoveLine?.(productId)}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground outline-none hover:bg-ops-accent-soft hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  ) : null}
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={editable ? 5 : 4} className="px-3 py-10 text-center text-muted-foreground">
                  {editable
                    ? "El pedido está vacío. Agregá productos desde Explorar."
                    : "No hay productos en este recorte. Probá quitar un filtro."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {skuCount > rows.length && (
        <p className="mt-2 text-[11px] text-muted-foreground">
          La tabla muestra una muestra de {nf.format(rows.length)} SKUs. Exportar descarga hasta{" "}
          {nf.format(skuCount)} del recorte.
        </p>
      )}

      {exportOpen ? (
        <div
          className="fixed inset-0 z-[60] grid place-items-center bg-ops-overlay p-4"
          onClick={() => setExportOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="oc-export-title"
            onClick={(event) => event.stopPropagation()}
            className="w-full max-w-md rounded-lg border border-ops-border bg-background p-4 shadow-2xl"
          >
            <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
              <div>
                <h3 id="oc-export-title" className="font-display text-base font-semibold">
                  Columnas del CSV
                </h3>
                <p className="mt-1 text-xs text-muted-foreground">
                  Elegí qué atributos exportar. Se descarga el pedido y se vacía el carrito.
                </p>
              </div>
              <button
                type="button"
                aria-label="Cerrar"
                onClick={() => setExportOpen(false)}
                className="grid h-8 w-8 place-items-center rounded-md text-muted-foreground outline-none hover:bg-ops-row hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setColumns([...DEFAULT_CART_CSV_COLUMNS])}
                className="rounded-md border border-ops-border px-2 py-1 text-[11px] text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
              >
                Solo barcode + cantidad
              </button>
              <button
                type="button"
                onClick={() => setColumns([...ALL_CART_CSV_COLUMNS])}
                className="rounded-md border border-ops-border px-2 py-1 text-[11px] text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
              >
                Todas
              </button>
            </div>

            <fieldset className="mt-3 space-y-2">
              <legend className="sr-only">Atributos a exportar</legend>
              {CART_CSV_COLUMN_DEFS.map((col) => (
                <label
                  key={col.id}
                  className="flex cursor-pointer items-center gap-2 rounded-md border border-ops-border px-3 py-2 text-sm hover:border-ops-accent"
                >
                  <input
                    type="checkbox"
                    checked={columns.includes(col.id)}
                    onChange={() => toggleColumn(col.id)}
                    className="h-4 w-4 accent-[hsl(var(--ops-accent))]"
                  />
                  <span>{col.label}</span>
                  <span className="ml-auto text-[10px] tabular-nums text-muted-foreground">{col.header}</span>
                </label>
              ))}
            </fieldset>

            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setExportOpen(false)}
                className="inline-flex h-9 items-center rounded-md border border-ops-border px-3 text-xs font-semibold text-muted-foreground outline-none hover:border-ops-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ops-focus"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={confirmExport}
                disabled={columns.length === 0}
                className="inline-flex h-9 items-center gap-2 rounded-md bg-ops-accent px-3 text-xs font-semibold text-ops-accent-foreground outline-none hover:bg-ops-accent-hover focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-40"
              >
                <Download className="h-4 w-4" />
                Exportar CSV
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
