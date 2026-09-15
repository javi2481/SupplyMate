/**
 * Capture README screenshots (requires Chrome + API/UI running).
 *
 *   UI_URL=http://127.0.0.1:8080 node scripts/capture-docs-screens.mjs
 *
 * Needs `playwright` resolvable (npx -p playwright or local install) and
 * `npx playwright install chrome` / system Google Chrome.
 */
import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, "../../docs/assets");
const base = process.env.UI_URL ?? "http://127.0.0.1:8080";
fs.mkdirSync(outDir, { recursive: true });

const storage = {
  threads: [
    {
      id: "shot",
      title: "Qué comprar esta semana",
      messages: [],
      cart: [
        {
          product_id: "6033436",
          product_name: "ISSUE FLOWPACK 6 RUBIO OSCURO",
          barcode: "7793008005537",
          category: "Cuidado del Cabello",
          supplier: "CUENCA (ISSUE)",
          suggested_quantity: 173,
          order_quantity: 173,
          estimated_purchase_value: 783004.92,
        },
        {
          product_id: "8139035",
          product_name: "ZONO PROTEC SOL LOC KIDS FPS50+",
          barcode: "7790299004164",
          category: "Bronceadores",
          supplier: "LABORATORIOS FERRINI",
          suggested_quantity: 167,
          order_quantity: 120,
          estimated_purchase_value: 1800000,
        },
      ],
    },
  ],
  activeId: "shot",
};

const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(base, { waitUntil: "domcontentloaded", timeout: 60_000 });
await page.evaluate((payload) => {
  sessionStorage.setItem("supplymate.chat.threads.v1", JSON.stringify(payload));
}, storage);
await page.reload({ waitUntil: "domcontentloaded" });
await page.waitForTimeout(3500);
await page.screenshot({ path: path.join(outDir, "explore-panel.png") });
await page.locator("button:visible", { hasText: "Revisar OC" }).first().click({ timeout: 15_000 });
await page.waitForTimeout(700);
await page.locator("button:visible", { hasText: "Exportar y terminar" }).click();
await page.waitForSelector("text=Columnas del CSV", { timeout: 15_000 });
await page.screenshot({ path: path.join(outDir, "oc-export-columns.png") });
await browser.close();
console.log("Wrote screenshots to", outDir);
