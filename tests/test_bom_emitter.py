"""bom_emitter — the generic BOM-driven emitter (runbook-as-data).

Locks the deterministic replacement of Prompt 3: curriculum.md + BOM YAML →
v1.0 envelope with ONE authored template per section kind, stamped over
dataModel arrays via the ChildList TEMPLATE variant. The pairing test runs
the REAL emitted envelope through the REAL decoder (atoms_v1_decode.gs via
the bundle core) and the REAL renderers — emit and decode proven together,
on real brevet content."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "knowledge-catalogue"))

import bom_emitter  # noqa: E402
import gen_mcp_apps_bundle as gen  # noqa: E402
import yaml  # noqa: E402

BOM = ROOT / "knowledge-catalogue" / "schemas" / "national-education" / "fr" / "dnb-2026.yaml"
MATHS = ROOT / "knowledge-catalogue" / "brevet-2026-maths.curriculum.md"
GENERIC_DEMO_BOM = ROOT / "knowledge-catalogue" / "schemas" / "generic-demo.yaml"
FIXTURES_DIR = ROOT / "knowledge-catalogue" / "tests" / "fixtures"
STABLE_ATOMS = {b["type"] for b in yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]
                if b.get("stage", "stable") == "stable"}


@pytest.fixture(scope="module")
def envelope():
    return bom_emitter.emit(BOM, [MATHS])


def test_parser_reads_real_curriculum():
    front, groups = bom_emitter.parse_curriculum(MATHS)
    assert front["id"] == "brevet-2026-maths"
    sections = [s for g in groups for s in g["sections"]]
    assert len(sections) == 14
    kinds = {s["kind"] for s in sections}
    assert {"drill", "glossary", "concept"} <= kinds
    assert all(s["competency"] for s in sections), "every section carries its anchor"


def test_parser_accepts_fenced_frontmatter():
    """Real (unpolished) LLM extraction output — not hand-authored examples —
    sometimes wraps the YAML frontmatter in a ```yml fenced code block
    instead of bare --- delimiters. Confirmed live 2026-07-14
    (@cf/meta/llama-3.3-70b-instruct-fp8-fast): this used to be a hard crash
    (ValueError: curriculum.md missing YAML frontmatter) on a file a human
    would read as obviously well-formed."""
    text = (
        "```yml\n"
        "id: fenced-test\n"
        "type: Course\n"
        "required_competencies:\n"
        "  - id: c1\n"
        "    label: Test\n"
        "    weight: high\n"
        "```\n"
        "\n"
        "<!-- competency: c1 -->\n"
        "## Some concept {#concept}\n"
        "Body text.\n"
    )
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "fenced.curriculum.md"
        p.write_text(text)
        front, groups = bom_emitter.parse_curriculum(p)
    assert front["id"] == "fenced-test"
    sections = [s for g in groups for s in g["sections"]]
    assert len(sections) == 1
    assert sections[0]["competency"] == "c1"


def test_glossary_matches_non_bold_formats():
    """The bold-colon format (- **term**: def) is one style among several a
    real model actually produces. Confirmed live 2026-07-14: a glossary
    section with backtick+em-dash lines (- `term` — def) silently collapsed
    6 real terms into ONE flashcard containing the whole raw bullet list as
    unreadable body text — no error, no signal, just a much worse card."""
    assert bom_emitter.match_glossary_line("- **term**: definition") == ("term", "definition")
    assert bom_emitter.match_glossary_line("- **term** — definition") == ("term", "definition")
    assert bom_emitter.match_glossary_line("- `term` — definition") == ("term", "definition")
    assert bom_emitter.match_glossary_line("- `term`: definition") == ("term", "definition")
    assert bom_emitter.match_glossary_line("- term: definition") == ("term", "definition")
    assert bom_emitter.match_glossary_line("not a glossary line") is None


