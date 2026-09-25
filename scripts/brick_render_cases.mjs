// Render brick_build_3d for a list of prop objects using the ACTUAL atoms_brick.gs, print the HTML as JSON.
// Used by tests/test_brick_web_twin.py to hold renderers/web_article.py's twin to the JS source.
// usage: node scripts/brick_render_cases.mjs cases.json
import { readFileSync } from "fs";
import vm from "vm";

const root = new URL("..", import.meta.url);
const gs = readFileSync(new URL("apps-script-surface/gas-wired-renderer/atoms_brick.gs", root), "utf8");
const ctx = { _RENDERERS: {} };
vm.createContext(ctx);
vm.runInContext(gs, ctx);
const cases = JSON.parse(readFileSync(process.argv[2], "utf8"));
process.stdout.write(JSON.stringify(cases.map(b => ctx._RENDERERS.brick_build_3d(b))));
