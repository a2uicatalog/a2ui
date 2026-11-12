#!/usr/bin/env python3
"""Renderer matrix generator (DRAFT, stdlib only, deterministic, no network).

Reads the renderer registry (atoms/renderers.yaml) and the read-only gate results
of each renderer, and writes two NEW files:

  public/catalogue/renderer-matrix-v1.json
  public/catalogue/a2ui-atoms-v1.renderers-draft.json   (live catalogue + `x-renderers` per atom)

It never writes public/catalogue/a2ui-atoms-v1.json. Only the PUBLIC atoms (the keys of
components in that file) are emitted; the lane data also holds non-public atoms, which are
dropped. Output contains no wall-clock time: dates come from the data.

Status vocabulary (per atom and renderer):
  native         drawn by the renderer's own implementation of the atom
  degraded       drawn through Basic components
  not_supported  draws nothing or errors
  not_measured   no per-atom data

Mapping (see README.md in the draft folder for the ambiguities):
  web renderers (react, lit, angular, copilotkit, a2ui-vue), `custom` lane detail record:
     error or broken            -> not_supported
     otherwise                  -> native
     pixel parity with React, behaviour probe, loose/strict flags, allowance lists are
     evidence text only, never status.
  flutter, lane-results.json case status:
     painted (own type present) -> native;  basic_lowered -> degraded
     unsupported / unsupported_other / invalid_payload -> not_supported
     no lane case -> not_measured
"""
import glob
import json
import os
import re
import sys

WT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(WT, "public/catalogue/a2ui-atoms-v1.json")
REG = os.path.join(WT, "atoms/renderers.yaml")
OUT_MATRIX = os.path.join(WT, "public/catalogue/renderer-matrix-v1.json")
OUT_DRAFT = os.path.join(WT, "public/catalogue/a2ui-atoms-v1.renderers-draft.json")
W = "/mnt/hdd2/work"
SRC = {
    "react": (f"{W}/m5-react/baselines/react.baseline.json", f"{W}/m5-react/baselines/DETAIL-react.json", f"{W}/m5-react/unstable/react.json"),
    "lit": (f"{W}/m5-harness/baselines/lit.baseline.json", None, f"{W}/m5-harness/unstable/lit.json"),
    "angular": (f"{W}/m5-angular/baselines/ang.baseline.json", f"{W}/m5-angular/baselines/DETAIL-ang.json", f"{W}/m5-angular/unstable/ang.json"),
    "copilotkit": (f"{W}/m5-ck-gate/baselines/ck.baseline.json", None, f"{W}/m5-ck-gate/unstable/ck.json"),
    "a2ui-vue": (f"{W}/m5-vue-gate/baselines/vue.baseline.json", None, f"{W}/m5-vue-gate/unstable/vue.json"),
}
PIX_LANES = [("pixel", "light 480"), ("pixel_dark", "dark 480"), ("pixel_360", "light 360"), ("pixel_dark360", "dark 360")]
FLUTTER_RUNS = f"{W}/flutter-m4/cloudci/runs/*/results/lane-results.json"
PARITY = f"{W}/flutter-m4/audit/parity_sweep.tsv"
STATUSES = ["native", "degraded", "not_supported", "not_measured"]
FL_RANK = {"painted": 0, "basic_lowered": 1, "unsupported_other": 2, "unsupported": 3, "invalid_payload": 4}


def load(p):
    with open(p, encoding="utf8") as f:
        return json.load(f)


def parse_registry(path):
    """Tiny parser for the flat registry: top-level `key: scalar`, then `renderers:` list of `- id:` items."""
    top, items, cur = {}, [], None
    in_list = False

    def val(s):
        s = s.strip()
        if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
            return json.loads(s)
        return s

    with open(path, encoding="utf8") as f:
        for line in f:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line.startswith("renderers:"):
                in_list = True
                continue
            if not in_list:
                k, v = line.split(":", 1)
                top[k.strip()] = val(v)
                continue
            m = re.match(r"^- (\w+):\s*(.*)$", line)
            if m:
                cur = {m.group(1): val(m.group(2))}
                items.append(cur)
                continue
            m = re.match(r"^  (\w+):\s*(.*)$", line)
            if m and cur is not None:
                cur[m.group(1)] = val(m.group(2))
    return top, items


