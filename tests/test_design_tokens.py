"""Design-token layer for the web renderer's report cluster.

Report atoms read var(--a2ui-<token>,<historical value>); `palette` sets the
tokens. Guards: (1) the cluster really uses tokens (no raw card border/radius
creeping back), (2) a palette that sets nothing changes nothing, (3) preset and
explicit fields work, (4) hostile token values are dropped, not injected.
"""
import re
import pytest
import renderers.web_article as w

SAMPLES = {
    "metric_delta": {"label": "Rev", "current_value": "1", "delta_value": "2%", "delta_type": "increase"},
    "status_dashboard": {"title": "S", "items": [{"name": "API", "status": "operational"}]},
    "uptime_timeline": {"uptime": 99.7, "days": 5},
    "table": {"headers": ["a"], "rows": [["1"]]},
    "timeline": {"events": [{"date": "1", "title": "T"}]},
    "badge": {"text": "x"},
    "entity_list": {"items": [{"name": "P", "status": "active"}]},
}


@pytest.mark.parametrize("atom", sorted(SAMPLES))
def test_report_cluster_uses_tokens(atom):
    html = w._RENDERERS[atom](SAMPLES[atom])
    assert "var(--a2ui-" in html
    assert "border:1px solid #e5e7eb" not in html
    assert not re.search(r"border-radius:(?:10|8)px", html)


def test_default_palette_sets_no_tokens():
    css = w._RENDERERS["palette"]({})
    assert "--a2ui-radius" not in css and "--a2ui-shadow" not in css


def test_modern_preset_and_override():
    css = w._RENDERERS["palette"]({"preset": "modern", "radius": "20px"})
    assert "--a2ui-border:#eaeaea" in css
    assert "--a2ui-radius:20px" in css and "--a2ui-radius:12px" not in css
    assert "--a2ui-shadow:" in css


def test_hostile_token_value_dropped():
    css = w._RENDERERS["palette"]({"radius": "4px;}</style><script>x</script>"})
    assert "<script" not in css and "--a2ui-radius" not in css


# ── cross-surface parity (GAS / MCP Apps <-> Python) ─────────────────────────
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

_CASES = [
    {},
    {"preset": "modern"},
    {"preset": "modern", "radius": "20px", "shadow": "none"},
    {"radius": "4px;}</style><script>x</script>"},          # hostile: dropped
    {"preset": "nope", "border_color": "#abc"},               # unknown preset
    {"preset": "__proto__"},                                  # prototype-key probe
    {"preset": "constructor", "radius": 12},                  # non-string dropped
    {"radius": True, "muted_color": "rgba(0,0,0,.5)"},
    {"surface_color": "x" * 121},                             # over length cap
    {"text_color": "#111", "faint_color": "#999", "border_soft_color": "#eee"},
]


def test_generated_token_outputs_are_current():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_design_tokens.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_token_css_matches_between_python_and_gas():
    gs = (ROOT / "apps-script-surface" / "gas-wired-renderer" / "atoms_tokens.gs").read_text()
    with tempfile.TemporaryDirectory() as td:
        drv = Path(td) / "d.js"
        drv.write_text(gs + "\nconsole.log(JSON.stringify("
                       + json.dumps(_CASES) + ".map(_tokenCss)));")
        p = subprocess.run(["node", str(drv)], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr[-1500:]
    js = json.loads(p.stdout)
    py = [w._token_css(c) for c in _CASES]
    assert js == py, [(c, a, b) for c, a, b in zip(_CASES, js, py) if a != b]


def _gas_render(blocks):
    import gen_mcp_apps_bundle as gen
    bundle = gen.build_bundle()
    core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
            if "a2ui-core" in b[:300]][0]
    with tempfile.TemporaryDirectory() as td:
        drv = Path(td) / "d.js"
        drv.write_text("global.window = global;\n" + core
                       + "\nconsole.log(JSON.stringify(" + json.dumps(blocks)
                       + ".map(function(b){return renderAtoms([b],{theme:'light'});})));")
        p = subprocess.run(["node", str(drv)], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr[-1500:]
    return json.loads(p.stdout), bundle


def test_gas_palette_sets_tokens_and_cluster_reads_them():
    blocks = [{"component": "palette", "preset": "modern", "accent": "#0070f3"}]
    blocks += [{"component": t, **SAMPLES_GAS[t]} for t in ("metric_delta", "badge", "timeline")]
    out, bundle = _gas_render(blocks)
    assert "--a2ui-border:#eaeaea" in out[0] and "--a2ui-radius:12px" in out[0]
    for html in out[1:]:
        assert "var(--a2ui-" in html
    # class-styled atoms carry the tokens in the bundled stylesheet
    for sel in (".a2ui-status-dashboard {", ".a2ui-entity-card {"):
        rule = bundle[bundle.index(sel):][:400]
        assert "var(--a2ui-border," in rule and "var(--a2ui-radius," in rule


SAMPLES_GAS = {
    "metric_delta": {"label": "Rev", "current_value": "1", "delta_value": "2%", "delta_type": "increase"},
    "badge": {"text": "new"},
    "timeline": {"events": [{"date": "1", "label": "T", "text": "x"}]},
}
