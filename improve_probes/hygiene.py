import subprocess, sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from _lib import REPO, spec, schema
preview = {b["type"] for b in schema() if b.get("stage")=="preview"}
published = {a["type"] for a in spec()}
idx = REPO/"public"/"index.html"; marks = idx.read_text(errors="ignore") if idx.exists() else ""
sig = {
 "no preview atom published": not (preview & published),
 "google disclaimed": "not affiliated" in marks and "Google" in marks,
 "anthropic disclaimed": "Anthropic" in marks,
 "openai disclaimed": "OpenAI" in marks,
 "private tier untracked": subprocess.run(["git","-C",str(REPO),"ls-files","ops/"],capture_output=True,text=True).stdout.strip()=="",
}
bad = [k for k,v in sig.items() if not v]
print(f"failing: {bad}" if bad else "all hygiene signals pass")
print(sum(1 for v in sig.values() if v)/len(sig))