def test_glossary_matches_table_format():
    """A THIRD real glossary format, found live 2026-07-14 in an
    already-shipped, previously-untested artifact
    (brevet-2026-francais.curriculum.md, "figures de style"): a markdown
    TABLE (term | definition | example), not a bullet list at all — no
    bullet pattern could ever match this. Both real sections silently
    collapsed to 1 flashcard each despite 900+/350+ chars of real table
    content, until bom_emitter started trying _md_table() (already used for
    drill sections) before falling back to bullet-line matching."""
    body = (
        "| Figure | Définition | Exemple |\n"
        "|---|---|---|\n"
        "| **Métaphore** | Comparaison implicite | « un long fleuve tranquille » |\n"
        "| **Hyperbole** | Exagération forte | « je meurs de faim » |\n"
    )
    sect = {"title": "Figures de style", "kind": "glossary", "classes": [],
            "weight": "medium", "competency": "c1", "body": body}
    item, _ = bom_emitter.extract_section(sect)
    assert len(item["cards"]) == 2
    assert item["cards"][0]["front"] == "Métaphore"
    assert "long fleuve" in item["cards"][0]["back"]


def test_frontmatter_tolerates_unquoted_colon_in_value():
    """A FOURTH real bug, found live 2026-07-14 testing a genuinely random
    source document (Wikipedia's Kubernetes article, pro-cert schema): the
    model wrote `source: Wikipedia: Kubernetes (fetched 2026-07-14)` — an
    unquoted value containing its own colon, which YAML parses as an
    illegal nested mapping ("mapping values are not allowed here"). A hard
    crash on a line a human would read as obviously a single string."""
    text = (
        "---\n"
        "id: colon-test\n"
        "source: Wikipedia: Kubernetes (fetched 2026-07-14)\n"
        "required_competencies: []\n"
        "---\n"
        "Body.\n"
    )
    front, _ = bom_emitter.parse_frontmatter(text)
    assert front["source"] == "Wikipedia: Kubernetes (fetched 2026-07-14)"


