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
  * no file path, host name or unpushed commit SHA is written. `measured_on: shipped` runs carry the
    public SHA of the shipped commit (passed with --commit); runs measured on a commit that is on no
    remote (`preview-unmerged`) or on a private build (`private-build`) carry no SHA;
  * the output is deterministic for a given input (no wall clock).

The schema of the files is documented in docs/renderer-matrix.md. To replace the data later
(for example a DETERMINISTIC-mode full pass of the web gates) a NEW EXPORT is enough: point
--web-root / --web-run at the new run (same layout: <root>/<renderer dir>/runs/<run>/DETAIL-*.json and
RESULTS-*.json), keep --measured-on shipped and --commit <public sha>; the generator does not change.

Sources (all read-only):
  web (react, lit, angular, a2ui-vue, copilotkit 1.85)  <web-root>/<dir>/runs/<web-run>/{RESULTS,DETAIL}-*.json
  copilotkit 1.87.0 (A2UI 1.0)                          <work>/m5-ck187 raw gate outputs
  flutter                                               <work>/flutter-m4/cloudci/runs/<flutter-run>/results/lane-results.json
                                                        + <work>/flutter-m4/audit/parity_sweep.tsv
  compose                                               <work>/compose-m4/raw/compose.json (+ out/basic_analysis.json counts)

Usage:
  python3 scripts/export_renderer_results.py [--work /mnt/hdd2/work] [--web-root /mnt/hdd2/work/m5-f111]
        [--web-run F] [--measured-on shipped --commit <40-hex>] [--flutter-run 20261113-012244]
        [--only react,lit]
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

# rid -> (renderer dir under the web root, detail file, results file, frozen allowance list (relative to --work),
#         version string, dialect, reference renderer or None, expected package pairs)
# The allowance lists are the FROZEN `orig` lists (derived from the A/B runs before any later extension).
WEB = {
    "react": ("react", "DETAIL-react.json", "RESULTS-react.json", "m5-react/unstable/react.json",
              "@a2ui/react 0.15.0 (web_core 0.15.0)", "v1.0", None, {"@a2ui/react": "0.15.0", "@a2ui/web_core": "0.15.0"}),
    "lit": ("lit", "DETAIL-lit.json", "RESULTS-lit.json", "m5-harness/unstable/lit.json",
            "@a2ui/lit 0.15.0 (web_core 0.15.0)", "v0.9", "react", {"@a2ui/lit": "0.15.0", "@a2ui/web_core": "0.15.0"}),
    "angular": ("angular", "DETAIL-ang.json", "RESULTS-ang.json", "m5-angular/unstable/ang.json",
                "@a2ui/angular 0.14.0 (web_core 0.15.0)", "v0.9", "react", {"@a2ui/angular": "0.14.0", "@a2ui/web_core": "0.15.0"}),
    "a2ui-vue": ("vue", "DETAIL-vue.json", "RESULTS-vue.json", "m5-vue-gate/unstable/vue.json",
                 "a2ui-vue 0.9.5 (Vue 3.5.13, web_core 0.9.1)", "v0.9", "react",
                 {"a2ui-vue": "0.9.5", "vue": "3.5.13", "@a2ui/web_core": "0.9.1"}),
}
# CopilotKit 1.87.0 on A2UI 1.0: custom + four pixel lanes only (no behaviour lane was run).
CK187 = {"dir": "m5-ck187", "unstable": "m5-ck-gate/unstable/ck.json", "date": "2026-11-12",
         "version": "@copilotkit/a2ui-renderer 1.87.0 (A2UI 1.0, web_core 0.15.0)", "run_id": "copilotkit-1.87.0-20261112"}
CK187_LANES = [("light480", "pixel", "raw_pixel.json", 480), ("dark480", "pixel_dark", "raw_pixel_dark.json", 480),
               ("light360", "pixel_360", "raw_pixel_360.json", 360), ("dark360", "pixel_dark360", "raw_pixel_dark360.json", 360)]
