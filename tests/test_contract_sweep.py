"""Build contract coverage for every atom (I75 sweep, owner 2026-10-23).

tests/fixtures/contract_registry.json lists every schema atom: keyed (the D3 charts, tested in test_build_contract_v12),
sweep (a collection atom being keyed, its sample and pre-sweep hashes in contract_sweep.json), single (one visual unit,
keyed later as a whole block), exempt (with a reason) or todo. A new atom fails test_every_schema_atom_is_registered until
it is classified: that is the onboarding check.

A sweep atom whose status is "keyed" (or named in A2UI_SWEEP_ATOMS, the batch being worked on) must, in Python and in
GAS: render; put data-cb with a kind from the registry's list on at least two elements; give each a non-empty data-key,
unique among the shapes and among the labels; and be purely additive (stripping data-cb, data-key and the cb-fade class
gives the pre-sweep hash). Twins that were byte-identical before stay byte-identical.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from test_motion_atoms import _norm, _py_keyed, core_js  # noqa: E402,F401

ROOT = Path(__file__).parent.parent
REG = json.loads((ROOT / "tests/fixtures/contract_registry.json").read_text())
SWEEP = json.loads((ROOT / "tests/fixtures/contract_sweep.json").read_text())
BATCH = [a for a in os.environ.get("A2UI_SWEEP_ATOMS", "").split(",") if a]
KEYED = sorted({n for n, v in SWEEP.items() if v["status"] == "keyed"} | set(BATCH))

TAG = re.compile(r'<\w+\b[^>]*\sdata-cb="([^"]*)"[^>]*>')
KEY = re.compile(r'\sdata-key="([^"]*)"')
STRIP = (re.compile(r' data-cb="[^"]*"'), re.compile(r' data-key="[^"]*"'))


def test_every_schema_atom_is_registered():
    schema = [b["type"] for b in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]]
    missing = [t for t in schema if t not in REG["atoms"]]
    assert not missing, ("atoms with no build-contract status: %s. Add each to tests/fixtures/contract_registry.json "
                         "(keyed / sweep / single / exempt with a reason); a collection atom gets data-cb + data-key "
                         "(scratchpad sweep runner, or by hand) and a sample in contract_sweep.json." % missing)


def test_registry_entries_are_well_formed():
    for t, v in REG["atoms"].items():
        assert v["status"] in ("keyed", "sweep", "single", "exempt", "todo"), t
        if v["status"] in ("exempt", "single", "todo"):
            assert v.get("reason"), t
        if v["status"] == "sweep":
            assert t in SWEEP, t
    for t, v in SWEEP.items():
        assert v["kind"] in REG["kinds"] and v["label_kind"] in REG["kinds"], t


def _reset_counters():
    """Python renderers number their ids with mutable default counters (def _render_tabs(b, _tab_counter=[0])): reset them all,
    so an atom renders the same bytes whatever rendered before it (the GAS side gets a fresh context per atom)."""
    import renderers.web_article as wa
    for f in vars(wa).values():
        for d in (getattr(f, "__defaults__", None) or ()):
            if isinstance(d, list) and len(d) == 1 and isinstance(d[0], int):
                d[0] = 0


def _py_fresh(block):
    _reset_counters()
    return _py_keyed(dict(block))


def _strip(html):
    for r in STRIP:
        html = r.sub("", html)
    return html.replace(' class="cb-fade"', "").replace(" cb-fade", "")


def _gas_isolated(core_js, blocks):
    """GAS renders, each block in a FRESH JavaScript context (the GAS core keeps state between renders, so a batch would
    make one atom's bytes depend on the atoms before it) with Math.random seeded (some atoms draw random class prefixes)."""
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "core.js").write_text("var window = this;\n" + core_js + "\nthis.renderAtoms = renderAtoms;")
        (Path(td) / "blocks.json").write_text(json.dumps(blocks))
        (Path(td) / "run.js").write_text(
            "var vm = require('vm'), fs = require('fs'), path = require('path');"
            "var script = new vm.Script(fs.readFileSync(path.join(__dirname, 'core.js'), 'utf8'));"
            "var B = JSON.parse(fs.readFileSync(path.join(__dirname, 'blocks.json'), 'utf8'));"
            "console.log(JSON.stringify(B.map(function(b){ var s = 1; var M = Object.create(Math); M.random = function(){ s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };"
            " var ctx = vm.createContext({console: console, Math: M, JSON: JSON, Date: Date}); try { script.runInContext(ctx); return ctx.renderAtoms([b], {}); }"
            " catch (e) { return 'GAS ERROR: ' + (e && e.stack || e); } })));")
        proc = subprocess.run(["node", str(Path(td) / "run.js")], capture_output=True, text=True, timeout=600)
        assert proc.returncode == 0, proc.stderr[-1500:]
        return json.loads(proc.stdout.strip().split("\n")[-1])


@pytest.fixture(scope="module")
def pairs(core_js):
    names = sorted(SWEEP)   # every sweep atom renders: the keyed ones are checked, the rest must still give their pre-sweep bytes
    blocks = [SWEEP[n]["block"] for n in names]
    gas = _gas_isolated(core_js, blocks) if names else []
    out = {}
    for n, b, g in zip(names, blocks, gas):
        try:
            py = _py_fresh(b)
        except Exception as e:  # one crash fails only its own atom
            py = "PY ERROR: %s: %s" % (type(e).__name__, e)
        out[n] = {"py": py, "gas": g}
    return out


def _check(html, kinds):
    tags = [(m.group(1), m.group(0)) for m in TAG.finditer(html)]
    assert len(tags) >= 2, "fewer than two data-cb elements"
    bad = [k for k, _ in tags if k not in kinds]
    assert not bad, "kinds outside the contract: %s" % sorted(set(bad))
    nokey = [t[:160] for _, t in tags if not (KEY.search(t) and KEY.search(t).group(1).strip())]
    assert not nokey, "data-cb without a data-key: %s" % nokey[:3]
    shapes = [(k, KEY.search(t).group(1)) for k, t in tags if k != "label"]
    labels = [KEY.search(t).group(1) for k, t in tags if k == "label"]
    for g in (shapes, labels):
        dup = sorted({x for x in g if g.count(x) > 1})
        assert not dup, "duplicate keys: %s" % dup[:5]


@pytest.mark.parametrize("name", KEYED)
@pytest.mark.parametrize("twin", ["py", "gas"])
def test_contract_and_keys(name, twin, pairs):
    html = pairs[name][twin]
    assert not html.startswith(("PY ERROR", "GAS ERROR")), html[:600]
    _check(html, REG["kinds"])


@pytest.mark.parametrize("name", sorted(SWEEP))
@pytest.mark.parametrize("twin", ["py", "gas"])
def test_the_contract_is_purely_additive(name, twin, pairs):
    """For a keyed atom: the contract adds attributes only. For an atom not keyed yet: its output has not moved at all
    (an edit meant for another atom that landed in shared code shows up here)."""
    html = pairs[name][twin]
    assert hashlib.sha256(_norm(_strip(html)).encode()).hexdigest() == SWEEP[name][twin + "_sha"], \
        "stripping data-cb, data-key and cb-fade does not give the pre-sweep bytes"


@pytest.mark.parametrize("name", [n for n in KEYED if SWEEP[n]["parity"]])
def test_twins_that_matched_still_match(name, pairs):
    assert _norm(pairs[name]["py"]) == _norm(pairs[name]["gas"])
