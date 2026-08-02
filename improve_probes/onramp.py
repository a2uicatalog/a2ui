import json, sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from _lib import get
st, body = get("/openapi.json")
if st != 200: print("openapi.json unreachable"); print(0.0); raise SystemExit
doc = json.loads(body); r = doc.get("paths",{}).get("/api/render",{}).get("post",{})
sig = {
 "render endpoint published": bool(r),
 "worked example in contract": bool(r.get("requestBody",{}).get("content",{}).get("application/json",{}).get("example")),
 "llms.txt served": get("/llms.txt")[0]==200,
 "agents.md served": get("/agents.md")[0]==200,
 "surface parameter offered": "surface" in json.dumps(r.get("parameters",[])) or "surface" in json.dumps(r.get("requestBody",{})),
}
missing = [k for k,v in sig.items() if not v]
print(f"missing: {missing}" if missing else "all onramp signals present")
print(sum(1 for v in sig.values() if v)/len(sig))