STRICT_PAINTED_DIR = "a2ui-react-all/review4"  # harness module that defines loose/strict/broken (read-only import)
FLUTTER_VERSION = "a2ui_flutter 0.3.0 (a2ui_core 0.7.0), private build"
COMPOSE_VERSION = "a2ui-kmp 1.0.0-alpha02 (third-party Kotlin Multiplatform rebuild of androidx.a2ui 1.0.0-alpha02; spec v0.9.1 only)"
# Deterministic (det) mode inputs. det key per renderer id; React is the reference and has no parity entry.
DET_KEY = {"lit": "lit", "angular": "ang", "a2ui-vue": "vue"}
DET_LANES = {"light480": "pixel", "dark480": "pixel_dark", "light360": "pixel_360", "dark360": "pixel_dark360"}
DET_DATE = "2026-11-13"
# the two atoms whose Math.random draws are consumed per renderer by the page-global seeded sequence: pixel and text
# parity vs React are excluded (recorded with a note code, never as a failure). Open item: reseed per case in the slicer.
RANDOM_ATOMS = {"gmail_unread_count", "match_exercise"}
NOTE_RANDOM = "seeded_random_order_differs"
DET_FACTS = {"mode": "det-ab", "runs": 2, "chunk_size": 12, "fixed_id_order_required": True, "byte_identical_cells": 15, "cells": 20,
             "rule_identical_cells": 20, "dither_max_pixels": 15, "dither_max_delta_of_765": 2,
             "chunk_1_vs_12_differs_atoms": 10, "chunk_test_atoms": 33}
SHA40 = re.compile(r"^[0-9a-f]{40}$")


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


def web_case(rid, atom, rec, detail, unstable, has_ref, behaviour_run=True):
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
    if not behaviour_run:
        beh = "not_run"  # the lane was not run for this measurement (never "pass")
    elif b is None:
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


def web_head(rid, version, dialect, ref, date, run_id, measured_on, commit, code, wall):
    ext = code.get("extract") or {}
    return {
        "schema": RESULTS_SCHEMA,
        "renderer": rid,
        "kind": "web",
        "renderer_version": version,
        "dialect": dialect,
        "reference_renderer": ref,
        "measured_date": date[:10],
        "run_id": run_id,
        "measured_on": measured_on,
        "commit": commit if measured_on == "shipped" else None,  # never an unpushed SHA
        "core_sha256": code["core_sha256"],
        "css_sha256": code["css_sha256"],
        # the COMMITTED public/surfaces/mcp-apps/renderer-bundle.html hash (not the harness's test bundle)
        "renderer_bundle_sha256": ext.get("committed_bundle_sha256"),
        "case_sha256": None,  # pending the public case generator (design item 1)
        "wall_seconds": wall,
    }


def export_web(rid, work, public, measured_on, root, run, commit):
    d, dname, rname, upath, version, dialect, ref, pkgs = WEB[rid]
    res = load(os.path.join(root, d, "runs", run, rname))
    detail = load(os.path.join(root, d, "runs", run, dname))
    unstable = load(os.path.join(work, upath))
    for k, v in pkgs.items():  # a changed package version must be a deliberate edit of the table
        if res["package"].get(k) != v:
            sys.exit("%s: package %s is %r in the results, the exporter table says %r" % (rid, k, res["package"].get(k), v))
    if not res.get("complete"):
        sys.exit("%s: results are not marked complete" % rid)
    code = res["code"]
    if measured_on == "shipped":
        if code.get("head") != commit or code.get("dirty_tracked"):
            sys.exit("%s: results were measured on %s (dirty=%s), not on the shipped commit %s" % (rid, code.get("head"), code.get("dirty_tracked"), commit))
        if not (code.get("extract") or {}).get("committed_bundle_equals_built"):
            sys.exit("%s: committed bundle does not equal the built bundle in the run" % rid)
    date = res["date"]
    atoms = {}
    for atom in public:
        rec = detail["custom"].get(atom)
        if rec is None:
            atoms[atom] = {"cases": {}, "no_case": "no_example"}
            continue
        c = web_case(rid, atom, rec, detail, unstable, ref is not None)
        c["dialect"] = dialect
        atoms[atom] = {"cases": {atom: c}}
    head = web_head(rid, version, dialect, ref, date, "%s-%s" % (rid, re.sub(r"[-:]", "", date)), measured_on, commit, code,
                    (res.get("timings_s") or {}).get("total"))
    return head, atoms


