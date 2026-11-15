"""Null fields must behave like missing fields (the payload guard drops them), and three renderer faults found in the T1-T6 benchmark renders stay fixed.

Cause of the crash class: dict.get(k, default) returns None, not the default, when the key is PRESENT with a null value (an LLM reshape emits
"rating": null for a field it has nothing for), so int(b.get("rating", 0)) and string methods raised for ~190 atoms.
"""
import re

import pytest
import yaml

import renderers.web_article as wa
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def render(block):
    return wa.render([block])


def test_testimonial_with_null_rating_and_avatar_renders():
    html = render({"type": "testimonial_card", "text": "It paid for itself in a week.", "author_name": "Priya Nair",
                   "author_title": "VP Engineering", "author_avatar_url": None, "rating": None})
    assert "It paid for itself" in html and "Priya Nair" in html and "TypeError" not in html


@pytest.mark.parametrize("block", [
    {"type": "body", "text": None},
    {"type": "bullet_list", "items": None},
    {"type": "steps", "items": None},
    {"type": "table", "rows": None, "headers": None},
])
def test_basic_atoms_survive_null_fields(block):
    render(block)   # must not raise


def test_null_equals_missing_for_every_atom():
    """Every atom rendered with all fields null must not raise, apart from the two known exceptions (image_pair hard-requires a url; agent_sketchpad validates its own payload and is exempt from the guard)."""
    known = {"image_pair", "agent_sketchpad"}
    crashed = {}
    for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]:
        t, f = a.get("type"), a.get("fields")
        if not t or not isinstance(f, dict):
            continue
        try:
            render({"type": t, **{k: None for k in f}})
        except Exception as e:  # noqa: BLE001
            crashed[t] = type(e).__name__
    assert set(crashed) <= known, sorted(set(crashed) - known)


def test_animated_counter_renders_the_schema_counters_list():
    """The Batch 6 definition used to shadow the schema-correct one and read only a top-level target, so `counters` showed 0 and no label."""
    html = render({"type": "animated_counter", "duration": 2,
                   "counters": [{"value": 1540, "label": "Deployments Today"}, {"value": 99, "label": "Success Percentage", "suffix": "%"}]})
    assert "Deployments Today" in html and "Success Percentage" in html and "1540" in html and "target=0" not in html


def test_animated_counter_single_target_still_works():
    html = render({"type": "animated_counter", "value": 7, "label": "Open items"})
    assert "Open items" in html and "target=7" in html


def test_status_pill_list_label_is_joined_not_printed_as_a_python_list():
    html = render({"type": "status_pill", "label": ["In progress", "Blocked", "Done"]})
    assert "In progress, Blocked, Done" in html and "['" not in html and "&#x27;" not in html


def test_icon_list_empty_icon_falls_back_to_the_bullet():
    html = render({"type": "icon_list", "items": [{"icon": "", "label": "Migrate billing", "text": "In progress"}]})
    assert "•" in html and "Migrate billing" in html
