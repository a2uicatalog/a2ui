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
    return re.sub(r"(anhl|wg|isr-|sl-|cu-|gl-|pt_|nf-|sb-|tw-|ros-|gb-|sp-|rh-btn-|rh-count-|srs-|tb-cur-|tb-bl-|tb-|vs-|variant-|ck_|asp_|gauge_sla_|cp-(?:wrap|hd|lbl|btn|body)-|su-(?:in-|glow-)?|sr-(?:t|b|top|bot)-|fco|fci|fcf|fcb|fch|cbg-|choice_|pr-|tbmc_|tbmb_|tbm_|tbf_|tbct_|tok_|ti_|mqs_|mq_|nf_|punch-|donut-)[0-9a-f]{6,8}", r"\1UID", _norm(h))


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
    {"type": "table_of_contents", "title": "Guide", "headings": [{"level": 1, "text": "Intro", "anchor": "#intro"}, {"level": 2, "title": "Setup guide", "anchor": "setup guide", "children": [{"text": "Child", "level": 3}]}, "Plain"]},
])
MUST.update({
    "avatar_group": ["Elena Rostova", 'src="https://example.com/a.png"', "MC", "PP", "+8", "Responders"],
    "capability_checklist": ["Tiers", "Zero Downtime", "RBAC", "Standard", "Pro", 'scope="row"'],
    "contributor_list": ["Maintainers", "Alex Rivera", "Lead", 'href="https://example.com/alex"', "42 contributions", "#112233", "Zoe"],
    "document_link": ["Technical specification", 'href="https://example.com/specs.docx"', "[DOCX]", "\U0001F4DD"],
    "env_var_list": ["NODE_ENV", "Runtime target", "production", "required", "optional", "MAX", "16", "PLAIN", ">Value<"],
    "faq_accordion": ["FAQ", "What is the SLA?", "<strong>99.95%</strong>", 'href="https://example.com/t"', "Old label", "old content"],
    "keyboard_shortcut": ["Ctrl", "Shift", "Open Command Palette", "(Windows)"],
    "table_of_contents": ["Guide", "Intro", 'href="#intro"', 'href="#setup-guide"', "Setup guide", "Child", "Plain"],
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
        for w in ("Readiness", "Accordion", "Maps", "Chat", "beta", "plain", '>partial<', '>unavailable<'):
            assert w in html


# ---- batch b5/2 ----
EQUAL.extend([
    {"type": "chip_group", "label": "Filter", "layout": "scroll", "same_tab": True, "chips": [{"label": "All", "active": True}, {"label": "Auth", "url": "https://example.com/auth", "color": "#6366f1"}, {"label": "Billing", "color": "#abc"}, "plain"]},
    {"type": "tab_bar", "tabs": [{"label": "Overview", "url": "https://example.com/o", "is_active": True, "icon": "home"}, {"label": "Incidents", "url": "https://example.com/i", "icon": "alert"}, {"text": "No link"}, "Str"]},
    {"type": "timeline", "title": "Launch", "accent": "#6366f1", "events": [{"date": "2026-07-01", "label": "Freeze", "text": "Core **API** stable", "tag": "Release"}, {"time": "Jul", "title": "Audit", "description": "Pen test"}, {"date": 2026, "label": "Beta", "body": "old body"}, "Plain"]},
    {"type": "resources_list", "title": "Downloads", "items": [{"title": "Helm Chart", "size": "42 KB", "type": "tar.gz", "url": "https://example.com/helm"}, {"label": "No url", "type": "pdf", "icon": "\U0001F4C4"}, "Str"]},
    {"type": "video_card", "video_url": "https://example.com/v.mp4", "thumbnail_url": "https://example.com/a.png", "title": "Scaling", "description": "Failover patterns.", "alt_text": "Speaker slide", "duration": "8:45"},
    {"type": "social_proof_banner", "metric_value": "500M+", "metric_label": "events daily", "icon_url": "https://example.com/a.png", "link_url": "https://example.com/m", "testimonial": "Great", "logos": [{"name": "Acme", "url": "https://example.com/l.png"}, {"name": "Beta"}]},
    {"type": "media_mention_card", "publication_name": "TechDispatch", "publication_logo_url": "https://example.com/a.png", "headline": "How NextGen Streamlines", "article_url": "https://example.com/p", "date": "2024-05-18", "excerpt": "Short"},
    {"type": "source_citation", "heading": "Sources", "sources": [{"number": 1, "title": "Paper", "url": "https://example.com/p", "excerpt": "quote", "author": "Ann", "date": "2024", "publisher": "ACM", "note": "see s3"}, {"title": "No number", "author": ["A", "B"]}, "Str"]},
])
MUST.update({
    "chip_group": ["Filter", "All", "Auth", 'href="https://example.com/auth"', 'target="_top"', "Billing", "plain", "overflow-x:auto", "#6366f118"],
    "tab_bar": ["Overview", 'href="https://example.com/o"', 'aria-current="page"', "Incidents", "No link", "Str", 'data-icon="home"'],
    "timeline": ["Launch", "2026-07-01", "Freeze", "<strong>API</strong>", "Release", "Pen test", "Audit", "old body", "Plain", "<ol"],
    "resources_list": ["Downloads", "Helm Chart", "42 KB", "TAR.GZ", 'href="https://example.com/helm"', "No url", "PDF", "Str"],
    "video_card": ["Scaling", "Failover patterns.", 'alt="Speaker slide"', 'src="https://example.com/a.png"', 'href="https://example.com/v.mp4"'],
    "social_proof_banner": ["500M+", "events daily", 'src="https://example.com/a.png"', 'href="https://example.com/m"', "Great", "Acme", "Beta"],
    "media_mention_card": ["TechDispatch", 'src="https://example.com/a.png"', "How NextGen Streamlines", 'href="https://example.com/p"', "2024-05-18", "Short"],
    "source_citation": ["Sources", "[1]", "Paper", 'href="https://example.com/p"', "quote", "Ann", "2024", "ACM", "see s3", "No number", "[2]", "A, B", "Str", "[3]"],
})
OLD.extend([
    {"type": "chip_group", "chips": [{"text": "Old chip"}]},
    {"type": "tab_bar", "tabs": [{"text": "Old tab", "url": "#", "active": True}, {"name": "Second"}], "active_tab": 1},
    {"type": "timeline", "events": [{"date": "2024", "title": "A2UI v1", "body": "First atoms defined."}]},
    {"type": "resources_list", "items": [{"label": "Old res", "url": "https://example.com/r", "size": "1 MB"}]},
    {"type": "video_card", "url": "https://example.com/old.mp4", "thumbnail": "https://example.com/t.png", "title": "Old video"},
    {"type": "social_proof_banner", "text": "Old banner text", "count": 1500},
    {"type": "media_mention_card", "source": "Wired", "quote": "Old quote", "url": "https://example.com/q"},
    {"type": "source_citation", "title": "Single", "url": "https://example.com/s", "authors": ["X", "Y"], "year": 2020, "publisher": "Pub", "note": "n1"},
])
OLD_WORDS.update({
    "chip_group": ["Old chip"], "tab_bar": ["Old tab", "Second"], "timeline": ["A2UI v1", "First atoms defined."], "resources_list": ["Old res", "1 MB", 'href="https://example.com/r"'],
    "video_card": ["Old video", 'href="https://example.com/old.mp4"', 'src="https://example.com/t.png"'], "social_proof_banner": ["Old banner text", "1500"],
    "media_mention_card": ["Wired", "Old quote", 'href="https://example.com/q"'], "source_citation": ["Single", 'href="https://example.com/s"', "X, Y", "2020", "Pub", "n1"],
})


# ---- batch b5/3 ----
EQUAL.extend([
    {"type": "github_repo_card", "repo": "acme/stream-engine", "label": "Stream Engine", "description": "Telemetry daemon.", "stars": 0, "forks": 12, "language": "Python", "visibility": "public", "topics": ["iot", "mqtt"], "license": "MIT"},
    {"type": "product_thumbnail", "title": "Smart Hub", "vendor": "Nordic IoT", "sku": "GW-901", "price": "$129.00", "compare_at_price": "$149.00", "status": "draft", "image_url": "https://example.com/a.png", "badge": "NEW", "url": "https://example.com/p", "tags": ["Hardware", "Zigbee", 7]},
    {"type": "confidence_bar", "label": "Intent", "value": 94.2, "color": "#22c55e", "items": [{"label": "Upgrade", "value": 94}, {"label": "Support", "value": "6"}, {"name": "Churn", "value": 45}]},
    {"type": "split_stat", "value": "99.99", "prefix": "~", "suffix": "%", "heading": "Service Uptime", "body": "SLA held **all** year.", "colour": "#10b981", "flip": True},
    {"type": "count_up_stat", "value": 14200, "label": "Active Deployments", "prefix": "$", "suffix": "+", "colour": "#22d3ee", "duration": 1800, "size": "4rem"},
    {"type": "leaderboard_card", "title": "Top", "limit": 3, "items": [{"name": "Aria", "score": 985}, {"name": "Kai", "score": 940, "unit": "pts"}, {"email": "n@x.org", "score": "n/a"}, {"name": "Cut", "score": 1}]},
    {"type": "next_step_strip", "accent": "#0284c7", "steps": [{"number": 1, "label": "Provision VPC", "detail": "Create subnets", "url": "https://example.com/n"}, {"label": "Certs", "action": "Rotate TLS"}, "Plain step"]},
    {"type": "take_away_card", "headline": "Premature abstraction is debt.", "sub": "Handbook **2026**", "accent": "#ec4899", "size": "1.5rem", "gradient": ["#1e1b4b", "#312e81"], "text_color": "#fff"},
])
MUST.update({
    "github_repo_card": ["acme/stream-engine", 'href="https://github.com/acme/stream-engine"', "Stream Engine", "Telemetry daemon.", "⭐ 0", "\U0001F374 12", "Python", "public", "iot", "MIT"],
    "product_thumbnail": ["Smart Hub", "Nordic IoT", "GW-901", "$129.00", "$149.00", "draft", "NEW", 'src="https://example.com/a.png"', 'href="https://example.com/p"', "Hardware", "Zigbee", ">7<"],
    "confidence_bar": ["Intent", "94%", "Upgrade", "Support", "6%", "Churn", "45%", 'aria-valuenow="94"', "#22c55e"],
    "split_stat": ["~", "99.99", "%", "Service Uptime", "<strong>all</strong>", "#10b981"],
    "count_up_stat": ["14200", "Active Deployments", "$", "+", "#22d3ee", "font-size:4rem", "1800", "requestAnimationFrame"],
    "leaderboard_card": ["Top", "Aria", "985", "Kai", "940pts", "n@x.org", "n/a", "\U0001F947", "<ol"],
    "next_step_strip": ["Provision VPC", "Create subnets", 'href="https://example.com/n"', "Certs", "Rotate TLS", "Plain step", "#0284c7"],
    "take_away_card": ["Premature abstraction is debt.", "Handbook <strong>2026</strong>", "linear-gradient(135deg,#1e1b4b,#312e81)"],
})
OLD.extend([
    {"type": "github_repo_card", "owner": "acme", "repo": "engine", "stars": 5},
    {"type": "product_thumbnail", "name": "Old name", "thumbnail": "https://example.com/t.png", "price": 9, "badge": "SALE"},
    {"type": "confidence_bar", "label": "Old bar", "value": "50"},
    {"type": "split_stat", "value": 7, "color": "#123456", "heading": "Old split"},
    {"type": "count_up_stat", "value": "5", "color": "#654321", "label": "Old count"},
    {"type": "leaderboard_card", "rows": [{"name": "Old row", "score": 3}]},
    {"type": "next_step_strip", "steps": [{"title": "Old title step", "label": "Old label", "detail": "d"}]},
    {"type": "take_away_card", "text": "Old text", "source": "Old source"},
])
OLD_WORDS.update({
    "github_repo_card": ["acme/engine", "⭐ 5"], "product_thumbnail": ["Old name", 'src="https://example.com/t.png"', "9", "SALE"], "confidence_bar": ["Old bar", "50%"],
    "split_stat": ["7", "Old split", "#123456"], "count_up_stat": ["Old count", "#654321"], "leaderboard_card": ["Old row", "3"], "next_step_strip": ["Old label", "d"],
    "take_away_card": ["Old text", "Old source"],
})


def test_take_away_card_aliases_and_a_malformed_gradient(core_js):
    blocks = [{"type": "take_away_card", "quote": "Alias quote", "author": "Alias author", "accent": "#4f46e5"},
              {"type": "take_away_card", "headline": "H", "gradient": "linear-gradient(red,blue)"},
              {"type": "take_away_card", "headline": "H", "gradient": ["#111"]}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        py = _py_fresh(b)
        assert _norm_uid(py) == _norm_uid(g)
        assert "object Object" not in py and "['" not in py
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert "Alias quote" in html and "Alias author" in html
    for html in (_py_fresh(blocks[1]), gas[1], _py_fresh(blocks[2]), gas[2]):
        assert "linear-gradient(135deg,color-mix" in html


def test_confidence_bar_reads_fractions_and_percentages(core_js):
    cases = [(0.87, "87%"), (1, "100%"), (87, "87%"), (0, "0%"), (0.004, "0%")]
    blocks = [{"type": "confidence_bar", "label": "L", "value": v} for v, _ in cases]
    blocks.append({"type": "confidence_bar", "label": "L", "value": 0.5, "isPercent": True})
    blocks.append({"type": "confidence_bar", "items": [{"label": "A", "value": 0.25}, {"label": "B", "value": 25}]})
    gas = _gas_isolated(core_js, blocks)
    for (v, want), b, g in zip(cases, blocks, gas):
        for html in (_py_fresh(b), g):
            assert ('aria-valuenow="%s"' % want[:-1]) in html and ">%s<" % want in html, (v, want)
    for html in (_py_fresh(blocks[5]), gas[5]):
        assert 'aria-valuenow="1"' in html and ">1%<" in html or 'aria-valuenow="1"' in html
    for html in (_py_fresh(blocks[6]), gas[6]):
        assert html.count('aria-valuenow="25"') == 2
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)


def test_env_var_list_value_column_only_when_a_row_has_a_value_and_no_invented_optional(core_js):
    a = {"type": "env_var_list", "vars": [{"name": "FIREBASE_PROJECT", "value": "proj-1", "description": "d"}, {"name": "K", "value": "•••", "default": "dflt"}]}
    b = {"type": "env_var_list", "variables": [{"key": "A", "default": "x", "required": True}, {"key": "B", "requirement_status": "optional"}, {"key": "C"}]}
    gas = _gas_isolated(core_js, [a, b])
    for blk, g in zip((a, b), gas):
        assert _norm_uid(_py_fresh(blk)) == _norm_uid(g)
    for html in (_py_fresh(a), gas[0]):
        assert ">Value</th>" in html and "proj-1" in html and "dflt" in html and "optional" not in html
    for html in (_py_fresh(b), gas[1]):
        assert ">Value</th>" not in html and html.count("optional") == 1 and html.count(">required<") == 1


def test_leaderboard_has_an_empty_state_and_no_invented_rows_or_units(core_js):
    blocks = [{"type": "leaderboard_card"}, {"type": "leaderboard_card", "items": []}, {"type": "leaderboard_card", "items": [{"name": "A", "score": 5}]}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0], _py_fresh(blocks[1]), gas[1]):
        assert "No scores yet" in html and "alice" not in html and "<ol" not in html
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert ">5<" in html and "%" not in html.replace("width:", "").replace("%;", "")


def test_status_marks_use_hidden_text_not_aria_label_on_spans_and_tab_nav_labels(core_js):
    blocks = [{"type": "capability_checklist", "capability_names": ["A"], "items": [{"name": "X", "capabilities": [True]}, {"name": "Y", "capabilities": [False]}]},
              {"type": "capability_checklist", "items": [{"name": "X", "status": "partial"}]},
              {"type": "tab_bar", "title": "Sections", "tabs": [{"label": "One", "url": "https://example.com/1", "is_active": True}, {"label": "Two"}]},
              {"type": "tab_bar", "tabs": ["Only"]}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        py = _py_fresh(b)
        assert _norm_uid(py) == _norm_uid(g)
        for html in (py, g):
            assert "<span aria-label" not in html
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert ">yes<" in html and ">no<" in html and 'aria-hidden="true">✓<' in html
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert ">partial<" in html
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert 'aria-label="Sections"' in html and html.count("cursor:pointer") == 1
    for html in (_py_fresh(blocks[3]), gas[3]):
        assert 'aria-label="Tabs"' in html and "cursor:pointer" not in html


# ---- batch b6/1 ----
EQUAL.extend([
    {"type": "depth_stack", "count": 3, "cards": [{"title": "Alpha", "text": "First **card**"}, {"title": "Beta", "body": "Second"}, "Plain", {"title": "Cut"}]},
    {"type": "glitch_text", "text": "SYSTEM FAULT", "size": "3rem"},
    {"type": "prompt_template", "label": "Triage", "template": "Summarise {topic} for <b>{audience}</b>\nthen {{old}}", "accent": "#0f766e", "copyable": True},
    {"type": "noise_card", "title": "Q3 plan", "text": "Ship **fast**", "bg": "#111827", "color": "#f9fafb"},
    {"type": "shimmer_button", "label": "Start now", "href": "https://example.com/go", "size": "lg", "accent": "#38bdf8", "background": "#1e293b", "speed": "fast", "description": "No card needed"},
    {"type": "typewriter_text", "text": "Hello, world", "size": "32px", "weight": "700", "color": "#111111", "speed": "slow", "cursor": True, "delay": "0.5s"},
    {"type": "tooltip_glossary", "text": "An **intro** line", "terms": [{"term": "SLA", "definition": "Service **level** agreement"}, {"word": "RPO", "def": "Recovery point"}, "Bare"]},
    {"type": "lens_synthesis", "source_excerpt": "Alpha beta gamma.", "points": [{"point": "First", "evidence": "beta"}, {"point": "Second", "evidence": "nope"}, {"point": "Third"}, None, "x"]},
])
MUST.update({
    "depth_stack": ["Alpha", "First <strong>card</strong>", "Beta", "Second", "Plain", "data-cb=\"tile\"", "height:200px"],
    "glitch_text": ["SYSTEM FAULT", 'data-t="SYSTEM FAULT"', "font-size:3rem", "prefers-reduced-motion"],
    "prompt_template": ["Triage", "&lt;b&gt;", "{topic}", "{{old}}", "#0f766e", "Copy", "prompt template"],
    "noise_card": ["Q3 plan", "<strong>fast</strong>", "#111827", "#f9fafb", "feTurbulence", "opacity:0.8"],
    "shimmer_button": ["Start now", 'href="https://example.com/go"', 'rel="noopener"', "No card needed", "16px 40px", "0.9s", "rgba(56,189,248,0.5)", "prefers-reduced-motion"],
    "typewriter_text": ["Hello, world", "font-size:32px", "color:#111111", "steps(12,end)", "animation-delay:0.5s", "1.4s", "white-space:pre-wrap", "prefers-reduced-motion"],
    "tooltip_glossary": ["An <strong>intro</strong> line", "SLA", 'aria-hidden="true"', "Service <strong>level</strong> agreement", "RPO", "Recovery point", "Bare", 'tabindex="0"'],
    "lens_synthesis": ["First", "Second", "Third", "UNVERIFIED", "no supporting quote"],
})
OLD.extend([
    {"type": "depth_stack", "items": [{"title": "Old card", "text": "old text"}]},
    {"type": "glitch_text", "title": "Old title"},
    {"type": "prompt_template", "title": "Old header", "use_case": "Old use case", "template": "Hi {{name}}", "variables": [{"name": "name", "description": "Who", "example": "Ann"}]},
    {"type": "noise_card", "content": "old content"},
    {"type": "shimmer_button", "text": "Old text"},
    {"type": "typewriter_text", "content": "Old content", "speed": 100},
    {"type": "tooltip_glossary", "intro": "Old intro", "items": [{"word": "W", "def": "D"}]},
])
OLD_WORDS.update({
    "depth_stack": ["Old card", "old text"], "glitch_text": ["Old title"],
    "prompt_template": ["Old header", "Old use case", "{{name}}", "Variables", "Who", "Ann"], "noise_card": ["old content"], "shimmer_button": ["Old text"],
    "typewriter_text": ["Old content", "1.3s"], "tooltip_glossary": ["Old intro", ">W<", ">D<"],
})


def test_depth_stack_puts_the_first_card_in_front_and_invents_nothing(core_js):
    blocks = [{"type": "depth_stack", "cards": [{"title": "Front"}, {"title": "Back"}]}, {"type": "depth_stack"}, {"type": "depth_stack", "cards": [], "items": [{"title": "I"}], "count": 99},
              {"type": "depth_stack", "cards": [{"title": "a"}, {"title": "b"}, {"title": "c"}], "count": 2}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert html.index("Front") < html.index("Back") and "top:0px;left:0px" in html and "z-index:2" in html
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert "No cards supplied." in html and "tile" not in html
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert ">I<" in html
    for html in (_py_fresh(blocks[3]), gas[3]):
        assert ">a<" in html and ">b<" in html and ">c<" not in html


def test_prompt_template_slots_copy_button_and_variables_only_when_given(core_js):
    blocks = [{"type": "prompt_template", "template": "Say {x}", "copyable": False},
              {"type": "prompt_template", "template": "Say {x}", "variables": [{"name": "x", "description": "d"}, "junk", {}]},
              {"type": "prompt_template", "template": "Say {x}", "accent": "red", "variables": []}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert ">Copy<" not in html and "Variables" not in html and "{x}" in html
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert ">Copy<" in html and "Variables" in html and "{x}</td>" in html and html.count("<tr") == 2 and "junk" not in html
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert "color-mix(in srgb, red 10%, transparent)" in html and "Variables" not in html


def test_shimmer_button_drops_an_unsafe_href_and_typewriter_validates_delay_and_clamps(core_js):
    blocks = [{"type": "shimmer_button", "label": "L", "href": "javascript:alert(1)"}, {"type": "shimmer_button"},
              {"type": "typewriter_text", "text": "abc", "delay": "1s;x", "cursor": False, "speed": "50"}, {"type": "typewriter_text", "text": "x" * 3000, "speed": "fast"},
              {"type": "typewriter_text"}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert "<button" in html and "<a " not in html and "javascript" not in html
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert ">Click me<" in html
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert "animation-delay:0s" in html and "-blink 0.75s" not in html and "steps(3,end)" in html and "0.2s steps" in html
    for html in (_py_fresh(blocks[3]), gas[3]):
        assert "steps(" not in html and "white-space:pre-wrap" in html and html.count("x") >= 3000
    for html in (_py_fresh(blocks[4]), gas[4]):
        assert "steps(1,end)" in html


def test_lens_synthesis_survives_junk_points_and_evidence(core_js):
    blocks = [{"type": "lens_synthesis", "source_excerpt": "x", "points": [None, 5, {"point": {"a": 1}, "evidence": {}}]}, {"type": "lens_synthesis", "points": [None]}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        py = _py_fresh(b)
        assert _norm_uid(py) == _norm_uid(g)
        for html in (py, g):
            assert "object Object" not in html and "Error" not in html
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert "No synthesis points supplied." in html


# ---- batch b6/2 ----
EQUAL.extend([
    {"type": "reveal_on_scroll", "title": "Launch notes", "body": "Ships **Friday**", "direction": "left", "duration": 1.2, "accent": "#0f766e", "background": "#f0fdfa"},
    {"type": "glow_button", "label": "Deploy", "state": "ready", "href": "https://example.com/d", "color_ready": "#38bdf8", "size": "lg", "description": "One click"},
    {"type": "rating_stars", "rating": 3.5, "max_rating": 5, "label": "Quality"},
    {"type": "score_summary", "correct": 8, "total": 10, "time_taken": "2m 14s", "pass_threshold": 70, "retry_label": "Retry", "continue_label": "Next", "continue_url": "https://example.com/n"},
    {"type": "sonar_pulse", "variant": "warning", "active": True, "label": "Syncing", "size": "lg", "body": "Replica lag"},
    {"type": "uptime_timeline", "label": "API", "uptime": 99.125, "period": "30 days", "days": [1, 1, 0.6, 0, {"date": "2026-10-01", "status": 1}, {"status": "x"}, True]},
])
SAFE.append({"type": "raise_hand", "question": "Ready?", "label": "\u270b Yes", "write_url": "https://example.com/w", "sheet_url": "https://example.com/s.csv", "poll": 2000, "accent": "#0f766e"})
SAFE.append({"type": "match_exercise", "pairs": [{"term": "SLA", "definition": "Service level agreement"}, {"term": "RPO", "definition": "Recovery point objective"}, "junk", None]})
MUST.update({
    "reveal_on_scroll": ["Launch notes", "<strong>Friday</strong>", "translateX(32px)", "1.2s ease", "#0f766e", "#f0fdfa", "IntersectionObserver", "prefers-reduced-motion"],
    "glow_button": ["Deploy", 'href="https://example.com/d"', 'rel="noopener"', "18px 36px", "One click", "#0c1e2e", "color-mix(in srgb,#38bdf8 27%,transparent)", "prefers-reduced-motion"],
    "rating_stars": ["Quality", "Rating: 3.5 of 5", "3.5"],
    "score_summary": ["80%", "Passed", "8 / 10 correct", "Time: 2m 14s", ">Retry<", 'href="https://example.com/n"', "#047857"],
    "sonar_pulse": ["Syncing", "Replica lag", "#f59e0b", "width:130px", ">warning<", "prefers-reduced-motion"],
    "raise_hand": ["Ready?", "\u270b Yes", "#0f766e"],
    "uptime_timeline": ["API", "99.13%", "30 days", "#22c55e", "#f59e0b", "#ef4444", "#94a3b8", "2026-10-01", "Day 1", 'width="7"', 'role="img"'],
    "match_exercise": ["SLA", "Service level agreement", "RPO", "Recovery point objective"],
})
OLD.extend([
    {"type": "reveal_on_scroll", "text": "old text", "delay": 0.4},
    {"type": "glow_button", "text": "Old text", "color": "#123456"},
    {"type": "score_summary", "correct": "3", "total": "4"},
    {"type": "sonar_pulse", "title": "Old title", "color": "#123456"},
    {"type": "uptime_timeline", "uptime_percent": 97.5, "days": [1, 1]},
])
OLD_WORDS.update({
    "reveal_on_scroll": ["old text", "0.4s"], "glow_button": ["Old text", "#123456"], "score_summary": ["75%", "3 / 4 correct"], "sonar_pulse": ["Old title", "#123456"],
    "uptime_timeline": ["97.50%"],
})


def test_timelines_and_defaults_invent_nothing(core_js):
    blocks = [{"type": "uptime_timeline"}, {"type": "uptime_timeline", "uptime": 0}, {"type": "uptime_timeline", "uptime": 99.9, "days": 30},
              {"type": "reveal_on_scroll"}, {"type": "sonar_pulse"}, {"type": "glow_button", "label": "X", "state": "disabled", "href": "https://example.com"}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert "%" not in html.replace("100%", "") and "var(--a2ui-border,#eaeaea)" in html
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert ">0.00%<" in html
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert 'width="480"' in html and "var(--a2ui-border,#eaeaea)" in html and html.count("<rect") == 1 and ">99.90%<" in html
    for html in (_py_fresh(blocks[3]), gas[3]):
        assert "Revealed on scroll" not in html and "fades in" not in html
    for html in (_py_fresh(blocks[4]), gas[4]):
        assert ">Live<" not in html
    for html in (_py_fresh(blocks[5]), gas[5]):
        assert "<a " not in html and " disabled" in html and "not-allowed" in html


def test_score_summary_rounds_half_up_clamps_and_links_safely(core_js):
    blocks = [{"type": "score_summary", "correct": 5, "total": 8, "pass_threshold": 63}, {"type": "score_summary", "correct": 0, "total": 0}, {"type": "score_summary", "correct": 99, "total": 3},
              {"type": "score_summary", "correct": 1, "total": 2, "continue_label": "Go", "continue_url": "javascript:alert(1)"}, {"type": "score_summary", "retry_label": "Again"}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert ">63%<" in html and "Passed" in html
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert ">0%<" in html and "0 / 1 correct" in html
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert ">100%<" in html
    for html in (_py_fresh(blocks[3]), gas[3]):
        assert 'href="#"' in html and "javascript" not in html
    for html in (_py_fresh(blocks[4]), gas[4]):
        assert "<button" in html and "location.reload()" in html and "<a " not in html


def test_raise_hand_live_script_only_in_gas_and_only_to_absolute_http_urls(core_js):
    blocks = [{"type": "raise_hand", "write_url": "javascript:alert(1)", "sheet_url": "/relative.csv"}, {"type": "raise_hand", "write_url": "https://example.com/w?x=1", "poll": 1}]
    gas = _gas_isolated(core_js, blocks)
    for b in blocks:
        py = _py_fresh(b)
        assert "<script" not in py and "fetch(" not in py and "example.com" not in py and "setInterval" not in py
    assert 'var writeUrl="";' in gas[0] and 'var sheetUrl="";' in gas[0]
    assert 'var writeUrl="https://example.com/w?x=1";' in gas[1] and "var poll=1000;" in gas[1] and 'indexOf("?")' in gas[1]


# ---- batch b6/3 ----
EQUAL.extend([
    {"type": "rubric_card", "title": "Essay rubric", "levels": ["Low", "Mid", "High"], "accent": "#0f766e", "criteria": [{"criterion": "Thesis", "descriptors": ["Vague", "Clear"]}, {"criterion": "Evidence", "descriptors": ["a", "b", "c", "d"]}]},
    {"type": "roadmap_card", "title": "2027", "periods": [{"label": "Q1", "items": [{"text": "Ship v2", "status": "done"}, {"text": "Audit", "status": "in_progress"}, "Plain"]}, {"label": "Q2", "items": [{"text": "Launch", "status": "deferred"}, {"text": "Odd", "status": "weird"}]}]},
    {"type": "rating_comparison", "title": "Reviews", "max": 5, "items": [{"label": "Alpha", "rating": 4.5}, {"name": "Beta", "value": 2, "max": 4}, {"label": "Gamma", "rating": 9}]},
    {"type": "step_reveal_sequence", "steps": [{"title": "Plan", "text": "Do **it**"}, {"title": "Ship", "content": "old content"}, "Plain"]},
    {"type": "terminal_boot", "title": "boot", "speed": 500, "lines": ["loading kernel", "mount ok", "\u2717 disk", "token created"]},
    {"type": "variant_selector", "name": "plan", "label": "Pick a plan", "default_value": "pro", "items": [{"value": "free", "title": "Free", "description": "Hobby"}, {"value": "pro", "title": "Pro"}, {"value": "dup", "title": "Dup", "color": "#ff0000", "disabled": True}, "Plain"]},
    {"type": "stepper", "label": "Deploy", "active_index": 1, "color": "#0f766e", "steps": ["Build", {"label": "Test", "description": "Unit and e2e"}, {"title": "Ship"}]},
    {"type": "atom_anatomy", "label": "Badge", "accent": "#0f766e", "schema": {"type": "difficulty_badge", "level": "advanced"}},
])
MUST.update({
    "rubric_card": ["Essay rubric", "Thesis", "Vague", "Clear", "\u2014", "Evidence", "Low", "High", "#1b7c59", "#0f766e", 'scope="row"', 'scope="col"'],
    "roadmap_card": ["2027", "Q1", "Ship v2", "done: ", "in progress: ", "Plain", "planned: ", "deferred: ", "Odd", "#065f46"],
    "rating_comparison": ["Reviews", "Alpha", "(4.5", "Beta", "(2", "out of 4", "Gamma", "(9", "#fbbf24"],
    "step_reveal_sequence": ["Plan", "Do <strong>it</strong>", "old content", "Plain", "1. Plan", "3. Plain", 'role="radiogroup"', "prefers-reduced-motion", "focus-visible"],
    "terminal_boot": ["boot", "loading kernel", "mount ok", "\u2717 disk", "token created", "setTimeout(next,500)", "prefers-reduced-motion"],
    "variant_selector": ["Pick a plan", 'name="plan"', 'value="pro" checked', "Free", "Hobby", "#ff0000", " disabled", "Plain", 'role="radiogroup"'],
    "stepper": ["Deploy", "Build", "Test", "Unit and e2e", "Ship", "completed: ", "current: ", "upcoming: ", 'aria-current="step"', "#0f766e"],
    "atom_anatomy": ["Badge", "#0f766e", "Rendered", "Schema", "Advanced", "&quot;level&quot;: &quot;advanced&quot;"],
})
OLD.extend([
    {"type": "rubric_card", "levels": ["L1", "L2"], "criteria": [{"name": "Old name", "descriptions": ["aa", "bb"]}]},
    {"type": "roadmap_card", "quarter": "Q4", "status": "in_progress", "title": "Old", "description": "Old desc", "items": ["Item one", "Item two"]},
    {"type": "rating_comparison", "items": [{"name": "Old", "value": 4}]},
    {"type": "step_reveal_sequence", "steps": ["Plain step", {"title": "T", "content": "old content"}]},
    {"type": "variant_selector", "variants": [{"label": "Red", "value": "r", "color": "#ff0000"}, {"label": "Blue", "value": "b", "disabled": True}]},
    {"type": "stepper", "steps": [{"label": "A", "is_completed": True}, {"label": "B", "is_current": True}, {"label": "C"}]},
])
OLD_WORDS.update({
    "rubric_card": ["L1", "L2", "Old name", ">aa<", ">bb<"], "roadmap_card": ["Q4", "Old", "Old desc", "Item one", "Item two", "in progress: "], "rating_comparison": ["Old", "(4"],
    "step_reveal_sequence": ["Plain step", "old content"], "variant_selector": ["Red", 'value="r"', "#ff0000", " disabled"], "stepper": ["completed: ", "current: ", "upcoming: "],
})


def test_rubric_never_has_an_empty_header_and_levels_default(core_js):
    blocks = [{"type": "rubric_card", "levels": ["", None, "Top"], "criteria": [{"criterion": "C"}]}, {"type": "rubric_card"}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert "Level 1" in html and "Level 2" in html and "Top" in html and "<th" in html and ">\u2014<" in html
        assert not re.search(r"<th[^>]*></th>", html)
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert "Assessment Rubric" in html and "Exemplary" in html


def test_terminal_boot_colours_only_real_ok_and_error_words(core_js):
    b = {"type": "terminal_boot", "lines": ["token created", "boot OK", "\u2713 done", "FAILED step", "erase cache", 5, None, ""]}
    g = _gas_isolated(core_js, [b])[0]
    assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(b), g):
        assert html.count("line-height:1.9;color:#22c55e") == 2 and html.count("line-height:1.9;color:#f87171") == 1 and html.count("line-height:1.9;color:#94a3b8") == 3
        assert "Raise" not in html
    e = {"type": "terminal_boot"}
    ge = _gas_isolated(core_js, [e])[0]
    assert _norm_uid(_py_fresh(e)) == _norm_uid(ge)
    for html in (_py_fresh(e), ge):
        assert "initializing" not in html and "var els=[];for(var i=0;i<0;" in html


def test_step_reveal_and_variant_selector_radios(core_js):
    blocks = [{"type": "step_reveal_sequence"}, {"type": "step_reveal_sequence", "steps": ["a", "b"]},
              {"type": "variant_selector", "default_value": "x", "items": [{"value": "x"}, {"value": "x"}]}, {"type": "variant_selector"}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert html == ""
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert html.count('type="radio"') == 2 and html.count(" checked") == 1
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert html.count('type="radio"') == 2 and html.count(" checked>") == 1 and 'name="variant-' in html


def test_stepper_states_come_from_active_index_and_legacy_flags(core_js):
    blocks = [{"type": "stepper", "active_index": 2, "steps": ["a", "b", "c", "d"]}, {"type": "stepper", "active_index": 99, "steps": ["a", "b"]}, {"type": "stepper"}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert html.count("completed: ") == 2 and html.count("current: ") == 1 and html.count("upcoming: ") == 1 and html.count('aria-current="step"') == 1
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert html.count("completed: ") == 2 and "current: " not in html


def test_atom_anatomy_parses_json_string_schemas_and_never_nests_itself(core_js):
    blocks = [{"type": "atom_anatomy", "schema": "{\"type\": \"difficulty_badge\", \"level\": \"beginner\"}"}, {"type": "atom_anatomy", "schema": "not json"},
              {"type": "atom_anatomy", "schema": {"type": "atom_anatomy", "schema": {"type": "difficulty_badge"}}}, {"type": "atom_anatomy", "schema": {"type": "no_such_atom"}},
              {"type": "atom_anatomy"}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert "Beginner" in html and "&quot;level&quot;: &quot;beginner&quot;" in html
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert "not json" in html and "Could not render preview" not in html
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert "Could not render preview" in html and "Beginner" not in html
    for html in (_py_fresh(blocks[3]), gas[3]):
        assert "Could not render preview" in html
    for html in (_py_fresh(blocks[4]), gas[4]):
        assert ">{}</pre>" in html and "Could not render preview" not in html


def test_roadmap_status_names_and_legacy_card(core_js):
    b = {"type": "roadmap_card", "periods": [{"label": "Q1", "items": [{"text": "A", "status": "In Progress"}, {"text": "B", "status": ["x"]}, {"text": ""}, None]}, "junk"]}
    g = _gas_isolated(core_js, [b])[0]
    assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(b), g):
        assert "in progress: " in html and "planned: " in html and html.count("planned: ") == 1


def test_typewriter_long_multiline_and_cjk_text_is_shown_whole(core_js):
    blocks = [{"type": "typewriter_text", "text": "A long sentence that certainly does not fit on one line of a narrow column, with more words."},
              {"type": "typewriter_text", "text": "Line one\nLine two\nLine three"}, {"type": "typewriter_text", "text": "こんにちは世界"}, {"type": "typewriter_text", "text": "Short"}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for k in (0, 1, 2):
        for html in (_py_fresh(blocks[k]), gas[k]):
            css = html.split("</style>")[0]
            assert "steps(" not in css and "width:0" not in css and "display:block;white-space:pre-wrap" in css
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert "Line one\nLine two\nLine three" in html
    for html in (_py_fresh(blocks[3]), gas[3]):
        assert "steps(5,end)" in html


def test_rating_comparison_shows_numbers_as_given_and_reads_aliases(core_js):
    blocks = [{"type": "rating_comparison", "items": [{"label": "Survey", "value": 72, "max": 100}]}, {"type": "rating_comparison", "items": [{"label": "N", "rating": 9}]},
              {"type": "rating_comparison", "items": [{"name": "Auth0", "score": 4.6, "reviews_count": 820}]}, {"type": "rating_comparison", "ratings": [{"label": "Load", "rating": 4.9}]}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert "(72" in html and "out of 100" in html and "width:72%" in html and "★" not in html
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert "(9)" in html and "out of" not in html and html.count("★") == 5
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert "(4.6)" in html and "820 reviews" in html
    for html in (_py_fresh(blocks[3]), gas[3]):
        assert "(4.9)" in html and "Load" in html


def test_aliases_for_match_pairs_and_step_body_and_stack_markdown(core_js):
    blocks = [{"type": "match_exercise", "pairs": [{"key": "K1", "value": "V1"}, {"left": "L2", "right": "R2"}]}, {"type": "step_reveal_sequence", "steps": [{"title": "T", "body": "Body **b**"}]},
              {"type": "depth_stack", "cards": [{"title": "A", "text": "x **y**"}, {"title": "B"}, {"title": "C"}], "count": 2}]
    gas = _gas_isolated(core_js, blocks)
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert all(w in html for w in ("K1", "V1", "L2", "R2"))
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert "Body <strong>b</strong>" in html
    for b, g in zip(blocks[1:], gas[1:]):
        assert _norm_uid(_py_fresh(b)) == _norm_uid(g)
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert "x <strong>y</strong>" in html and "3 items" in html


def test_unnamed_variant_selectors_get_their_own_radio_group(core_js):
    a, b = {"type": "variant_selector", "items": [{"value": "a"}]}, {"type": "variant_selector", "items": [{"value": "b"}]}
    names = [re.search(r'name="([^"]+)"', h).group(1) for h in (_py_fresh(a), _py_fresh(b))]
    assert names[0] != names[1]
    g = _gas_isolated(core_js, [a, b])
    assert re.search(r'name="([^"]+)"', g[0]).group(1) != re.search(r'name="([^"]+)"', g[1]).group(1)


# ---- batch b7/1 ----
EQUAL.extend([
    {"type": "choicebox_group", "label": "Plan", "name": "plan", "accent": "#0f766e", "submit_label": "Continue", "items": [{"value": "free", "title": "Free", "description": "For hobbies", "icon": "\U0001F331"}, {"value": "pro", "title": "Pro", "disabled": True}, "Plain"]},
    {"type": "sprint_board", "sprint_name": "Sprint 42", "columns": [{"name": "To Do", "items": [{"key": "A-1", "summary": "Fix login", "type": "bug", "priority": "high"}, {"key": "A-2", "summary": "No priority"}]}, {"title": "Done", "cards": [{"id": "A-3", "title": "Old shape", "assignee": "zoe", "labels": ["ui", 5]}]}, "junk"]},
    {"type": "token_budget_meter", "used": 150000, "total": 200000, "model": "claude-sonnet-4-6", "label": "Context", "warn_at": 60, "critical_at": 95},
    {"type": "typing_indicator", "name": "Claude", "variant": "light"},
    {"type": "marquee", "title": "Trusted by", "speed": 20, "gap": 32, "direction": "right", "separator": "\u2022", "pause_on_hover": False, "bg": "#0f172a", "rounded": False, "items": [{"text": "Acme", "url": "https://example.com/a", "icon": "\u2605"}, {"label": "Logo", "image_url": "https://example.com/l.png"}, "Plain"]},
    {"type": "marquee_strip", "label": "Stack", "speed": "fast", "direction": "right", "gap": "24px", "separator": "/", "items": ["Go", {"text": "Rust", "image_url": "https://example.com/r.png", "icon": "R"}, {"label": "Old label"}]},
    {"type": "number_flip", "value": "1,204.5", "prefix": "$", "suffix": "k", "label": "Revenue", "size": "4rem", "color": "#22c55e", "duration": 900, "align": "left"},
    {"type": "progress_reveal", "value": 85, "label": "Migration", "color": "#0f766e", "suffix": " pts", "height": 14},
])
MUST.update({
    "choicebox_group": ["Plan", "Free", "For hobbies", "Pro", "Plain", "Continue", 'name="plan"', 'type="radio"', "#0f766e", " disabled", 'role="group"'],
    "sprint_board": ["Sprint 42", "To Do", "A-1", "Fix login", "No priority", "Done", "A-3", "Old shape", ">Z<", "ui", "#ff7a00", "#d1d5db"],
    "token_budget_meter": ["Context", "claude-sonnet-4-6", "150.0k / 200.0k (75%)", "#f59e0b"],
    "typing_indicator": ["Claude", "is typing", "#f1f5f9", 'role="status"', "prefers-reduced-motion"],
    "marquee": ["Trusted by", "Acme", 'href="https://example.com/a"', 'src="https://example.com/l.png"', "Logo", "Plain", "\u2022", "reverse", "20s", "padding:0 32px", "#0f172a", "border-radius:0"],
    "marquee_strip": ["Stack", "Go", "Rust", 'src="https://example.com/r.png"', "Old label", "12s", "reverse", "gap:24px", ">/<"],
    "number_flip": ["$", "1,204.5", "k", "Revenue", "font-size:4rem", "#22c55e", "text-align:left", "prefers-reduced-motion", 'aria-hidden="true"'],
    "progress_reveal": ["Migration", "85 pts", "#0f766e", "height:14px", 'data-target="85"', "IntersectionObserver"],
})
OLD.extend([
    {"type": "choicebox_group", "question": "Pick", "options": [{"value": "a", "label": "Option A", "desc": "Because"}]},
    {"type": "sprint_board", "columns": [{"title": "Old", "items": [{"id": "X-9", "title": "Old ticket", "priority": "low"}]}]},
    {"type": "token_budget_meter", "used": 10, "total": 100},
    {"type": "typing_indicator", "label": "Claude is thinking", "color": "#6366f1", "bg": "#ede9fe"},
    {"type": "marquee", "items": [{"label": "Old marquee"}], "accent": "#123456"},
    {"type": "marquee_strip", "tags": ["old-a", "old-b"], "words": ["ignored"], "speed": 30, "bg": "#101010", "color": "#eeeeee"},
    {"type": "number_flip", "value": 42, "accent": "#654321"},
    {"type": "progress_reveal", "percent": 40, "title": "Old title"},
])
OLD_WORDS.update({
    "choicebox_group": ["Pick", "Option A", "Because", 'value="a"'], "sprint_board": ["Old", "X-9", "Old ticket", "#0065ff"],
    "token_budget_meter": ["Context window", "10 / 100 (10%)"], "typing_indicator": ["Claude is thinking", "#6366f1", "#ede9fe"],
    "marquee": ["Old marquee"], "marquee_strip": ["old-a", "old-b", "30s", "#101010", "#eeeeee"], "number_flip": ["#654321"], "progress_reveal": ["Old title", "40%", 'data-target="40"'],
})


def test_b7_1_inherited_names_and_odd_values_do_not_leak_prototype_members(core_js):
    blocks = [{"type": "sprint_board", "columns": [{"name": "c", "items": [{"key": "k", "summary": "s", "type": "constructor", "priority": "__proto__"}]}]},
              {"type": "sprint_board", "columns": [{"name": "c", "items": [{"key": "k", "assignee": "\U0001F600smile"}]}]},
              {"type": "typing_indicator", "name": "\U0001F600 bot"}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        py = _py_fresh(b)
        assert _norm_uid(py) == _norm_uid(g)
        for html in (py, g):
            assert "function" not in html and "object Object" not in html
    for html in (_py_fresh(blocks[1]), gas[1], _py_fresh(blocks[2]), gas[2]):
        assert "\U0001F600" in html


def test_b7_1_number_formats_agree_on_rounding_ties(core_js):
    blocks = [{"type": "token_budget_meter", "used": 1250, "total": 2500},      # 1.25k rounds up in both twins
              {"type": "token_budget_meter", "used": 1, "total": 8},            # 12.5 %
              {"type": "token_budget_meter", "used": 3, "total": 8, "animate": True, "duration": 0.125},
              {"type": "token_budget_meter", "used": 5, "total": 0.0001},
              {"type": "token_budget_meter", "used": 1e30, "total": 1e30},
              {"type": "marquee", "speed": 0.125, "items": ["a"]}]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        py = _py_fresh(b)
        assert _norm_uid(py) == _norm_uid(g), b
        assert "Infinity" not in py and "NaN" not in py and "e+" not in py
    for html in (_py_fresh(blocks[0]), gas[0]):
        assert "1.3k / 2.5k" in html
    for html in (_py_fresh(blocks[1]), gas[1]):
        assert "width:12.5%" in html
    for html in (_py_fresh(blocks[2]), gas[2]):
        assert "@property" in html and "prefers-reduced-motion" in html and "0.125s" in html and "3 of 8" in html


def test_b7_1_number_flip_keeps_its_value_without_motion_and_for_screen_readers(core_js):
    b = {"type": "number_flip", "value": "9\u00b2a7", "prefix": "~"}
    for html in (_py_fresh(b), _gas_isolated(core_js, [b])[0]):
        assert "translateY(-900%)" in html and "translateY(-700%)" in html     # the end position is the resting style, not only the keyframe
        assert ">~9\u00b2a7<" in html and "\u00b2" in html                       # full text for screen readers; a superscript is no digit column
        assert html.count("-roll") >= 3
    long = {"type": "number_flip", "value": "1" * 500}
    for html in (_py_fresh(long), _gas_isolated(core_js, [long])[0]):
        assert html.count("@keyframes") <= 40


def test_b7_1_progress_reveal_and_choicebox_script_free_of_payload(core_js):
    b = {"type": "progress_reveal", "value": 50, "suffix": "</script><b>x", "label": "L"}
    c = {"type": "choicebox_group", "items": [{"value": "v", "title": "t", "disabled": []}], "multiple": [], "accent": "red;}</style><script>alert(1)</script>"}
    for html in (_py_fresh(b), _gas_isolated(core_js, [b])[0]):
        scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
        assert len(scripts) == 1 and "<b>" not in scripts[0]
        assert 'data-suffix="&lt;/script&gt;&lt;b&gt;x"' in html
    for html in (_py_fresh(c), _gas_isolated(core_js, [c])[0]):
        assert "<script" not in html and 'type="radio"' in html and " disabled" not in html
        assert "#1a73e8" in html


# ---- batch b7/2 ----
EQUAL.extend([
    {"type": "punch_card", "title": "Commits", "subtitle": "org/core", "color": "#0f766e", "labels_days": ["Mon", "Tue"], "data": [[0, 3, 9, 1], [2, 0, 5, "7"]]},
    {"type": "order_status_card", "order_number": "#1042", "date": "2026-10-01", "status": "partial", "customer": "Ada", "total": "$124.00", "items": [{"title": "Cable", "qty": 2, "price": "$4"}, {"name": "Old name", "price": "$9"}, "junk"]},
    {"type": "metric_comparison_card", "label": "Latency", "value": 118, "previous": 145, "lower_is_better": True},
    {"type": "entity_list", "title": "Services", "items": [{"name": "Auth", "subtitle": "Identity", "status": "active", "meta": "99.9%", "icon": "\U0001F510"}, {"name": "Billing", "description": "Invoices", "type": "product", "link": "https://example.com/b", "id": "svc-2"}, "junk"]},
    {"type": "donut_stat", "value": 84, "max_value": 100, "label": "Quota", "unit": "%", "color": "#f59e0b", "size": "120px"},
    {"type": "mini_sparkline_set", "series": [{"label": "CPU", "data": [10, 20, 15, 30], "unit": "%", "color": "#0f766e"}, {"name": "Mem", "data": [4.2, 4.3, 4.5]}, "junk"]},
    {"type": "llm_comparison_table", "prompt": "Summarize.", "show_meta": True, "models": [{"name": "A", "output": "Fast answer", "latency_ms": 280, "cost_usd": 0.003, "tokens": 82}, {"name": "B", "output": "Slow"}]},
])
SAFE.append({"type": "quiz_result_summary", "score": 9, "total": 10, "quiz_id": "sre-101", "pass_mark": 80, "time_secs": 145, "next_url": "https://example.com/n", "retry_url": "javascript:alert(1)", "questions": [{"label": "Q1", "correct": True}, {"correct": False}, "x"]})
MUST.update({
    "punch_card": ["Commits", "org/core", "#0f766e", "Mon", "Tue", "Mon 01:00 - 3 commits", "Tue 03:00 - 7 commits", "<title>"],
    "order_status_card": ["#1042", "2026-10-01", "Partial", "Ada", "$124.00", "Cable", "\u00d72", "Old name", "Shipped"],
    "metric_comparison_card": ["Latency", "145", "118", "-18.6%", "#12863d"],
    "entity_list": ["Services", "Auth", "Identity", "99.9%", "active", 'href="https://example.com/b"', 'data-key="svc-2"', "Invoices", "a2ui-entity-card{"],
    "donut_stat": ["Quota", "84", "%", "#f59e0b", 'viewBox="0 0 120 120"', "prefers-reduced-motion"],
    "mini_sparkline_set": ["CPU", "30 %", "Mem", "4.5", "#0f766e", "a2ui-sparkline-row{", 'aria-label="CPU: 30 %"'],
    "llm_comparison_table": ["Summarize.", "Fast answer", "280 ms", "82 tok", "$0.0030", "Slow"],
    "quiz_result_summary": ["Passed!", "90", "9 / 10 correct", "2m 25s", "80%", 'href="https://example.com/n"', "Question breakdown", "Q1", "Q2"],
})
OLD.extend([
    {"type": "metric_comparison_card", "label": "Traffic", "baseline": {"label": "Last week", "value": 10, "unit": "k"}, "comparison": {"label": "This week", "value": 12.5, "unit": "k"}},
    {"type": "order_status_card", "order_id": "#77", "status": "shipped", "items": [{"name": "Thing", "qty": 1, "price": "$1"}]},
    {"type": "entity_list", "entities": [{"name": "Old entity", "description": "d", "type": "person"}]},
    {"type": "mini_sparkline_set", "sparklines": [{"label": "Old spark", "data": [1, 2, 3]}]},
    {"type": "donut_stat", "value": 5, "max_value": 5},
])
OLD_WORDS.update({"metric_comparison_card": ["Traffic", "Last week", "This week", "12.5", "+25.0%"], "order_status_card": ["#77", "Shipped", "Thing"], "entity_list": ["Old entity", "d"], "mini_sparkline_set": ["Old spark", "3"], "donut_stat": [">5<", "%"]})
