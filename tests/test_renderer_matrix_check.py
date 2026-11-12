"""Unit tests for the renderer-dimension generator rules and scripts/check_renderer_matrix.py.

Each check is fed a tiny valid fixture (must pass) and then deliberately broken variants (must fail).
No harness, no network, no schema.yaml load: fast.
"""
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _load("gen_renderer_matrix")
chk = _load("check_renderer_matrix")

STABLE = ["alpha", "beta"]
CORE = "a" * 63 + "1"


def web_case(**over):
    ck = {
        "painted": {"result": "pass", "error_code": None},
        "text_visible": {"loose": True, "strict": True, "strict_text": True, "allowance": False},
        "pixel": {e: {"result": "pass", "allowance": False, "low": 0, "low_ref": 0, "one_blank": False}
                  for e in gen.ENVS},
        "overflow_360": {"light360": False, "dark360": False},
        "behaviour": "n/a (no probe)",
        "stability": "stable",
    }
    ck.update(over)
    return {"dialect": "v0.9", "checks": ck}


def fl_case(status, own=True, codes=()):
    return {"dialect": "v1.0", "checks": {"painted": {"result": status, "own_type_present": own, "text_chars": 5,
                                                       "error_codes": list(codes)}, "parity_text": None}}


def head(rid, atoms, **kw):
    h = {"schema": "a2ui-renderer-results/1", "renderer": rid, "kind": "web", "renderer_version": "x 1.0",
         "dialect": "v0.9", "reference_renderer": "react", "measured_date": "2026-11-10", "run_id": rid + "-1",
         "measured_on": "preview-unmerged", "commit": None, "core_sha256": CORE, "css_sha256": "b" * 63 + "2",
         "renderer_bundle_sha256": "c" * 63 + "3", "case_sha256": None, "wall_seconds": 1, "atoms": atoms}
    h.update(kw)
    return h


REGISTRY = {
    "rules": {"version": 2}, "trademark_note": "tm", "trademark_note_extra": "tm2", "independence_note": "ind",
    "renderers": [
        {"id": "lit", "name": "Lit", "kind": "web", "measured": True, "package": "p", "protocol": "v0.9", "platform": "w", "logo": "", "note": "n"},
        {"id": "compose", "name": "Compose", "kind": "compose", "measured": False, "package": "n/a", "protocol": "n/a", "platform": "a", "logo": "", "note": "n"},
    ],
}


def make_ctx():
    raw = {"lit": head("lit", {"alpha": {"cases": {"alpha": web_case()}}, "beta": {"cases": {}, "no_case": "no_example"}})}
    raw_bytes = {"lit": json.dumps(raw["lit"], sort_keys=True).encode()}
    sha = hashlib.sha256(raw_bytes["lit"]).hexdigest()
    manifest = {"renderers": {"lit": {
        "file": "lit.json", "file_sha256": sha, "run_id": "lit-1", "measured_date": "2026-11-10",
        "measured_on": "preview-unmerged", "commit": None, "core_sha256": CORE, "css_sha256": "b" * 63 + "2",
        "renderer_bundle_sha256": "c" * 63 + "3", "renderer_version": "x 1.0"}}}
    matrix = gen.build(REGISTRY, raw, manifest, STABLE)
    text = gen.dumps(matrix)
    ctx = {"stable": STABLE, "registry": REGISTRY, "raw": raw, "raw_bytes": raw_bytes, "manifest": manifest,
           "matrix": json.loads(text), "matrix_text": text, "draft_text": None,
           "pages": {"index.html": '<a href="atoms/alpha.html">alpha</a>'}, "today": datetime.date(2026, 11, 12)}
    committed = {chk.MATRIX_REL: text, chk.PAGES_DIR + "/index.html": ctx["pages"]["index.html"]}
    ctx["regen"] = lambda: dict(committed)
    return ctx


def fails(errs, code):
    return [m for c, m in errs if c == code]


def run(ctx):
    errs, warns = chk.run_all(ctx)
    return errs, warns


def test_fixture_passes():
    errs, _ = run(make_ctx())
    assert errs == []


# ------------------------------------------------------------------ rules


@pytest.mark.parametrize("over,status,reason", [
    ({}, "drawn", None),
    ({"text_visible": {"loose": False, "strict": False, "strict_text": False, "allowance": False}}, "not_verified", "no_visible_text"),
    ({"painted": {"result": "fail", "error_code": "error"}}, "not_supported", "painted_fail_error"),
    ({"overflow_360": {"light360": True}}, "drawn_with_differences", "overflow_360"),
    ({"behaviour": "DIFFERENT"}, "drawn_with_differences", "behaviour_differs"),
    ({"behaviour": "INERT"}, "drawn", None),
])
def test_web_rules(over, status, reason):
    st, reasons, _ = gen.web_case_status(web_case(**over))
    assert st == status
    assert (reason in reasons) if reason else reasons == []


