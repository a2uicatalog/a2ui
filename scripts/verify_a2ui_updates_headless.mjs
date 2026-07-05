// Headless end-to-end verify: an A2UI v1.0 updateDataModel message, applied via
// the engine bridge (A2UIState.applyA2uiUpdate), actually REPAINTS the DOM through
// the real reactive graph (ValueStore -> _set -> registerListener callback). Uses
// the ACTUAL renderer JS (A2UIState.html engine + A2uiUpdates.html applier) in real
// headless chromium — proves the wired receiver, not a unit stub.
// Run: NODE_PATH=/home/curtis/a2ui-private/node_modules node scripts/verify_a2ui_updates_headless.mjs
import { readFileSync } from "fs";
import { createRequire } from "module";
// puppeteer-core lives in the sibling private repo's node_modules (ESM ignores NODE_PATH)
const require = createRequire(import.meta.url);
const puppeteer = require("/home/curtis/a2ui-private/node_modules/puppeteer-core");

const DIR = new URL("../apps-script-surface/gas-wired-renderer/", import.meta.url);
const scriptOf = (name) => {
  const h = readFileSync(new URL(name, DIR), "utf8");
  return h.slice(h.indexOf("<script>") + 8, h.lastIndexOf("</script>"));
};
const engineJS = scriptOf("A2UIState.html");
const applierJS = scriptOf("A2uiUpdates.html");

const browser = await puppeteer.launch({
  executablePath: "/usr/bin/chromium", headless: true,
  args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
});
let fail = 0;
try {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.setContent('<!doctype html><meta charset="utf-8"><div id="out">?</div>');
  await page.addScriptTag({ content: engineJS });
  await page.addScriptTag({ content: applierJS });
  // Boot the REAL engine with a ValueStore + a DOM subscriber wired exactly the way
  // an atom binds (registerListener -> update textContent). This IS the repaint path.
  await page.evaluate(() => {
    const engine = new A2UIStateEngine({
      state_primitives: [{ id: "msg_count", primitive: "ValueStore", props: { initialValue: 0 } }],
      actions: [],
    });
    engine.registerListener("msg_count", "value", (v) => {
      document.getElementById("out").textContent =
        (v && typeof v === "object") ? JSON.stringify(v) : String(v);
    });
    window.__engine = engine;
  });
  const read = () => page.$eval("#out", (el) => el.textContent);
  const step = async (name, mutate, want) => {
    if (mutate) await page.evaluate(mutate);
    const got = await read();
    const ok = got === want;
    console.log((ok ? "  ✓ " : "  ✗ ") + name + (ok ? "" : `  got ${got} want ${want}`));
    if (!ok) fail++;
  };

  await step("initial render (ValueStore initialValue=0)", null, "0");
  await step("updateDataModel /msg_count value=42 repaints",
    () => window.__engine.applyA2uiUpdate({ version: "v1.0", updateDataModel: { surfaceId: "s", path: "/msg_count", value: 42 } }),
    "42");
  await step("updateDataModel /msg_count value={a:1}",
    () => window.__engine.applyA2uiUpdate({ version: "v1.0", updateDataModel: { surfaceId: "s", path: "/msg_count", value: { a: 1 } } }),
    JSON.stringify({ a: 1 }));
  await step("deep-path patch /msg_count/a value=9 repaints",
    () => window.__engine.applyA2uiUpdate({ version: "v1.0", updateDataModel: { surfaceId: "s", path: "/msg_count/a", value: 9 } }),
    JSON.stringify({ a: 9 }));

  if (errors.length) { console.log("  page errors: " + errors.join(" | ")); fail += errors.length; }
  console.log(`\n${fail ? "✗" : "✓"} headless repaint verify: ${fail ? "FAILED" : "all steps repainted"}`);
} finally {
  await browser.close();
}
process.exit(fail ? 1 : 0);
