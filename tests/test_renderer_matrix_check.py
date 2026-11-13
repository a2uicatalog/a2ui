"""Unit tests for the renderer-dimension generator rules and scripts/check_renderer_matrix.py.

Each check is fed a tiny valid fixture (must pass) and then deliberately broken variants (must fail).
No harness, no network, no schema.yaml load: fast.
"""
import copy
import datetime
import hashlib
import importlib.util
import json
import os
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
           "pages": {"index.html": '<a href="atoms/alpha.html">alpha</a>'}, "today": datetime.date(2026, 11, 12),
           "repo_bundle_sha256": "c" * 63 + "3"}
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


# ------------------------------------------------------------------ FRESH by bundle hash (web)


def test_fresh_bundle_hash_matches_passes():
    assert fails(run(make_ctx())[0], "FRESH") == []


def test_fresh_bundle_changed_since_measurement_fails_loudly():
    ctx = make_ctx()
    ctx["repo_bundle_sha256"] = "e" * 64
    msgs = fails(run(ctx)[0], "FRESH")
    assert any("shipped bundle changed since the measurement" in m and "re-measure lit" in m for m in msgs)


def test_fresh_bundle_file_missing_fails():
    ctx = make_ctx()
    ctx["repo_bundle_sha256"] = None
    assert any("cannot be verified" in m for m in fails(run(ctx)[0], "FRESH"))


def test_fresh_web_matrix_without_bundle_hash_fails():
    ctx = make_ctx()
    ctx["matrix"]["renderers"]["lit"]["measurement"]["renderer_bundle_sha256"] = None
    assert any("records no renderer_bundle_sha256" in m for m in fails(run(ctx)[0], "FRESH"))


def test_fresh_shipped_needs_public_commit_and_others_name_none():
    ctx = make_ctx()
    ctx["manifest"]["renderers"]["lit"]["measured_on"] = "shipped"
    assert any("no 40-hex public commit" in m for m in fails(run(ctx)[0], "FRESH"))
    ctx = make_ctx()
    ctx["manifest"]["renderers"]["lit"]["commit"] = "a" * 40
    assert any("only a shipped commit may be named" in m for m in fails(run(ctx)[0], "FRESH"))
    ctx = make_ctx()
    ctx["manifest"]["renderers"]["lit"]["measured_on"] = "shipped"
    ctx["manifest"]["renderers"]["lit"]["commit"] = "a" * 40
    assert not any("40-hex" in m or "named" in m for m in fails(run(ctx)[0], "FRESH"))


@pytest.mark.parametrize("on,warn", [("private-build", "private build"), ("unrecorded", "not recorded"), ("preview-unmerged", "pre-merge")])
def test_build_label_warnings(on, warn):
    ctx = make_ctx()
    ctx["manifest"]["renderers"]["lit"]["measured_on"] = on
    ctx["matrix"]["renderers"]["lit"]["measurement"]["measured_on"] = on
    warns = chk.check_fresh(ctx)[1]
    assert any(warn in w for w in warns)
    ctx["manifest"]["renderers"]["lit"]["measured_on"] = "release-package"
    assert not any("provenance" in w or "private build" in w for w in chk.check_fresh(ctx)[1])


# ------------------------------------------------------------------ not_run behaviour, compose rules


def test_behaviour_not_run_is_neutral_but_visible():
    st, reasons, derived = gen.web_case_status(web_case(behaviour="not_run"))
    assert st == "drawn" and derived["behaviour"] == "not_run" and reasons == []


def cp_case(status, own=True):
    return {"dialect": "v0.9", "checks": {"painted": {"result": status, "own_type_present": own, "text_chars": 3, "error_codes": []},
                                          "parity_text": None, "basic_lane": {"rendered": True, "text_sha_equal": False}}}


@pytest.mark.parametrize("raw,own,status", [("painted", True, "native"), ("unsupported", False, "not_supported")])
def test_compose_rules(raw, own, status):
    assert gen.compose_case_status(cp_case(raw, own))[0] == status