def test_pixel_fail_blank_allowance_rules():
    c = web_case()
    c["checks"]["pixel"]["dark480"]["result"] = "fail"
    assert gen.web_case_status(c)[:2] == ("drawn_with_differences", ["pixel_fail_dark480"])
    c = web_case()
    c["checks"]["pixel"]["light480"]["result"] = "blank_both"
    assert gen.web_case_status(c)[:2] == ("not_verified", ["blank_both_light480"])
    c = web_case()
    c["checks"]["pixel"]["light360"].update(result="fail", allowance=True)
    st, reasons, d = gen.web_case_status(c)
    assert st == "not_verified" and d["pixel"]["light360"] == "unstable"  # never pass, never a hard fail
    c = web_case()
    c["checks"]["pixel"]["dark360"] = {"result": "not_a_lane"}
    assert gen.web_case_status(c)[0] == "drawn"
    c = web_case()
    c["checks"]["pixel"]["light360"].update(low=3, low_ref=1)
    assert gen.web_case_status(c)[:2] == ("drawn_with_differences", ["contrast_worse_light360"])
    c["checks"]["pixel"]["light360"].update(low=3, low_ref=5)
    assert gen.web_case_status(c)[0] == "drawn"


@pytest.mark.parametrize("raw,own,status", [
    ("painted", True, "native"), ("basic_lowered", False, "degraded"), ("unsupported", False, "not_supported"),
    ("unsupported_other", False, "not_supported"), ("invalid_payload", False, "not_measured"), ("painted", False, "degraded"),
])
def test_flutter_rules(raw, own, status):
    assert gen.flutter_case_status(fl_case(raw, own))[0] == status


def test_worst_case_wins_flutter_and_web():
    h = head("flutter", {}, kind="flutter", dialect="v1.0", reference_renderer=None)
    rec = {"cases": {"a": fl_case("painted"), "a#schema": fl_case("unsupported")}}
    e = gen.entry_for("flutter", h, rec)
    assert e["status"] == "not_supported" and e["worst_case"] == "a#schema" and e["cases"] == 2
    rec = {"cases": {"a": fl_case("painted"), "a#x": fl_case("invalid_payload")}}
    assert gen.entry_for("flutter", h, rec)["status"] == "not_measured"
    bad = web_case(overflow_360={"light360": True})
    e = gen.entry_for("web", head("lit", {}), {"cases": {"x": web_case(), "y": bad}})
    assert e["status"] == "drawn_with_differences" and e["worst_case"] == "y"


def test_matrix_has_no_clock_and_compose_unmeasured():
    m = make_ctx()["matrix"]
    assert m["renderers"]["compose"]["measured"] is False
    assert m["atoms"]["alpha"]["compose"]["status"] == "not_measured"
    assert m["atoms"]["beta"]["lit"]["status"] == "not_measured"
    assert m["atoms"]["alpha"]["lit"]["status"] == "drawn"


# ------------------------------------------------------------------ COMPLETE


def test_complete_missing_matrix_entry():
    ctx = make_ctx()
    del ctx["matrix"]["atoms"]["beta"]["lit"]
    assert any("beta x lit" in m for m in fails(run(ctx)[0], "COMPLETE"))


def test_complete_missing_raw_entry():
    ctx = make_ctx()
    del ctx["raw"]["lit"]["atoms"]["beta"]
    assert any("raw result" in m and "beta" in m for m in fails(run(ctx)[0], "COMPLETE"))


def test_complete_skips_unmeasured_renderer():
    ctx = make_ctx()
    assert "compose" not in ctx["raw"]
    assert fails(run(ctx)[0], "COMPLETE") == []


# ------------------------------------------------------------------ FRESH


def test_fresh_raw_file_edited_without_reexport():
    ctx = make_ctx()
    ctx["raw_bytes"]["lit"] += b" "
    assert any("file_sha256" in m for m in fails(run(ctx)[0], "FRESH"))


def test_fresh_matrix_entry_core_stale():
    ctx = make_ctx()
    ctx["matrix"]["atoms"]["alpha"]["lit"]["core_sha256"] = "d" * 64
    assert any("alpha x lit" in m and "core_sha256" in m for m in fails(run(ctx)[0], "FRESH"))


def test_fresh_manifest_entry_missing():
    ctx = make_ctx()
    ctx["manifest"]["renderers"] = {}
    assert any("no manifest entry" in m for m in fails(run(ctx)[0], "FRESH"))


def test_fresh_age_only_warns():
    ctx = make_ctx()
    ctx["today"] = datetime.date(2027, 6, 1)
    errs, warns = run(ctx)
    assert fails(errs, "FRESH") == [] and any("days ago" in w for w in warns)


