import { afterEach, describe, expect, it, vi } from "vitest";
import {
  fetchReplenishment,
  fetchSlice,
  postChat,
  purchaseListCsvUrl,
  toSearchParams,
} from "@/lib/api";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("api client", () => {
  it("fetchSlice builds query string with coverage and health", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        scope: {},
        evidence: "",
        dashboard: {
          skus: 1,
          stockout_risk: 0,
          understock: 0,
          overstock: 0,
          healthy: 1,
          avg_coverage: 10,
          estimated_purchase_value: 0,
          by_category: [],
        },
        purchase_list: [],
        suggested_filters: [],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchSlice({
      category: ["Pañales"],
      coverage_bucket: ["0–3 días"],
      health_bucket: ["stockout_risk"],
      limit: 25,
    });

    expect(fetchMock).toHaveBeenCalledOnce();
    const url = String(fetchMock.mock.calls[0]?.[0]);
    const decoded = decodeURIComponent(url.replace(/\+/g, "%20"));
    expect(url).toContain("/replenishment/slice?");
    expect(url).toContain("category=Pa%C3%B1ales");
    expect(decoded).toContain("coverage_bucket=0–3 días");
    expect(url).toContain("health_bucket=stockout_risk");
    expect(url).toContain("limit=25");
  });

  it("postChat sends message and optional scope JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        answer: "ok",
        mode: "chat",
        product_id: "",
        product_name: "",
        recommended_quantity: 0,
        calculation: null,
        purchase_list: [],
        dashboard: null,
        scope: null,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await postChat("¿Qué comprar?", { categories: ["Pañales"] });

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/chat");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({
      message: "¿Qué comprar?",
      scope: { categories: ["Pañales"] },
    });
  });

  it("fetchReplenishment encodes product id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        product_id: "a/b",
        product_name: "x",
        recommended_quantity: 1,
        calculation: {
          product_id: "a/b",
          average_daily_demand: 1,
          demand_horizon: 7,
          demand_lead_time: 2,
          stock_target: 10,
          current_stock: 0,
          recommended_quantity: 1,
          horizon_days: 7,
          history_days: 30,
          lead_time_days: 2,
          safety_stock: 1,
        },
        context: {
          product_name: "x",
          current_stock: 0,
          units_sold_30d: 30,
          average_daily_demand: 1,
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchReplenishment("a/b#1");
    const url = String(fetchMock.mock.calls[0]?.[0]);
    expect(url).toContain("/products/a%2Fb%231/replenishment");
  });

  it("throws on 404 without including raw host in a product-facing helper", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
        text: async () => "missing",
      }),
    );
    await expect(fetchSlice({})).rejects.toThrow(/404/);
  });

  it("purchaseListCsvUrl uses same scope params", () => {
    const url = purchaseListCsvUrl({
      category: ["Nutrición"],
      coverage_bucket: ["3–7 días"],
      limit: 100,
    });
    const decoded = decodeURIComponent(url.replace(/\+/g, "%20"));
    expect(url).toContain("/replenishment/purchase-list.csv?");
    expect(decoded).toContain("coverage_bucket=3–7 días");
    expect(decoded).toContain("category=Nutrición");
  });

  it("toSearchParams omits empty optional dims", () => {
    const qs = toSearchParams({ limit: 10 });
    expect(qs.get("limit")).toBe("10");
    expect(qs.getAll("category")).toEqual([]);
    expect(qs.getAll("coverage_bucket")).toEqual([]);
  });
});