def web_evidence(rid, atom, rec, detail, unstable):
    flags = "loose %s, strict %s, strict text %s" % tuple("yes" if rec.get(k) else "no" for k in ("loose", "strict", "strict_text"))
    if not rec.get("loose"):
        flags += "; no visible text found in the lane example"
    parts = ["custom lane example painted without error (%s)" % flags]
    if rid == "react":
        parts.append("pixel lanes compare React with its own frozen reference, so parity is the reference itself")
    else:
        px = []
        for lane, label in PIX_LANES:
            r = detail.get(lane, {}).get(atom)
            if r is None:
                continue
            if r.get("blank_both"):
                px.append("%s blank in both" % label)
            else:
                px.append("%s %s" % (label, "pass" if r.get("passed") else "FAIL"))
        if px:
            parts.append("pixel vs React: " + ", ".join(px))
        listed = [lab for lane, lab in PIX_LANES if atom in unstable.get(lane, [])]
        if listed:
            parts.append("on the unstable allowance list for pixel (%s)" % ", ".join(listed))
    if atom in unstable.get("atoms", {}).get("custom", []):
        parts.append("custom text on the unstable allowance list (time or animation dependent)")
    b = detail.get("behaviour_custom", {}).get(atom)
    if b:
        parts.append("behaviour probe %s" % str(b.get("verdict", "")).split(":")[0])
    return "; ".join(parts)


def build_web(rid, atoms):
    bpath, dpath, upath = SRC[rid]
    base = load(bpath)
    detail = load(dpath) if dpath else base["detail"]
    unstable = load(upath)
    date = base["date"][:10]
    custom = detail["custom"]
    out, notes = {}, []
    for atom in atoms:
        rec = custom.get(atom)
        if rec is None:
            out[atom] = {"status": "not_measured", "evidence": "no example payload for this atom in the 670-case lane data (22 public atoms were not exercised)", "measured": date}
            continue
        if rec.get("error") or rec.get("broken"):
            st = "not_supported"
            ev = "custom lane example flagged %s; " % ("error" if rec.get("error") else "broken") + web_evidence(rid, atom, rec, detail, unstable)
        else:
            st = "native"
            ev = web_evidence(rid, atom, rec, detail, unstable)
        out[atom] = {"status": st, "evidence": ev, "measured": date}
    info = {"measured": date, "package": base.get("package"), "protocol_recorded": base.get("protocol"),
            "code_head": base.get("code", {}).get("head")}
    return out, info, notes


def build_flutter(atoms):
    runs = sorted(glob.glob(FLUTTER_RUNS))
    path = runs[-1]
    run_id = path.split("/runs/")[1].split("/")[0]
    date = "%s-%s-%s" % (run_id[:4], run_id[4:6], run_id[6:8])
    res = load(path)["results"]
    by_atom = {}
    for case, r in res.items():
        by_atom.setdefault(r["atom"], []).append((case, r))
    parity = {}
    with open(PARITY, encoding="utf8") as f:
        head = f.readline().rstrip("\n").split("\t")
        for line in f:
            row = dict(zip(head, line.rstrip("\n").split("\t")))
            parity[row["atom"]] = row
    out = {}
    for atom in atoms:
        cases = by_atom.get(atom)
        if not cases:
            out[atom] = {"status": "not_measured", "evidence": "no example payload for this atom in the lane data (22 public atoms were not exercised); lane run %s" % run_id, "measured": date}
            continue
        case, r = sorted(cases, key=lambda c: (FL_RANK[c[1]["status"]], c[0]))[0]
        s = r["status"]
        extra = ""
        if len(cases) > 1:
            extra = "; %d lane cases, best one taken (%s: %s; others %s)" % (
                len(cases), case, s, ", ".join(sorted(c[1]["status"] for c in cases if c[0] != case)))
        if s == "painted":
            st = "native"
            ev = "lane case painted with the atom's own type present, no error (a2ui_flutter 0.3.0, run %s)%s" % (run_id, extra)
            p = parity.get(atom)
            if p:
                miss, web = int(p["missing_in_flutter"]), int(p["web_words"])
                if miss == 0:
                    ev += "; text parity with the web painter checked 12 Nov: no web word missing in Flutter (%d web words)" % web
                else:
                    ev += "; text parity with the web painter checked 12 Nov: %d of %d web words missing in Flutter (e.g. %s)" % (miss, web, p["missing_sample"][:60])
            else:
                ev += "; text parity with the web painter not checked for this atom"
        elif s == "basic_lowered":
            st = "degraded"
            ev = "lane example was lowered to Basic components (own type absent), Basic drew it; not the atom's own implementation (run %s)" % run_id
        elif s == "unsupported":
            st = "not_supported"
            ev = "lane example: UNKNOWN_COMPONENT_TYPE for the atom, nothing drawn, onError only (run %s)" % run_id
        elif s == "unsupported_other":
            st = "not_supported"
            ev = "lane example: a nested atom type is unknown (%s); parent lowered to Basic (run %s)" % (", ".join(r.get("error_codes", [])) or "UNKNOWN_COMPONENT_TYPE", run_id)
        else:
            st = "not_supported"
            ev = "lane example payload rejected (%s); the example lowering produced an invalid component type, so the atom itself is untested; classed not_supported (run %s)" % (", ".join(r.get("error_codes", [])) or s, run_id)
        out[atom] = {"status": st, "evidence": ev, "measured": date}
    info = {"measured": date, "lane_run": run_id, "parity_rows": len(parity), "parity_rows_public": sum(1 for a in parity if a in set(atoms))}
    return out, info


