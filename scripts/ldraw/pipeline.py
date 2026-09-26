#!/usr/bin/env python3
"""Catalogue pipeline queue for baked LDraw parts: checks -> render -> Gemini QA -> report. Deterministic, resumable.

State lives in scripts/ldraw/qa/queue.json (gitignored working state). Every stage result is stamped with the SHA-256
of the part's baked mesh (public/parts/<id>.json) plus a stage version; a result is valid only while both still match,
so a re-bake that changes a part silently re-queues exactly that part and nothing else. Re-running is always safe.

  status                     counts by state and by stage, what is stale
  run [--stages ...]         run the missing/stale stages (default: checks,render,qa) for every part in the queue
        --only ID ...          restrict to some parts        --model M   Gemini model (default gemini-3.7-flash)
        --cap USD              hard spend cap (shared ledger with gemini_qa.py)   --workers N
  requeue --ids ID ... | --failing | --all [--stage S]   drop stored results so `run` redoes them
  gate                       deterministic checks only, no network; exit 1 if any part has an error-level finding (CI/pytest)
  rebake-diff                re-bake into a temp dir and report parts whose committed mesh differs (needs the LDraw cache)
  report                     write scripts/ldraw/qa/report.md, flags pre-classified as render-limitation vs review

Stages
  checks  scripts/ldraw/part_checks.py (geometry facts, no LLM)
  render  our flat-shaded render of the baked mesh (studs drawn from connectors)
  qa      Gemini compares the render with the Rebrickable photo and only FLAGS; it never changes a part
State of a part: failed (deterministic error) | needs_review (Gemini flagged, checks clean) | clean | pending
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import part_checks  # noqa: E402

PARTS = ROOT / "public" / "parts"
QA = HERE / "qa"
STATE = QA / "queue.json"
VERSIONS = {"checks": 2, "render": 1, "qa": 1}      # bump to invalidate every stored result of a stage
STAGES = ["checks", "render", "qa"]
LIMITATION = re.compile(r"hollow|solid|open stud|low.?poly|facet|logo|stud.*(shape|round|smooth)", re.I)


def part_ids():
    return sorted(json.loads((PARTS / "index.json").read_text())["parts"])


def mesh_sha(pid):
    return hashlib.sha256((PARTS / (pid + ".json")).read_bytes()).hexdigest()[:16]


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(st):
    QA.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1, sort_keys=True))
    tmp.replace(STATE)


def valid(rec, stage, sha, model=None):
    r = (rec or {}).get("stages", {}).get(stage)
    return bool(r) and r.get("sha") == sha and r.get("v") == VERSIONS[stage] and (stage != "qa" or r.get("model") == model)


def classify(rec):
    s = rec.get("stages", {})
    if "checks" in s and any(f["level"] == "error" for f in s["checks"]["findings"]):
        return "failed"
    q = s.get("qa")
    if q and q["verdict"] in ("fail", "warn"):
        return "needs_review"
    if q and q["verdict"] == "error":
        return "pending"
    return "clean" if "checks" in s and q else "pending"


def hint(rec):
    q = rec.get("stages", {}).get("qa")
    if not q or q["verdict"] not in ("fail", "warn"):
        return ""
    issues = q.get("issues") or []
    return "render-limitation?" if issues and all(LIMITATION.search(i) for i in issues) else "review"


def cmd_status(a):
    st, ids = load_state(), part_ids()
    n = {"failed": 0, "needs_review": 0, "clean": 0, "pending": 0}
    stale = {s: 0 for s in STAGES}
    for pid in ids:
        rec = st.get(pid, {})
        sha = mesh_sha(pid)
        n[classify(rec)] += 1
        for s in STAGES:
            if not valid(rec, s, sha, a.model):
                stale[s] += 1
    print("parts %d | %s" % (len(ids), " | ".join("%s %d" % kv for kv in n.items())))
    print("stages needing work: " + ", ".join("%s %d" % kv for kv in stale.items()))


def run_checks(pid, rec, sha):
    findings, metrics = part_checks.check_id(pid)
    rec.setdefault("stages", {})["checks"] = {"sha": sha, "v": VERSIONS["checks"], "findings": findings, "metrics": metrics}


def cmd_run(a):
    import gemini_qa as gq
    ids = a.only or part_ids()
    stages = a.stages.split(",")
    st = load_state()
    todo_qa = []
    for pid in ids:
        rec, sha = st.setdefault(pid, {}), mesh_sha(pid)
        if "checks" in stages and not valid(rec, "checks", sha):
            run_checks(pid, rec, sha)
        if "render" in stages and not valid(rec, "render", sha):
            gq.OUT.mkdir(parents=True, exist_ok=True)
            (gq.OUT / "renders").mkdir(exist_ok=True)
            gq.render(part_checks.load(pid)).save(gq.OUT / "renders" / (pid + ".png"))
            rec.setdefault("stages", {})["render"] = {"sha": sha, "v": VERSIONS["render"]}
        if "qa" in stages and not valid(rec, "qa", sha, a.model):
            checks = rec.get("stages", {}).get("checks")
            if checks and any(f["level"] == "error" for f in checks["findings"]) and not a.force:
                continue                                    # fix deterministic errors first; don't pay to describe a known-bad part
            todo_qa.append(pid)
    save_state(st)
    print("checks/render done; qa queue: %d parts (batch size %d)" % (len(todo_qa), a.batch))
    if not todo_qa:
        return
    gq.MODEL = a.model
    gq.PRICE_IN, gq.PRICE_OUT = gq.PRICES[a.model]
    meter = gq.Meter(a.cap)
    key = gq.get_key()
    rb_key = None if a.no_ref else gq._gcloud(["secrets", "versions", "access", "latest", "--secret=rebrickable", "--project", gq.PROJECT]).strip()

    def fetch(pid):
        mesh = part_checks.load(pid)
        img = gq.Image.open(gq.OUT / "renders" / (pid + ".png")).convert("RGB")
        ref = None if a.no_ref else gq.rebrickable_image(pid, rb_key)
        return pid, mesh, img, ref

    with ThreadPoolExecutor(a.workers) as ex:
        fetched = list(ex.map(fetch, todo_qa))
    batches = [fetched[i:i + a.batch] for i in range(0, len(fetched), max(1, a.batch))]

    def work_batch(batch):
        items = [(mesh, img, ref) for _, mesh, img, ref in batch]
        try:
            results = [gq.ask(key, meter, *items[0])] if len(items) == 1 else gq.ask_batch(key, meter, items)
        except SystemExit:
            raise
        except Exception as e:
            msg = str(e).replace(key, "[redacted]")[:120]
            results = [{"verdict": "error", "issues": [msg]}] * len(items)
        return [(pid, r) for (pid, _, _, _), r in zip(batch, results)]

    try:
        with ThreadPoolExecutor(a.workers) as ex:
            for batch_results in ex.map(work_batch, batches):
                for pid, r in batch_results:
                    st[pid].setdefault("stages", {})["qa"] = {"sha": mesh_sha(pid), "v": VERSIONS["qa"], "model": a.model,
                        "verdict": r["verdict"], "issues": r.get("issues", []), "matches_reference": r.get("matches_reference"),
                        "at": int(time.time())}
                    save_state(st)
                    print("%-8s %-5s %s ($%.3f)" % (pid, r["verdict"], "; ".join(r.get("issues", []))[:80], meter.spent), flush=True)
    finally:
        save_state(st)
        print("spent $%.4f of $%.2f" % (meter.spent, a.cap))


def cmd_seed_qa(a):
    """Import verdicts from a gemini_qa.py results file so already-paid QA is not repeated. Parts whose mesh changed
    since (per --changed) are skipped so they get re-QA'd."""
    res = json.loads(Path(a.file).read_text())
    st, n = load_state(), 0
    for pid, r in res.items():
        if r.get("verdict") == "error" or pid in (a.changed or []):
            continue
        st.setdefault(pid, {}).setdefault("stages", {})["qa"] = {"sha": mesh_sha(pid), "v": VERSIONS["qa"], "model": a.model,
            "verdict": r["verdict"], "issues": r.get("issues", []), "matches_reference": r.get("matches_reference"), "at": 0}
        n += 1
    save_state(st)
    print("seeded %d QA verdicts (%s)" % (n, a.model))


