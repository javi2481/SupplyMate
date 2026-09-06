import { describe, expect, it } from "vitest";
import { CATEGORY_COLOR, categoryColor } from "@/lib/chart-colors";

describe("categoryColor", () => {
  it("keeps Lovable colors for the demo catalog", () => {
    expect(categoryColor("Mamaderas")).toBe(CATEGORY_COLOR.Mamaderas);
    expect(categoryColor("Pañales")).toBe(CATEGORY_COLOR.Pañales);
  });

  it("assigns a palette color to live catalog names instead of the accent blue", () => {
    expect(categoryColor("Cuidado del Cabello")).not.toBe("var(--ops-accent)");
    expect(categoryColor("Cosmetica")).not.toBe("var(--ops-accent)");
    expect(categoryColor("Cuidado del Cabello")).not.toBe(categoryColor("Cosmetica"));
  });
});