def build_compose(atoms):
    return {a: {"status": "not_measured", "evidence": "on hold: no measurement exists for Compose", "measured": None} for a in atoms}


def counts(per_atom):
    c = {s: 0 for s in STATUSES}
    for v in per_atom.values():
        c[v["status"]] += 1
    return c


def main():
    cat = load(CAT)
    comps = cat["components"]
    atoms = sorted(comps)
    top, reg = parse_registry(REG)
    regd = {r["id"]: r for r in reg}
    per = {}
    info = {}
    for rid in ("react", "lit", "angular", "copilotkit", "a2ui-vue"):
        per[rid], info[rid], _ = build_web(rid, atoms)
        if info[rid]["measured"] != regd[rid]["measured"]:
            sys.exit("registry date mismatch for %s: %s vs %s" % (rid, regd[rid]["measured"], info[rid]["measured"]))
    per["flutter"], info["flutter"] = build_flutter(atoms)
    if info["flutter"]["measured"] != regd["flutter"]["measured"]:
        sys.exit("registry date mismatch for flutter")
    per["compose"] = build_compose(atoms)
    info["compose"] = {"measured": None}
    order = [r["id"] for r in reg]

    renderers = {}
    for rid in order:
        r = dict(regd[rid])
        r["coverage"] = counts(per[rid])
        r["coverage"]["total"] = len(atoms)
        r["source_info"] = info[rid]
        renderers[rid] = r
    matrix = {
        "$schema": "a2ui-renderer-matrix/1",
        "status": "DRAFT, local only, not published",
        "dimension": "renderer (what draws the atom); separate from x-surfaces (where the atom appears)",
        "status_values": {
            "native": "drawn by the renderer's own implementation of the atom",
            "degraded": "drawn through Basic components",
            "not_supported": "draws nothing or errors",
            "not_measured": "no per-atom data",
        },
        "atom_count": len(atoms),
        "trademark_note": top["trademark_note"],
        "trademark_note_extra": top["trademark_note_extra"],
        "independence_note": top["independence_note"],
        "renderers": renderers,
        "atoms": {a: {rid: per[rid][a] for rid in order} for a in atoms},
    }
    with open(OUT_MATRIX, "w", encoding="utf8") as f:
        f.write(json.dumps(matrix, indent=1, ensure_ascii=False, sort_keys=False) + "\n")

    draft = json.loads(json.dumps(cat))
    newc = {}
    for a in draft["components"]:
        comp = draft["components"][a]
        xr = {rid: per[rid][a] for rid in order}
        nc = {}
        for k, v in comp.items():
            nc[k] = v
            if k == "x-surfaces":
                nc["x-renderers"] = xr
        if "x-renderers" not in nc:
            nc["x-renderers"] = xr
        newc[a] = nc
    draft["components"] = newc
    with open(OUT_DRAFT, "w", encoding="utf8") as f:
        f.write(json.dumps(draft, indent=1, ensure_ascii=False) + "\n")
    for rid in order:
        print(rid, renderers[rid]["coverage"])


if __name__ == "__main__":
    main()
