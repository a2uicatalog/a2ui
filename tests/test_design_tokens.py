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
