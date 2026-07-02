"""Round-trip and lint tests for the training.md parser.

The round-trip fixture pair: examples/clasp-deployment.training.md must
reproduce payloads/clasp-runbook.json structurally — identical atom
sequence, props, wire topology, and state machinery, compared modulo
block/store identifier *names* (the reference was hand-built with
semantic ids like s_nvs; the parser generates s_1..s_n; the wire graph
must be isomorphic)."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from parse_training_md import parse  # noqa: E402

FIXTURE = ROOT / "examples" / "clasp-deployment.training.md"
REFERENCE = ROOT / "payloads" / "clasp-runbook.json"

FRONTMATTER = """---
id: t
domain: training
name: "T"
source: "s"
license: MIT
---
"""

MINIMAL_STEPS = """
# Steps
## 1. One {#command_step}
cmd: echo hi
verify: true
"""


def normalize_ids(payload):
    """Rename every id to a canonical name in first-seen order and rewrite
    all '#id.prop' references, jump_nav targets accordingly."""
    payload = json.loads(json.dumps(payload))
    mapping = {}

    def canon(old):
        if old not in mapping:
            mapping[old] = f"id{len(mapping)}"
        return mapping[old]

    for prim in payload.get("state_primitives", []):
        prim["id"] = canon(prim["id"])
    for block in payload.get("layout", []):
        block["id"] = canon(block["id"])

    def rewrite_ref(value):
        if isinstance(value, str) and value.startswith("#") and "." in value:
            old, _, prop = value[1:].partition(".")
            if old in mapping:
                return f"#{mapping[old]}.{prop}"
        return value

    for prim in payload.get("state_primitives", []):
        inputs = prim.get("props", {}).get("inputs")
        if inputs:
            prim["props"]["inputs"] = {k: rewrite_ref(v) for k, v in inputs.items()}
    for block in payload.get("layout", []):
        if "wire" in block:
            block["wire"] = {k: rewrite_ref(v) for k, v in block["wire"].items()}
        links = block.get("props", {}).get("links")
        if links:
            for link in links:
                if link.get("target") in mapping:
                    link["target"] = mapping[link["target"]]
    return payload


def test_round_trip_reproduces_clasp_runbook():
    payload, report = parse(FIXTURE.read_text())
    assert report["errors"] == [], report["errors"]
    reference = json.loads(REFERENCE.read_text())

    got, want = normalize_ids(payload), normalize_ids(reference)

    got_atoms = [b["atom"] for b in got["layout"]]
    want_atoms = [b["atom"] for b in want["layout"]]
    assert got_atoms == want_atoms

    for g, w in zip(got["layout"], want["layout"]):
        assert g == w, f"block mismatch:\n got: {json.dumps(g)}\nwant: {json.dumps(w)}"
    assert got["state_primitives"] == want["state_primitives"]
    assert got == want


def test_report_coverage():
    _, report = parse(FIXTURE.read_text())
    assert report["step_count"] == 7
    assert "Steps" in report["sections_present"]
    assert any(w.startswith("W02") for w in report["warnings"])


# --- lint rules ------------------------------------------------------------

def _errors(md):
    payload, report = parse(md)
    assert payload is None
    return report["errors"]


def test_e01_missing_frontmatter():
    assert any(e.startswith("E01") for e in _errors("# Steps\n"))


def test_e02_missing_required_key():
    md = "---\nid: t\ndomain: training\n---\n" + MINIMAL_STEPS
    errs = _errors(md)
    assert any(e.startswith("E02") and "'name'" in e for e in errs)
    assert any(e.startswith("E02") and "'license'" in e for e in errs)


def test_e03_wrong_domain():
    md = FRONTMATTER.replace("domain: training", "domain: sop") + MINIMAL_STEPS
    assert any(e.startswith("E03") for e in _errors(md))


def test_e04_no_steps():
    assert any(e.startswith("E04") for e in _errors(FRONTMATTER + "\n# Concepts\n- **a** — b\n"))
    assert any(e.startswith("E04") for e in _errors(FRONTMATTER + "\n# Steps\n"))


def test_e05_cmd_and_do():
    md = FRONTMATTER + "\n# Steps\n## 1. Bad\ncmd: x\ndo: y\n"
    assert any(e.startswith("E05") for e in _errors(md))
    md = FRONTMATTER + "\n# Steps\n## 1. Bad\nnote: neither\n"
    assert any(e.startswith("E05") for e in _errors(md))


def test_e06_non_sequential():
    md = FRONTMATTER + "\n# Steps\n## 1. A\ncmd: x\n\n## 3. B\ncmd: y\n"
    assert any(e.startswith("E06") for e in _errors(md))


def test_e07_unknown_step_key():
    md = FRONTMATTER + "\n# Steps\n## 1. A\ncmd: x\nbanana: y\n"
    assert any(e.startswith("E07") for e in _errors(md))


def test_e08_missing_separator():
    md = FRONTMATTER + MINIMAL_STEPS + "\n# Troubleshooting\n- symptom without sep\n"
    assert any(e.startswith("E08") for e in _errors(md))


def test_e09_forbidden_key():
    md = FRONTMATTER.replace("license: MIT", "license: MIT\nrender: full") + MINIMAL_STEPS
    assert any(e.startswith("E09") for e in _errors(md))


def test_e10_unmatched_q():
    md = FRONTMATTER + MINIMAL_STEPS + "\n# Checkpoints\nQ: only a question\n"
    assert any(e.startswith("E10") for e in _errors(md))


def test_e11_mixed_shapes():
    md = FRONTMATTER + "\n# Steps\n## 1. Flat step\ncmd: x\n\n## Phase\n### 1. Nested\ncmd: y\n"
    assert any(e.startswith("E11") for e in _errors(md))


def test_e12_unknown_section():
    md = FRONTMATTER + MINIMAL_STEPS + "\n# Bananas\n- x\n"
    assert any(e.startswith("E12") for e in _errors(md))


def test_w03_no_verify():
    md = FRONTMATTER + "\n# Steps\n## 1. A\ncmd: x\n"
    payload, report = parse(md)
    assert payload is not None
    assert any(w.startswith("W03") for w in report["warnings"])


def test_flat_shape_and_optional_sections():
    md = FRONTMATTER + """
# Prerequisites
- Node 18+

# Concepts
- **term** — definition

# Steps
## 1. One {#command_step}
cmd: echo one
verify: ok

## 2. Two {#command_step}
do: click the button
verify: ok

# Checkpoints
Q: q1
A: a1

# Troubleshooting
- broken :: fix it

# References
- docs — https://example.com
"""
    payload, report = parse(md)
    assert report["errors"] == []
    atoms = [b["atom"] for b in payload["layout"]]
    assert atoms == ["subheading", "prerequisite_checklist", "key_value",
                     "command_step", "command_step", "accordion_item",
                     "accordion_item", "resources_list"]
    assert payload["state_primitives"][-1]["props"]["expr"] == "n/2*100"
    assert payload["layout"][4]["props"]["command"] == "click the button"
