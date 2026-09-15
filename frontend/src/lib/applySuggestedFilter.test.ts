import { describe, expect, it } from "vitest";
import { applySuggestedFilter } from "@/lib/applySuggestedFilter";
import { EMPTY_SLICE } from "@/lib/scope";

describe("applySuggestedFilter", () => {
  it("unions category onto cats", () => {
    const result = applySuggestedFilter(
      { action: "filter_category", args: { category: "Cuidado" }, label: "¿Qué hay en Cuidado?" },
      { ...EMPTY_SLICE, cats: ["Cabello"] },
    );
    expect(result).toEqual({
      type: "slice",
      slice: { ...EMPTY_SLICE, cats: ["Cabello", "Cuidado"] },
    });
  });

  it("sets coverage to the chip band", () => {
    const result = applySuggestedFilter(
      {
        action: "filter_coverage",
        args: { coverage_bucket: "0–3 días" },
        label: "¿Cobertura 0–3 días?",
      },
      EMPTY_SLICE,
    );
    expect(result).toEqual({
      type: "slice",
      slice: { ...EMPTY_SLICE, coverage: "0–3 días" },
    });
  });

  it("maps stockout_risk to riesgo_quiebre and overstock to sobrestock", () => {
    const risk = applySuggestedFilter(
      {
        action: "filter_health",
        args: { health_bucket: "stockout_risk" },
        label: "¿Riesgo de quiebre?",
      },
      EMPTY_SLICE,
    );
    expect(risk).toEqual({
      type: "slice",
      slice: { ...EMPTY_SLICE, health: ["riesgo_quiebre"] },
    });
    const over = applySuggestedFilter(
      { action: "filter_health", args: { health_bucket: "overstock" }, label: "¿Hay sobrestock?" },
      { ...EMPTY_SLICE, health: ["riesgo_quiebre"] },
    );
    expect(over).toEqual({
      type: "slice",
      slice: { ...EMPTY_SLICE, health: ["riesgo_quiebre", "sobrestock"] },
    });
  });

  it("unions supplier", () => {
    const result = applySuggestedFilter(
      {
        action: "filter_supplier",
        args: { supplier: "Higiene Sur" },
        label: "¿Qué pide Higiene Sur?",
      },
      EMPTY_SLICE,
    );
    expect(result).toEqual({
      type: "slice",
      slice: { ...EMPTY_SLICE, suppliers: ["Higiene Sur"] },
    });
  });

  it("returns open_sku and draft_oc commands without a slice send", () => {
    expect(
      applySuggestedFilter(
        { action: "open_sku", args: { product_id: "99" }, label: "¿Cuánto pedir de Top?" },
        EMPTY_SLICE,
      ),
    ).toEqual({ type: "open_sku", productId: "99" });
    expect(
      applySuggestedFilter({ action: "draft_oc", args: {}, label: "¿Armar la OC?" }, EMPTY_SLICE),
    ).toEqual({ type: "draft_oc" });
  });

  it("unknown actions are no-ops and never send chat", () => {
    expect(
      applySuggestedFilter({ action: "explode", args: { x: "1" }, label: "boom" }, EMPTY_SLICE),
    ).toEqual({ type: "noop" });
  });
});
