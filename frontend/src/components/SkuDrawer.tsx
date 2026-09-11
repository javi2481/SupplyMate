import { X } from "lucide-react";
import { HealthChips } from "@/components/HealthChips";
import { HORIZON_DAYS, PRIORITY_LABEL, dec, money, nf, type Calc } from "@/lib/supplymate";

export function SkuDrawer({ row, onClose }: { row: Calc; onClose: () => void }) {
  const facts: [string, string][] = [
    [
      "Venta diaria promedio",
      `${nf.format(row.sku.sales_30)} vendidas en 30 días = ${dec(row.avg_daily)} por día`,
    ],
    [
      `Lo que se vende en ${HORIZON_DAYS} días`,
      `${dec(row.avg_daily)} × ${HORIZON_DAYS} = ${dec(row.demand_horizon)}`,
    ],
    [
      "Lo que se vende mientras llega",
      `${dec(row.avg_daily)} × ${row.sku.lead_time_days} días de entrega = ${dec(row.demand_lead)}`,
    ],
    ["Reserva de seguridad", nf.format(row.sku.safety_stock)],
    [
      "Stock objetivo",
      `${dec(row.demand_horizon)} + ${dec(row.demand_lead)} + ${nf.format(row.sku.safety_stock)} = ${dec(row.stock_target)}`,
    ],
    [
      "Menos lo que ya tenés",
      `${dec(row.stock_target)} − ${nf.format(row.sku.stock)} = ${nf.format(row.recommended_quantity)}`,
    ],
  ];

  return (
    <div className="fixed inset-0 z-[60] flex justify-end bg-ops-overlay" onClick={onClose}>
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={`Detalle de ${row.sku.product_name}`}
        onClick={(event) => event.stopPropagation()}
        className="h-full w-full max-w-[460px] overflow-y-auto border-l border-ops-border bg-background p-5 shadow-2xl"
      >
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
          <div className="min-w-0">
            <div className="text-xs tabular-nums text-ops-accent">SKU {row.sku.barcode}</div>
            <h2 className="mt-1 font-display text-xl font-semibold">{row.sku.product_name}</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              {row.sku.category} · {row.sku.supplier}
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

        <div className="mt-5 rounded-lg border border-ops-accent/50 bg-ops-accent-soft p-4">
          <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
            Cantidad a pedir
          </div>
          <div className="mt-1 font-display text-5xl font-semibold tabular-nums text-foreground">
            {nf.format(row.recommended_quantity)}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            unidades para cubrir los próximos {HORIZON_DAYS} días
          </div>
        </div>

        <div className="mt-3 grid grid-cols-3 gap-3">
          {(
            [
              ["Prioridad", PRIORITY_LABEL[row.priority]],
              ["Cobertura", row.coverage_days >= 999 ? "sin venta" : `${dec(row.coverage_days)} d`],
              ["Valor estimado", money(row.estimated_purchase_value)],
            ] as const
          ).map(([label, amount]) => (
            <div key={label} className="rounded-lg border border-ops-border bg-ops-panel p-3">
              <div className="text-[10px] uppercase tracking-[0.08em] text-muted-foreground">{label}</div>
              <div className="mt-1 font-display text-base font-semibold tabular-nums">{amount}</div>
            </div>
          ))}
        </div>

        <div className="mt-3">
          <HealthChips row={row} />
        </div>

        <div className="mt-5 overflow-hidden rounded-lg border border-ops-border">
          <div className="border-b border-ops-border bg-ops-panel px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
            Cómo se llega a esa cantidad
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

        <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">
          La cobertura es el stock dividido por la venta diaria de los últimos 30 días, no una
          proyección. Las alertas de salud avisan cuándo mirar el producto; no suman unidades a la
          cantidad a pedir.
        </p>
      </aside>
    </div>
  );
}
