#!/usr/bin/env python3
"""Offline content check for the renderer dimension (stdlib + yaml; runs in seconds; no network,
no harness, no secrets). Fails closed: exit 1 with one precise line per failure.

Checks (design CI-DESIGN-v2.md, items H4/H5/H6/M6/M8):
  COMPLETE      every stable atom x every MEASURED renderer has an entry, in the matrix and in the raw
                results (a `no_example` entry counts; it shows as not_measured). Renderers whose
                registry says `measured: false` (Compose) are skipped.
  FRESH         matrix entries and raw-result headers carry the run id, build label and hashes
                recorded in the committed results manifest; the manifest records the sha256 of each
                raw results file. A raw file edited without a new manifest, or a matrix built from
                other data, fails. For the WEB renderers the matrix's recorded renderer_bundle_sha256
                must equal the sha256 of public/surfaces/mcp-apps/renderer-bundle.html in this
                checkout: if the shipped bundle changed since the measurement the check fails with
                a re-measure message. Clock-based age only WARNS.
  EVIDENCED     drawn / drawn_with_differences / native / degraded entries carry per-check evidence
                codes, a measured date and a renderer_version; a `drawn` entry has no reasons and a
                `drawn_with_differences` entry has at least one.
  CONSISTENT    re-running the generator reproduces the committed matrix and the committed draft pages byte
                for byte; the built catalogue documents (public/spec.json, public/catalogue/a2ui-atoms-v1.json,
                a2ui-bricks-v1.json) carry exactly the matrix's `x-renderers` for every atom; the built site
                pages (public/renderers/, every public/atoms/<atom>/index.html and .md twin) contain the
                fragments renderer_site.py produces from the matrix. In CI these files were just built by the
                generators, so this proves the wiring; nothing here reads the clock.
  PRIVATE-SAFE  no atom key outside the stable catalogue anywhere in matrix, raw results or pages;
                no path (/mnt, /home, ...) and no hex SHA outside the allowed set (the hashes recorded
                in the manifest). Messages print only public atom names, else `<non-public atom #n>`.

Run:  python3 scripts/check_renderer_matrix.py [--no-consistent]
"""
import datetime
import hashlib
import importlib.util
import json
import os
import re
import sys

WT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = "docs/renderer-draft"
MATRIX_REL = "public/catalogue/renderer-matrix-v1.json"
CATALOGUES_REL = ("public/catalogue/a2ui-atoms-v1.json", "public/catalogue/a2ui-bricks-v1.json")
SPEC_REL = "public/spec.json"
BUNDLE_REL = "public/surfaces/mcp-apps/renderer-bundle.html"
AGE_WARN_DAYS = 30
DRAWN_STATUSES = ("drawn", "drawn_with_differences", "native", "degraded")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HEX_RE = re.compile(r"(?<![0-9A-Za-z])[0-9a-f]{12,64}(?![0-9A-Za-z])")
PATH_RE = re.compile(r"(?:^|[\s\"'(=:,\[])/(?:mnt|home|Users|root|tmp|var|media)/|[A-Za-z]:\\\\")
PAGE_ATOM_RE = re.compile(r"""href=["'](?:\.\./|\./)?atoms/([^"'/#?]+?)\.html""")
MANIFEST_FIELDS = ("run_id", "measured_date", "measured_on", "commit", "core_sha256", "css_sha256",
                   "renderer_bundle_sha256", "renderer_version")


