import json, sys, urllib.request; sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from _lib import get, BASE, UA
paths = ["/openapi.json","/spec.json","/llms.txt","/.well-known/ai-catalog.json",
         "/catalogue/index.json","/.well-known/mcp.json","/agents.md"]
ok = [p for p in paths if get(p)[0]==200]
try:
    r = urllib.request.Request(BASE+"/api/render", method="POST",
        data=json.dumps({"blocks":[{"type":"paragraph","text":"probe"}]}).encode(),
        headers={"Content-Type":"application/json", **UA})
    with urllib.request.urlopen(r, timeout=25) as resp: render = resp.status==200
except Exception: render = False
print(f"{len(ok)}/{len(paths)} discovery docs reachable by stdlib; render={'ok' if render else 'FAIL'}")
print(len(ok)/len(paths)*0.6 + (0.4 if render else 0.0))