def test_section_and_timeline_accept_shifted_heading_levels():
    """A FIFTH real bug, same Kubernetes test: the model nested a timeline
    section one level deeper than the spec (### instead of ##, #### instead
    of ### for its events) — apparently to reflect a perceived thematic
    grouping, not a formatting mistake a human would even notice. Both the
    section AND its competency anchor were silently dropped with no error;
    the heading LEVEL carries no semantic meaning here, only the {#kind}
    tag and the anchor do."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "shifted.curriculum.md"
        p.write_text(
            "---\n"
            "id: shifted-test\n"
            "required_competencies:\n"
            "  - id: c1\n"
            "    label: Test\n"
            "    weight: high\n"
            "---\n"
            "\n"
            "<!-- competency: c1 -->\n"
            "### Some Timeline {#timeline}\n"
            "#### 2020 | An event\n"
            "It happened.\n"
        )
        front, groups = bom_emitter.parse_curriculum(p)
    sections = [s for g in groups for s in g["sections"]]
    assert len(sections) == 1
    assert sections[0]["kind"] == "timeline"
    assert sections[0]["competency"] == "c1"
    item, _ = bom_emitter.extract_section(sections[0])
    assert len(item["events"]) == 1
    assert item["events"][0]["date"] == "2020"


def test_method_steps_keep_nested_content():
    """A SIXTH real bug, found live 2026-07-14 (fresh SQL extraction, pro-cert
    schema): a numbered step's indented sub-bullets and inline code examples
    ("1. DDL: ...\\n   - Example: `CREATE TABLE ...`") were silently DROPPED —
    only the bare top-level numbered line survived, discarding the actual
    CREATE/INSERT/UPDATE/DELETE examples with no error. Verified against all
    10 real method sections in togaf-10.curriculum.md: item counts unchanged
    (no regression), confirming this only recovers previously-lost content."""
    body = (
        "1. **DDL**: governs structure.\n"
        "   - Example: `CREATE TABLE x (id INT)`\n"
        "2. **DML**: handles data.\n"
        "   - **INSERT**: adds rows\n"
        "   - **UPDATE**: modifies rows\n"
    )
    sect = {"title": "Languages", "kind": "method", "classes": [],
            "weight": "medium", "competency": "c1", "body": body}
    item, _ = bom_emitter.extract_section(sect)
    assert len(item["items"]) == 2
    assert "CREATE TABLE" in item["items"][0]
    assert "INSERT" in item["items"][1] and "UPDATE" in item["items"][1]


def test_glossary_matches_asterisk_bullets_with_parenthetical():
    """A SEVENTH real bug, found live 2026-07-14 (fresh Renaissance
    extraction, pro-cert schema): the model used `*` bullets exclusively
    (never `-`), AND put a parenthetical between the bold term and the
    separator ("* **Leonardo da Vinci** (1452-1519): ..."). Both defeated
    the existing patterns simultaneously — 6 real figures collapsed to 1
    body-dump card."""
    assert bom_emitter.match_glossary_line(
        "* **Leonardo da Vinci** (1452-1519): Renaissance polymath."
    ) == ("Leonardo da Vinci", "Renaissance polymath.")
    assert bom_emitter.match_glossary_line("* **term** — definition") == ("term", "definition")


def test_timeline_matches_date_only_heading():
    """An EIGHTH real bug, same Renaissance extraction: a timeline section
    used a DATE-ONLY heading with the description as separate body prose
    ("### 1396" then a new paragraph) — no pipe, no title on the heading
    line at all. Zero events were extracted: since no line ever matched the
    pipe-separated pattern, the per-line state machine never opened an
    event, so the body-accumulation branch never fired either. 9 real dated
    events were lost with no error, not even a degraded fallback."""
    sect = {"title": "Timeline", "kind": "timeline", "classes": [],
            "weight": "medium", "competency": "c1", "body": (
                "### 1250-1300\n"
                "Proto-Renaissance emerges in Italy.\n"
                "\n"
                "### 1396\n"
                "Greek scholarship begins in Florence.\n"
            )}
    item, _ = bom_emitter.extract_section(sect)
    assert len(item["events"]) == 2
    assert item["events"][0]["date"] == "1250-1300"
    assert "Proto-Renaissance" in item["events"][0]["desc"]
    assert item["events"][1]["date"] == "1396"


def test_envelope_is_template_shaped(envelope):
    comps = {c["id"]: c for c in envelope["createSurface"]["components"]}
    assert "root" in comps
    # ONE authored subtree per kind — templates are shared, not per-section
    tpl_ids = [i for i in comps if i.startswith("tpl_")]
    assert len(tpl_ids) == len(set(tpl_ids))
    # every content wrapper binds children via the TEMPLATE variant
    template_wrappers = [c for c in comps.values()
                         if isinstance(c.get("children"), dict)]
    assert template_wrappers, "no ChildList template bindings emitted"
    for w in template_wrappers:
        assert set(w["children"]) == {"componentId", "path"}
        assert w["children"]["componentId"] in comps
    # content lives in the data model, not in components
    dm = envelope["createSurface"]["dataModel"]
    maths = dm["subjects"][0]
    assert any("drill" in sl for sl in maths["slides"])
    drill_items = next(sl["drill"] for sl in maths["slides"] if "drill" in sl)
    assert drill_items[0]["questions"], "drill table extracted to questions"


def test_bom_atom_map_drives_component_choice(envelope):
    comps = {c["id"]: c for c in envelope["createSurface"]["components"]}
    # fr-dnb BOM (or SPEC default): drill -> brevet_automatismes, concept -> flashcard_deck
    assert comps["tpl_drill_atom"]["component"] == "brevet_automatismes"
    assert comps["tpl_concept"]["component"] == "flashcard_deck"


def test_piege_downgrade_is_declared_not_silent(envelope):
    e = envelope["_emitter"]
    assert e["piege_downgrades"] > 0, "maths curriculum has PIÈGE callouts"
    comps = {c["id"]: c for c in envelope["createSurface"]["components"]}
    assert comps["tpl_piege"]["component"] == "callout"   # no invented MCQs
    assert not any(c.get("component") == "knowledge_check"
                   for c in comps.values())


def test_pairing_emit_decodes_and_renders_real_content(envelope):
    """The runbook-as-data proof: real curriculum in, real pixels out —
    through the SAME decoder and renderers both surfaces ship."""
    bundle = gen.build_bundle()
    core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
            if "a2ui-core" in b[:300]][0]
    with tempfile.TemporaryDirectory() as td:
        env_path = Path(td) / "env.json"
        env_path.write_text(json.dumps(envelope, ensure_ascii=False))
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core + f"""
var env = JSON.parse(require('fs').readFileSync({json.dumps(str(env_path))}, 'utf8'));
var out = _rehydrateV1Surface(env.createSurface);
var html = renderAtoms(out.blocks, {{theme: 'dark'}});
console.log(JSON.stringify({{len: html.length,
  err: html.indexOf('Error rendering') > -1 || html.indexOf('unknown or unsupported') > -1,
  markers: ['Pythagore', 'Carrés parfaits', 'divisibilité', 'Mathématiques']
    .map(function(m) {{ return html.indexOf(m) > -1; }})}}));
