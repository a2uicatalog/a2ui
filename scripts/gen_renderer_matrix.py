#!/usr/bin/env python3
"""Renderer matrix generator (PUBLIC, deterministic, offline; stdlib + yaml.safe_load only).

Reads ONLY committed files:
  atoms/renderers.yaml              registry (renderers, rules version, `measured:` flag per renderer)
  data/renderer-results/*.json      RAW RESULTS per renderer (schema: docs/renderer-matrix.md)
  data/renderer-results/manifest.json
  atoms/schema.yaml                 the stable atom list (stage: stable or no stage)
  public/catalogue/a2ui-atoms-v1.json   (only to build the x-renderers draft copy)

Writes:
  public/catalogue/renderer-matrix-v1.json
  public/catalogue/a2ui-atoms-v1.renderers-draft.json   (live catalogue + derived `x-renderers`)

It never writes the live catalogue or spec.json. The output holds no wall-clock time and no
path: every date comes from the raw results.

Status rules (registry `rules.version` 2; v2 design item H4):
  web:     painted check failed                          -> not_supported
           pixel fail outside the allowance, overflow at 360, contrast worse than React,
           behaviour differs from React                  -> drawn_with_differences
           no visible text, blank on both sides, or any check recorded `unstable`
                                                         -> not_verified
           everything passes (or is not applicable)      -> drawn
           no example in the gate data                   -> not_measured
  flutter: painted + own type                            -> native
           basic_lowered                                 -> degraded
           unsupported / unsupported_other               -> not_supported
           invalid_payload / no case                     -> not_measured (invalid example / no example)
  compose: painted (the atom's own type is a Basic component)  -> native
           unsupported (type not in the Basic catalog)           -> not_supported
           no case                                              -> not_measured
  Several cases: the WORST case wins. The per-check results of that case are stored.
  An allowance-listed check records `unstable`, never `pass`.
"""
import hashlib
import json
import os
import sys

import yaml

WT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(WT, "atoms/renderers.yaml")
SCHEMA = os.path.join(WT, "atoms/schema.yaml")
RESDIR = os.path.join(WT, "data/renderer-results")
CAT = os.path.join(WT, "public/catalogue/a2ui-atoms-v1.json")
OUT_MATRIX = os.path.join(WT, "public/catalogue/renderer-matrix-v1.json")
OUT_DRAFT = os.path.join(WT, "public/catalogue/a2ui-atoms-v1.renderers-draft.json")

ENVS = ["light480", "dark480", "light360", "dark360"]
WEB_STATUSES = ["drawn", "drawn_with_differences", "not_verified", "not_supported", "not_measured"]
FLUTTER_STATUSES = ["native", "degraded", "not_supported", "not_measured"]
COMPOSE_STATUSES = ["native", "not_supported", "not_measured"]
KIND_STATUSES = {"web": WEB_STATUSES, "flutter": FLUTTER_STATUSES, "compose": COMPOSE_STATUSES}
# behaviour tokens that do not make an atom differ from React: `n/a (no probe)` (no probe exists) and
# `not_run` (the behaviour lane was not run for this measurement; shown as such, never as a pass)
BEHAVIOUR_NEUTRAL = ("SAME", "INERT", "n/a (no probe)", "not_run")
STATUS_LABEL = {
    "drawn": "Drawn", "drawn_with_differences": "Drawn with differences", "not_verified": "Not verified",
    "native": "Native", "degraded": "Degraded", "not_supported": "Not supported", "not_measured": "Not measured",
}
STATUS_HELP = {
    "drawn": "drawn by the renderer; every check passed",
    "drawn_with_differences": "drawn, but at least one check differs from React (pixels, overflow at 360, contrast or behaviour)",
    "not_verified": "no difference found, but the atom could not be verified (no visible text, blank on both sides, or an unstable check)",
    "native": "drawn by the renderer's own implementation of the atom (Compose: by a Basic component, the atom's root type)",
    "degraded": "drawn through Basic components, not the atom's own implementation",
    "not_supported": "draws nothing or errors",
    "not_measured": "no per-atom data (no example, or the example is invalid)",
}
WEB_WORST = {"drawn": 0, "not_verified": 1, "drawn_with_differences": 2, "not_supported": 3}
FL_STATUS = {"painted": "native", "basic_lowered": "degraded", "unsupported": "not_supported",
             "unsupported_other": "not_supported", "invalid_payload": "not_measured"}
FL_WORST = {"native": 0, "degraded": 1, "not_measured": 2, "not_supported": 3}


def load_json(p):
    with open(p, encoding="utf8") as f:
        return json.load(f)


def load_yaml(p):
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)  # CSafeLoader = the C build of SafeLoader
    with open(p, encoding="utf8") as f:
        return yaml.load(f, Loader=loader)


def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def stable_atoms(schema=None):
    s = schema if schema is not None else load_yaml(SCHEMA)
    return sorted(b["type"] for b in s["blocks"] if b.get("stage", "stable") == "stable")


# ---------------------------------------------------------------- web


