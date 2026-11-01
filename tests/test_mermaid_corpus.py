"""Corpus test for the Mermaid / D2 -> motion_arch converter (scripts/mermaid_arch).

Every file in tests/mermaid_corpus is converted once by tests/mermaid_corpus_runner.mjs (one node process,
options film + numbered + hint web, each file converted twice for the determinism check). The manifest
tests/mermaid_corpus/expected.json says what each input must do. An entry may carry "known_gap": a list of
{kind, reason} for behaviour that is unideal but not wrong. A gap is an expected failure of exactly one check
(strict, so fixing the converter flips it to XPASS and the entry must then be removed):
  outcome | error_message | error_line | labels | warnings | readability
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "mermaid_corpus"
MANIFEST = json.loads((CORPUS / "expected.json").read_text(encoding="utf-8"))
FILES = sorted(p.name for p in CORPUS.iterdir() if p.suffix in (".mmd", ".d2", ".json") and p.name != "expected.json")

FLIP = re.compile(r"^drawn .* instead of")  # informational layout-direction note, not a content warning
NEEDLES = ("<script", "onerror=", "<iframe", "<img", "javascript:")

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")


@pytest.fixture(scope="module")
def results():
    proc = subprocess.run(["node", str(HERE / "mermaid_corpus_runner.mjs"), str(CORPUS)],
                          capture_output=True, text=True, timeout=120, check=False)
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout)


def gap_kinds(name):
    return {g["kind"]: g["reason"] for g in MANIFEST.get(name, {}).get("known_gap", [])}


def run_check(name, kind, check):
    """Run check(); a recorded gap must fail (strict xfail), anything else must pass."""
    reason = gap_kinds(name).get(kind)
    try:
        check()
    except AssertionError:
        if reason is None:
            raise
        pytest.xfail(reason)
    if reason is not None:
        pytest.fail(f"known gap '{kind}' no longer reproduces ({reason}); remove it from expected.json")


def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, list):
        for y in x:
            yield from strings(y)
    elif isinstance(x, dict):
        for y in x.values():
            yield from strings(y)


def test_manifest_matches_corpus():
    assert sorted(MANIFEST) == FILES, (
        f"files without an entry: {sorted(set(FILES) - set(MANIFEST))}; entries without a file: {sorted(set(MANIFEST) - set(FILES))}")
    assert len(FILES) >= 40


@pytest.mark.parametrize("name", FILES)
def test_no_crash_and_fast(results, name):
    r = results[name]
    assert not r.get("crash"), f"{name}: converter crashed (not an ArchError): {r.get('errors')} {r.get('stack')}"
    assert r["ms"] < 2000, f"{name}: took {r['ms']:.0f} ms"
    assert r["deterministic"], f"{name}: two runs gave different output"


@pytest.mark.parametrize("name", FILES)
def test_outcome(results, name):
    exp, r = MANIFEST[name], results[name]
    want = exp["outcome"]

    def check():
        if want == "error":
            assert not r["ok"], f"{name}: expected an error, converted fine ({r.get('counts')})"
        else:
            assert r["ok"], f"{name}: expected a diagram, got {r.get('errors')}"
            assert r["counts"] == exp["counts"], f"{name}: counts {r['counts']} != {exp['counts']}"
            sig = [w for w in r["warnings"] if not FLIP.match(w)]
            assert bool(sig) == (want == "ok_with_warnings"), f"{name}: expected {want}, warnings were {sig}"
    run_check(name, "outcome", check)


@pytest.mark.parametrize("name", [n for n in FILES if MANIFEST[n]["outcome"] == "error"])
def test_error_message(results, name):
    exp, r = MANIFEST[name], results[name]
    assert not r["ok"] and not r.get("crash")
    text = "\n".join(r["errors"])
    want = exp["message"] if isinstance(exp["message"], list) else [exp["message"]]
    def has_text():
        for w in want:
            assert w in text, f"{name}: {w!r} not in {text!r}"
    run_check(name, "error_message", has_text)
    assert "internal error" not in text and "cli.mjs" not in text, f"{name}: internal or CLI wording leaked: {text}"
    if exp.get("line_relevant"):
        def names_line():
            assert re.search(r"\bline \d+", text), f"{name}: error does not name a line: {text!r}"
        run_check(name, "error_line", names_line)


@pytest.mark.parametrize("name", [n for n in FILES if MANIFEST[n]["outcome"] != "error"])
def test_payload_sound(results, name):
    r = results[name]
    if not r["ok"]:
        pytest.skip("outcome gap, covered by test_outcome")
    assert r["blockErrors"] == [], f"{name}: validateBlock: {r['blockErrors']}"
    assert r["tableRows"] == r["counts"]["edges"] == r["steps"], f"{name}: step rows {r['tableRows']} / edges {r['counts']['edges']}"
    payload = json.loads(r["payload"])
    low = r["payload"].lower()
    for needle in NEEDLES:
        assert needle not in low, f"{name}: {needle!r} survived into the payload"
    # every node label is in the payload, or is cut and the cut is warned about
    texts = set(strings(payload))
    for label in r["nodeLabels"]:
        if label in texts:
            continue
        assert len(label) > 40 and any("will be cut" in w or "at most 40" in w for w in r["warnings"]), \
            f"{name}: label {label!r} is missing from the payload and no cut warning was given"


@pytest.mark.parametrize("name", [n for n in FILES if MANIFEST[n].get("labels")])
def test_labels_intact(results, name):
    r = results[name]
    if not r["ok"]:
        pytest.skip("outcome gap")
    texts = set(strings(json.loads(r["payload"])))
    want = MANIFEST[name]["labels"]

    def check():
        missing = [w for w in want if w not in texts]
        assert not missing, f"{name}: labels not in the payload as written: {missing}; node labels were {r['nodeLabels']}"
    run_check(name, "labels", check)


@pytest.mark.parametrize("name", [n for n in FILES if MANIFEST[n].get("warning")])
def test_warning_text(results, name):
    r = results[name]
    want = MANIFEST[name]["warning"]
    def check():
        assert any(want in w for w in r["warnings"]), f"{name}: no warning mentions {want!r}: {r['warnings']}"
    run_check(name, "warnings", check)


@pytest.mark.parametrize("name", [n for n in FILES if MANIFEST[n]["outcome"] != "error"])
def test_readable(results, name):
    r = results[name]
    if not r["ok"]:
        pytest.skip("outcome gap")
    px = [int(m.group(1)) for w in r["warnings"] for m in [re.search(r"text about (\d+) px", w)] if m]

    def check():
        assert all(p >= 10 for p in px), f"{name}: text drawn at {px} px"
    run_check(name, "readability", check)


def test_gap_kinds_are_known():
    allowed = {"outcome", "error_message", "error_line", "labels", "warnings", "readability"}
    for name, e in MANIFEST.items():
        for g in e.get("known_gap", []):
            assert g["kind"] in allowed and g["reason"], f"{name}: bad known_gap {g}"
