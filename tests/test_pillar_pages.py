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


# ---- the how-to guide and the Basic Catalog page (14 Nov 2026) ----
LIVE_META = ROOT / "tests/fixtures/a2ui_v1_0_live/catalog_definition_v1_0.json"
ALLOWED_OUT_HOSTS = {"a2ui.org"}   # house rule (owner, 14 Nov): we help readers directly; a2ui.org only for one specific topic


def _live_catalog_validator():
    return conformance._RegexAwareValidator(json.loads(LIVE_META.read_text()), registry=conformance._REGISTRY)


SITE_CHROME_LINKS = {"https://www.linkedin.com/in/curtiskrygier", "https://github.com/a2uicatalog/a2ui"}   # the page template's own author and repo links


def _body_links(page):
    main = re.search(r"<main.*?</main>", page, re.S)
    links = re.findall(r'href="(https?://[^"]+)"', main.group(0) if main else page)
    return [u for u in links if u not in SITE_CHROME_LINKS]


def test_weather_catalog_example_validates_against_the_live_meta_schema():
    f = pillar.facts()
    doc = json.loads(f["JSON_WEATHER_CATALOG"])
    errs = sorted(e.message[:160] for e in _live_catalog_validator().iter_errors(doc))
    assert not errs, errs
    assert doc["$id"] == doc["catalogId"]                       # the guide says the examples use one value for both
    comp = doc["components"]["weather_now"]
    assert comp["type"] == "object" and comp["properties"]["component"] == {"const": "weather_now"}   # flat, names itself
    assert not {"oneOf", "anyOf", "allOf"} & set(comp)          # no structural combinators at the component root
    assert not any(k.startswith("x-") for k in comp)            # our extension keys are not part of the lesson


def test_weather_surface_example_mixes_basic_and_ours_and_conforms():
    f = pillar.facts()
    msg = json.loads(f["JSON_WEATHER_SURFACE"])
    conformance.assert_conforms(msg, conformance.AGENT_TO_RENDERER)
    cs = msg["createSurface"]
    assert cs["catalogId"] == f["BASIC_ID"]                     # Basic is the surface default
    mine = [c for c in cs["components"] if c.get("component") == "weather_now"]
    assert len(mine) == 1 and mine[0]["@catalogId"] == f["CATALOG_ID"]
    assert "metadata" not in cs                                  # our own surface metadata is left out of the lesson


def test_how_to_and_basic_pages_build_clean(tmp_path, monkeypatch):
    monkeypatch.setattr(pillar, "PUBLIC", str(tmp_path))
    for slug in ("what-is-a2ui/custom-catalog/how-to", "what-is-a2ui/basic-catalog"):
        pillar.build(slug)
        page = (tmp_path / slug / "index.html").read_text()
        assert "@@" not in page, slug                            # incl. the breadcrumb data (a parent title with a token used to leak)
        assert '"@type": "FAQPage"' in page, slug
        hosts = {re.sub(r"^https?://([^/]+).*", r"\1", u) for u in _body_links(page)}
        assert hosts <= ALLOWED_OUT_HOSTS, (slug, hosts)         # no third-party links in the guide text
        desc = re.search(r'name="description" content="([^"]*)', page).group(1)
        assert len(desc) <= 170, (slug, len(desc))
    f = pillar.facts()
    basic = (tmp_path / "what-is-a2ui/basic-catalog/index.html").read_text()
    assert f["BASIC_COMPONENT_NAMES"] in basic and f["BASIC_FUNCTION_NAMES"] in basic
    assert f"{f['BASIC_N']} Components and {f['BASIC_FN']} Functions" in basic
    howto = (tmp_path / "what-is-a2ui/custom-catalog/how-to/index.html").read_text()
    assert '"item": "https://a2uicatalog.ai/what-is-a2ui/custom-catalog/"' in howto   # the parent is in the breadcrumb


def test_function_and_component_counts_match_the_vendored_basic_catalog():
    f = pillar.facts()
    basic = json.loads(pillar.BASIC_CATALOG and open(pillar.BASIC_CATALOG, encoding="utf-8").read())
    assert int(f["BASIC_N"]) == len(basic["components"]) and int(f["BASIC_FN"]) == len(basic["functions"])
