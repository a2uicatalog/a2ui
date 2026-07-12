"""gen_mcp_apps_bundle.py concatenates the FULL renderer catalog (verbatim
.gs files + shims) into a browser-portable MCP Apps View bundle. Assert
structure, not just "did it run" — and sweep EVERY mcp-apps-tagged atom
through the real bundle in one Node batch (structure-not-status discipline:
an atom that registers but errors at render time is the failure this suite
exists to catch).
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as gen  # noqa: E402
import generate_atom_pages as gap  # noqa: E402  (reuse example blocks)


@pytest.fixture(scope="module")
def bundle():
    return gen.build_bundle()


@pytest.fixture(scope="module")
def core_js(bundle):
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]]
    assert core, "a2ui-core script block missing"
    return core[0]


@pytest.fixture(scope="module")
def schema_atoms():
    data = yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())
    return {a["type"]: a for a in data["blocks"]}


# Schema-only aliases with no renderer implementation on ANY surface —
# pre-existing catalog debt (gen_renderer_manifest warns about exactly these
# two); exempt from the sweep rather than pretending they render.
SCHEMA_ONLY = {"chat_thread", "form_field"}


def _example_block(atom):
    atom_type = atom.get("type", "")
    block = dict(gap._EXAMPLE_BLOCKS.get(atom_type)
                 or json.loads(gap.example_payload(atom)))
    # Dispatch via `component`: a few atoms (alert_banner, inline_alert, ...)
    # declare a FIELD literally named `type`, which example_payload fills
    # with a variant value that would otherwise clobber the dispatch key.
    # renderAtoms reads block.component || block.type.
    block["component"] = atom_type
    return block


@pytest.fixture(scope="module")
def sweep_results(core_js, schema_atoms):
    """Render every mcp-apps-tagged atom's example block through the bundle
    core in a SINGLE Node invocation; return {type: {len,error,unknown}}."""
    cases = []
    for t, atom in schema_atoms.items():
        works_on = (atom.get("surfaces") or {}).get("works_on") or []
        if "mcp-apps" in works_on or t in gen.CLASS_C:
            cases.append({"type": t, "block": _example_block(atom)})

    with tempfile.TemporaryDirectory() as td:
        cases_path = Path(td) / "cases.json"
        cases_path.write_text(json.dumps(cases))
        driver = Path(td) / "driver.js"
        driver.write_text(
            "global.window = global;\n"
            + core_js
            + f"""