def cmd_requeue(a):
    st = load_state()
    ids = list(st) if a.all else (a.ids or [p for p, r in st.items() if classify(r) in ("failed", "needs_review", "pending")])
    for pid in ids:
        if pid in st:
            if a.stage:
                st[pid].get("stages", {}).pop(a.stage, None)
            else:
                st[pid] = {}
    save_state(st)
    print("requeued %d parts%s" % (len(ids), " (stage %s)" % a.stage if a.stage else ""))


def cmd_gate(a):
    bad = 0
    for pid in part_ids():
        f, _ = part_checks.check_id(pid)
        errs = [x for x in f if x["level"] == "error"]
        if errs:
            bad += 1
            print("ERROR %s: %s" % (pid, "; ".join("%s: %s" % (x["check"], x["msg"]) for x in errs)))
    print("gate: %d/%d parts with error-level findings" % (bad, len(part_ids())))
    return 1 if bad else 0


def cmd_rebake_diff(a):
    lib = HERE / "_ldraw_cache" / "ldraw"
    if not lib.exists():
        print("LDraw library not fetched (scripts/ldraw/fetch_library.py)")
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        text = (HERE / "bake_parts.py").read_text().replace('OUT_DIR = os.path.join(ROOT, "public", "parts")', "OUT_DIR = %r" % tmp)
        script = HERE / "_bake_tmp.py"
        script.write_text(text)
        try:
            r = subprocess.run([sys.executable, str(script)], cwd=HERE, env={**__import__("os").environ, "LDRAW_DIR": str(lib)},
                               capture_output=True, text=True)
        finally:
            script.unlink(missing_ok=True)
        if r.returncode:
            print(r.stdout + r.stderr)
            return 2
        changed = [pid for pid in part_ids() if json.loads((Path(tmp) / (pid + ".json")).read_text()) != json.loads((PARTS / (pid + ".json")).read_text())]
    print("re-bake differs from committed for %d parts: %s" % (len(changed), ", ".join(changed) or "none"))
    return 1 if changed else 0