class Names:
    """Public atom names print as themselves; anything else as `<non-public atom #n>`."""

    def __init__(self, stable):
        self.stable = set(stable)
        self.seen = {}

    def __call__(self, atom):
        if atom in self.stable:
            return atom
        n = self.seen.setdefault(atom, len(self.seen) + 1)
        return "<non-public atom #%d>" % n


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_context(root=WT, consistent=True):
    gen = _import("gen_renderer_matrix", os.path.join(HERE, "gen_renderer_matrix.py"))
    registry, raw, manifest = gen.load_inputs()
    stable = gen.stable_atoms()

    def rd(rel):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            return None
        with open(p, encoding="utf8") as f:
            return f.read()

    raw_texts = {}
    for rid, m in manifest["renderers"].items():
        p = os.path.join(gen.RESDIR, m["file"])
        with open(p, "rb") as f:
            raw_texts[rid] = f.read()
    pages_dir = os.path.join(root, PAGES_DIR)
    pages = {}
    for dp, _, fs in sorted(os.walk(pages_dir)):
        for fn in sorted(fs):
            if fn.endswith(".html"):
                rel = os.path.relpath(os.path.join(dp, fn), pages_dir)
                with open(os.path.join(dp, fn), encoding="utf8") as f:
                    pages[rel] = f.read()
    bundle = None
    bp = os.path.join(root, BUNDLE_REL)
    if os.path.exists(bp):
        with open(bp, "rb") as f:
            bundle = hashlib.sha256(f.read()).hexdigest()
    ctx = {
        "repo_bundle_sha256": bundle,
        "stable": stable, "registry": registry, "raw": raw, "manifest": manifest, "raw_bytes": raw_texts,
        "matrix_text": rd(MATRIX_REL), "pages": pages, "root": root,
        "today": datetime.date.today(),
    }
    ctx["matrix"] = json.loads(ctx["matrix_text"]) if ctx["matrix_text"] else None
    if consistent:
        pg = _import("gen_renderer_draft_pages", os.path.join(HERE, "gen_renderer_draft_pages.py"))

        def regen():
            files, matrix = gen.render_files(registry, raw, manifest, stable)
            files.update({PAGES_DIR + "/" + k: v for k, v in pg.render_pages(matrix, registry).items()})
            return files

        ctx["regen"] = regen
    return ctx


def measured_renderers(ctx):
    return [r["id"] for r in ctx["registry"]["renderers"] if r.get("measured")]


# ------------------------------------------------------------------ checks (each returns [(code, message)])


def check_complete(ctx):
    errs, nm = [], Names(ctx["stable"])
    matrix = ctx["matrix"]
    if matrix is None:
        return [("COMPLETE", "matrix file %s is missing" % MATRIX_REL)]
    for rid in measured_renderers(ctx):
        raw_atoms = ctx["raw"].get(rid, {}).get("atoms", {})
        for atom in ctx["stable"]:
            if atom not in matrix["atoms"] or rid not in matrix["atoms"][atom]:
                errs.append(("COMPLETE", "no matrix entry for %s x %s" % (nm(atom), rid)))
            if atom not in raw_atoms:
                errs.append(("COMPLETE", "no raw result entry for %s x %s (export a `no_example` entry if there is no case)" % (nm(atom), rid)))
    return errs


def check_fresh(ctx):
    errs, warns = [], []
    man = ctx["manifest"].get("renderers", {})
    for rid in measured_renderers(ctx):
        m = man.get(rid)
        if m is None:
            errs.append(("FRESH", "renderer %s is measured but has no manifest entry" % rid))
            continue
        got = hashlib.sha256(ctx["raw_bytes"][rid]).hexdigest() if rid in ctx["raw_bytes"] else None
        if got != m["file_sha256"]:
            errs.append(("FRESH", "raw results of %s do not match the manifest file_sha256 (edited without re-export?)" % rid))
        head = ctx["raw"].get(rid, {})
        for k in MANIFEST_FIELDS:
            mk = k
            if head.get(k) != m.get(mk):
                errs.append(("FRESH", "raw results of %s: %s differs from the manifest" % (rid, k)))
        for atom, row in (ctx["matrix"] or {}).get("atoms", {}).items():
            e = row.get(rid)
            if e is None:
                continue
            for ek, mk in (("run_id", "run_id"), ("measured_on", "measured_on"), ("core_sha256", "core_sha256"),
                           ("renderer_version", "renderer_version")):
                if e.get(ek) != m.get(mk):
                    errs.append(("FRESH", "matrix entry %s x %s: %s differs from the manifest (stale entry)" % (Names(ctx["stable"])(atom), rid, ek)))
                    break
        if m.get("measured_on") == "shipped":
            if not SHA40_RE.match(str(m.get("commit") or "")):
                errs.append(("FRESH", "%s is measured_on=shipped but records no 40-hex public commit" % rid))
        elif m.get("commit"):
            errs.append(("FRESH", "%s records a commit although measured_on=%s (only a shipped commit may be named)" % (rid, m.get("measured_on"))))
        reg = next((r for r in ctx["registry"]["renderers"] if r["id"] == rid), {})
        if reg.get("kind") == "web":
            meas = (((ctx["matrix"] or {}).get("renderers", {}).get(rid) or {}).get("measurement") or {}).get("renderer_bundle_sha256")
            if not meas:
                errs.append(("FRESH", "web renderer %s records no renderer_bundle_sha256 in the matrix" % rid))
            elif ctx.get("repo_bundle_sha256") is None:
                errs.append(("FRESH", "%s is missing in this checkout, so the measured bundle of %s cannot be verified" % (BUNDLE_REL, rid)))
            elif meas != ctx["repo_bundle_sha256"]:
                errs.append(("FRESH", "%s was measured on renderer bundle %s but %s in this checkout is %s: the shipped bundle changed since the measurement; re-measure %s and re-export" % (
                    rid, meas[:12], BUNDLE_REL, ctx["repo_bundle_sha256"][:12], rid)))
        try:
            d = datetime.date.fromisoformat(m["measured_date"])
            age = (ctx["today"] - d).days
            if age > AGE_WARN_DAYS:
                warns.append("%s measured %d days ago (warning only)" % (rid, age))
        except (ValueError, KeyError):
            errs.append(("FRESH", "manifest measured_date of %s is not a date" % rid))
        if m.get("measured_on") == "preview-unmerged":
            warns.append("%s measured on a pre-merge build, superseded until re-measured on a shipped build" % rid)
        elif m.get("measured_on") == "private-build":
            warns.append("%s measured on a private build: not reproducible from a public commit" % rid)
        elif m.get("measured_on") not in ("shipped", "release-package"):
            warns.append("%s: build provenance not recorded (measured_on=%s)" % (rid, m.get("measured_on")))
    return errs, warns