def det_case(rid, atom, rec, detail, det, stable_ab, has_ref):
    """One web case in det mode. Provenance per check: painted/text_visible/behaviour (and React's own overflow and
    contrast) come from the F111 run ('f111'); pixel parity vs React, overflow, contrast, text parity and stability
    come from the deterministic A/B pass ('det-ab'). The allowance lists play no part: stability is A==B."""
    painted = "fail" if (rec.get("error") or rec.get("broken")) else "pass"
    err = "error" if rec.get("error") else ("broken" if rec.get("broken") else None)
    rnd = atom in RANDOM_ATOMS
    pix, over = {}, {}
    for env, lane in DET_LANES.items():
        if has_ref:
            r = det.get(lane, {}).get(atom)
            if r is None:
                pix[env] = {"result": "not_a_lane"}
                continue
            res = "excluded_random" if rnd else ("blank_both" if r["blank_both"] else ("pass" if r["passed"] else "fail"))
            pix[env] = {"result": res, "allowance": False, "frac": num(r["frac"]), "hdiff": r["hdiff"],
                        "one_blank": bool(r["one_blank"]), "low": r["low"], "low_ref": r["low_ref"]}
            if env.endswith("360"):
                over[env] = bool(r["overflow"])
        else:
            r = detail.get(lane, {}).get(atom)
            if r is None:
                pix[env] = {"result": "not_a_lane"}
                continue
            pix[env] = {"result": "reference", "allowance": False, "frac": None, "hdiff": None, "one_blank": False,
                        "low": r.get("low"), "low_ref": None}
            if env.endswith("360"):
                over[env] = None if r.get("overflow") is None else bool(r["overflow"])
    b = detail.get("behaviour_custom", {}).get(atom)
    if b is None:
        beh = "n/a (no probe)"
    else:
        beh = str(b.get("verdict", "")).split(":")[0]
        if beh not in BEHAVIOUR_TOKENS:
            sys.exit("unknown behaviour verdict token %r for %s/%s" % (beh, rid, atom))
    if not has_ref:
        tp = "n/a"
    elif rnd:
        tp = "excluded_random"
    else:
        tp = "pass" if det["pixel"][atom]["text_same"] else "fail"
    case = {"dialect": None, "checks": {
        "painted": {"result": painted, "error_code": err},
        "text_visible": {"loose": bool(rec.get("loose")), "strict": bool(rec.get("strict")),
                         "strict_text": bool(rec.get("strict_text")), "allowance": False},
        "pixel": pix, "overflow_360": over, "behaviour": beh, "text_parity": tp,
        "stability": "stable",
        "sources": {"painted": "f111", "text_visible": "f111", "behaviour": "f111", "stability": "det-ab",
                    "pixel": "det-ab" if has_ref else "f111",
                    "overflow_360": "det-ab" if has_ref else "f111", "contrast": "det-ab" if has_ref else "f111",
                    "text_parity": "det-ab" if has_ref else "n/a"}}}
    if rnd and has_ref:
        case["notes"] = [NOTE_RANDOM]
    return case


def export_web_det(rid, work, public, measured_on, root, run, commit, det_dir):
    """Web raw results from the F111 run (painted, text, behaviour) plus the deterministic A/B gate (everything else)."""
    head, f111_atoms = export_web(rid, work, public, measured_on, root, run, commit)
    d, dname = WEB[rid][0], WEB[rid][1]
    detail = load(os.path.join(root, d, "runs", run, dname))
    raw = load(os.path.join(det_dir, "det_gate_raw.json"))["renderers"]
    base = load(os.path.join(det_dir, "det_baselines_sha256.json"))
    has_ref = rid != "react"
    det = {}
    if has_ref:
        for lane, v in raw[DET_KEY[rid]].items():
            if not v.get("fail_identical_in_run_B"):
                sys.exit("%s/%s: det fail list differs between run A and run B" % (rid, lane))
            det[lane] = v["atoms"]
    atoms = {}
    for atom in public:
        rec = detail["custom"].get(atom)
        if rec is None:
            atoms[atom] = {"cases": {}, "no_case": "no_example"}
            continue
        c = det_case(rid, atom, rec, detail, det, True, has_ref)
        c["dialect"] = head["dialect"]
        atoms[atom] = {"cases": {atom: c}}
    exc = [k for k in base.get("ab_exceptions", {}) if k.split("/")[0] == (DET_KEY.get(rid) or "react")]
    head["measured_date"] = DET_DATE
    head["run_id"] = "%s-det-ab-%s" % (rid, DET_DATE.replace("-", ""))
    head["facts"] = {"determinism": dict(DET_FACTS, dither_exception_cells=len(exc))}
    return head, atoms