def test_compose_unknown_status_refused_and_none_means_not_measured():
    with pytest.raises(ValueError):
        gen.compose_case_status(cp_case("basic_lowered"))
    reg = {"id": "compose", "name": "Compose", "kind": "compose", "measured": True, "package": "p", "protocol": "v0.9",
           "platform": "x", "logo": "", "note": "n"}
    registry = dict(REGISTRY, renderers=[reg])
    raw = {"compose": head("compose", {"alpha": {"cases": {"alpha": cp_case("painted")}}, "beta": {"cases": {}, "no_case": "no_example"}},
                           kind="compose", facts={"basic_lane": {"cases": 2}})}
    manifest = {"renderers": {"compose": {"file_sha256": "x" * 64}}}
    m = gen.build(registry, raw, manifest, STABLE)
    assert m["atoms"]["alpha"]["compose"]["status"] == "native" and m["atoms"]["beta"]["compose"]["status"] == "not_measured"
    assert m["renderers"]["compose"]["statuses"] == ["native", "not_supported", "not_measured"]
    assert m["renderers"]["compose"]["measurement"]["facts"] == {"basic_lane": {"cases": 2}}


def test_compose_native_without_basic_root_is_rejected():
    ctx = make_ctx()
    ctx["registry"] = dict(REGISTRY, renderers=[dict(REGISTRY["renderers"][0], id="cx", kind="compose")])
    ctx["matrix"]["atoms"]["alpha"]["cx"] = {"status": "native", "reasons": ["basic_component_rendered"], "measured": "2026-11-13",
                                             "renderer_version": "v", "run_id": "r", "checks": {"own_type_present": False}}
    assert any("not a Basic component" in m for m in fails(chk.check_evidenced(ctx), "EVIDENCED"))


# ------------------------------------------------------------------ private-side exporter (fixtures in a temp dir)


exp = _load("export_renderer_results")


def test_exporter_behaviour_not_run_and_swap_refusals(tmp_path):
    rec = {"broken": False, "error": False, "loose": True, "strict": True, "strict_text": True}
    case = exp.web_case("copilotkit", "alpha", rec, {"behaviour_custom": {"alpha": {"verdict": "SAME"}}}, {}, True, behaviour_run=False)
    assert case["checks"]["behaviour"] == "not_run"
    assert exp.web_case("lit", "alpha", rec, {"behaviour_custom": {}}, {}, True)["checks"]["behaviour"] == "n/a (no probe)"
    # a run measured on another commit, or dirty, or with a changed package version, is refused for --measured-on shipped
    import json as _j
    (tmp_path / "react" / "runs" / "F").mkdir(parents=True)
    code = {"head": "b" * 40, "dirty_tracked": False, "core_sha256": CORE, "css_sha256": "b" * 63 + "2",
            "extract": {"committed_bundle_sha256": "c" * 63 + "3", "committed_bundle_equals_built": True}}
    res = {"package": {"@a2ui/react": "0.15.0", "@a2ui/web_core": "0.15.0"}, "complete": True, "date": "2026-11-12T10:00:00", "code": code,
           "timings_s": {"total": 5}}
    (tmp_path / "react/runs/F/RESULTS-react.json").write_text(_j.dumps(res))
    (tmp_path / "react/runs/F/DETAIL-react.json").write_text(_j.dumps({"custom": {}}))
    (tmp_path / "m5-react" / "unstable").mkdir(parents=True)
    (tmp_path / "m5-react/unstable/react.json").write_text("{}")
    with pytest.raises(SystemExit) as e:
        exp.export_web("react", str(tmp_path), ["alpha"], "shipped", str(tmp_path), "F", "a" * 40)
    assert "not on the shipped commit" in str(e.value)
    code["head"] = "a" * 40
    (tmp_path / "react/runs/F/RESULTS-react.json").write_text(_j.dumps(res))
    head, atoms = exp.export_web("react", str(tmp_path), ["alpha"], "shipped", str(tmp_path), "F", "a" * 40)
    assert head["commit"] == "a" * 40 and head["renderer_bundle_sha256"] == "c" * 63 + "3" and atoms["alpha"]["no_case"] == "no_example"
    head, _ = exp.export_web("react", str(tmp_path), ["alpha"], "preview-unmerged", str(tmp_path), "F", "a" * 40)
    assert head["commit"] is None
    res["package"]["@a2ui/react"] = "0.16.0"
    (tmp_path / "react/runs/F/RESULTS-react.json").write_text(_j.dumps(res))
    with pytest.raises(SystemExit):
        exp.export_web("react", str(tmp_path), ["alpha"], "shipped", str(tmp_path), "F", "a" * 40)