def check_evidenced(ctx):
    errs, nm = [], Names(ctx["stable"])
    ctx_kind = {r["id"]: r["kind"] for r in ctx["registry"]["renderers"]}
    for atom, row in (ctx["matrix"] or {}).get("atoms", {}).items():
        for rid, e in row.items():
            st = e.get("status")
            where = "%s x %s" % (nm(atom), rid)
            if st in DRAWN_STATUSES:
                if not e.get("checks"):
                    errs.append(("EVIDENCED", "%s is %s but has no per-check evidence" % (where, st)))
                if not DATE_RE.match(str(e.get("measured") or "")):
                    errs.append(("EVIDENCED", "%s is %s but has no measured date" % (where, st)))
                if not e.get("renderer_version"):
                    errs.append(("EVIDENCED", "%s is %s but has no renderer_version" % (where, st)))
                if not e.get("run_id"):
                    errs.append(("EVIDENCED", "%s is %s but has no run_id" % (where, st)))
            if st == "drawn" and e.get("reasons"):
                errs.append(("EVIDENCED", "%s is drawn but lists reasons %s" % (where, e["reasons"])))
            if st == "native" and (ctx_kind.get(rid) == "compose") and not (e.get("checks") or {}).get("own_type_present"):
                errs.append(("EVIDENCED", "%s is native on Compose but the atom's root type is not a Basic component" % where))
            if st == "drawn_with_differences" and not e.get("reasons"):
                errs.append(("EVIDENCED", "%s is drawn_with_differences but lists no reason code" % where))
            if st == "drawn":
                ck = e.get("checks") or {}
                bad = [k for k in ("painted", "text_visible") if ck.get(k) != "pass"]
                bad += ["pixel." + k for k, v in (ck.get("pixel") or {}).items() if v in ("fail", "unstable", "blank_both")]
                if bad:
                    errs.append(("EVIDENCED", "%s is drawn but checks are not all passing: %s" % (where, ", ".join(bad))))
    return errs


def check_consistent(ctx):
    errs = []
    files = ctx["regen"]()
    committed = {k: v for k, v in ((MATRIX_REL, ctx["matrix_text"]),) if v is not None}
    committed.update({PAGES_DIR + "/" + k: v for k, v in ctx["pages"].items()})
    for rel in sorted(files):
        if committed.get(rel) is None:
            errs.append(("CONSISTENT", "%s is not committed (run the generators)" % rel))
        elif committed[rel] != files[rel]:
            errs.append(("CONSISTENT", "%s differs from what the generator produces from the committed inputs" % rel))
    for rel in sorted(set(committed) - set(files)):
        errs.append(("CONSISTENT", "%s is committed but no generator produces it" % rel))
    if ctx.get("root"):
        errs += check_site_wiring(ctx)
    return errs


