// Client-side A2UI incremental-update applier tests — evals the ACTUAL JS out of
// apps-script-surface/gas-wired-renderer/A2uiUpdates.html (no reimplementation)
// and proves it matches the Python reference semantics (renderers/a2ui_v1_updates
// + tests/test_a2ui_v1_updates.py) — so the GAS host and the server agree on how
// updateComponents / updateDataModel / deleteSurface apply.
import { readFileSync } from "fs";

const html = readFileSync(
  new URL("../apps-script-surface/gas-wired-renderer/A2uiUpdates.html", import.meta.url), "utf8");
const js = html.slice(html.indexOf("<script>") + 8, html.indexOf("</script>"));

// eval the IIFE against a fake global; it hangs A2uiUpdates on it.
const g = {};
new Function("globalThis_", js.replace(/typeof window !== 'undefined' \? window : this/, "globalThis_"))(g);
const { stateFromCreate, applyUpdate } = g.A2uiUpdates;

let pass = 0, fail = 0;
const eq = (name, got, want) => {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  console.log((ok ? "  ✓ " : "  ✗ ") + name + (ok ? "" : `\n     got ${JSON.stringify(got)}\n     want ${JSON.stringify(want)}`));
  ok ? pass++ : fail++;
};
const CREATE = { version: "v1.0", createSurface: {
  surfaceId: "s1", catalogId: "a2ui-atoms-v1",
  components: [{ id: "root", component: "Column", children: ["t"] },
              { id: "t", component: "Text", text: "old" }],
  dataModel: { user: { name: "A" }, count: 1 } } };

// updateComponents upserts by id
let st = stateFromCreate(CREATE);
applyUpdate(st, { version: "v1.0", updateComponents: { surfaceId: "s1", components: [
  { id: "t", component: "Text", text: "new" }, { id: "t2", component: "Text", text: "added" }] } });
eq("upsert updates existing", st.components.t.text, "new");
eq("upsert adds new", st.components.t2.text, "added");
eq("upsert leaves others", st.components.root.component, "Column");

// updateDataModel pointer patch + auto-vivify
st = stateFromCreate(CREATE);
applyUpdate(st, { version: "v1.0", updateDataModel: { surfaceId: "s1", path: "/user/name", value: "B" } });
eq("pointer patch", st.dataModel.user.name, "B");
eq("sibling untouched", st.dataModel.count, 1);
applyUpdate(st, { version: "v1.0", updateDataModel: { surfaceId: "s1", path: "/a/b/c", value: 9 } });
eq("auto-vivify deep path", st.dataModel.a.b.c, 9);

// whole-model replace (path '/') + remove (value omitted)
st = stateFromCreate(CREATE);
applyUpdate(st, { version: "v1.0", updateDataModel: { surfaceId: "s1", path: "/", value: { fresh: true } } });
eq("path '/' replaces all", st.dataModel, { fresh: true });
st = stateFromCreate(CREATE);
applyUpdate(st, { version: "v1.0", updateDataModel: { surfaceId: "s1", path: "/count" } });
eq("omitted value removes key", st.dataModel.hasOwnProperty("count"), false);
eq("remove leaves siblings", st.dataModel.user.name, "A");

// deleteSurface tears down
st = stateFromCreate(CREATE);
applyUpdate(st, { version: "v1.0", deleteSurface: { surfaceId: "s1" } });
eq("delete sets flag", st.deleted, true);
eq("delete clears components", st.components, {});

// surfaceId guard
st = stateFromCreate(CREATE);
let threw = false;
try { applyUpdate(st, { version: "v1.0", updateDataModel: { surfaceId: "WRONG", path: "/count", value: 1 } }); }
catch (e) { threw = /surfaceId mismatch/.test(e.message); }
eq("surfaceId guard throws", threw, true);

// full session parity with the Python reference test_full_incremental_session
st = stateFromCreate(CREATE);
[{ updateDataModel: { surfaceId: "s1", path: "/count", value: 2 } },
 { updateComponents: { surfaceId: "s1", components: [{ id: "t", component: "Text", text: "live" }] } },
 { updateDataModel: { surfaceId: "s1", path: "/user", value: { name: "Z" } } }]
  .forEach((m) => applyUpdate(st, { version: "v1.0", ...m }));
eq("session: count", st.dataModel.count, 2);
eq("session: component", st.components.t.text, "live");
eq("session: user", st.dataModel.user, { name: "Z" });

console.log(`\n${fail ? "✗" : "✓"} A2uiUpdates client applier: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
