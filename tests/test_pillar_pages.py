"""Guide ("pillar") pages: counts and code come from data, and the custom-catalog example is real.

Written 2026-11-13 with /what-is-a2ui/custom-catalog/ (owner: "make the numbers mechanical going
forward"). The page prints our catalogue document, one component definition and a surface that mixes
the Basic Catalog with ours; all three are read at build time, and the mixed surface is checked here
against the official v1.0 schema, against our own stat_card definition, and through a real render.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT))
import gen_pillar_pages as pillar  # noqa: E402
import a2ui_v1_conformance as conformance  # noqa: E402

TYPED_COUNT = re.compile(r"\b\d{3} (?:published |typed )?(?:UI )?(?:components|atoms)\b")
SPEC_JSON = ROOT / "tests/fixtures/a2ui_v1_0_spec/json"


def _catalog_validator(catalog, component):
    """Validate one component against our published catalogue. Its $refs are relative
    (common_types.json, catalog.json), as in the official Basic Catalog, so a host maps them;
    this does the same with the vendored spec's common_types.json."""
    common = json.loads((SPEC_JSON / "common_types.json").read_text())
    base = catalog["$id"].rsplit("/", 1)[0]
    reg = Registry().with_resources([
        (catalog["$id"], Resource.from_contents(catalog)),
        (f"{base}/catalog.json", Resource.from_contents(catalog)),
        (f"{base}/common_types.json", Resource.from_contents(common)),
        (common["$id"], Resource.from_contents(common)),
    ])
    return Draft202012Validator({"$ref": f"{catalog['$id']}#/components/{component}"}, registry=reg)


def test_mixed_example_is_valid_against_both_catalogs_and_renders():
    msg = pillar.mixed_example()
    surface = msg["createSurface"]
    # envelope + the Basic Catalog components, strictly; extension components are checked below
    conformance.assert_conforms(msg, conformance.AGENT_TO_RENDERER)
    assert surface["catalogId"] == json.loads(Path(pillar.BASIC_CATALOG).read_text())["catalogId"]
    catalog = json.loads(Path(pillar.CATALOG).read_text())
    ours = [c for c in surface["components"] if c.get("@catalogId") == catalog["catalogId"]]
    assert [c["component"] for c in ours] == ["stat_card"]
    v = _catalog_validator(catalog, "stat_card")
    assert not [e.message for e in v.iter_errors(ours[0])]
    assert list(v.iter_errors(dict(ours[0], is_up="yes"))), "the catalogue check must reject a wrong type"

    import gen_mcp_apps_bundle as gen
    core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", gen.build_bundle(), re.S) if "a2ui-core" in b[:300]][0]
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core +
                     f"\nvar out = _rehydrateV1Surface({json.dumps(surface)});"
                     "\nconsole.log(JSON.stringify(renderAtoms(out.blocks, {})));")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr[-1500:]
    html = json.loads(p.stdout.strip().split("\n")[-1])
    for want in ("Weekly sales", "1,234", "Orders this week", "+12%"):
        assert want in html, want


def test_custom_catalog_page_numbers_and_code_come_from_data(tmp_path, monkeypatch):
    monkeypatch.setattr(pillar, "PUBLIC", str(tmp_path))
    pillar.build("what-is-a2ui/custom-catalog")
    page = (tmp_path / "what-is-a2ui/custom-catalog/index.html").read_text()
    f = pillar.facts()
    assert "@@" not in page
    assert f"Worked Example with {f['ATOMS']} Components" in page
    assert "<th>Renderer</th>" in page  # the renderer table became a real table
    assert f"<td>{f['DRAWN_REACT']} of {f['ATOMS']}</td>" in page
    assert "&quot;@catalogId&quot;: &quot;" + f["CATALOG_ID"] in page  # the mixed example, as emitted
    assert '"item": "https://a2uicatalog.ai/what-is-a2ui/"' in page        # parent in the breadcrumb
    claimed = {m.split()[0] for m in TYPED_COUNT.findall(re.sub(r"<[^>]+>", " ", page))}
    assert claimed <= {f["ATOMS"]}, claimed


def test_no_typed_in_counts_in_guide_content():
    """Counts in content/*.md are @@ATOMS@@-style tokens; dated measurements (bytes, tokens) are fine."""
    bad = []
    for md in sorted((ROOT / "content").rglob("*.md")):
        for n, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            for m in TYPED_COUNT.finditer(line):
                bad.append(f"{md.relative_to(ROOT)}:{n}: {m.group(0)}")
    assert not bad, "typed-in counts (use a token from gen_pillar_pages.facts()):\n" + "\n".join(bad)


def test_unknown_token_fails_the_build():
    try:
        pillar._fill("@@NO_SUCH_FACT@@", "x")
    except SystemExit as e:
        assert "NO_SUCH_FACT" in str(e)
    else:
        raise AssertionError("an unknown token must fail the build")


def test_guide_pages_are_built_on_deploy():
    wf = (ROOT / ".github/workflows/deploy.yml").read_text()
    assert "python3 scripts/gen_pillar_pages.py" in wf
    assert wf.index("scripts/gen_public_catalog.py") < wf.index("scripts/gen_pillar_pages.py")