def check_site_wiring(ctx):
    """The built catalogue documents (compact status map + pointer header) and site pages carry what the matrix says."""
    errs, nm = [], Names(ctx["stable"])
    matrix = ctx["matrix"]
    if matrix is None:
        return errs
    gen = _import("gen_renderer_matrix", os.path.join(HERE, "gen_renderer_matrix.py"))
    site = _import("renderer_site", os.path.join(HERE, "renderer_site.py"))
    root = ctx["root"]

    def load(rel):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            return None
        with open(p, encoding="utf8") as f:
            return f.read()

    # catalogue documents: x-renderers == projection of the matrix, for every atom the matrix covers, and only for those
    docs = {SPEC_REL: lambda d: {a["type"]: a.get("x-renderers") for a in d["atoms"]}}
    for rel in CATALOGUES_REL:
        docs[rel] = lambda d: {k: c.get("x-renderers") for k, c in d["components"].items()}
    url = "https://a2uicatalog.ai/" + MATRIX_REL.split("public/", 1)[1]
    for rel, getter in docs.items():
        text = load(rel)
        if text is None:
            errs.append(("CONSISTENT", "%s is missing (run gen_public_catalog.py)" % rel))
            continue
        doc = json.loads(text)
        if rel == SPEC_REL:
            if doc.get("x-renderers-matrix") != url or doc.get("x-renderers-rules-version") != matrix["rules_version"]:
                errs.append(("CONSISTENT", "%s header does not point to the matrix %s with rules version %s" % (rel, url, matrix["rules_version"])))
        elif url not in doc.get("instructions", ""):
            errs.append(("CONSISTENT", "%s instructions do not point to %s" % (rel, url)))
        for atom, got in getter(doc).items():
            want = gen.x_renderers(matrix, atom) if atom in matrix["atoms"] else None
            if got != want:
                errs.append(("CONSISTENT", "%s: x-renderers of %s %s the matrix statuses" % (rel, nm(atom), "is missing or differs from" if want else "has no entry in")))
    # site pages
    want_pages = {"public/renderers/index.html": [site.hub_body(matrix)]}
    for rid in matrix["renderers"]:
        want_pages["public/renderers/%s/index.html" % rid] = [site.renderer_body(matrix, rid)]
    want_pages.update({"public/renderers.md": [site.hub_md(matrix)]})
    for rid in matrix["renderers"]:
        want_pages["public/renderers/%s.md" % rid] = [site.renderer_md(matrix, rid)]
    for atom in matrix["atoms"]:
        want_pages["public/atoms/%s/index.html" % atom] = [site.atom_block(matrix, atom)]
        want_pages["public/atoms/%s.md" % atom] = ["\n".join(site.atom_md(matrix, atom))]
    for rel, frags in sorted(want_pages.items()):
        text = load(rel)
        if text is None:
            errs.append(("CONSISTENT", "page %s is missing (run generate_atom_pages.py)" % (rel if "/atoms/" not in rel else rel.replace(rel.split("/")[2].split(".")[0], nm(rel.split("/")[2].split(".")[0]), 1))))
            continue
        for fr in frags:
            if fr not in text:
                errs.append(("CONSISTENT", "page %s does not contain the renderer fragment the matrix produces" % rel))
    return errs