def export_ck187(work, public, root, run, measured_on, commit):
    """CopilotKit 1.87.0 on A2UI 1.0: text lane from the custom run, four pixel lanes from the gate. No
    behaviour lane was run: behaviour is recorded `not_run`. The shipped-commit hashes (core, css,
    committed bundle) come from the React F run's recorded extract, which the report states are the same."""
    base = os.path.join(work, CK187["dir"], "runs")
    custom = load(os.path.join(base, "ck187_full.json"))
    custom = custom.get("cases", custom)
    gate = load(os.path.join(base, "G", "GATE.json"))
    raw_px = {lane: load(os.path.join(base, "G", f)) for env, lane, f, w in CK187_LANES}
    unstable = load(os.path.join(work, CK187["unstable"]))
    S = _strict_painted(work)
    react_res = load(os.path.join(root, "react/runs", run, "RESULTS-react.json"))
    code = react_res["code"]
    if measured_on == "shipped" and code.get("head") != commit:
        sys.exit("copilotkit 1.87: the shipped-commit hashes come from the React run, which was measured on %s" % code.get("head"))
    detail = {"behaviour_custom": {}}
    detail["custom"] = {}
    for k, v in custom.items():
        t = " ".join((v.get("text") or "").split())
        detail["custom"][k] = {"loose": bool(S.loose(v)), "strict": bool(S.strict(k, v)), "strict_text": bool(S.strict_text(k, v)),
                               "broken": bool(S.broken(v)), "error": bool(v.get("error")) or bool(v.get("crashed")) or bool(v.get("errors"))}
    for env, lane, f, width in CK187_LANES:
        det = {}
        for atom, g in gate[lane]["detail"].items():
            r = raw_px[lane].get(atom, {})
            det[atom] = {"blank_both": g["blank_both"], "passed": g["passed"], "frac": g["frac"], "hdiff": g["hdiff"],
                         "one_blank": bool(r.get("one_blank")), "low": g.get("low"), "low_ref": g.get("low_ref"),
                         "overflow": bool(g["sw"] > width)}
        detail[lane] = det
    atoms = {}
    for atom in public:
        rec = detail["custom"].get(atom)
        if rec is None:
            atoms[atom] = {"cases": {}, "no_case": "no_example"}
            continue
        c = web_case("copilotkit", atom, rec, detail, unstable, True, behaviour_run=False)
        c["dialect"] = "v1.0"
        atoms[atom] = {"cases": {atom: c}}
    head = web_head("copilotkit", CK187["version"], "v1.0", "react", CK187["date"], CK187["run_id"], measured_on, commit, code, None)
    return head, atoms


def _strict_painted(work):
    sys.dont_write_bytecode = True
    sys.path.insert(0, os.path.join(work, STRICT_PAINTED_DIR))
    import strict_painted  # the harness's own definition of loose/strict/broken (read-only)
    return strict_painted


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


