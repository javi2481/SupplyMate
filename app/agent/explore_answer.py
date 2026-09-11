from __future__ import annotations

from app.core.models import ChatInterpretation, GroupSummary, GuidanceDecision, ReplenishmentSlice

REPORT_TOP_N = 8


def group_summaries_from_resolved(resolved: list) -> list[GroupSummary]:
    summaries: list[GroupSummary] = []
    for ref in resolved:
        if ref.match_kind not in ("group", "exact_sku"):
            continue
        if ref.recommended_quantity <= 0 and ref.sku_count <= 0:
            continue
        label = ref.label or ref.user_text
        summaries.append(
            GroupSummary(
                label=label,
                recommended_quantity=ref.recommended_quantity,
                sku_count=ref.sku_count,
            )
        )
    return summaries


def format_explore_answer(
    slice_data: ReplenishmentSlice,
    interpretation: ChatInterpretation,
    group_summaries: list[GroupSummary],
    guidance: GuidanceDecision | None = None,
    *,
    horizon_days: int = 7,
) -> str:
    """Plain-text purchase report for the Lovable chat bubble (no markdown)."""
    from app.services.analytics import metrics

    lines: list[str] = []
    dash = slice_data.dashboard
    scope = slice_data.scope
    days = horizon_days or 7

    label_parts = list(interpretation.understood_labels or [])
    for bucket in scope.coverage_buckets:
        if bucket not in label_parts:
            label_parts.append(bucket)
    if any(b == metrics.BUCKET_STOCKOUT_RISK for b in scope.health_buckets):
        if "Riesgo de quiebre" not in label_parts and "Críticos" not in label_parts:
            label_parts.append("Críticos")
    labels = " · ".join(label_parts)

    purchase_count = dash.purchase_skus or (
        len(slice_data.purchase_list) if slice_data.purchase_list else 0
    )
    empty_purchase = not slice_data.purchase_list and purchase_count == 0
    # Never invent totals from per-ref group_summaries when the applied slice is empty.
    if empty_purchase:
        total_units = 0
        sku_hint = 0
    elif slice_data.purchase_list:
        total_units = dash.recommended_units or sum(
            i.recommended_quantity for i in slice_data.purchase_list
        )
        sku_hint = purchase_count or len(slice_data.purchase_list)
    else:
        total_units = 0
        sku_hint = purchase_count or dash.skus

    if labels:
        if interpretation.relation == "refinement":
            lines.append(f"Recorte: {labels}.")
        else:
            lines.append(f"{labels} · próximos {days} días.")
    elif sku_hint:
        lines.append(f"Recorte · {sku_hint} SKUs · próximos {days} días.")

    if empty_purchase:
        if len(group_summaries) >= 2:
            lines.append(
                "No hay productos que cumplan todos esos criterios a la vez "
                "en este recorte."
            )
        else:
            lines.append(
                "Con el stock y las ventas de los últimos 30 días, "
                "no hay productos que requieran reposición en este recorte."
            )
        return "\n".join(lines)

    if not slice_data.purchase_list and not group_summaries:
        lines.append(
            "Con el stock y las ventas de los últimos 30 días, "
            "no hay productos que requieran reposición en este recorte."
        )
        return "\n".join(lines)

    header_parts: list[str] = []
    if total_units:
        header_parts.append(f"{total_units} unidades a reponer")
    if sku_hint:
        header_parts.append(f"{sku_hint} SKUs a reponer")
    if header_parts:
        lines.append(" · ".join(header_parts) + ".")

    ranked = sorted(
        slice_data.purchase_list,
        key=lambda i: i.recommended_quantity,
        reverse=True,
    )[:REPORT_TOP_N]
    if ranked:
        lines.append("")
        lines.append("Prioridad de compra:")
        for i, item in enumerate(ranked, 1):
            lines.append(
                f"{i}. {item.product_name} — {item.recommended_quantity} unidades"
            )
        remaining = max(0, (purchase_count or len(slice_data.purchase_list)) - len(ranked))
        if remaining > 0:
            lines.append(f"… y {remaining} más en el panel.")
    elif group_summaries:
        lines.append("")
        for item in group_summaries:
            lines.append(f"- {item.label} — {item.recommended_quantity} unidades")

    guide = guidance
    if (
        guide
        and guide.action == "draft_oc"
        and guide.question
        and slice_data.purchase_list
    ):
        lines.append("")
        lines.append(_strip_md(guide.question))
    else:
        lines.append("")
        lines.append("Usá el panel para filtrar por formato, riesgo o SKU.")

    return "\n".join(lines)


def _strip_md(text: str) -> str:
    return text.replace("**", "")


def format_disambiguation_answer(
    question: str,
    options: list[str],
) -> str:
    lines = [_strip_md(question), ""]
    if options:
        lines.append("Opciones:")
        for i, opt in enumerate(options[:5], 1):
            lines.append(f"{i}. {opt}")
        lines.append("")
        lines.append("Escribí el nombre completo o elegí una opción.")
    return "\n".join(lines)
