"""Design-token layer for the web renderer's report cluster.

Report atoms read var(--a2ui-<token>,<fallback>). The fallback IS the modern
preset's value (2026-09-26: flipped from the historical per-atom hex/px so the
DEFAULT render -- no palette block at all, which is what most agent-authored
payloads send -- looks modern, not just an opt-in). `palette` still lets a
payload override individual tokens or declare `preset` for a future alternate
look; "modern" as an explicit preset is now a no-op (its values equal the
fallback) but stays valid for anything that already set it. Guards: (1) the
cluster really uses tokens, not raw hex/px, (2) the default (no palette block)
render IS the modern look, (3) explicit overrides still win, (4) hostile token
values are dropped, not injected.
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
    """No palette block -> no :root override -> every var() falls through to its own
    fallback. Separate from whether that fallback IS the modern look (next test)."""
    css = w._RENDERERS["palette"]({})
    assert "--a2ui-radius" not in css and "--a2ui-shadow" not in css


# Not every report atom hooks every token -- entity_list and timeline, e.g., were only ever
# wired for text/faint (no card-style border/radius). Checking against MODERN's own values
# means this can't silently drift out of sync with what gen_design_tokens.py actually emits.
import yaml as _yaml
_MODERN = _yaml.safe_load(open("atoms/design-tokens.yaml"))["presets"]["modern"]


@pytest.mark.parametrize("atom", sorted(SAMPLES))
def test_default_render_uses_only_modern_token_values(atom):
    """No palette block at all -- the common case, since most agent-authored payloads never
    author one. Whatever a2ui-* tokens THIS atom hooks, their fallback (= what actually
    renders by default) must be the modern preset's value, not the old historical one."""
    html = w._RENDERERS[atom](SAMPLES[atom])
    found = _find_a2ui_vars(html)
    assert found, f"{atom} default render uses no a2ui-* tokens at all"
    for name, fallback in found:
        if fallback.startswith("var("):   # dark-theme-chained (page's own theme var) -- untouched by design
            continue
        assert fallback == _MODERN[name], f"{atom}: --a2ui-{name} fallback is {fallback!r}, not modern {_MODERN[name]!r}"



def test_modern_preset_and_override():
    css = w._RENDERERS["palette"]({"preset": "modern", "radius": "20px"})
    assert "--a2ui-border:#eaeaea" in css
    assert "--a2ui-radius:20px" in css and "--a2ui-radius:12px" not in css
    assert "--a2ui-shadow:" in css


def test_hostile_token_value_dropped():
    css = w._RENDERERS["palette"]({"radius": "4px;}</style><script>x</script>"})
    assert "<script" not in css and "--a2ui-radius" not in css


def _find_a2ui_vars(html):
    """[(name, fallback), ...] for every var(--a2ui-<name>,<fallback>) in html, matching
    parens by depth so a fallback that itself contains parens (the shadow token's
    rgba(...),rgba(...) value) is captured whole, not truncated at the first ')'."""
    out = []
    for m in re.finditer(r"var\(--a2ui-([a-z-]+),", html):
        name = m.group(1)
        i, depth = m.end(), 1
        while depth and i < len(html):
            depth += (html[i] == "(") - (html[i] == ")")
            i += 1
        out.append((name, html[m.end():i - 1]))
    return out


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
