import re, sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from _lib import REPO, schema
blocks = schema()
rdir = REPO/"apps-script-surface"/"gas-wired-renderer"
bodies = {}
for f in rdir.glob("*.gs"):
    if f.name == "atoms_schema_snapshot.gs": continue
    t = f.read_text(errors="ignore")
    for m in re.finditer(r"_RENDERERS\[\s*['\"]([a-z0-9_]+)['\"]\s*\]\s*=\s*function", t):
        n = t.find("_RENDERERS[", m.end()); bodies[m.group(1)] = t[m.start(): n if n>0 else len(t)]
DEP = ["DriveApp","GmailApp","SpreadsheetApp","CalendarApp","DocumentApp","SlidesApp","FormApp",
       "MailApp","Session.getActiveUser","AdminDirectory","PropertiesService","CacheService",
       "UrlFetchApp","LockService","ScriptApp","google.script.run","runCustomScript","_gpGenerate"]
gas_only = [b["type"] for b in blocks if set((b.get("surfaces") or {}).get("works_on") or []) == {"google-apps-script-web","mcp-apps"}]
unjust = [t for t in gas_only if not any(k in bodies.get(t,"") for k in DEP)]
print(f"{len(unjust)}/{len(blocks)} atoms GAS-only with no GAS dependency")
print(1 - len(unjust)/len(blocks))
