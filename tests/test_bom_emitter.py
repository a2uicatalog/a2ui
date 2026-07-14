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

BOM = ROOT / "knowledge-catalogue" / "schemas" / "national-education" / "fr" / "dnb-2026.yaml"
MATHS = ROOT / "knowledge-catalogue" / "brevet-2026-maths.curriculum.md"


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