# ------------------------------------------------------------------ EVIDENCED


def test_evidenced_missing_date_and_version():
    ctx = make_ctx()
    e = ctx["matrix"]["atoms"]["alpha"]["lit"]
    e["measured"] = None
    e["renderer_version"] = ""
    msgs = fails(run(ctx)[0], "EVIDENCED")
    assert any("measured date" in m for m in msgs) and any("renderer_version" in m for m in msgs)


def test_evidenced_missing_checks():
    ctx = make_ctx()
    ctx["matrix"]["atoms"]["alpha"]["lit"]["checks"] = None
    assert any("no per-check evidence" in m for m in fails(run(ctx)[0], "EVIDENCED"))


def test_evidenced_drawn_with_reasons_or_failing_check():
    ctx = make_ctx()
    ctx["matrix"]["atoms"]["alpha"]["lit"]["reasons"] = ["overflow_360"]
    assert any("lists reasons" in m for m in fails(run(ctx)[0], "EVIDENCED"))
    ctx = make_ctx()
    ctx["matrix"]["atoms"]["alpha"]["lit"]["checks"]["pixel"]["dark480"] = "fail"
    assert any("not all passing" in m for m in fails(run(ctx)[0], "EVIDENCED"))


def test_evidenced_differences_need_a_reason():
    ctx = make_ctx()
    e = ctx["matrix"]["atoms"]["alpha"]["lit"]
    e["status"] = "drawn_with_differences"
    e["reasons"] = []
    assert any("no reason code" in m for m in fails(run(ctx)[0], "EVIDENCED"))


# ------------------------------------------------------------------ CONSISTENT


def test_consistent_matrix_hand_edited():
    ctx = make_ctx()
    ctx["matrix_text"] = ctx["matrix_text"].replace('"drawn"', '"native"', 1)
    assert any(chk.MATRIX_REL in m and "differs" in m for m in fails(run(ctx)[0], "CONSISTENT"))


def test_consistent_extra_and_missing_pages():
    ctx = make_ctx()
    ctx["pages"]["stray.html"] = "<p>x</p>"
    assert any("stray.html" in m for m in fails(run(ctx)[0], "CONSISTENT"))
    ctx = make_ctx()
    ctx["pages"] = {}
    assert any("index.html" in m and "not committed" in m for m in fails(run(ctx)[0], "CONSISTENT"))


# ------------------------------------------------------------------ PRIVATE-SAFE


def test_private_atom_in_matrix_is_masked():
    ctx = make_ctx()
    ctx["matrix"]["atoms"]["secret_atom_name"] = ctx["matrix"]["atoms"]["alpha"]
    errs = chk.check_private_safe(ctx)
    msgs = [m for _, m in errs]
    assert any("<non-public atom #1>" in m for m in msgs)
    assert not any("secret_atom_name" in m for m in msgs)


def test_private_atom_in_raw_case_and_page_link():
    ctx = make_ctx()
    ctx["raw"]["lit"]["atoms"]["alpha"]["cases"]["hidden_one#schema"] = web_case()
    ctx["pages"]["index.html"] += ' <a href="atoms/hidden_two.html">x</a>'
    msgs = [m for _, m in chk.check_private_safe(ctx)]
    assert any("a case of <non-public atom" in m for m in msgs)
    assert any("links <non-public atom" in m for m in msgs)
    assert not any("hidden_" in m for m in msgs)


@pytest.mark.parametrize("snippet", ["/mnt/hdd2/work/x", " /home/ck/y", "path=\"/Users/me/z\""])
def test_private_path_rejected(snippet):
    ctx = make_ctx()
    ctx["matrix_text"] += snippet
    assert any("machine path" in m for _, m in chk.check_private_safe(ctx))


def test_private_unknown_sha_rejected_but_manifest_sha_allowed():
    ctx = make_ctx()
    ctx["matrix_text"] += " 39477f95f34a2dbb8b07ea2b62ae80333917991d"
    assert any("hex string" in m for _, m in chk.check_private_safe(ctx))
    ctx = make_ctx()
    ctx["matrix_text"] += " " + CORE + " " + CORE[:12]
    assert not any("hex string" in m for _, m in chk.check_private_safe(ctx))


def test_exit_code_nonzero_on_failure(capsys, monkeypatch):
    ctx = make_ctx()
    ctx["matrix_text"] += " /mnt/x"
    monkeypatch.setattr(chk, "load_context", lambda consistent=True: ctx)
    assert chk.main([]) == 1
    assert "FAIL  PRIVATE-SAFE" in capsys.readouterr().out
    monkeypatch.setattr(chk, "load_context", lambda consistent=True: make_ctx())
    assert chk.main([]) == 0