var fs = require('fs');
var cases = JSON.parse(fs.readFileSync({json.dumps(str(cases_path))}, 'utf8'));
var results = {{}};
cases.forEach(function (c) {{
  var html = '';
  try {{ html = renderAtoms([c.block], {{theme: 'light'}}); }}
  catch (e) {{ html = 'THREW: ' + e.message; }}
  results[c.type] = {{
    len: html.length,
    threw: html.indexOf('THREW: ') === 0,
    error: html.indexOf('Error rendering') > -1,
    unknown: html.indexOf('unknown or unsupported atom') > -1,
    degraded: html.indexOf('needs a live backend') > -1,
    fetches: (html.match(/fetch\\((["'])https?:\\/\\/[^"']+\\1/g) || [])
  }};
}});
console.log(JSON.stringify(results));
"""
        )
        proc = subprocess.run(["node", str(driver)], capture_output=True,
                              text=True, timeout=120)
        assert proc.returncode == 0, proc.stderr[-2000:]
        return json.loads(proc.stdout)


# ── the sweep ────────────────────────────────────────────────────────────────

def test_every_tagged_atom_renders(sweep_results):
    bad = {t: r for t, r in sweep_results.items()
           if t not in gen.CLASS_C and t not in SCHEMA_ONLY
           and (r["threw"] or r["error"] or r["unknown"] or r["len"] == 0)}
    assert not bad, (
        f"{len(bad)} mcp-apps-tagged atoms fail to render cleanly: "
        f"{json.dumps(dict(list(bad.items())[:10]), indent=1)}"
    )


def test_sweep_covers_the_catalog(sweep_results):
    # ~494 tagged + 6 class-C; a collapse here means the schema tags or the
    # example-block source broke, not the renderers.
    assert len(sweep_results) >= 480, f"sweep only covered {len(sweep_results)} atoms"


def test_class_c_atoms_render_degraded_card(sweep_results):
    for t in gen.CLASS_C:
        r = sweep_results[t]
        assert r["degraded"] and not r["threw"], f"{t}: expected degraded card, got {r}"


# ── bundle structure ─────────────────────────────────────────────────────────

def test_bundle_contains_view_protocol_handshake(bundle):
    assert "ui/initialize" in bundle
    assert "ui/notifications/initialized" in bundle
    assert "ui/notifications/tool-result" in bundle
    assert "window.parent.postMessage" in bundle


def test_bundle_re_executes_injected_scripts(bundle):
    # innerHTML-injected <script> tags never run — paint() must re-create
    # + re-append them, or every interactive atom's script does nothing.
    assert "createElement('script')" in bundle
    assert "replaceChild(fresh, old)" in bundle


def test_bundle_inlines_atom_styles_css(bundle):
    assert "h2 {" in bundle
    assert ".asw-callout" in bundle
    assert ".asw-degraded-card" in bundle  # class-C override styling
    assert "--accent" in bundle


def test_bundle_excludes_schema_snapshot(bundle):
    assert "_ATOM_SCHEMA_SNAPSHOT" not in bundle


def test_bundle_includes_pack_map_and_partials(bundle):
    assert "ATOM_PACK" in bundle
    assert "==== AtomScripts.html ====" in bundle
    assert "==== A2UIState.html ====" in bundle
    assert "==== A2uiUpdates.html ====" in bundle


def test_rocket_panel_sourced_from_renderer_not_handport(bundle):
    # The v1 hand-port (GDM_ROCKET_PANEL_JS) is gone; the rocket now comes
    # from atoms_canvas.gs via concat — single source of truth. Graduated
    # 2026-07-12: position/layer/loop are field-driven, so assert the field
    # branches rather than a single hardcoded position string.
    assert not hasattr(gen, "GDM_ROCKET_PANEL_JS")
    assert "_RENDERERS['gdm_rocket_panel']" in bundle
    assert "'left:0;' : 'right:0;'" in bundle          # side: both branches
    assert "side + '-half" in bundle                   # overlay still self-declares
    assert "b.layer === 'front' ? 150 : 50" in bundle  # layer: the two z variants
    assert "var LOOP=" in bundle                       # loop: relaunch wiring


def test_fireworks_panel_present(bundle):
    # The current off-catalog resident (iso_fireworks_panel, stage:preview,
    # field-less) — same overlay contract the rocket had before graduating.
    assert "_RENDERERS['iso_fireworks_panel']" in bundle
    assert 'data-a2ui-overlay="right-half"' in bundle
    assert "prefers-reduced-motion" in bundle


def test_layout_is_overlay_aware(bundle):
    # The 50% content constraint applies ONLY when the rendered payload
    # declares a half-viewport overlay atom — every other payload (e.g. the
    # ATC deck) gets the full viewport. Regression for the 2026-07-10
    # "half-screen radar" screenshot. Left-half overlays push content right.
    assert "a2ui-with-overlay" in bundle
    assert "root.classList.toggle('a2ui-with-overlay'" in bundle
    assert "a2ui-overlay-left" in bundle
    assert "#a2ui-root { max-width: 50%" not in bundle  # the old static squeeze


def test_presets_render(core_js):
    """Every hand-picked playground demo renders cleanly through the real
    bundle — a rotted demo fails CI, not on stage. PRESETS[0] doubles as the
    default fixture, so the flagship Launch demo is covered too."""
    cases = [{"type": p["id"], "block": None, "payload": p["payload"]}
             for p in gap.PLAYGROUND_PRESETS]
    with tempfile.TemporaryDirectory() as td:
        cases_path = Path(td) / "presets.json"
        cases_path.write_text(json.dumps(cases))
        driver = Path(td) / "driver.js"
        driver.write_text(
            "global.window = global;\n" + core_js + f"""
var fs = require('fs');
var cases = JSON.parse(fs.readFileSync({json.dumps(str(cases_path))}, 'utf8'));
var results = {{}};
cases.forEach(function (c) {{
  var html = '';
  try {{ html = renderAtoms(c.payload.blocks, {{theme: c.payload.theme}}); }}
  catch (e) {{ html = 'THREW: ' + e.message; }}
  results[c.type] = {{
    len: html.length,
    threw: html.indexOf('THREW: ') === 0,
    error: html.indexOf('Error rendering') > -1,
    unknown: html.indexOf('unknown or unsupported atom') > -1
  }};
}});
console.log(JSON.stringify(results));
""")
        proc = subprocess.run(["node", str(driver)], capture_output=True,
                              text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-1000:]
        results = json.loads(proc.stdout)
    bad = {t: r for t, r in results.items()
           if r["threw"] or r["error"] or r["unknown"] or r["len"] < 200}
    assert not bad, f"preset demos broken: {json.dumps(bad, indent=1)}"


def test_csp_connect_conformance(sweep_results, bundle):
    """A2 (ops runbook §8): CSP posture is catalogue DATA. Three layers:
    declared yaml == compiled registry == bundle const (no drift between the
    three copies); proxy_base sits inside the declared connect domains; and
    every absolute fetch target ANY tagged atom renders resolves to a
    declared connect domain. Upstream hosts may appear only as registry
    declarations, never as fetch targets — the proxy is the only road out."""
    declared = yaml.safe_load((ROOT / "atoms" / "data-sources.yaml").read_text())
    domains = declared["csp"]["connect_domains"]

    compiled = json.loads(
        (ROOT / "public" / "catalogue" / "data-sources-v1.json").read_text())
    assert compiled["csp"]["connect_domains"] == domains
    assert any(compiled["proxy_base"].startswith(d) for d in domains)

    inlined = re.search(r"var A2UI_DATA_SOURCES = (.+?);\n", bundle)
    assert inlined, "registry const missing from bundle"
    const = json.loads(inlined.group(1))
    assert const["csp"]["connect_domains"] == domains
    assert const["proxy_base"] == compiled["proxy_base"]

    def origin_ok(url):
        return any(url.startswith(d + "/") or url == d for d in domains)

    # behavioral layer: fetch targets in every tagged atom's rendered output
    bad = {t: r["fetches"] for t, r in sweep_results.items()
           if any(not origin_ok(f.split("(", 1)[1][1:-1]) for f in r["fetches"])}
    assert not bad, f"undeclared fetch origins rendered: {json.dumps(bad, indent=1)}"

    # static layer: no absolute-URL fetch literal in the bundle text either
    for quote, url in re.findall(r"""fetch\((["'])(https?://[^"']+)\1""", bundle):
        assert origin_ok(url), f"undeclared fetch literal in bundle: {url}"


def test_gallery_page_reconciles_with_catalog():
    """A3 (ops runbook §8): the gallery is generated, so a generator
    regression ships silently unless the output is reconciled against the
    catalog: every stable mcp-apps-tagged atom gets exactly one render
    button, every button has an entry in the examples map, and the map
    parses. 1:1:1 — no orphans in either direction."""
    html = (ROOT / "public" / "surfaces" / "mcp-apps" / "index.html").read_text()
    buttons = re.findall(r'data-atom="([^"]+)"', html)
    assert len(buttons) == len(set(buttons)), "duplicate render buttons"

    m = re.search(r"A2UI_GALLERY_EXAMPLES = (.+?);\n", html)
    assert m, "examples map missing from gallery page"
    examples = json.loads(m.group(1))

    schema = yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())
    tagged = {a["type"] for a in schema["blocks"]
              if "mcp-apps" in ((a.get("surfaces") or {}).get("works_on") or [])
              and a.get("stage", "stable") == "stable"}

    assert set(buttons) == tagged, (
        f"buttons≠catalog: extra={sorted(set(buttons)-tagged)[:5]} "
        f"missing={sorted(tagged-set(buttons))[:5]}")
    assert set(examples) == set(buttons), "examples map ≠ buttons"


def test_graduation_flyby_on_surface_page():
    """The rocket flyby is outer-page chrome (the atom's renderer is jailed
    inside the iframe) — assert it ships on the mcp-apps surface page, honors
    reduced motion, and self-removes so it can't linger as a perf cost."""
    html = (ROOT / "public" / "surfaces" / "mcp-apps" / "index.html").read_text()
    assert "Graduation flyby" in html
    assert "prefers-reduced-motion" in html
    assert "cv.remove()" in html


def test_fullscreen_deck_breaks_out_of_host_chrome(core_js):
    """height:'fullscreen' must actually take: the deck emits the host-chrome
    breakout (bundle body padding, asw-page 860px max-width) — the 100vh div
    alone still rendered inset 24px (the 'not full screen still' incident,
    2026-07-10). A sized deck must NOT strip the host's chrome."""
    breakout = ".asw-page{max-width:none!important"
    full = _run_blocks(core_js, [{"type": "airspace_command_deck",
                                  "height": "fullscreen"}])
    assert breakout in full and "height:100vh" in full
    sized = _run_blocks(core_js, [{"type": "airspace_command_deck"}])
    assert breakout not in sized


def test_declared_data_sources_inlined(bundle, core_js):
    """Network access is DECLARED (atoms/data-sources.yaml), never hand-wired:
    the registry must be inlined, the feed transports must read it, and the
    proxy base must match the declaration."""
    assert "var A2UI_DATA_SOURCES = " in core_js
    assert '"data:adsb:read"' in core_js       # access scope travels with the registry
    assert "declared-data-source feed transports" in core_js
    # graduated feeds must NOT be class-C degraded cards anymore
    assert "adsb_feed" not in gen.CLASS_C and "metar_feed" not in gen.CLASS_C


def test_feed_transports_render_declared_proxy_urls(core_js):
    out = _run_blocks(core_js, [
        {"type": "adsb_feed", "name": "adsb1", "refresh": 15},
        {"type": "metar_feed", "name": "wx1", "station": "LFBO"},
    ])
    assert "https://a2uicatalog.ai/api/data/adsb?lat=" in out
    assert "https://a2uicatalog.ai/api/data/metar?station=LFBO" in out
    assert "Error rendering" not in out
    # polling clamped to the DECLARED floor (min_client_refresh_s), so client
    # refresh can never outrun the edge cache into the CF pipe
    assert "setInterval(pull,15000)" in out


def _run_blocks(core_js, blocks):
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "d.js"
        driver.write_text("global.window = global;\n" + core_js +
                          f"\nconsole.log(renderAtoms({json.dumps(blocks)}, {{theme:'dark'}}));")
        proc = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-500:]
        return proc.stdout


def test_no_script_block_self_terminates(bundle):
    # A raw `</script` inside a JS string is fine for Node's parser but ends
    # the WHOLE <script> element for the browser's HTML parser, dumping the
    # rest of the bundle into the DOM as text (the 'Video placeholder'
    # incident, 2026-07-10). node --check cannot catch this; only an
    # HTML-level check can.
    body = bundle[bundle.index("<body"):]
    blocks = re.findall(r"<script>(.*?)</script>", body, re.S)
    assert len(blocks) == 3, f"expected 3 script blocks, found {len(blocks)}"
    for i, block in enumerate(blocks):
        assert "</script" not in block, f"script block {i} contains a raw </script"
        # and the escape actually survived into the output
    assert r"<\/script" in bundle


def test_bundle_size_guard(bundle):
    # Catches accidental inclusion of Code.gs / schema snapshots / vendored
    # blobs. Raw concat is ~1.2 MB today.
    assert len(bundle) < 2_000_000, f"bundle ballooned to {len(bundle)} bytes"
    assert len(bundle) > 800_000, "bundle suspiciously small — files missing?"


def test_view_reports_size_changed(bundle):
    """The rendered-but-invisible incident (claude.ai, 2026-07-11): flexible-
    height hosts size the iframe FROM ui/notifications/size-changed — a view
    that never sends it mounts at zero height. The handshake must send it
    after every paint and on resize."""
    handshake = bundle[bundle.rindex("MCP Apps View protocol handshake"):]
    assert "ui/notifications/size-changed" in handshake
    assert "reportSize()" in handshake and "ResizeObserver" in handshake
    # sent after paint, not only on observer (first paint must always report):
    # the tool-result handler itself must pair paint(...) with reportSize()
    handler = handshake[handshake.index("ui/notifications/tool-result'"):][:400]
    assert "paint(result.structuredContent" in handler and "reportSize();" in handler
