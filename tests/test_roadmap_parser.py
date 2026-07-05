"""Round-trip and lint tests for the roadmap.md parser.

The round-trip fixture pair: examples/artemis.roadmap.md must reproduce
payloads/artemis-roadmap.json exactly — both sides are parser-generated
(unlike the training reference, which was hand-built and needs
id-isomorphism), so the comparison is strict deep equality. The fixture
is the spec's test suite: any parser change that alters the payload must
consciously regenerate the fixture.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from parse_roadmap_md import parse, emit  # noqa: E402

FIXTURE = ROOT / "examples" / "artemis.roadmap.md"
REFERENCE = ROOT / "payloads" / "artemis-roadmap.json"

FRONTMATTER = """---
id: t
domain: roadmap
name: "T"
source: "s"
license: MIT
---
"""

MINIMAL_PHASES = """
# Phases
## 1 · One {.status-shipped}
1. Thing
   status: done
"""


def _run(text):
    parsed, lint, _ = parse(text)
    return parsed, lint


# ── Round-trip fixture ─────────────────────────────────────────────────────

def test_artemis_roundtrip():
    parsed, lint = _run(FIXTURE.read_text())
    assert not lint.errors, lint.errors
    payload = emit(parsed)
    reference = json.loads(REFERENCE.read_text())
    assert payload == reference, (
        "examples/artemis.roadmap.md no longer reproduces "
        "payloads/artemis-roadmap.json — if the parser change is "
        "intentional, regenerate the fixture via "
        "scripts/parse_roadmap_md.py"
    )


def test_artemis_coverage_full():
    parsed, lint = _run(FIXTURE.read_text())
    assert len(parsed["phases"]) == 3
    assert parsed["timeline"] and parsed["backlog"] and parsed["risks"]


# ── Lint contract ──────────────────────────────────────────────────────────

def test_minimal_valid():
    parsed, lint = _run(FRONTMATTER + MINIMAL_PHASES)
    assert not lint.errors
    payload = emit(parsed)
    atoms = [n["atom"] for n in payload["layout"]]
    assert "roadmap_card" in atoms
    assert "data_table_sortable" in atoms


def test_missing_phases_is_E03():
    parsed, lint = _run(FRONTMATTER + "\n# Timeline\n- now :: x\n")
    assert any(e.startswith("E03") for e in lint.errors)


def test_missing_status_is_E06():
    bad = FRONTMATTER + "\n# Phases\n## 1 · P\n1. Thing\n   below: x\n"
    parsed, lint = _run(bad)
    assert any(e.startswith("E06") for e in lint.errors)


def test_invalid_status_is_E06():
    bad = FRONTMATTER + "\n# Phases\n## 1 · P\n1. Thing\n   status: shipped\n"
    parsed, lint = _run(bad)
    assert any(e.startswith("E06") for e in lint.errors)


def test_unknown_item_key_is_E05():
    bad = FRONTMATTER + MINIMAL_PHASES + "   owner: me\n"
    parsed, lint = _run(bad)
    assert any(e.startswith("E05") for e in lint.errors)


def test_forbidden_frontmatter_is_E02():
    bad = FRONTMATTER.replace("---\n", "render: x\n---\n", 1)
    # splice render: into the frontmatter block
    bad = ("---\nid: t\ndomain: roadmap\nname: T\nsource: s\nlicense: MIT\n"
           "render: fancy\n---\n" + MINIMAL_PHASES)
    parsed, lint = _run(bad)
    assert any(e.startswith("E02") for e in lint.errors)


def test_wrong_domain_is_E01():
    bad = FRONTMATTER.replace("domain: roadmap", "domain: training") + MINIMAL_PHASES
    parsed, lint = _run(bad)
    assert any(e.startswith("E01") for e in lint.errors)


def test_invalid_risk_level_is_E07():
    bad = (FRONTMATTER + MINIMAL_PHASES +
           "\n# Risks\n- catastrophic :: t :: d :: m\n")
    parsed, lint = _run(bad)
    assert any(e.startswith("E07") for e in lint.errors)


def test_unknown_section_is_E04():
    bad = FRONTMATTER + MINIMAL_PHASES + "\n# Epics\n- x\n"
    parsed, lint = _run(bad)
    assert any(e.startswith("E04") for e in lint.errors)


def test_unknown_status_class_is_W02_not_error():
    text = (FRONTMATTER +
            "\n# Phases\n## 1 · P {.status-someday}\n1. Thing\n   status: planned\n")
    parsed, lint = _run(text)
    assert not lint.errors
    assert any(w.startswith("W02") for w in lint.warnings)
    assert parsed["phases"][0]["status"] == "planned"  # fallback


def test_private_license_sets_flag():
    text = (FRONTMATTER.replace("license: MIT", "license: private") +
            MINIMAL_PHASES)
    parsed, lint = _run(text)
    assert emit(parsed).get("private") is True


def test_backlog_checkbox_states():
    text = (FRONTMATTER + MINIMAL_PHASES +
            "\n# Backlog\n- [x] done thing\n- [ ] open thing\n")
    parsed, lint = _run(text)
    assert parsed["backlog"][0]["done"] is True
    assert parsed["backlog"][1]["done"] is False