def _walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_strings(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_strings(v, path + "[%d]" % i)
    elif isinstance(obj, str):
        yield path, obj


def allowed_hashes(ctx):
    out = set()
    for m in ctx["manifest"].get("renderers", {}).values():
        for k in ("file_sha256", "core_sha256", "css_sha256", "renderer_bundle_sha256", "commit"):
            if m.get(k):
                out.add(m[k])
    return out


def _scan_text(label, text, allowed, errs):
    if PATH_RE.search(text):
        errs.append(("PRIVATE-SAFE", "%s contains a machine path (/mnt, /home, ...)" % label))
    for tok in sorted(set(HEX_RE.findall(text))):
        if not (re.search(r"[0-9]", tok) and re.search(r"[a-f]", tok)):
            continue
        if not any(a.startswith(tok) for a in allowed):
            errs.append(("PRIVATE-SAFE", "%s contains a hex string (%d chars) that is not a manifest hash" % (label, len(tok))))


def check_private_safe(ctx):
    errs, nm = [], Names(ctx["stable"])
    stable = set(ctx["stable"])
    allowed = allowed_hashes(ctx)
    for atom in (ctx["matrix"] or {}).get("atoms", {}):
        if atom not in stable:
            errs.append(("PRIVATE-SAFE", "matrix holds %s" % nm(atom)))
    for rid, head in ctx["raw"].items():
        for atom, rec in head.get("atoms", {}).items():
            if atom not in stable:
                errs.append(("PRIVATE-SAFE", "raw results of %s hold %s" % (rid, nm(atom))))
            for cid in (rec.get("cases") or {}):
                if cid.split("#")[0] not in stable:
                    errs.append(("PRIVATE-SAFE", "raw results of %s hold a case of %s" % (rid, nm(cid.split("#")[0]))))
    for rel in (CATALOGUES_REL + (SPEC_REL,)) if ctx.get("root") else ():
        p = os.path.join(ctx["root"], rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf8") as f:
            doc = json.load(f)
        items = list((doc.get("components") or {}).items()) if "components" in doc else [(a["type"], a) for a in doc.get("atoms", [])]
        xr = {}
        for atom, comp in items:
            if "x-renderers" in comp:
                xr[atom] = comp["x-renderers"]
                if atom not in stable:
                    errs.append(("PRIVATE-SAFE", "%s carries x-renderers for %s" % (rel, nm(atom))))
        _scan_text(rel + " x-renderers", json.dumps(xr), allowed, errs)
    # built site pages: no machine path, no stray hash, no non-public atom link
    for rel in ("public/renderers/index.html", "public/renderers.md") if ctx.get("root") else ():
        p = os.path.join(ctx["root"], rel)
        if os.path.exists(p):
            with open(p, encoding="utf8") as f:
                _scan_text(rel, f.read(), allowed, errs)
    rdir = os.path.join(ctx.get("root") or "/nonexistent", "public/renderers")
    if os.path.isdir(rdir):
        for dp_, _, fs in sorted(os.walk(rdir)):
            for fn in sorted(fs):
                if fn.endswith((".html", ".md")):
                    with open(os.path.join(dp_, fn), encoding="utf8") as f:
                        text = f.read()
                    rel = os.path.relpath(os.path.join(dp_, fn), ctx["root"])
                    for a in re.findall(r"/atoms/([A-Za-z0-9_]+)/", text):
                        if a not in stable:
                            errs.append(("PRIVATE-SAFE", "page %s links %s" % (rel, nm(a))))
                    _scan_text(rel, text, allowed, errs)
    _scan_text("matrix", ctx["matrix_text"] or "", allowed, errs)
    for rid, b in ctx["raw_bytes"].items():
        _scan_text("raw results of %s" % rid, b.decode("utf8"), allowed, errs)
    for rel, text in ctx["pages"].items():
        for a in PAGE_ATOM_RE.findall(text):
            if a not in stable:
                errs.append(("PRIVATE-SAFE", "page %s links %s" % (rel, nm(a))))
        _scan_text("page " + rel, text, allowed, errs)
    return errs


def run_all(ctx, consistent=True):
    errs, warns = [], []
    errs += check_complete(ctx)
    e, w = check_fresh(ctx)
    errs += e
    warns += w
    errs += check_evidenced(ctx)
    if consistent:
        errs += check_consistent(ctx)
    errs += check_private_safe(ctx)
    if ctx["matrix"]:
        for rid, r in ctx["matrix"]["renderers"].items():
            nm_ = r["coverage"].get("not_measured", 0)
            if r.get("measured") and nm_:
                warns.append("%s: %d atoms not_measured (no example in the gate data)" % (rid, nm_))
    return errs, warns


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ctx = load_context(consistent="--no-consistent" not in argv)
    errs, warns = run_all(ctx, consistent="--no-consistent" not in argv)
    for w in warns:
        print("WARN  " + w)
    for code, msg in errs:
        print("FAIL  %s: %s" % (code, msg))
    if errs:
        print("%d failure(s)" % len(errs))
        return 1
    print("renderer matrix: all checks passed (%d stable atoms, %d measured renderers)" % (len(ctx["stable"]), len(measured_renderers(ctx))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
