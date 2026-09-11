import { ArrowLeft, Download } from "lucide-react";
import { money, nf, type Calc } from "@/lib/supplymate";

export function PurchaseOrder({
  rows,
  labels,
  units,
  value,
  skuCount,
  onExport,
  onBack,
}: {
  rows: Calc[];
  labels: string[];
  units: number;
  value: number;
  skuCount: number;
  onExport: () => void;
  onBack: () => void;
}) {
  return (
    <div className="min-h-0 flex-1 overflow-y-auto p-4 lg:p-5">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
        <div className="min-w-0">
          <h2 className="truncate font-display text-lg font-semibold">Revisar orden de compra</h2>
          <p className="text-xs text-muted-foreground">El recorte queda congelado en esta vista.</p>
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
            onClick={onExport}
            disabled={rows.length === 0}
            className="inline-flex h-9 items-center gap-2 rounded-md bg-ops-accent px-3 text-xs font-semibold text-ops-accent-foreground outline-none hover:bg-ops-accent-hover focus-visible:ring-2 focus-visible:ring-ops-focus disabled:opacity-40"
          >
            <Download className="h-4 w-4" />
            Exportar orden
          </button>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-ops-border bg-ops-panel p-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
          Recorte congelado
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
            </tr>
          </thead>
          <tbody className="divide-y divide-ops-border">
            {rows.map((row) => (
              <tr key={row.sku.barcode} className="hover:bg-ops-row">
                <td className="px-3 py-3">
                  <div className="font-medium">{row.sku.product_name}</div>
                  <div className="text-[10px] text-muted-foreground">{row.sku.barcode}</div>
                </td>
                <td className="px-3 py-3 text-muted-foreground">{row.sku.supplier}</td>
                <td className="px-3 py-3 text-right font-semibold tabular-nums">
                  {nf.format(row.recommended_quantity)}
                </td>
                <td className="px-3 py-3 text-right tabular-nums">
                  {money(row.estimated_purchase_value)}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={4} className="px-3 py-10 text-center text-muted-foreground">
                  No hay productos en este recorte. Probá quitar un filtro.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {skuCount > rows.length && (
        <p className="mt-2 text-[11px] text-muted-foreground">
          La tabla muestra una muestra de {nf.format(rows.length)} SKUs. Exportar orden descarga hasta{" "}
          {nf.format(skuCount)} del recorte.
        </p>
      )}
    </div>
  );
}
