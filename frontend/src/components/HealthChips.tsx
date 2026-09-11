import { AlertTriangle, Box, CheckCircle2, CircleAlert } from "lucide-react";
import {
  HEALTH_FILTERS,
  HEALTH_LABEL,
  PRIORITY_LABEL,
  type Calc,
  type HealthTag,
} from "@/lib/supplymate";

const healthIcon: Record<HealthTag, typeof AlertTriangle> = {
  riesgo_quiebre: AlertTriangle,
  sin_stock: CircleAlert,
  sobrestock: Box,
};

export function visibleHealth(row: Calc): HealthTag[] {
  return row.health.filter((tag) => HEALTH_FILTERS.includes(tag));
}

export function PriorityCell({ row }: { row: Calc }) {
  const label = PRIORITY_LABEL[row.priority];
  const tone =
    row.priority === "Alta"
      ? "text-ops-danger"
      : row.priority === "Media"
        ? "text-ops-warn"
        : "text-muted-foreground";
  return <span className={`font-medium ${tone}`}>{label}</span>;
}

export function HealthChips({ row }: { row: Calc }) {
  const tags = visibleHealth(row);
  if (tags.length === 0) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-ops-ok/40 bg-ops-ok-soft px-2 py-0.5 text-[10px] text-ops-ok">
        <CheckCircle2 className="h-3 w-3" />
        Saludable
      </span>
    );
  }
  return (
    <div className="flex flex-wrap gap-1">
      {tags.map((tag) => {
        const Icon = healthIcon[tag];
        return (
          <span
            key={tag}
            className="inline-flex items-center gap-1 rounded-full border border-ops-border bg-ops-panel px-2 py-0.5 text-[10px] text-muted-foreground"
          >
            <Icon className="h-3 w-3" />
            {HEALTH_LABEL[tag]}
          </span>
        );
      })}
    </div>
  );
}