def export_compose(work, public, measured_on):
    """Compose (a2ui-kmp on Compose Desktop). The source file is already sanitised by its producer; this
    keeps only stable atoms, enumerated codes and numbers, and adds the Basic-lane and behaviour counts
    as header `facts`. Mapping (done by the public generator): painted -> native, unsupported ->
    not_supported, no case -> not_measured."""
    d = os.path.join(work, "compose-m4")
    src = load(os.path.join(d, "raw/compose.json"))
    ba = load(os.path.join(d, "out/basic_analysis.json"))["summary"]
    pubset = set(public)
    atoms = {}
    for atom in public:
        rec = src["atoms"].get(atom)
        if rec is None or not rec.get("cases"):
            atoms[atom] = {"cases": {}, "no_case": "no_example"}
            continue
        out = {}
        for cid, c in rec["cases"].items():
            if cid not in pubset:
                sys.exit("compose raw holds a case of a non-public atom")
            ck = c["checks"]
            pr = ck["painted"]
            if pr["result"] not in ("painted", "unsupported"):
                sys.exit("unexpected compose painted status %r" % pr["result"])
            codes = sorted(set(pr.get("error_codes", [])))
            for x in codes:
                if not ERR_CODE.match(x):
                    sys.exit("error code %r is not an enumerated code" % x)
            pt = ck.get("parity_text") or {}
            bl = ck.get("basic_lane") or {}
            px = (ck.get("pixel") or {}).get("light480") or {}
            out[cid] = {"dialect": "v0.9", "checks": {
                "painted": {"result": pr["result"], "own_type_present": bool(pr.get("own_type_present")),
                            "text_chars": pr.get("text_chars"), "error_codes": codes},
                "parity_text": {k: pt.get(k) for k in ("web_words", "compose_words", "missing_in_compose", "extra_in_compose")} if pt else None,
                "basic_lane": {"rendered": bool(bl.get("rendered")), "text_sha_equal": bool(bl.get("text_sha_equal"))},
                "pixel": {"light480": {"result": px.get("result"), "frac": num(px.get("frac")), "hdiff": px.get("hdiff")}} if px else None,
            }}
        atoms[atom] = {"cases": out}
    stable_basic = [c["checks"]["basic_lane"] for r in atoms.values() for c in r["cases"].values()]
    beh = src["basic_behaviour"]["counts"]
    facts = {
        "basic_lane": {
            "cases": ba["status"].get("rendered", 0) + sum(v for k, v in ba["status"].items() if k != "rendered"),
            "rendered": ba["status"].get("rendered", 0),
            "text_identical_to_react": ba["text_sha_equal"], "loose": ba["loose"], "strict": ba["strict"],
            "strict_text": ba["strict_text"], "broken": ba["broken"],
            "stable_atoms": len(stable_basic), "stable_rendered": sum(1 for b in stable_basic if b["rendered"]),
            "stable_text_identical": sum(1 for b in stable_basic if b["text_sha_equal"]),
        },
        "basic_behaviour": {"probes": sum(beh.values()), "same": beh.get("SAME", 0), "different": beh.get("DIFFERENT", 0),
                            "same_reject": beh.get("SAME_REJECT", 0), "error": beh.get("ERROR", 0), "not_runnable": beh.get("NOT_RUNNABLE", 0)},
    }
    head = {
        "schema": RESULTS_SCHEMA, "renderer": "compose", "kind": "compose", "renderer_version": COMPOSE_VERSION,
        "dialect": "v0.9", "reference_renderer": "react", "measured_date": src["measured_date"], "run_id": src["run_id"],
        "measured_on": measured_on, "commit": None, "core_sha256": None, "css_sha256": None, "renderer_bundle_sha256": None,
        "case_sha256": None, "wall_seconds": None, "facts": facts,
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
    ap.add_argument("--web-root", default="/mnt/hdd2/work/m5-f111", help="root of the web gate run directories")
    ap.add_argument("--web-run", default="F", help="run sub-directory under <web-root>/<renderer>/runs/")
    ap.add_argument("--det-dir", default="/mnt/hdd2/work/m5-det/proposed",
                    help="deterministic A/B gate outputs (det_gate_raw.json, det_baselines_sha256.json); '' = F111 data only")
    ap.add_argument("--flutter-run", default="20261113-012244")
    ap.add_argument("--measured-on", default="shipped", choices=["shipped", "preview-unmerged"],
                    help="web runs: shipped needs --commit (the public SHA the run was measured on)")
    ap.add_argument("--commit", default="f111cde17643744f1e4145297b79c6fa84df38c5", help="public SHA of the shipped commit")
    ap.add_argument("--flutter-measured-on", default="private-build", choices=["shipped", "preview-unmerged", "private-build", "unrecorded"])
    ap.add_argument("--compose-measured-on", default="release-package")
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=OUTDIR)
    a = ap.parse_args()
    public = stable_atoms()
    os.makedirs(a.out, exist_ok=True)
    only = set(filter(None, a.only.split(",")))
    manifest_path = os.path.join(a.out, "manifest.json")
    manifest = load(manifest_path) if os.path.exists(manifest_path) else {"schema": "a2ui-renderer-results-manifest/1", "renderers": {}}
    if a.measured_on == "shipped" and not SHA40.match(a.commit):
        sys.exit("--commit must be a 40-hex public SHA")
    jobs = list(WEB) + ["copilotkit", "flutter", "compose"]
    for rid in jobs:
        if only and rid not in only:
            continue
        if rid == "flutter":
            head, atoms = export_flutter(a.work, public, a.flutter_run, a.flutter_measured_on)
        elif rid == "compose":
            head, atoms = export_compose(a.work, public, a.compose_measured_on)
        elif rid == "copilotkit":
            head, atoms = export_ck187(a.work, public, a.web_root, a.web_run, a.measured_on, a.commit)
        elif a.det_dir:
            head, atoms = export_web_det(rid, a.work, public, a.measured_on, a.web_root, a.web_run, a.commit, a.det_dir)
        else:
            head, atoms = export_web(rid, a.work, public, a.measured_on, a.web_root, a.web_run, a.commit)
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
