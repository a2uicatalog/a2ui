#!/usr/bin/env python3
"""PRIVATE-HARNESS-ONLY exporter: gate outputs -> data/renderer-results/*.json.

*** Not run in CI. *** It reads the private measurement harness output directories (the web
gate baselines and the Flutter lane results) and writes the committed RAW RESULTS files that
the public generator (scripts/gen_renderer_matrix.py) and the offline check
(scripts/check_renderer_matrix.py) read. Run it by hand on the machine that holds the
harness output; commit the files it writes.

What it guarantees about its output (the public repo must be able to hold it):
  * only atoms in the public stable catalogue (stage: stable, or no stage, in
    atoms/schema.yaml) are exported; every other atom in the gate data is dropped;
  * evidence is enumerated codes and numbers; harness free text is never copied
    (Flutter error messages, text samples and web text hashes are discarded);
  * no file path, host name or unpushed commit SHA is written. Runs measured on a commit that
    is on no remote are labelled `measured_on: preview-unmerged` and carry no commit SHA;
  * the output is deterministic for a given input (no wall clock).

The schema of the files is documented in docs/renderer-matrix.md. To replace the data later
(for example with the results of a gate run on the shipped commit), write the same schema
from the new run's output: the generator does not change.

Usage:
  python3 scripts/export_renderer_results.py [--work /mnt/hdd2/work] [--flutter-run 20261112-214805]
                                             [--measured-on preview-unmerged] [--only react,lit]
"""
import argparse
import hashlib
import json
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required")

WT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(WT, "atoms/schema.yaml")
OUTDIR = os.path.join(WT, "data/renderer-results")
RESULTS_SCHEMA = "a2ui-renderer-results/1"

ENVS = [("light480", "pixel"), ("dark480", "pixel_dark"), ("light360", "pixel_360"), ("dark360", "pixel_dark360")]
BEHAVIOUR_TOKENS = {"SAME", "INERT", "DIFFERENT", "DIFF", "ran"}
FLUTTER_STATUS = {"painted", "basic_lowered", "unsupported", "unsupported_other", "invalid_payload"}
ERR_CODE = re.compile(r"^[A-Z][A-Z_]{2,40}$")

# rid -> (baseline, detail or None (detail inside the baseline), unstable allowance file, version string,
#         dialect, reference renderer or None)
WEB = {
    "react": ("m5-react/baselines/react.baseline.json", "m5-react/baselines/DETAIL-react.json", "m5-react/unstable/react.json",
              "@a2ui/react 0.15.0 (web_core 0.15.0)", "v1.0", None),
    "lit": ("m5-harness/baselines/lit.baseline.json", None, "m5-harness/unstable/lit.json",
            "@a2ui/lit 0.15.0 (web_core 0.15.0)", "v0.9", "react"),
    "angular": ("m5-angular/baselines/ang.baseline.json", "m5-angular/baselines/DETAIL-ang.json", "m5-angular/unstable/ang.json",
                "@a2ui/angular 0.14.0 (web_core 0.15.0)", "v0.9", "react"),
    "copilotkit": ("m5-ck-gate/baselines/ck.baseline.json", None, "m5-ck-gate/unstable/ck.json",
                   "@copilotkit/a2ui-renderer 1.85.0 (web_core 0.15.0)", "v0.9", "react"),
    "a2ui-vue": ("m5-vue-gate/baselines/vue.baseline.json", None, "m5-vue-gate/unstable/vue.json",
                 "a2ui-vue 0.9.5 (Vue 3.5.13, web_core 0.9.1)", "v0.9", "react"),
}
FLUTTER_VERSION = "a2ui_flutter 0.3.0 (a2ui_core 0.7.0)"


def load(p):
    with open(p, encoding="utf8") as f:
        return json.load(f)


def stable_atoms():
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    with open(SCHEMA, encoding="utf8") as f:
        s = yaml.load(f, Loader=loader)  # CSafeLoader is the C build of SafeLoader
    return sorted(b["type"] for b in s["blocks"] if b.get("stage", "stable") == "stable")


def num(x, nd=6):
    return None if x is None else round(float(x), nd)


