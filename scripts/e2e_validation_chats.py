"""E2E: 5 validation questions in separate chats (no prior scope).

Checks chat answer, scope/filters, dashboard, chart policy, and /slice parity.
Writes a JSON report under logs/e2e-validation-report.json.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from app.agent.turn_log import read_recent_turns

API = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "logs" / "e2e-validation-report.json"


def chart_mode(scope: dict, purchase_list: list, dashboard: dict) -> str:
    """Mirror frontend isListShapedRecorte + chartBarMode."""
    list_shaped = bool(
        scope.get("health_buckets")
        or scope.get("coverage_buckets")
        or scope.get("suppliers")
        or scope.get("name_tokens")
        or scope.get("out_of_stock_only")
    )
    purchase = [i for i in purchase_list if int(i.get("recommended_quantity") or 0) > 0]
    if list_shaped and purchase:
        return "sku"
    cats = [b for b in (dashboard.get("by_category") or []) if int(b.get("recommended_quantity") or 0) > 0]
    subs = [b for b in (dashboard.get("by_subcategory") or []) if int(b.get("recommended_quantity") or 0) > 0]
    if len(cats) <= 1 and subs:
        return "subcategory"
    return "category"


def post_chat(message: str) -> dict:
    body = json.dumps({"message": message, "scope": None}).encode()
    req = urllib.request.Request(
        f"{API}/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def fetch_slice(scope: dict) -> dict:
    params: list[tuple[str, str]] = [("limit", "50")]
    for cat in scope.get("categories") or []:
        params.append(("category", cat))
    for sub in scope.get("subcategories") or []:
        params.append(("subcategory", sub))
    for h in scope.get("health_buckets") or []:
        params.append(("health_bucket", h))
    for c in scope.get("coverage_buckets") or []:
        params.append(("coverage_bucket", c))
    for s in scope.get("suppliers") or []:
        params.append(("supplier", s))
    hz = scope.get("horizon_days")
    if hz:
        params.append(("horizon_days", str(hz)))
    qs = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{API}/replenishment/slice?{qs}", timeout=120) as resp:
        return json.load(resp)


def check(name: str, cond: bool, detail: str) -> dict:
    return {"check": name, "ok": bool(cond), "detail": detail}


CASES = [
    {
        "id": "Q1_30",
        "message": "¿Qué tengo que comprar para los próximos 30 días?",
        "expect": lambda r, s, d, mode: [
            check("mode_list_or_explore", r.get("mode") in ("list", "explore"), r.get("mode")),
            check("horizon_30", int(s.get("horizon_days") or r.get("horizon_days") or 0) == 30, str(s.get("horizon_days"))),
            check("has_units", int(d.get("recommended_units") or 0) > 0, str(d.get("recommended_units"))),
            check("chart_category", mode == "category", mode),
            check("no_false_coverage", not (s.get("coverage_buckets") or []), str(s.get("coverage_buckets"))),
            check("answer_mentions_30", "30" in (r.get("answer") or ""), (r.get("answer") or "")[:120]),
            check("no_single_sku", not (r.get("product_id") or "").strip(), r.get("product_id")),
        ],
    },
    {
        "id": "Q1_60",
        "message": "¿Qué tengo que comprar para los próximos 60 días?",
        "expect": lambda r, s, d, mode: [
            check("horizon_60", int(s.get("horizon_days") or r.get("horizon_days") or 0) == 60, str(s.get("horizon_days"))),
            check("units_gt_30d_ballpark", int(d.get("recommended_units") or 0) > 100_000, str(d.get("recommended_units"))),
            check("chart_category", mode == "category", mode),
            check("answer_mentions_60", "60" in (r.get("answer") or ""), (r.get("answer") or "")[:120]),
        ],
    },
    {
        "id": "Q2_cosmetica",
        "message": "¿Qué cosmética tengo que comprar?",
        "expect": lambda r, s, d, mode: [
            check("mode_explore", r.get("mode") == "explore", r.get("mode")),
            check("cat_cosmetica", "Cosmetica" in (s.get("categories") or []), str(s.get("categories"))),
            check("no_health", not (s.get("health_buckets") or []), str(s.get("health_buckets"))),
            check("no_coverage", not (s.get("coverage_buckets") or []), str(s.get("coverage_buckets"))),
            check("chart_subcategory", mode == "subcategory", mode),
            check("has_subs", len(d.get("by_subcategory") or []) >= 1, str(d.get("by_subcategory"))),
            check("not_basiccare", "BASICCARE" not in (r.get("answer") or "").upper(), (r.get("answer") or "")[:80]),
            check("no_single_sku", not (r.get("product_id") or "").strip(), r.get("product_id")),
        ],
    },
    {
        "id": "Q3_compound",
        "message": (
            "Mostrame los productos críticos de cosmética que tengan "
            "menos de 3 días de cobertura y ordenalos por unidades a pedir"
        ),
        "expect": lambda r, s, d, mode: [
            check("cat_cosmetica", "Cosmetica" in (s.get("categories") or []), str(s.get("categories"))),
            check("health_stockout", "stockout_risk" in (s.get("health_buckets") or []), str(s.get("health_buckets"))),
            check("coverage_0_3", any("0" in c and "3" in c for c in (s.get("coverage_buckets") or [])), str(s.get("coverage_buckets"))),
            check("chart_sku", mode == "sku", mode),
            check("purchase_list_n", len(r.get("purchase_list") or []) >= 3, str(len(r.get("purchase_list") or []))),
            check("not_basiccare", "BASICCARE" not in (r.get("answer") or "").upper(), (r.get("answer") or "")[:100]),
            check("not_demanda_7", "demanda 7" not in (r.get("answer") or "").lower(), (r.get("answer") or "")[:100]),
            check("no_single_sku", not (r.get("product_id") or "").strip(), r.get("product_id")),
        ],
    },
    {
        "id": "Q4_riesgo",
        "message": "¿Qué hay en riesgo de quiebre?",
        "expect": lambda r, s, d, mode: [
            check("health_stockout", "stockout_risk" in (s.get("health_buckets") or []), str(s.get("health_buckets"))),
            check("chart_sku_or_category", mode in ("sku", "category"), mode),
            check("has_answer", bool((r.get("answer") or "").strip()), (r.get("answer") or "")[:80]),
            check("not_basiccare_hijack", "BASICCARE" not in (r.get("answer") or "").upper() or mode != "single", r.get("mode")),
        ],
    },
    {
        "id": "Q5_sku",
        "message": "¿Cuánto pedir de 8112743?",
        "expect": lambda r, s, d, mode: [
            check("mode_single", r.get("mode") in ("single", "single_sku") or bool(r.get("product_id")), r.get("mode")),
            check("product_8112743", (r.get("product_id") or "") == "8112743" or "8112743" in (r.get("answer") or ""), r.get("product_id")),
            check("qty_positive", int(r.get("recommended_quantity") or 0) > 0, str(r.get("recommended_quantity"))),
            check("has_calculation", r.get("calculation") is not None or "unidades" in (r.get("answer") or "").lower(), str(r.get("calculation") is not None)),
        ],
    },
]


def main() -> int:
    # health
    with urllib.request.urlopen(f"{API}/health", timeout=10) as resp:
        health = json.load(resp)
    assert health.get("status") == "ok", health

    debug_ok = False
    try:
        with urllib.request.urlopen(f"{API}/debug/chat-turns?limit=1", timeout=10) as resp:
            debug_ok = resp.status == 200
    except urllib.error.HTTPError:
        debug_ok = False

    results = []
    failed = 0
    for case in CASES:
        print(f"\n=== {case['id']} (chat separado) ===")
        print(case["message"])
        try:
            r = post_chat(case["message"])
        except Exception as exc:
            results.append({"id": case["id"], "error": str(exc), "checks": []})
            failed += 1
            print("FAIL request", exc)
            continue
        s = r.get("scope") or {}
        d = r.get("dashboard") or {}
        mode = chart_mode(s, r.get("purchase_list") or [], d)
        server_hint = (r.get("trace") or {}).get("chart_hint") if isinstance(r.get("trace"), dict) else None
        checks = list(case["expect"](r, s, d, mode))
        # slice parity when scoped explore/list
        slice_info = None
        if s and r.get("mode") in ("explore", "list") and (
            s.get("categories") or s.get("health_buckets") or s.get("coverage_buckets")
        ):
            sl = fetch_slice(s)
            sd = sl.get("dashboard") or {}
            slice_info = {
                "units": sd.get("recommended_units"),
                "purchase_skus": sd.get("purchase_skus"),
            }
            chat_units = int(d.get("recommended_units") or 0)
            slice_units = int(sd.get("recommended_units") or 0)
            # allow small drift only if both positive / same ballpark
            checks.append(
                check(
                    "slice_filter_parity",
                    chat_units == slice_units,
                    f"chat={chat_units} slice={slice_units}",
                )
            )
        if r.get("trace"):
            checks.append(check("has_trace", True, str((r.get("trace") or {}).get("route"))))
        else:
            checks.append(check("has_trace", False, "trace missing — server may be stale"))

        case_failed = [c for c in checks if not c["ok"]]
        if case_failed:
            failed += len(case_failed)
        status = "PASS" if not case_failed else "FAIL"
        print(status, "mode=", r.get("mode"), "chart=", mode, "server_hint=", server_hint)
        print("horizon=", s.get("horizon_days") or r.get("horizon_days"), "units=", d.get("recommended_units"))
        print("scope cats/health/cov=", s.get("categories"), s.get("health_buckets"), s.get("coverage_buckets"))
        print("answer:", (r.get("answer") or "")[:200].replace("\n", " | "))
        for c in checks:
            mark = "OK" if c["ok"] else "XX"
            print(f"  [{mark}] {c['check']}: {c['detail']}")
        results.append(
            {
                "id": case["id"],
                "message": case["message"],
                "status": status,
                "mode": r.get("mode"),
                "chart_mode": mode,
                "server_chart_hint": server_hint,
                "horizon_days": s.get("horizon_days") or r.get("horizon_days"),
                "scope": {
                    "categories": s.get("categories"),
                    "health_buckets": s.get("health_buckets"),
                    "coverage_buckets": s.get("coverage_buckets"),
                },
                "units": d.get("recommended_units"),
                "purchase_skus": d.get("purchase_skus"),
                "answer_preview": (r.get("answer") or "")[:280],
                "slice": slice_info,
                "checks": checks,
            }
        )

    turns = []
    try:
        turns = read_recent_turns(20)
    except Exception:
        turns = []

    report = {
        "api_health": health,
        "debug_endpoint": debug_ok,
        "failed_checks": failed,
        "cases": results,
        "turn_log_n": len(turns),
        "turn_messages": [t.get("message") for t in turns[-10:]],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== SUMMARY failed_checks={failed} report={REPORT} debug={debug_ok} turns={len(turns)} ===")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