# ------------------------------------------------------------------ rules v4: deterministic mode


def test_text_parity_fail_is_a_difference_and_excluded_random_is_not():
    st, reasons, d = gen.web_case_status(web_case(text_parity="fail"))
    assert st == "drawn_with_differences" and "text_differs" in reasons
    c = web_case(text_parity="excluded_random")
    c["notes"] = ["seeded_random_order_differs"]
    c["checks"]["pixel"]["light480"]["result"] = "excluded_random"
    st, reasons, d = gen.web_case_status(c)
    assert st == "drawn" and reasons == [] and d["notes"] == ["seeded_random_order_differs"]


def test_det_stable_entry_has_no_unverified_reason_and_entry_carries_notes():
    c = web_case(text_parity="pass", sources={"pixel": "det-ab"})
    e = gen.entry_for("web", head("lit", {}), {"cases": {"alpha": dict(c, notes=["seeded_random_order_differs"])}})
    assert e["status"] == "drawn" and e["notes"] == ["seeded_random_order_differs"] and e["checks"]["sources"] == {"pixel": "det-ab"}


def test_exporter_det_case_provenance_and_exclusions():
    rec = {"broken": False, "error": False, "loose": True, "strict": True, "strict_text": True}
    px = {"blank_both": False, "one_blank": False, "passed": False, "frac": 0.3, "hdiff": 2, "overflow": True, "low": 1, "low_ref": 0, "text_same": False}
    det = {lane: {"alpha": dict(px)} for lane in exp.DET_LANES.values()}
    c = exp.det_case("lit", "alpha", rec, {"behaviour_custom": {}}, det, True, True)
    ck = c["checks"]
    assert ck["pixel"]["light480"]["result"] == "fail" and ck["overflow_360"]["light360"] is True
    assert ck["text_parity"] == "fail" and ck["stability"] == "stable" and ck["sources"]["pixel"] == "det-ab" and ck["sources"]["painted"] == "f111"
    assert "notes" not in c
    det = {lane: {"gmail_unread_count": dict(px)} for lane in exp.DET_LANES.values()}
    c = exp.det_case("lit", "gmail_unread_count", rec, {"behaviour_custom": {}}, det, True, True)
    assert c["notes"] == [exp.NOTE_RANDOM] and c["checks"]["pixel"]["dark480"]["result"] == "excluded_random" and c["checks"]["text_parity"] == "excluded_random"
    r = exp.det_case("react", "alpha", rec, {"behaviour_custom": {}, "pixel": {"alpha": {"low": 0, "overflow": False}}}, {}, True, False)
    assert r["checks"]["pixel"]["light480"]["result"] == "reference" and r["checks"]["text_parity"] == "n/a"
    assert gen.web_case_status(r)[0] == "drawn"


def test_exporter_det_refuses_when_run_a_and_b_fail_lists_differ(tmp_path):
    import json as _j
    d = tmp_path / "det"
    d.mkdir()
    (d / "det_gate_raw.json").write_text(_j.dumps({"renderers": {"lit": {"pixel": {"fail_identical_in_run_B": False, "atoms": {}}}}}))
    (d / "det_baselines_sha256.json").write_text(_j.dumps({"ab_exceptions": {}}))
    (tmp_path / "lit" / "runs" / "F").mkdir(parents=True)
    (tmp_path / "m5-harness" / "unstable").mkdir(parents=True)
    (tmp_path / "m5-harness/unstable/lit.json").write_text("{}")
    res = {"package": {"@a2ui/lit": "0.15.0", "@a2ui/web_core": "0.15.0"}, "complete": True, "date": "2026-11-12T10:00:00",
           "code": {"head": "a" * 40, "dirty_tracked": False, "core_sha256": CORE, "css_sha256": "b" * 64,
                    "extract": {"committed_bundle_sha256": "c" * 64, "committed_bundle_equals_built": True}}}
    (tmp_path / "lit/runs/F/RESULTS-lit.json").write_text(_j.dumps(res))
    (tmp_path / "lit/runs/F/DETAIL-lit.json").write_text(_j.dumps({"custom": {}}))
    with pytest.raises(SystemExit) as e:
        exp.export_web_det("lit", str(tmp_path), ["alpha"], "shipped", str(tmp_path), "F", "a" * 40, str(d))
    assert "differs between run A and run B" in str(e.value)