def web_case(rid, atom, rec, detail, unstable, has_ref):
    painted = "fail" if (rec.get("error") or rec.get("broken")) else "pass"
    err = "error" if rec.get("error") else ("broken" if rec.get("broken") else None)
    unst_text = atom in unstable.get("atoms", {}).get("custom", [])
    pix, over = {}, {}
    for env, lane in ENVS:
        r = detail.get(lane, {}).get(atom)
        if r is None:
            pix[env] = {"result": "not_a_lane"}
            continue
        if not has_ref:
            res = "reference"
        elif r.get("blank_both"):
            res = "blank_both"
        else:
            res = "pass" if r.get("passed") else "fail"
        pix[env] = {
            "result": res,
            "allowance": atom in unstable.get(lane, []),
            "frac": num(r.get("frac")),
            "hdiff": r.get("hdiff"),
            "one_blank": bool(r.get("one_blank")),
            "low": r.get("low"),
            "low_ref": r.get("low_ref"),
        }
        if env.endswith("360"):
            over[env] = None if r.get("overflow") is None else bool(r["overflow"])
    b = detail.get("behaviour_custom", {}).get(atom)
    if b is None:
        beh = "n/a (no probe)"
    else:
        beh = str(b.get("verdict", "")).split(":")[0]
        if beh not in BEHAVIOUR_TOKENS:
            sys.exit("unknown behaviour verdict token %r for %s/%s; extend BEHAVIOUR_TOKENS deliberately" % (beh, rid, atom))
    allow = unst_text or any(p.get("allowance") for p in pix.values())
    return {
        "dialect": None,  # filled by caller (file level)
        "checks": {
            "painted": {"result": painted, "error_code": err},
            "text_visible": {"loose": bool(rec.get("loose")), "strict": bool(rec.get("strict")),
                             "strict_text": bool(rec.get("strict_text")), "allowance": unst_text},
            "pixel": pix,
            "overflow_360": over,
            "behaviour": beh,
            "stability": "allowance_listed" if allow else "stable",
        },
    }


def export_web(rid, work, public, measured_on):
    bpath, dpath, upath, version, dialect, ref = WEB[rid]
    base = load(os.path.join(work, bpath))
    detail = load(os.path.join(work, dpath)) if dpath else base["detail"]
    unstable = load(os.path.join(work, upath))
    code = base["code"]
    date = base["date"]
    run_id = "%s-%s" % (rid, re.sub(r"[-:]", "", date))
    atoms = {}
    for atom in public:
        rec = detail["custom"].get(atom)
        if rec is None:
            atoms[atom] = {"cases": {}, "no_case": "no_example"}
            continue
        c = web_case(rid, atom, rec, detail, unstable, ref is not None)
        c["dialect"] = dialect
        atoms[atom] = {"cases": {atom: c}}
    head = {
        "schema": RESULTS_SCHEMA,
        "renderer": rid,
        "kind": "web",
        "renderer_version": version,
        "dialect": dialect,
        "reference_renderer": ref,
        "measured_date": date[:10],
        "run_id": run_id,
        "measured_on": measured_on,
        "commit": None,  # never an unpushed SHA; fill with a public SHA when measured on a shipped commit
        "core_sha256": code["core_sha256"],
        "css_sha256": code["css_sha256"],
        "renderer_bundle_sha256": code.get("bundle_sha256"),
        "case_sha256": None,  # pending the public case generator (design item 1)
        "wall_seconds": (base.get("timings_s") or {}).get("total"),
    }
    return head, atoms


