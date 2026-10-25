"""I136 markup ports (batch b4): the GAS twin and the Python twin read the schema's fields and draw the same markup.

Three groups, each a dict keyed by atom type:
* EQUAL: twins must be byte-identical (ids normalised) for the schema payload, for the old-name payloads and for a fuzz of every leaf;
* SAFE: twins differ by design (client script, logo URL tables, ids) but every field shows in both, and no hostile value crashes or injects;
* OLD: payloads using the field names the old GAS twin read keep their content in both twins.
"""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_motion_atoms import _norm, core_js  # noqa: E402,F401
from test_contract_sweep import _gas_isolated, _py_fresh  # noqa: E402

ATTACK = '"><img src=x onerror=alert(1)><script>alert(2)</script>\'`${x}'

# atoms whose twins are byte-identical after the shared normalisation
EQUAL = [
    {"type": "markdown_block", "content": "Deploy **now** with `kubectl` and [docs](https://example.com/d)", "variant": "compact"},
    {"type": "pdf_preview", "pdf_url": "https://example.com/report.pdf", "thumbnail_url": "https://example.com/a.png", "title": "SOC2 Audit", "alt_text": "Cover page"},
    {"type": "json_tree_viewer", "data": "{\"cluster\": \"prod\", \"n\": [1, 2.5, null], \"s\": \"<b>&\"}"},
    {"type": "framed_screenshot", "image_url": "https://example.com/a.png", "alt_text": "Telemetry", "device_type": "phone", "caption": "Live view"},
    {"type": "footnote_group", "footnotes": [{"id": "fn-1", "text": "First **bold**"}, {"id": 2, "text": "Second"}, "plain"]},
    {"type": "deprecation_notice", "alternative": "Use the v2 endpoint.", "removal_version": "v3.0", "since": "v2.1", "message": "Old **auth** call"},
    {"type": "surface_unlocked", "icon": "\U0001F513", "surface": "Admin Console", "sub": "NEW", "accent": "#f59e0b"},
    {"type": "prerequisite_checklist", "title": "Before you start", "items": ["Docker 24", {"text": "Node 20", "done": True}, {"label": "AWS keys"}]},
    {"type": "split_reveal", "title": "Project Titan", "text": "Ships in **Q3**", "color": "#3b82f6", "delay": 0.5},
    {"type": "further_reading", "title": "Reading", "links": [{"title": "DDIA", "url": "https://example.com/ddia", "annotation": "Distributed systems"}, {"title": "No link"}]},
    {"type": "parallax_card", "title": "Enterprise Cloud", "body": "Edge **compute**", "badge": "Pro", "accent": "#4f46e5", "background": "#0f172a", "depth": 12},
    {"type": "copy_prompt", "prompt": "Summarise the incident.", "label": "Triage prompt", "accent": "#4f46e5"},
    {"type": "stagger_list", "direction": "left", "stagger": 0.15, "items": [{"icon": "\u26a1", "text": "Fast", "sub": "Sub line"}, "plain **md**"]},
    {"type": "follow_cta", "message": "Follow **us**", "platform_links": {"github": "https://example.com/gh", "bluesky": "https://example.com/bs", "bad": "javascript:alert(1)"}},
    {"type": "progress_bar", "value": 72, "label": "Migration", "accent": "#3b82f6", "show_percent": True, "caption": "7.2M of 10M"},
    {"type": "difficulty_badge", "level": "advanced"},
    {"type": "search_result_card", "title": "Redis replicas", "description": "Read replicas guide", "url": "https://example.com/docs/redis"},
    {"type": "icon_stat_row", "cols": 3, "accent": "#0f766e", "stats": [{"icon": "\U0001F680", "value": 99.98, "label": "Uptime", "suffix": "%"}, {"value": 0, "label": "Breaches", "prefix": "~", "sub": "last 90d", "accent": "#b91c1c"}]},
    {"type": "star_rating_display", "rating": 4.8, "max_rating": 5, "review_count": 1312},
    {"type": "learning_objectives", "title": "You will learn", "objectives": ["Provision a VPC", {"text": "Deploy **ECS**", "id": "obj-2"}]},
]
# atoms whose twins differ by design
SAFE = [
    {"type": "gauge_sla", "title": "Uptime", "value": 99.4, "max_value": 100, "unit": "%", "label": "Operational", "threshold": 95},
    {"type": "workspace_logo_grid", "title": "Connectors", "size": 40, "cols": 3, "greyscale": True, "show_labels": True, "apps": ["gmail", "drive", "nonesuch"]},
    {"type": "flip_card", "front_content": "Front **side**", "back_content": "Back side", "trigger_on_hover": True},
    {"type": "annotation_highlight", "text": "Zero-trust needs mutual TLS everywhere.",
     "notes": [{"term": "Zero-trust", "explanation": "No implicit trust.", "color": "#ef4444"}, {"term": "mutual TLS", "explanation": "Both sides prove identity."}]},
]
MUST = {
    "markdown_block": ["<strong>now</strong>", "<code>kubectl</code>", 'href="https://example.com/d"', "margin:0.5rem 0;"],
    "pdf_preview": ["SOC2 Audit", 'href="https://example.com/report.pdf"', 'src="https://example.com/a.png"', 'alt="Cover page"'],
    "json_tree_viewer": ["&quot;cluster&quot;: &quot;prod&quot;", "2.5", "null", "&lt;b&gt;&amp;"],
    "framed_screenshot": ['alt="Telemetry"', "Live view", "border:8px solid #1f2937", 'src="https://example.com/a.png"'],
    "footnote_group": ["[fn-1]", "<strong>bold</strong>", "[2]", "[3]", "Second", "plain"],
    "deprecation_notice": ["Use the v2 endpoint.", "Alternative:", "Removed in: <code>v3.0</code>", "Deprecated since v2.1", "<strong>auth</strong>"],
    "surface_unlocked": ["Admin Console", "NEW", "#f59e0b12", "prefers-reduced-motion"],
    "prerequisite_checklist": ["Before you start", "Docker 24", "line-through", "AWS keys", "\u2705", "\u2b1c"],
    "split_reveal": ["Project Titan", "<strong>Q3</strong>", "#3b82f6", "0.5s", "prefers-reduced-motion"],
    "further_reading": ["Reading", "DDIA", 'href="https://example.com/ddia"', "Distributed systems", "No link"],
    "parallax_card": ["Enterprise Cloud", "<strong>compute</strong>", "Pro", 'data-depth="12"', "d=12", "background:#0f172a"],
    "copy_prompt": ["Triage prompt", "Summarise the incident.", "#4f46e5", "navigator.clipboard"],
    "flip_card": ["<strong>side</strong>", "Back side"],
    "stagger_list": ["Fast", "Sub line", "<strong>md</strong>", "translateX(-22px)", "animation-delay:0.15s", "prefers-reduced-motion"],
    "follow_cta": ["Follow <strong>us</strong>", 'href="https://example.com/gh"', "\U0001F419 github", "\U0001F98B bluesky", "border-radius:100px"],
    "progress_bar": ["Migration", "72%", "#3b82f6", 'aria-valuenow="72"', "7.2M of 10M", "width:72%"],
    "difficulty_badge": ["Advanced", "#f59e0b", 'aria-hidden="true"'],
    "search_result_card": ["Redis replicas", "Read replicas guide", 'href="https://example.com/docs/redis"', "https://example.com/docs/redis"],
    "icon_stat_row": ["Uptime", "99.98", "%", "Breaches", "~", "last 90d", "#0f766e", "#b91c1c", "repeat(2,1fr)", "repeat(2,1fr)"],
    "star_rating_display": ["4.8", "(1,312 reviews)", 'aria-label="Rated 4.8 out of 5 by 1,312 reviews"', "opacity:0.55"],
    "learning_objectives": ["You will learn", "Provision a VPC", "<strong>ECS</strong>", 'data-key="obj-2"'],
    "gauge_sla": ["Uptime", "99.4%", "HEALTHY", "OPERATIONAL"],
    "workspace_logo_grid": ["Connectors", "Gmail", "Drive", "Nonesuch", "grayscale(1)", "repeat(3,1fr)", 'width="40"'],
    "annotation_highlight": ["Zero-trust", "mutual TLS", "#ef4444", "#996206"],
}
OLD = [
    {"type": "pdf_preview", "url": "https://example.com/old.pdf", "title": "Old Doc"},
    {"type": "json_tree_viewer", "json": "{\"a\": 1}"},
    {"type": "framed_screenshot", "url": "https://example.com/o.png", "alt": "Old alt", "frame": "none"},
    {"type": "markdown_block", "text": "old *text*"},
    {"type": "footnote_group", "items": [{"number": 7, "text": "seven"}]},
    {"type": "deprecation_notice", "replacement": "new()", "text": "legacy call", "removal_version": 4},
    {"type": "copy_prompt", "text": "old prompt text"},
    {"type": "further_reading", "items": [{"label": "Old item", "url": "https://example.com/o"}]},
    {"type": "parallax_card", "title": "Old", "subtitle": "old subtitle"},
    {"type": "split_reveal", "title": "T", "content": "old content"},
    {"type": "follow_cta", "text": "old text", "url": "https://example.com/f", "label": "Go", "platform": "github"},
    {"type": "progress_bar", "value": 30, "max": 60, "label": "Old", "color": "#112233"},
    {"type": "star_rating_display", "value": 3, "count": 12, "reviews": 5, "label": "lbl"},
    {"type": "learning_objectives", "items": ["old objective"]},
    {"type": "search_result_card", "title": "T", "url": "https://example.com/u", "breadcrumb": ["a", "b"], "date": "2026"},
    {"type": "stagger_list", "items": [{"label": "L1", "description": "D1"}]},
    {"type": "icon_stat_row", "items": [{"label": "X", "value": "7", "color": "#123456"}]},
]
OLD_WORDS = {"pdf_preview": ["Old Doc", "https://example.com/old.pdf"], "json_tree_viewer": ["&quot;a&quot;: 1"],
             "framed_screenshot": ['alt="Old alt"', "https://example.com/o.png"], "markdown_block": ["<em>text</em>"], "footnote_group": ["[7]", "seven"],
             "deprecation_notice": ["new()", "legacy call", "Removed in: <code>4</code>"], "copy_prompt": ["old prompt text"], "further_reading": ["Old item", "https://example.com/o"],
             "parallax_card": ["old subtitle"], "split_reveal": ["old content"],
             "follow_cta": ["old text", 'href="https://example.com/f"', "Go"], "progress_bar": ["Old", "50%", "#112233"], "star_rating_display": ["3.0", "(12 reviews)", "lbl"],
             "learning_objectives": ["old objective"], "search_result_card": ["a › b", "2026"], "stagger_list": ["L1", "D1"], "icon_stat_row": ["X", "7", "#123456"]}
