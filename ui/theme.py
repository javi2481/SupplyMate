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
    metrics.BUCKET_STOCKOUT_RISK: metrics.METRIC_CONTRACTS["stockout_risk"].caveat,
    metrics.BUCKET_UNDERSTOCK: metrics.METRIC_CONTRACTS["understock"].caveat,
    metrics.BUCKET_OVERSTOCK: metrics.METRIC_CONTRACTS["overstock"].caveat,
    metrics.BUCKET_HEALTHY: "Stock alineado con la demanda",
}

TREND_LABELS: dict[str, str] = {
    metrics.BUCKET_STOCKOUT_RISK: "↓ quiebre",
    metrics.BUCKET_UNDERSTOCK: "→ reponer",
    metrics.BUCKET_OVERSTOCK: "↑ exceso",
    metrics.BUCKET_HEALTHY: "↔ estable",
}

SHELL_TOKENS: dict[str, str] = {
    "sidebar_bg": "#0b0f17",
    "panel_bg": "#12151c",
    "panel_grad_start": "#1a1f2e",
    "panel_grad_end": "#12151c",
    "primary_accent": "#1E88E5",
    "danger_accent": "#E05252",
    "success_accent": "#43A047",
    "border": "#2d3548",
    "muted_text": "rgba(255,255,255,0.65)",
}

KPI_ICONS: dict[str, str] = {
    "products": """
<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <path d="M12 2 4 6v12l8 4 8-4V6l-8-4Zm0 2.2 5.2 2.6L12 9.4 6.8 6.8 12 4.2Zm-6 4.2 5 2.5v8.3l-5-2.5V8.4Zm7 10.8v-8.3l5-2.5v8.3l-5 2.5Z"/>
</svg>
""".strip(),
    "understock": """
<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Zm1 15h-2v-2h2v2Zm0-4h-2V7h2v6Z"/>
</svg>
""".strip(),
    "stockout_risk": """
<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <path d="M1 21h22L12 2 1 21Zm12-3h-2v-2h2v2Zm0-4h-2v-4h2v4Z"/>
</svg>
""".strip(),
    "coverage": """
<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <path d="M7 2h2v2h6V2h2v2h3v18H4V4h3V2Zm11 8H6v10h12V10Z"/>
</svg>
""".strip(),
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root {
  --sm-sidebar-bg: #0b0f17;
  --sm-panel-bg: #12151c;
  --sm-primary-accent: #1E88E5;
  --sm-danger-accent: #E05252;
  --sm-success-accent: #43A047;
  --sm-border: #2d3548;
  --sm-muted-text: rgba(255,255,255,0.65);
  --sm-accent: var(--sm-primary-accent);
}
html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
}
.block-container {
  max-width: 1150px !important;
  padding-top: 1.5rem !important;
}
/* ── Sidebar siempre visible (mockup) ── */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
  display: none !important;
}
section[data-testid="stSidebar"] {
  background: var(--sm-sidebar-bg) !important;
  min-width: 240px !important;
  max-width: 260px !important;
  transform: translateX(0) !important;
  visibility: visible !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
  transform: translateX(0) !important;
  margin-left: 0 !important;
  min-width: 240px !important;
}
.sm-kpi-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.sm-kpi {
  flex: 1 1 140px;
  border-radius: 12px;
  padding: 0.85rem 1rem;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
}
.sm-kpi-hint { display: none; }
.sm-kpi-top {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}
.sm-kpi-icon {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--sm-accent) 18%, transparent);
  color: var(--sm-accent);
  flex: 0 0 auto;
}
.sm-kpi-icon svg {
  width: 1.2rem;
  height: 1.2rem;
  fill: currentColor;
}
.sm-kpi-copy {
  min-width: 0;
}
.sm-kpi-label { font-size: 0.78rem; opacity: 0.85; margin-bottom: 0.15rem; }
.sm-kpi-value { font-size: 1.6rem; font-weight: 700; line-height: 1.1; }
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
/* ── Sidebar rail (mockup) ── */
[data-testid="stSidebar"] .rail-section {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.5;
  margin: 1rem 0 0.35rem 0;
}
[data-testid="stSidebar"] .rail-day {
  font-size: 0.72rem;
  opacity: 0.42;
  margin: 0.5rem 0 0.15rem 0;
}
[data-testid="stSidebar"] .rail-empty {
  font-size: 0.8rem;
  opacity: 0.45;
  margin: 0.15rem 0 0.5rem 0;
}
[data-testid="stSidebar"] .rail-footer {
  font-size: 0.85rem;
  font-weight: 600;
  opacity: 0.7;
  margin-top: 1.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] button[kind="secondary"] {
  text-align: left;
  justify-content: flex-start;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0.35rem 0.5rem !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
  background: rgba(255,255,255,0.05) !important;
}
[data-testid="stSidebar"] button[kind="primary"] {
  border-radius: 8px !important;
  font-weight: 600 !important;
  background: var(--sm-primary-accent) !important;
  border: none !important;
}
/* Active thread row: soft fill + left accent (not a hard bordered box) */
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255, 255, 255, 0.06) !important;
  border: none !important;
  border-left: 3px solid var(--sm-primary-accent) !important;
  border-radius: 8px !important;
  padding-left: 0.25rem !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > div {
  border: none !important;
  background: transparent !important;
}
[data-testid="stSidebar"] button.rail-pin-btn {
  font-size: 0.78rem !important;
  opacity: 0.7 !important;
}
.sm-chat-summary {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 0.7rem 1rem;
  font-size: 0.92rem;
  font-weight: 500;
  width: 100%;
  box-sizing: border-box;
}
.sm-chat-summary-icon {
  width: 1.7rem;
  height: 1.7rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(30, 136, 229, 0.2);
  color: #90CAF9;
  flex: 0 0 auto;
}
.sm-chat-summary-icon svg {
  width: 0.95rem;
  height: 0.95rem;
  fill: currentColor;
}
[data-testid="stChatMessage"] {
  border-radius: 14px;
  background: transparent !important;
  border: none !important;
}
[data-testid="stChatMessage"]:has(.sm-role-user) {
  flex-direction: row-reverse;
  margin-left: auto;
  max-width: min(36rem, 78%);
  background: rgba(30, 136, 229, 0.12) !important;
  border: 1px solid rgba(30, 136, 229, 0.22) !important;
  border-radius: 16px 16px 4px 16px !important;
}
[data-testid="stChatMessage"]:has(.sm-chat-summary) [data-testid="stChatMessageAvatar"] {
  display: none !important;
}
</style>
"""
