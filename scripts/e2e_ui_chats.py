"""UI e2e with Playwright: separate chats, chart titles, filter chips."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

UI = "http://127.0.0.1:8080"
API = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "logs" / "e2e-ui-report.json"
SHOT = ROOT / "logs" / "e2e-shots"


def new_chat(page):
    btn = page.get_by_role("button", name=re.compile(r"Nueva|Nuevo chat|Nueva conversaci", re.I))
    if btn.count():
        btn.first.click()
        page.wait_for_timeout(500)
        return
    page.goto(UI, wait_until="domcontentloaded")
    page.wait_for_selector('input[aria-label="Consulta de reposición"]', timeout=30_000)
    page.wait_for_timeout(800)


def send_chat(page, text: str, timeout_ms: int = 120_000) -> dict:
    box = page.locator('input[aria-label="Consulta de reposición"]')
    box.wait_for(state="visible", timeout=30_000)
    box.click()
    box.fill(text)
    page.get_by_role("button", name="Enviar consulta").click()
    page.wait_for_function(
        """() => {
          const nodes = [...document.querySelectorAll('div,p,span,li')];
          const thinking = nodes.some(n => (n.textContent||'').trim().startsWith('Pensando'));
          return !thinking;
        }""",
        timeout=timeout_ms,
    )
    page.wait_for_timeout(1600)
    explore = page.get_by_role("button", name=re.compile("Explorar", re.I))
    if explore.count():
        explore.first.click()
        page.wait_for_timeout(700)
    body = page.locator("body").inner_text()
    chart_title = ""
    for t in (
        "Top productos a reponer",
        "Unidades a reponer por subcategoría",
        "Unidades a reponer por categoría",
    ):
        if t.lower() in body.lower():
            chart_title = t
            break
    recorte_el = page.locator("text=Recorte").first
    recorte = ""
    try:
        recorte = recorte_el.locator("xpath=following-sibling::*[1]").inner_text(timeout=2000)
    except Exception:
        m = re.search(r"Recorte\s*\n?\s*(.+)", body)
        if m:
            recorte = m.group(1).split("\n")[0][:200]
    filters = {
        "riesgo": bool(re.search(r"Riesgo de quiebre", body, re.I)),
        "cobertura_0_3": ("0–3" in body) or ("0-3" in body),
        "cosmetica": ("Cosmetica" in body) or ("Cosmética" in body),
        "horizon_30": ("30 días" in body) or ("30 dias" in body.lower()) or ("Horizonte 30" in body),
        "horizon_60": ("60 días" in body) or ("60 dias" in body.lower()),
        "coverage_chip_active": "Cobertura 0–3" in body or "0–3 días" in recorte,
        "health_in_recorte": "Crítico" in recorte or "quiebre" in recorte.lower() or "Riesgo" in recorte,
    }
    answer = ""
    for line in body.splitlines()[::-1]:
        line = line.strip()
        if len(line) > 40 and "Unidades a reponer" not in line and line != "Recorte":
            low = line.lower()
            if any(k in low for k in ("unidad", "reponer", "cosmet", "producto", "basiccare", "pedido", "próximos", "proximos")):
                answer = line[:300]
                break
    return {
        "chart_title": chart_title,
        "recorte": recorte,
        "filters_seen": filters,
        "answer_snip": answer,
        "body_has_basiccare": "BASICCARE" in body.upper() and "8112743" not in text,
        "body_has_demanda_7": "demanda 7" in body.lower(),
    }


def main() -> int:
    SHOT.mkdir(parents=True, exist_ok=True)
    cases = []
    scenarios = [
        {
            "id": "UI_Q1_30",
            "msg": "¿Qué tengo que comprar para los próximos 30 días?",
            "want_chart": "categoría",
            "want": lambda s: (
                s["filters_seen"]["horizon_30"] or "30" in s["recorte"] or "30" in s["answer_snip"],
                "chart" in s["chart_title"].lower() or "categoría" in s["chart_title"].lower(),
                not s["filters_seen"]["cobertura_0_3"] or "30+" not in s["recorte"],
            ),
        },
        {
            "id": "UI_Q2_cosmetica",
            "msg": "¿Qué cosmética tengo que comprar?",
            "want_chart": "subcategoría",
            "want": lambda s: (
                s["filters_seen"]["cosmetica"],
                "subcategor" in s["chart_title"].lower(),
                not s["body_has_basiccare"],
                "Horizonte 30" not in s["recorte"],
            ),
        },
        {
            "id": "UI_Q3_compound",
            "msg": "Mostrame los productos críticos de cosmética que tengan menos de 3 días de cobertura y ordenalos por unidades a pedir",
            "want_chart": "Top productos",
            "want": lambda s: (
                s["filters_seen"]["cosmetica"],
                "top productos" in s["chart_title"].lower(),
                not s["body_has_basiccare"] and not s["body_has_demanda_7"],
                "Riesgo" in s["recorte"] or s["filters_seen"]["health_in_recorte"],
                "0–3" in s["recorte"] or "0-3" in s["recorte"] or s["filters_seen"]["coverage_chip_active"],
            ),
        },
    ]
    failed = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.goto(UI, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_selector('input[aria-label="Consulta de reposición"]', timeout=60_000)
        page.wait_for_timeout(1200)
        for sc in scenarios:
            print(f"\n=== {sc['id']} ===")
            new_chat(page)
            try:
                snap = send_chat(page, sc["msg"])
                page.screenshot(path=str(SHOT / f"{sc['id']}.png"), full_page=True)
            except Exception as exc:
                print("FAIL", exc)
                cases.append({"id": sc["id"], "error": str(exc), "ok": False})
                failed += 1
                continue
            flags = sc["want"](snap)
            ok = all(flags)
            if not ok:
                failed += 1
            print("chart:", snap["chart_title"])
            print("recorte:", snap["recorte"])
            print("answer:", snap["answer_snip"][:160])
            print("checks:", flags, "=>", "PASS" if ok else "FAIL")
            cases.append({"id": sc["id"], "ok": ok, "flags": list(flags), **snap})
        browser.close()

    report = {"failed": failed, "cases": cases, "ui": UI}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSUMMARY failed={failed} report={OUT}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