def contrast_result(low, low_ref):
    if low is None:
        return "n/a"
    if low == 0:
        return "pass"
    if low_ref is None:
        return "not_compared"
    return "inherited" if low <= low_ref else "worse"


def web_case_status(case):
    """-> (status, reasons[], derived_checks). Pure function of one raw case."""
    ck = case["checks"]
    reasons = []
    painted = ck["painted"]["result"]
    if painted != "pass":
        reasons.append("painted_fail_" + (ck["painted"].get("error_code") or "error"))
    tv = ck["text_visible"]
    if tv.get("allowance"):
        text = "unstable"
    else:
        text = "pass" if tv["loose"] else "no_visible_text"
    pixel, contrast = {}, {}
    blank = []
    for env in ENVS:
        p = ck["pixel"].get(env, {"result": "not_a_lane"})
        raw = p["result"]
        if raw == "not_a_lane":
            pixel[env] = "n/a"
            contrast[env] = "n/a"
            continue
        if p.get("allowance"):
            pixel[env] = "unstable"
        else:
            pixel[env] = raw  # pass | fail | blank_both | reference
        if raw == "blank_both":
            blank.append(env)
        contrast[env] = contrast_result(p.get("low"), p.get("low_ref"))
    ov = ck.get("overflow_360") or {}
    vals = [v for v in ov.values() if v is not None]
    overflow = "n/a" if not vals else ("fail" if any(vals) else "pass")
    beh = ck["behaviour"]
    derived = {
        "painted": painted, "text_visible": text, "pixel": pixel, "overflow_360": overflow,
        "contrast": contrast, "behaviour": beh, "stability": ck["stability"],
    }
    diffs = ["pixel_fail_" + e for e in ENVS if pixel[e] == "fail"]
    if overflow == "fail":
        diffs.append("overflow_360")
    diffs += ["contrast_worse_" + e for e in ENVS if contrast[e] == "worse"]
    if beh not in BEHAVIOUR_NEUTRAL:
        diffs.append("behaviour_differs")
    nverified = []
    if text == "no_visible_text":
        nverified.append("no_visible_text")
    if text == "unstable":
        nverified.append("unstable_text")
    nverified += ["blank_both_" + e for e in blank]
    nverified += ["unstable_pixel_" + e for e in ENVS if pixel[e] == "unstable"]
    if painted != "pass":
        status = "not_supported"
    elif diffs:
        status = "drawn_with_differences"
    elif nverified:
        status = "not_verified"
    else:
        status = "drawn"
    if status != "not_supported":
        reasons += diffs + nverified
    return status, sorted(set(reasons)), derived


# ---------------------------------------------------------------- flutter


def flutter_case_status(case):
    ck = case["checks"]
    pr = ck["painted"]
    raw = pr["result"]
    status = FL_STATUS[raw]
    if raw == "painted" and not pr.get("own_type_present"):
        status = "degraded"
    reasons = {"painted": ["lane_painted_own_type"], "basic_lowered": ["lowered_to_basic"],
               "unsupported": ["unknown_component_type"], "unsupported_other": ["nested_type_unknown"],
               "invalid_payload": ["invalid_example"]}[raw]
    derived = {"painted": raw, "own_type_present": bool(pr.get("own_type_present")), "text_chars": pr.get("text_chars"),
               "error_codes": list(pr.get("error_codes", [])), "parity_text": ck.get("parity_text")}
    return status, reasons, derived


# ---------------------------------------------------------------- compose


def compose_case_status(case):
    """Compose has no implementation of our atoms: a case only draws when the atom's root is a Basic component."""
    ck = case["checks"]
    pr = ck["painted"]
    raw = pr["result"]
    if raw == "painted":
        status, reasons = "native", ["basic_component_rendered"]
    elif raw == "unsupported":
        status, reasons = "not_supported", ["unknown_component_type"]
    else:
        raise ValueError("unknown compose painted status %r" % raw)
    derived = {"painted": raw, "own_type_present": bool(pr.get("own_type_present")), "text_chars": pr.get("text_chars"),
               "error_codes": list(pr.get("error_codes", [])), "parity_text": ck.get("parity_text"),
               "basic_lane": ck.get("basic_lane")}
    return status, reasons, derived


# ---------------------------------------------------------------- assembly


def entry_for(kind, head, atom_rec):
    """The matrix entry for one (atom, renderer), derived from the raw record."""
    base = {
        "run_id": head["run_id"], "measured": head["measured_date"], "renderer_version": head["renderer_version"],
        "measured_on": head["measured_on"], "core_sha256": head.get("core_sha256"),
    }
    cases = atom_rec.get("cases") or {}
    if not cases:
        return dict(status="not_measured", reasons=["no_example"], cases=0, worst_case=None, dialect=head["dialect"],
                    checks=None, **base)
    fn = {"web": web_case_status, "flutter": flutter_case_status, "compose": compose_case_status}[kind]
    worst_rank = WEB_WORST if kind == "web" else FL_WORST
    results = []
    for cid in sorted(cases):
        st, reasons, derived = fn(cases[cid])
        results.append((worst_rank[st], cid, st, reasons, derived, cases[cid].get("dialect") or head["dialect"]))
    results.sort(key=lambda r: (-r[0], r[1]))
    _, cid, st, reasons, derived, dialect = results[0]
    return dict(status=st, reasons=reasons, cases=len(cases), worst_case=cid, dialect=dialect, checks=derived, **base)


