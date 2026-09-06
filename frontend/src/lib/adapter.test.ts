import { describe, expect, it } from "vitest";
import {
  HEALTH_BUCKET_LABEL,
  PRIORITY_LABELS,
  rowFromPurchaseItem,
  type SkuListRow,
} from "@/lib/adapter";
import type { PurchaseListItem } from "@/lib/api";

function item(overrides: Partial<PurchaseListItem> = {}): PurchaseListItem {
  return {
    product_id: "P-1",
    barcode: "111",
    product_name: "Pañales Talle M",
    supplier: "Higiene Sur",
    category: "Pañales",
    subcategory: "Talle M",
    current_stock: 12,
    reorder_point: 8,
    below_reorder_point: false,
    average_daily_demand: 2,
    days_of_supply: 6,
    health_bucket: "understock",
    recommended_quantity: 40,
    operational_priority: "high",
    purchase_cost: 100,
    estimated_purchase_value: 4000,
    ...overrides,
  };
}

describe("PRIORITY_LABELS", () => {
  it("maps critical/high/normal 1:1 without collapsing critical into high", () => {
    expect(PRIORITY_LABELS.critical).toBe("Crítica");
    expect(PRIORITY_LABELS.high).toBe("Alta");
    expect(PRIORITY_LABELS.normal).toBe("Normal");
    expect(PRIORITY_LABELS.critical).not.toBe(PRIORITY_LABELS.high);
  });
});

describe("rowFromPurchaseItem", () => {
  it("projects qty, stock, coverage, and priority from the purchase item", () => {
    const row = rowFromPurchaseItem(
      item({ operational_priority: "critical", recommended_quantity: 90, current_stock: 0 }),
    );
    expect(row.recommended_quantity).toBe(90);
    expect(row.stock).toBe(0);
    expect(row.coverage_days).toBe(6);
    expect(row.priority_label).toBe("Crítica");
    expect(row.priority).toBe("critical");
  });

  it("does not invent replenishment intermediates on the table row", () => {
    const row: SkuListRow = rowFromPurchaseItem(item());
    expect(row).not.toHaveProperty("demand_horizon");
    expect(row).not.toHaveProperty("demand_lead");
    expect(row).not.toHaveProperty("stock_target");
    expect(row).not.toHaveProperty("lead_time_days");
    expect(row).not.toHaveProperty("safety_stock");
  });

  it("labels understock as Falta de stock", () => {
    const row = rowFromPurchaseItem(item({ health_bucket: "understock", current_stock: 5 }));
    expect(HEALTH_BUCKET_LABEL.understock).toBe("Falta de stock");
    expect(row.health.some((chip) => chip.label === "Falta de stock")).toBe(true);
  });
});