""")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=120)
        assert p.returncode == 0, p.stderr[-1000:]
        r = json.loads(p.stdout)
    assert not r["err"], "emitted envelope rendered with errors"
    assert all(r["markers"]), f"real content missing from render: {r['markers']}"
    assert r["len"] > 5000


def test_drill_items_use_question_answer_keys():
    """Regression test for a real production bug found while designing the
    generic-demo schema: both brevet_automatismes and faq_accordion's
    renderers read q.question/q.answer (confirmed in atoms_brevet.gs and
    atom.gs), but extract_section used to emit {q, a} — every drill row
    rendered blank in production, silently, with no error anywhere."""
    body = "| Question | Answer |\n|---|---|\n| 7 × 8 | 56 |\n"
    sect = {"title": "Drill", "kind": "drill", "classes": [],
            "weight": "medium", "competency": "c1", "body": body}
    item, _ = bom_emitter.extract_section(sect)
    assert item["questions"] == [{"question": "7 × 8", "answer": "56"}]


def test_generic_demo_schema_drives_stable_atoms_only():
    """The Frugal AI Ops demo's output must never be the first place a
    preview atom reaches the public — generic-demo.yaml's atom_type_map
    should resolve only to atoms that are stage: stable (or unset, which
    defaults to stable) in atoms/schema.yaml."""
    curriculum = (
        "---\n"
        "id: generic-demo-test\n"
        "subject: general\n"
        "required_competencies: []\n"
        "---\n"
        "\n"
        "<!-- competency: c1 -->\n"
        "## A Concept {#concept}\n"
        "Some concept body.\n"
        "\n"
        "<!-- competency: c2 -->\n"
        "## Terms {#glossary}\n"
        "- **Term**: a definition\n"
        "\n"
        "<!-- competency: c3 -->\n"
        "## Quick Drill {#drill}\n"
        "| Question | Answer |\n"
        "|---|---|\n"
        "| 2+2 | 4 |\n"
        "\n"
        "<!-- competency: c4 -->\n"
        "## How To {#method}\n"
        "1. Do this.\n"
        "2. Then that.\n"
        "\n"
        "<!-- competency: c5 -->\n"
        "## Wrap-up {#key_takeaways}\n"
        "- Point one\n"
        "- Point two\n"
        "\n"
        "<!-- competency: c6 -->\n"
        "## History {#timeline}\n"
        "### 2020 | Event one\n"
        "It happened.\n"
    )
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "generic.curriculum.md"
        p.write_text(curriculum)
        env = bom_emitter.emit(GENERIC_DEMO_BOM, [p])
    used = {c["component"] for c in env["createSurface"]["components"]
            if "component" in c}
    non_atoms = {"Column", "Tabs"}  # layout primitives, not catalogue atoms
    atoms_used = used - non_atoms
    not_stable = atoms_used - STABLE_ATOMS
    assert not not_stable, f"generic-demo.yaml drives non-stable atom(s): {not_stable}"
    assert "faq_accordion" in atoms_used
    assert "flashcard_deck" in atoms_used
    assert "brevet_timeline" in atoms_used


# ── shared fixtures (knowledge-catalogue/tests/fixtures/) ────────────────────────
# These are the parity fixtures: full curriculum.md documents, not narrow
# function-level snippets like the tests above. They exist so a future JS
# port of bom_emitter can be run against the SAME files and deep-compared
# against this Python reference's output — mirroring the existing
# scripts/test_parser_parity.mjs pattern for parse_training_md.py /
# training_parser.gs. Kept separate from the earlier per-bug unit tests
# above (match_glossary_line, extract_section-on-a-bare-dict, etc.) since
# those test internal regex functions with no JS-visible equivalent —
# moving them to files would add no parity value.

def test_quirky_fixture_parses_every_section():
    """Locks in the combined-quirks fixture used for JS/Python parity:
    fenced frontmatter, unquoted-colon scalar, three glossary bullet styles
    plus a table-format glossary, a drill table, method continuation lines,
    a shifted-heading-level timeline mixing pipe and date-only formats, and
    a piège downgrade — all in one real-shaped document."""
    front, groups = bom_emitter.parse_curriculum(FIXTURES_DIR / "quirky-real-world.curriculum.md")
    assert front["id"] == "quirky-real-world-test"
    assert front["source"] == "Wikipedia: Quirky Test Document (fetched 2026-07-14)"
    sections = [s for g in groups for s in g["sections"]]
    assert len(sections) == 8
    kinds = [s["kind"] for s in sections]
    assert kinds == ["concept", "glossary", "glossary", "drill", "method",
                      "timeline", "key_takeaways", "concept"]
    by_title = {s["title"]: s for s in sections}
    glossary_a, _ = bom_emitter.extract_section(by_title["Glossary A"])
    assert [c["front"] for c in glossary_a["cards"]] == ["Alpha", "Beta", "Gamma"]
    glossary_b, _ = bom_emitter.extract_section(by_title["Glossary B"])
    assert [c["front"] for c in glossary_b["cards"]] == ["Delta", "Epsilon"]
    drill, _ = bom_emitter.extract_section(by_title["Quick Drill"])
    assert drill["questions"] == [{"question": "6 × 7", "answer": "42"},
                                   {"question": "9 × 9", "answer": "81"}]
    method, _ = bom_emitter.extract_section(by_title["How It Works"])
    assert len(method["items"]) == 2
    assert "do_thing(1)" in method["items"][0]
    timeline, _ = bom_emitter.extract_section(by_title["Shifted Timeline"])
    assert [e["date"] for e in timeline["events"]] == ["2020", "2021"]
    mistake, pieges = bom_emitter.extract_section(by_title["A Common Mistake"])
    assert pieges == ["People often confuse X with Y — the correction is Z."]


def test_minimal_clean_fixture_parses():
    front, groups = bom_emitter.parse_curriculum(FIXTURES_DIR / "minimal-clean.curriculum.md")
    assert front["id"] == "minimal-clean-test"
    sections = [s for g in groups for s in g["sections"]]
    assert len(sections) == 1
    assert sections[0]["kind"] == "concept"


def test_malformed_fixture_raises_missing_frontmatter():
    with pytest.raises(ValueError, match="missing YAML frontmatter"):
        bom_emitter.parse_curriculum(FIXTURES_DIR / "malformed-missing-frontmatter.curriculum.md")
