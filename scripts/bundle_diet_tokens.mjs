// Usage: node bundle_diet_tokens.mjs <file.js>  -> prints a hash and count of the acorn token stream (comments ignored).
// Used by tests/test_bundle_diet.py to prove strip_js() leaves the token stream identical.
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
const require = createRequire(import.meta.url);
let acorn;
for (const p of ["acorn", "/usr/share/nodejs/acorn"]) { try { acorn = require(p); break; } catch (e) {} }
if (!acorn) { console.log("NOACORN"); process.exit(0); }
const src = readFileSync(process.argv[2], "utf8");
const h = createHash("sha256");
let n = 0;
for (const t of acorn.tokenizer(src, { ecmaVersion: "latest", sourceType: "script", allowHashBang: true })) {
  h.update(t.type.label + "\u0001" + (t.value === undefined ? "" : (t.value && t.value.pattern !== undefined ? "/" + t.value.pattern + "/" + t.value.flags : String(t.value))) + "\u0002");
  n++;
}
console.log(h.digest("hex"), n);