WEIRD = [None, True, False, 0, -3, 2.5, 1e22, "", "  ", "7", "12ms", "javascript:alert(1)", "\x01javascript:alert(1)", ATTACK, "😀" * 30, [], [1, "a"], {},
         {"label": ATTACK, "name": "n", "term": ATTACK, "id": ATTACK}, "x" * 3000, 99999, [None], [{"term": None, "color": ATTACK}], "__proto__", "constructor"]


def _leaves(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _leaves(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _leaves(v, path + (i,))
    if path:
        yield path


def _fuzz(blocks):
    out = []
    for b in blocks:
        for p in _leaves(b):
            if p[0] == "type":
                continue
            for v in WEIRD:
                c = copy.deepcopy(b)
                o = c
                for k in p[:-1]:
                    o = o[k]
                o[p[-1]] = v
                out.append(c)
    return out


def _norm_uid(h):
    return re.sub(r"(anhl|wg|isr-|sl-|gauge_sla_|cp-(?:wrap|hd|lbl|btn|body)-|su-(?:in-|glow-)?|sr-(?:t|b|top|bot)-|fco|fci|fcf|fcb|fch)[0-9a-f]{6,8}", r"\1UID", _norm(h))


@pytest.fixture(scope="module")
def renders(core_js):
    blocks = EQUAL + SAFE + OLD
    gas = _gas_isolated(core_js, blocks)
    return [(b, _py_fresh(b), g) for b, g in zip(blocks, gas)]


def test_schema_payloads_show_every_documented_field_in_both_twins(renders):
    for b, py, gas in renders[:len(EQUAL) + len(SAFE)]:
        for twin, html in (("py", py), ("gas", gas)):
            for needle in MUST[b["type"]]:
                assert needle in html, "%s %s lacks %r" % (b["type"], twin, needle)
    for b, py, gas in renders[:len(EQUAL)]:
        assert _norm_uid(py) == _norm_uid(gas), b["type"]


def test_old_field_names_still_render_the_same_content_in_both_twins(renders):
    for b, py, gas in renders[len(EQUAL) + len(SAFE):]:
        for twin, html in (("py", py), ("gas", gas)):
            for w in OLD_WORDS[b["type"]]:
                assert w in html, "%s %s lacks %r" % (b["type"], twin, w)
        assert _norm_uid(py) == _norm_uid(gas), b["type"]


def test_hostile_and_odd_values_give_safe_markup_and_equal_twins(core_js):
    blocks = _fuzz(EQUAL + SAFE)
    gas = _gas_isolated(core_js, blocks)
    equal = {b["type"] for b in EQUAL}
    bad = []
    for b, g in zip(blocks, gas):
        py = _py_fresh(b)
        if b["type"] in equal and _norm_uid(py) != _norm_uid(g):
            bad.append(("differs", b))
        for html in (py, g):
            if html.startswith(("PY ERROR", "GAS ERROR")) or "<img src=x" in html or "<script>alert" in html or re.search(r'(src|href)="\s*[\x00-\x20]*javascript:', html, re.I):
                bad.append(("unsafe", b))
    assert not bad, bad[:3]


def test_gauge_shows_the_value_not_the_percentage_and_judges_it_against_the_threshold(core_js):
    blocks = [{"type": "gauge_sla", "value": 3, "max_value": 10, "unit": "ms"},
              {"type": "gauge_sla", "value": 85, "max_value": 100, "threshold": 90},
              {"type": "gauge_sla", "value": 95, "max_value": 100, "threshold": 90}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        for html in (_py_fresh(b), g):
            assert ">3ms<" in html or b["value"] != 3
    assert "WARNING" in gas[1] and "WARNING" in _py_fresh(blocks[1])
    assert "HEALTHY" in gas[2] and "HEALTHY" in _py_fresh(blocks[2])


def test_annotation_terms_are_matched_once_on_the_raw_text(core_js):
    b = {"type": "annotation_highlight", "text": "a <b> & b", "notes": [{"term": "<b>", "explanation": "y"}, {"term": "&", "explanation": "z"}, {"term": "b", "explanation": "x"}]}
    py, g = _py_fresh(b), _gas_isolated(core_js, [b])[0]
    for html in (py, g):
        assert html.count("&lt;b&gt;") >= 1 and "&amp;" in html and "<b>" not in html


def test_flip_card_hover_trigger_reaches_both_twins(core_js):
    b = {"type": "flip_card", "front_content": "F", "back_content": "B", "trigger_on_hover": True}
    assert 'data-hover="1"' in _py_fresh(b)
    assert ":hover #fci" in _gas_isolated(core_js, [b])[0]
    b["trigger_on_hover"] = "yes"
    assert 'data-hover' not in _py_fresh(b) and ":hover #fci" not in _gas_isolated(core_js, [b])[0]


def test_default_logo_grid_shows_all_twenty_apps_in_both_twins(core_js):
    blocks = [{"type": "workspace_logo_grid"},
              {"type": "workspace_logo_grid", "title": "All supported apps", "cols": 5, "size": 40, "greyscale": False},
              {"type": "workspace_logo_grid", "apps": ["gemini_enterprise"]}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks[:2], gas[:2]):
        for html in (_py_fresh(b), g):
            for label in ("Classroom", "Vault", "Groups", "Tasks", "Contacts", "Jamboard", "Admin", "Appsheet", "Currents"):
                assert ">%s<" % label in html
            assert html.count('font-weight:500;text-align:center;">') == 20
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert "Gemini enterprise" in html and "Gemini_enterprise" not in html


def test_gauge_judges_nothing_without_a_threshold_and_names_value_in_aria(core_js):
    b = {"type": "gauge_sla", "title": "Uptime", "value": 99.4, "max_value": 100, "unit": "%", "label": "ok"}
    for html in (_py_fresh(b), _gas_isolated(core_js, [b])[0]):
        assert "HEALTHY" not in html and "BREACHED" not in html and "WARNING" not in html
        assert 'aria-label="Uptime: 99.4%, ok"' in html
    b["threshold"] = 95
    for html in (_py_fresh(b), _gas_isolated(core_js, [b])[0]):
        assert 'aria-label="Uptime: 99.4%, healthy, ok"' in html
    j = {"type": "gauge_sla", "title": ["x"], "value": 1}
    for html in (_py_fresh(j), _gas_isolated(core_js, [j])[0]):
        assert "['x']" not in html and "object Object" not in html


def test_footnote_group_is_an_endnotes_list_and_junk_numbers_fall_back(core_js):
    b = {"type": "footnote_group", "footnotes": [{"id": {}, "text": "a"}, {"id": ["x"], "number": 5, "text": "b"}]}
    for html in (_py_fresh(b), _gas_isolated(core_js, [b])[0]):
        assert 'role="doc-endnotes"' in html and 'aria-label="Footnotes"' in html and "<ol" in html and "<sup" in html
        assert "[1]" in html and "[5]" in html and "object Object" not in html


def test_markdown_block_prefers_content_over_text(core_js):
    b = {"type": "markdown_block", "content": "new", "text": "old"}
    for html in (_py_fresh(b), _gas_isolated(core_js, [b])[0]):
        assert ">new<" in html and "old" not in html


# ---- batch b5/1 ----
EQUAL.extend([
    {"type": "avatar_group", "total_count": 12, "label": "Responders", "avatars": [{"name": "Elena Rostova", "url": "https://example.com/a.png"}, {"name": "Marcus Chen"}, "Priya Patel", {"name": "Sarah", "avatar_url": "https://example.com/s.png"}]},
    {"type": "capability_checklist", "title": "Tiers", "capability_names": ["Zero Downtime", "RBAC"], "items": [{"name": "Standard", "capabilities": [False, True]}, {"name": "Pro", "capabilities": [True]}]},
    {"type": "contributor_list", "title": "Maintainers", "contributors": [{"name": "Alex Rivera", "role": "Lead", "avatar_url": "https://example.com/a.png", "url": "https://example.com/alex", "contributions": 42}, {"name": "Dana White", "color": "#112233"}, "Zoe"]},
    {"type": "document_link", "document_url": "https://example.com/specs.docx", "label": "Technical specification", "icon_type": "docx"},
    {"type": "env_var_list", "variables": [{"key": "NODE_ENV", "description": "Runtime target", "required": True, "default": "production"}, {"name": "MAX", "requirement_status": "optional", "value": 16}, "PLAIN"]},
    {"type": "faq_accordion", "title": "FAQ", "items": [{"question": "What is the SLA?", "answer": "**99.95%** monthly, see [terms](https://example.com/t)"}, {"label": "Old label", "content": "old content"}]},
    {"type": "keyboard_shortcut", "keys": ["Ctrl", "Shift", "P"], "action": "Open Command Palette", "platform": "Windows"},
    {"type": "table_of_contents", "headings": [{"level": 1, "text": "Intro", "anchor": "#intro"}, {"level": 2, "title": "Setup guide", "anchor": "setup guide", "children": [{"text": "Child", "level": 3}]}, "Plain"]},
])
MUST.update({
    "avatar_group": ["Elena Rostova", 'src="https://example.com/a.png"', "MC", "PP", "+8", "Responders"],
    "capability_checklist": ["Tiers", "Zero Downtime", "RBAC", "Standard", "Pro", 'scope="row"'],
    "contributor_list": ["Maintainers", "Alex Rivera", "Lead", 'href="https://example.com/alex"', "42 contributions", "#112233", "Zoe"],
    "document_link": ["Technical specification", 'href="https://example.com/specs.docx"', "[DOCX]", "\U0001F4DD"],
    "env_var_list": ["NODE_ENV", "Runtime target", "production", "required", "optional", "MAX", "16", "PLAIN"],
    "faq_accordion": ["FAQ", "What is the SLA?", "<strong>99.95%</strong>", 'href="https://example.com/t"', "Old label", "old content"],
    "keyboard_shortcut": ["Ctrl", "Shift", "Open Command Palette", "(Windows)"],
    "table_of_contents": ["Table of Contents", "Intro", 'href="#intro"', 'href="#setup-guide"', "Setup guide", "Child", "Plain"],
})


def test_capability_checklist_list_shape_and_matrix_without_capabilities(core_js):
    blocks = [{"type": "capability_checklist", "title": "Readiness", "items": [{"name": "Accordion", "capable": True}, {"name": "Maps", "has": False}, {"label": "Chat", "status": "partial", "tier": "beta"}, "plain"]},
              {"type": "capability_checklist", "capability_names": ["A", "B"], "items": [{"label": "First"}, {"label": "Second"}]}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        py = _py_fresh(b)
        assert _norm_uid(py) == _norm_uid(g)
        assert "<table" not in py and "<ul" in py
    for html in (_py_fresh(blocks[0]), gas[0]):
        for w in ("Readiness", "Accordion", "Maps", "Chat", "beta", "plain", 'aria-label="partial"', 'aria-label="unavailable"'):
            assert w in html
