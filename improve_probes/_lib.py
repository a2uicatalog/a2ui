"""Shared helpers for improve probes. Each probe prints notes, then a float 0-1
on its LAST line (or 'n/a' if it cannot measure)."""
import json, urllib.request, urllib.error
from pathlib import Path
REPO = Path(__file__).absolute().parent.parent
PRIVATE = REPO.parent / "a2ui-private"
BASE = "https://a2uicatalog.ai"
UA = {"User-Agent": "a2ui-improve-probe/1.0"}
def get(path, timeout=20):
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE+path, headers=UA), timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, b""
    except Exception: return None, b""
def spec():
    p = REPO/"public"/"spec.json"
    return json.loads(p.read_text()).get("atoms", []) if p.exists() else []
def schema():
    import yaml
    return yaml.safe_load((REPO/"atoms"/"schema.yaml").read_text())["blocks"]
