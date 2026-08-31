"""Visual theme — colores semánticos para SupplyMate Operación."""

from __future__ import annotations

from app.services import metrics

# Cobertura: rojo (urgente) → verde (holgado)
COVERAGE_COLORS: dict[str, str] = {
    "0–3 días": "#E53935",
    "3–7 días": "#FB8C00",
    "7–14 días": "#FDD835",
    "14–30 días": "#7CB342",
    "30+ días": "#43A047",
}

HEALTH_COLORS: dict[str, str] = {
    metrics.BUCKET_STOCKOUT_RISK: "#E53935",
    metrics.BUCKET_UNDERSTOCK: "#FB8C00",
    metrics.BUCKET_OVERSTOCK: "#1E88E5",
    metrics.BUCKET_HEALTHY: "#43A047",
}

HEALTH_ICONS: dict[str, str] = {
    metrics.BUCKET_STOCKOUT_RISK: "🔴",
    metrics.BUCKET_UNDERSTOCK: "🟠",
    metrics.BUCKET_OVERSTOCK: "🔵",
    metrics.BUCKET_HEALTHY: "🟢",
}

HEALTH_HINTS: dict[str, str] = {
    metrics.BUCKET_STOCKOUT_RISK: "Stock bajo el punto de reorden — prioridad alta",
    metrics.BUCKET_UNDERSTOCK: "Hay que reponer para cubrir 7 días + lead time",
    metrics.BUCKET_OVERSTOCK: "Stock por encima del máximo — no pedir",
    metrics.BUCKET_HEALTHY: "Stock alineado con la demanda",
}

TREND_LABELS: dict[str, str] = {
    metrics.BUCKET_STOCKOUT_RISK: "↓ quiebre",
    metrics.BUCKET_UNDERSTOCK: "→ reponer",
    metrics.BUCKET_OVERSTOCK: "↑ exceso",
    metrics.BUCKET_HEALTHY: "↔ estable",
}

CSS = """
<style>
.sm-panel {
  background: linear-gradient(135deg, #1a1f2e 0%, #12151c 100%);
  border: 1px solid #2d3548;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
}
.sm-kpi-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.sm-kpi {
  flex: 1 1 140px;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  border-left: 4px solid var(--accent);
  background: rgba(255,255,255,0.04);
}
.sm-kpi-label { font-size: 0.78rem; opacity: 0.85; margin-bottom: 0.15rem; }
.sm-kpi-value { font-size: 1.6rem; font-weight: 700; line-height: 1.1; }
.sm-kpi-hint { font-size: 0.72rem; opacity: 0.65; margin-top: 0.25rem; }
.sm-legend { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.5rem 0 1rem 0; }
.sm-badge {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.25rem 0.6rem; border-radius: 999px;
  font-size: 0.78rem; font-weight: 600;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
}
.sm-badge-explore { border-color: #1E88E5; color: #64B5F6; }
.sm-badge-commit { border-color: #43A047; color: #81C784; }
.sm-tip {
  background: rgba(67, 160, 71, 0.12);
  border-left: 3px solid #43A047;
  padding: 0.6rem 0.9rem;
  border-radius: 0 8px 8px 0;
  font-size: 0.88rem;
  margin-bottom: 0.75rem;
}
</style>
"""