def export_flutter(work, public, run, measured_on):
    base = os.path.join(work, "flutter-m4/cloudci/runs", run, "results/lane-results.json")
    res = load(base)["results"]
    parity = {}
    with open(os.path.join(work, "flutter-m4/audit/parity_sweep.tsv"), encoding="utf8") as f:
        cols = f.readline().rstrip("\n").split("\t")
        for line in f:
            row = dict(zip(cols, line.rstrip("\n").split("\t")))
            parity[row["atom"]] = {k: int(row[k]) for k in ("web_words", "flutter_words", "missing_in_flutter", "extra_in_flutter")}
    pubset = set(public)
    by = {}
    for case, r in sorted(res.items()):
        if r["atom"] in pubset:
            by.setdefault(r["atom"], {})[case] = r
    atoms = {}
    for atom in public:
        cases = by.get(atom)
        if not cases:
            atoms[atom] = {"cases": {}, "no_case": "no_example"}
            continue
        out = {}
        for case, r in cases.items():
            if r["status"] not in FLUTTER_STATUS:
                sys.exit("unknown flutter lane status %r" % r["status"])
            codes = sorted(set(r.get("error_codes", [])))
            for c in codes:
                if not ERR_CODE.match(c):
                    sys.exit("error code %r is not an enumerated code; refusing to export free text" % c)
            out[case] = {
                "dialect": "v1.0",
                "checks": {
                    "painted": {"result": r["status"], "own_type_present": bool(r.get("own_type_present")),
                                "text_chars": r.get("text_chars"), "error_codes": codes},
                    "parity_text": parity.get(atom) if case == atom else None,
                },
            }
        atoms[atom] = {"cases": out}
    head = {
        "schema": RESULTS_SCHEMA,
        "renderer": "flutter",
        "kind": "flutter",
        "renderer_version": FLUTTER_VERSION,
        "dialect": "v1.0",
        "reference_renderer": None,
        "measured_date": "%s-%s-%s" % (run[:4], run[4:6], run[6:8]),
        "run_id": "flutter-%s" % run,
        "measured_on": measured_on,
        "commit": None,
        "core_sha256": None,
        "css_sha256": None,
        "renderer_bundle_sha256": None,
        "case_sha256": None,
        "wall_seconds": None,
    }
    return head, atoms


def dump(head, atoms):
    """Header fields, then one line per atom: stable, diff-friendly, deterministic."""
    lines = ["{"]
    for k, v in head.items():
        lines.append("%s: %s," % (json.dumps(k), json.dumps(v, ensure_ascii=False)))
    lines.append('"atoms": {')
    items = sorted(atoms)
    for i, a in enumerate(items):
        lines.append("%s: %s%s" % (json.dumps(a), json.dumps(atoms[a], sort_keys=True, ensure_ascii=False, separators=(",", ":")),
                                   "," if i < len(items) - 1 else ""))
    lines.append("}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--work", default="/mnt/hdd2/work")
    ap.add_argument("--flutter-run", default="20261112-214805")
    ap.add_argument("--measured-on", default="preview-unmerged", choices=["shipped", "preview-unmerged"],
                    help="web baselines of 2026-11-10/11 were measured on a commit on no remote")
    ap.add_argument("--flutter-measured-on", default="unrecorded", choices=["shipped", "preview-unmerged", "unrecorded"])
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=OUTDIR)
    a = ap.parse_args()
    public = stable_atoms()
    os.makedirs(a.out, exist_ok=True)
    only = set(filter(None, a.only.split(",")))
    manifest_path = os.path.join(a.out, "manifest.json")
    manifest = load(manifest_path) if os.path.exists(manifest_path) else {"schema": "a2ui-renderer-results-manifest/1", "renderers": {}}
    jobs = [(rid, None) for rid in WEB] + [("flutter", None)]
    for rid, _ in jobs:
        if only and rid not in only:
            continue
        head, atoms = export_flutter(a.work, public, a.flutter_run, a.flutter_measured_on) if rid == "flutter" else export_web(rid, a.work, public, a.measured_on)
        text = dump(head, atoms)
        name = rid + ".json"
        with open(os.path.join(a.out, name), "w", encoding="utf8") as f:
            f.write(text)
        manifest["renderers"][rid] = {
            "file": name,
            "file_sha256": sha(text.encode("utf8")),
            "run_id": head["run_id"],
            "measured_date": head["measured_date"],
            "measured_on": head["measured_on"],
            "commit": head["commit"],
            "core_sha256": head["core_sha256"],
            "css_sha256": head["css_sha256"],
            "renderer_bundle_sha256": head["renderer_bundle_sha256"],
            "renderer_version": head["renderer_version"],
            "atoms_total": len(atoms),
            "atoms_with_cases": sum(1 for v in atoms.values() if v["cases"]),
        }
        print("%-11s %d atoms, %d with cases, %d bytes" % (rid, len(atoms), manifest["renderers"][rid]["atoms_with_cases"], len(text)))
    manifest["renderers"] = dict(sorted(manifest["renderers"].items()))
    manifest["stable_atom_count"] = len(public)
    with open(manifest_path, "w", encoding="utf8") as f:
        f.write(json.dumps(manifest, indent=1, sort_keys=True, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