def cmd_report(a):
    st = load_state()
    rows, lines = [], []
    for pid in part_ids():
        rec = st.get(pid, {})
        s = rec.get("stages", {})
        c = classify(rec)
        if c in ("failed", "needs_review"):
            det = "; ".join("%s: %s" % (f["check"], f["msg"]) for f in s.get("checks", {}).get("findings", []) if f["level"] == "error")
            q = s.get("qa") or {}
            rows.append((c, hint(rec), pid, json.loads((PARTS / (pid + ".json")).read_text())["title"], det, "; ".join(q.get("issues", []))))
    order = {"failed": 0, "needs_review": 1}
    rows.sort(key=lambda r: (order[r[0]], r[1] != "review", r[2]))
    counts = {}
    for pid in part_ids():
        counts[classify(st.get(pid, {}))] = counts.get(classify(st.get(pid, {})), 0) + 1
    lines.append("# Part catalogue report\n\n%s\n" % ", ".join("%s: %d" % kv for kv in sorted(counts.items())))
    lines.append("| state | hint | part | title | deterministic | Gemini |\n|---|---|---|---|---|---|")
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s |" % tuple(x.replace("|", "/") for x in r))
    (QA / "report.md").write_text("\n".join(lines) + "\n")
    print("wrote", QA / "report.md", "-", len(rows), "flagged of", len(part_ids()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("status", "run", "requeue", "gate", "rebake-diff", "report", "seed-qa"):
        sp = sub.add_parser(name)
        sp.add_argument("--model", default="gemini-3.7-flash")
        if name == "run":
            sp.add_argument("--stages", default="checks,render,qa")
            sp.add_argument("--only", nargs="*")
            sp.add_argument("--cap", type=float, default=15.0)
            sp.add_argument("--workers", type=int, default=3)
            sp.add_argument("--force", action="store_true")
            sp.add_argument("--batch", type=int, default=6,
                            help="parts per Gemini QA call (amortises fixed prompt overhead; 1 disables batching)")
            sp.add_argument("--no-ref", action="store_true",
                            help="skip the Rebrickable reference photo (halves image tokens/part and removes its "
                                 "1 req/sec throttle -- lower marginal QA value for parts on an already-proven "
                                 "bake path, e.g. a library-wide expansion of an existing family)")
        if name == "seed-qa":
            sp.add_argument("file")
            sp.add_argument("--changed", nargs="*")
        if name == "requeue":
            sp.add_argument("--ids", nargs="*")
            sp.add_argument("--all", action="store_true")
            sp.add_argument("--failing", action="store_true")
            sp.add_argument("--stage", choices=STAGES)
    a = ap.parse_args()
    rc = {"status": cmd_status, "run": cmd_run, "requeue": cmd_requeue, "gate": cmd_gate, "rebake-diff": cmd_rebake_diff,
          "report": cmd_report, "seed-qa": cmd_seed_qa}[a.cmd](a)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