def test_ck187_det_case_provenance_not_run_and_no_random_exclusion():
    rec = {"broken": False, "error": False, "loose": True, "strict": True, "strict_text": True}
    px = {"blank_both": False, "one_blank": False, "passed": True, "frac": 0.0, "hdiff": 0, "overflow": False, "low": 0, "low_ref": 0, "text_same": True}
    det = {lane: {"gmail_unread_count": dict(px)} for lane in exp.DET_LANES.values()}
    c = exp.det_case("copilotkit", "gmail_unread_count", rec, {"behaviour_custom": {}}, det, True, True,
                     src_label="ck187", behaviour_run=False, exclude_random=False)
    ck = c["checks"]
    assert ck["behaviour"] == "not_run" and ck["text_parity"] == "pass" and "notes" not in c
    assert ck["sources"]["painted"] == "ck187" and ck["sources"]["pixel"] == "det-ab" and ck["stability"] == "stable"
    assert gen.web_case_status(c)[0] == "drawn"


def test_note_on_a_pixel_failing_atom_does_not_hide_the_difference():
    c = web_case()
    c["checks"]["pixel"]["light480"]["result"] = "fail"
    c["notes"] = ["vertical_offset_1px_cause_not_isolated"]
    e = gen.entry_for("web", head("copilotkit", {}), {"cases": {"alpha": c}})
    assert e["status"] == "drawn_with_differences" and e["notes"] == ["vertical_offset_1px_cause_not_isolated"]
    assert set(exp.CK187_NOTES) == {"page_header", "code_snippet_pair", "image_with_caption"}


# ------------------------------------------------------------------ site wiring (catalogue x-renderers, atom block, pages)


def _site():
    return chk._import("renderer_site", os.path.join(chk.HERE, "renderer_site.py"))


def test_atom_block_has_every_renderer_and_the_trademark_footer():
    site = _site()
    m = json.loads(open(os.path.join(chk.WT, chk.MATRIX_REL), encoding="utf8").read())
    atom = sorted(m["atoms"])[0]
    block = site.atom_block(m, atom)
    for rid, reg in m["renderers"].items():
        assert 'href="/renderers/%s/"' % rid in block and reg["name"] in block
    assert "rd-tm" in block and "do not imply affiliation" in block
    assert site.atom_block(m, "no_such_atom") == "" and site.atom_block(None, atom) == ""


def test_site_wiring_flags_catalogue_without_x_renderers(tmp_path):
    m = json.loads(open(os.path.join(chk.WT, chk.MATRIX_REL), encoding="utf8").read())
    atom = sorted(m["atoms"])[0]
    cat = tmp_path / "public" / "catalogue"
    cat.mkdir(parents=True)
    for rel in chk.CATALOGUES_REL:
        (tmp_path / rel).write_text(json.dumps({"components": {atom: {"x-surfaces": ["web"]}}}))
    (tmp_path / chk.SPEC_REL).write_text(json.dumps({"atoms": [{"type": atom}]}))
    ctx = {"stable": sorted(m["atoms"]), "matrix": m, "root": str(tmp_path)}
    errs = chk.check_site_wiring(ctx)
    assert any("x-renderers of %s" % atom in msg for _, msg in errs)
    assert any("page public/renderers/index.html is missing" in msg for _, msg in errs)
