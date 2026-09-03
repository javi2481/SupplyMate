from __future__ import annotations



from app.core.models import ChatInterpretation, GroupSummary, GuidanceDecision, ReplenishmentSlice





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

) -> str:

    lines: list[str] = []

    guide = guidance

    if guide and guide.progress_label and guide.progress_total:

        lines.append(

            f"_Paso {guide.progress_step} de {guide.progress_total} · {guide.progress_label}_\n"

        )



    if interpretation.relation == "refinement" and interpretation.understood_labels:

        labels = " · ".join(interpretation.understood_labels)

        lines.append(f"Perfecto. Analizo **{labels}**.\n")

    elif interpretation.understood_labels:

        labels = " · ".join(interpretation.understood_labels)

        lines.append(f"**Entendí:** {labels}\n")



    if group_summaries:

        lines.append("Necesitás reponer aproximadamente:\n")

        total = 0

        for item in group_summaries:

            lines.append(f"- **{item.label}** — **{item.recommended_quantity}** unidades")

            total += item.recommended_quantity

        if len(group_summaries) > 1:

            lines.append(f"- **Total** — **{total}** unidades")

        lines.append("")

    elif slice_data.purchase_list:

        total_qty = sum(i.recommended_quantity for i in slice_data.purchase_list)

        dash = slice_data.dashboard

        lines.append(

            f"**{dash.skus} SKUs** analizados · "

            f"**{len(slice_data.purchase_list)}** líneas de OC "

            f"({total_qty} unidades en este recorte).\n"

        )

    else:

        lines.append(

            "Con el stock y las ventas de los últimos 30 días, "

            "no hay productos que requieran reposición en este recorte.\n"

        )



    if interpretation.guidance_question:

        lines.append(interpretation.guidance_question)

        if interpretation.guidance_options:

            chips = " · ".join(f"**{opt}**" for opt in interpretation.guidance_options[:6])

            lines.append(chips)

    elif guide and guide.action == "draft_oc":

        lines.append(guide.question)

    else:

        lines.append("Usá el panel para explorar por grupo, riesgo o SKU.")

    return "\n".join(lines)





def format_disambiguation_answer(

    question: str,

    options: list[str],

) -> str:

    lines = [question, ""]

    if options:

        lines.append("Opciones:")

        for i, opt in enumerate(options[:5], 1):

            lines.append(f"{i}. **{opt}**")

        lines.append("")

        lines.append("Escribí el nombre completo o elegí una opción.")

    return "\n".join(lines)


