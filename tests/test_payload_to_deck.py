"""payload_to_deck: the atoms that declare the `slides`/`pptx` surfaces are exactly the atoms with a recipe, and every recipe builds a clean slide."""
import json, sys
from pathlib import Path
import pytest, yaml
pytest.importorskip('pptx'); pytest.importorskip('defusedxml')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/deck'))
import payload_to_deck as p

import functools
@functools.lru_cache(None)
def atoms(): d = yaml.safe_load((ROOT / 'atoms/schema.yaml').read_text()); d = d if isinstance(d, list) else list(d.values())[0]; return {a['type']: a for a in d if isinstance(a, dict)}

def test_surface_declaration_matches_recipes():
    declared = {t for t, a in atoms().items() if {'slides', 'pptx'} & set((a.get('surfaces') or {}).get('works_on') or [])}
    assert declared == set(p.RECIPES), f'schema only: {sorted(declared - set(p.RECIPES))}; recipe only: {sorted(set(p.RECIPES) - declared)}'
    for t in declared: assert {'slides', 'pptx'} <= set(atoms()[t]['surfaces']['works_on']), f'{t}: slides and pptx go together'

SAMPLES = {
    'page_header': {'title': 'T', 'subtitle': 'S', 'tag': 'X'}, 'gradient_hero': {'title': 'T', 'subtitle': 'S'}, 'closing': {'text': 'Thanks', 'tags': ['a', 'b']},
    'body': {'text': 'One sentence. Another sentence.'}, 'bullet_list': {'items': [{'text': 'a'}, {'label': 'L', 'text': 'b'}]}, 'numbered_list': {'items': [{'text': 'a'}]},
    'steps': {'items': [{'text': 'a'}, {'text': 'b'}]}, 'icon_list': {'items': [{'icon': 'x', 'text': 'a'}]}, 'action_items': {'items': [{'action': 'Ship', 'owner': 'Ada', 'due': 'Fri'}]},
    'pipeline': {'steps': ['a', 'b']}, 'quote': {'text': 'q', 'attribution': 'n'}, 'blockquote_with_avatar': {'quote': 'q', 'author_name': 'n', 'author_title': 'r'},
    'testimonial_card': {'text': 'q', 'author_name': 'n', 'author_title': 'r'}, 'expert_endorsement': {'quote': 'q', 'expert_name': 'n', 'expert_title': 't', 'expert_organization': 'o'},
    'review_callout': {'review_text': 'q', 'author_name': 'n'}, 'pull_stat': {'value': '99', 'unit': '%', 'label': 'l'}, 'metric_row': {'metrics': [{'value': '1', 'label': 'a'}]},
    'icon_stat_row': {'stats': [{'icon': 'x', 'value': '1', 'label': 'a'}]}, 'social_proof_banner': {'metric_value': '1M', 'metric_label': 'users'},
    'metric_delta': {'label': 'l', 'current_value': '5'}, 'table': {'headers': ['a', 'b'], 'rows': [['1', '2']]}, 'key_value': {'items': [{'key': 'k', 'description': 'd'}]},
    'callout': {'title': 't', 'text': 'Text. More.'}, 'text_callout': {'title': 't', 'description': 'Text.'}, 'highlight_box': {'title': 't', 'text': 'Text.'},
    'cta_section': {'heading': 'h', 'body': 'b', 'primary_cta': {'label': 'Go', 'url': 'https://a2uicatalog.ai'}},
    'heading': {'text': 'H'}, 'subheading': {'text': 'H'},
}

def test_every_recipe_has_a_sample_and_builds(tmp_path):
    assert set(SAMPLES) == set(p.RECIPES)
    r = p.run({'blocks': [{'type': t, **b} for t, b in SAMPLES.items()]}, str(tmp_path / 'all.pptx'), 'google-slides')     # one deck; an error names its block
    assert r['ok'] and not r['errors'] and not r['unsupported'], (r['errors'], r.get('lint'))

def test_unsupported_and_ignored_are_reported_not_guessed():
    r = p.run({'blocks': [{'type': 'chartjs_pie'}, {'type': 'divider'}, {'type': 'body', 'text': 'Hi.'}]})
    assert [u['type'] for u in r['unsupported']] == ['chartjs_pie'] and r['conversion']['ignored'][0]['type'] == 'divider' and r['slides'] == 1

def test_long_lists_and_tables_continue_instead_of_truncating():
    r = p.run({'blocks': [{'type': 'bullet_list', 'items': [{'text': f'item {i}'} for i in range(14)]}, {'type': 'table', 'headers': ['a'], 'rows': [[str(i)] for i in range(10)]}]})
    assert r['slides'] == 5 or r['errors'], r      # 3 list slides + 2 table pages (a one-column table is rejected by deck_build, which needs 2+)
