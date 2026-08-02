import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from _lib import spec
atoms = spec()
if not atoms: print("spec.json empty"); print("n/a"); raise SystemExit
S = ["web","google-apps-script-web","mcp-apps","google-meet-stage","google-chat","pdf","email"]
reach = {s: sum(1 for a in atoms if s in ((a.get("surfaces") or {}).get("works_on") or []))/len(atoms) for s in S}
worst = sorted(reach.items(), key=lambda kv: kv[1])[:3]
print("weakest: " + ", ".join(f"{k} {v*100:.0f}%" for k,v in worst))
print(sum(reach.values())/len(reach))