def counts(statuses, per_atom):
    c = {s: 0 for s in statuses}
    for v in per_atom.values():
        c[v["status"]] += 1
    c["total"] = len(per_atom)
    return c


def build(registry, raw, manifest, stable):
    """registry: parsed renderers.yaml; raw: {rid: results dict}; -> matrix dict (pure)."""
    order = [r["id"] for r in registry["renderers"]]
    per, renderers = {}, {}
    for r in registry["renderers"]:
        rid = r["id"]
        kind = r["kind"]
        statuses = KIND_STATUSES[kind]
        reg = {k: v for k, v in r.items() if k != "measured"}
        reg["measured"] = bool(r["measured"])
        if not r["measured"]:
            per[rid] = {a: {"status": "not_measured", "reasons": ["renderer_not_measured"], "cases": 0, "worst_case": None,
                            "dialect": None, "checks": None, "run_id": None, "measured": None, "renderer_version": None,
                            "measured_on": None, "core_sha256": None} for a in stable}
            reg["statuses"] = ["not_measured"]
            reg["measurement"] = None
            reg["coverage"] = counts(["not_measured"], per[rid])
        else:
            head = raw[rid]
            per[rid] = {a: entry_for(kind, head, head["atoms"].get(a, {"cases": {}})) for a in stable}
            reg["statuses"] = statuses
            m = manifest["renderers"][rid]
            reg["measurement"] = {
                "run_id": head["run_id"], "measured": head["measured_date"], "renderer_version": head["renderer_version"],
                "dialect": head["dialect"], "reference_renderer": head.get("reference_renderer"),
                "measured_on": head["measured_on"], "commit": head.get("commit"),
                "core_sha256": head.get("core_sha256"), "css_sha256": head.get("css_sha256"),
                "renderer_bundle_sha256": head.get("renderer_bundle_sha256"),
                "results_file_sha256": m["file_sha256"],
            }
            if head.get("facts"):
                reg["measurement"]["facts"] = head["facts"]
            reg["coverage"] = counts(statuses, per[rid])
        renderers[rid] = reg
    return {
        "$schema": "a2ui-renderer-matrix/2",
        "status": "DRAFT, local only, not published",
        "rules_version": registry["rules"]["version"],
        "rules": registry["rules"],
        "dimension": "renderer (what draws the atom); separate from x-surfaces (where the atom appears)",
        "status_labels": STATUS_LABEL,
        "status_help": STATUS_HELP,
        "atom_count": len(stable),
        "trademark_note": registry["trademark_note"],
        "trademark_note_extra": registry["trademark_note_extra"],
        "independence_note": registry["independence_note"],
        "renderers": renderers,
        "atoms": {a: {rid: per[rid][a] for rid in order} for a in stable},
    }


def x_renderers(matrix, atom):
    out = {}
    for rid, e in matrix["atoms"][atom].items():
        out[rid] = {k: e[k] for k in ("status", "reasons", "measured", "measured_on", "renderer_version")}
    return out


def build_draft_catalogue(cat, matrix):
    draft = json.loads(json.dumps(cat))
    newc = {}
    for a, comp in draft["components"].items():
        nc = {}
        for k, v in comp.items():
            nc[k] = v
            if k == "x-surfaces":
                nc["x-renderers"] = x_renderers(matrix, a)
        if "x-renderers" not in nc:
            nc["x-renderers"] = x_renderers(matrix, a)
        newc[a] = nc
    draft["components"] = newc
    return draft


def dumps(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False) + "\n"


def load_inputs():
    registry = load_yaml(REG)
    manifest = load_json(os.path.join(RESDIR, "manifest.json"))
    raw = {}
    for r in registry["renderers"]:
        if r["measured"]:
            raw[r["id"]] = load_json(os.path.join(RESDIR, manifest["renderers"][r["id"]]["file"]))
    return registry, raw, manifest


def render_files(registry, raw, manifest, stable, cat):
    """-> {repo-relative path: text} for the two generated catalogue files."""
    matrix = build(registry, raw, manifest, stable)
    draft = build_draft_catalogue(cat, matrix)
    if sorted(draft["components"]) != stable:
        raise SystemExit("live catalogue and atoms/schema.yaml disagree on the stable atom list")
    return {"public/catalogue/renderer-matrix-v1.json": dumps(matrix),
            "public/catalogue/a2ui-atoms-v1.renderers-draft.json": dumps(draft)}, matrix


def main():
    registry, raw, manifest = load_inputs()
    files, matrix = render_files(registry, raw, manifest, stable_atoms(), load_json(CAT))
    for rel, text in files.items():
        with open(os.path.join(WT, rel), "w", encoding="utf8") as f:
            f.write(text)
    for rid, r in matrix["renderers"].items():
        print(rid, {k: v for k, v in r["coverage"].items() if v})


if __name__ == "__main__":
    main()
