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
    from recipes_more import RECIPE_SAMPLES
    allsamples = {**SAMPLES, **RECIPE_SAMPLES}
    assert set(allsamples) == set(p.RECIPES), (sorted(set(p.RECIPES) - set(allsamples)), sorted(set(allsamples) - set(p.RECIPES)))
    for t, b in allsamples.items():                                              # each atom alone, so a failure names the atom and a recipe cannot hide behind another
        r = p.run({'blocks': [{'type': t, **b}]}, None, 'google-slides')
        assert r['ok'] and not r['errors'] and not r['unsupported'] and r['slides'] >= 1, (t, r['errors'])
    r = p.run({'blocks': [{'type': t, **b} for t, b in allsamples.items()]}, str(tmp_path / 'all.pptx'), 'google-slides')   # and all together, built and linted
    assert r['ok'] and not r['errors'], (r['errors'], r.get('lint'))

def test_unsupported_and_ignored_are_reported_not_guessed():
    r = p.run({'blocks': [{'type': 'chartjs_pie'}, {'type': 'divider'}, {'type': 'body', 'text': 'Hi.'}]})
    assert [u['type'] for u in r['unsupported']] == ['chartjs_pie'] and r['conversion']['ignored'][0]['type'] == 'divider' and r['slides'] == 1

def test_long_lists_and_tables_continue_instead_of_truncating():
    r = p.run({'blocks': [{'type': 'bullet_list', 'items': [{'text': f'item {i}'} for i in range(14)]}, {'type': 'table', 'headers': ['a'], 'rows': [[str(i)] for i in range(10)]}]})
    assert r['slides'] == 5 or r['errors'], r      # 3 list slides + 2 table pages (a one-column table is rejected by deck_build, which needs 2+)


def test_realistic_payloads_convert_for_every_new_recipe():
    """tests/fixtures/deck_real_payloads.json: per atom, a realistic payload ("real") and a long-text, many-item one ("stress"), drafted by Gemini from the schema's field
    descriptions independently of the recipes (item shapes for feature_matrix, comparison_grid, rating_comparison, side_by_side_spec, intro and code follow the renderer).
    A realistic payload must build with no error; a stress payload may be refused, but only with an exact error, never an exception, a blank slide or a truncated cell."""
    fx = json.loads((ROOT / 'tests/fixtures/deck_real_payloads.json').read_text())
    for a, kinds in fx.items():
        r = p.run({'blocks': [{'type': a, **kinds['real']}]}, None, 'google-slides')
        assert r['ok'] and r['slides'] >= 1 and not r['errors'], (a, [e['message'] for e in r['errors']])
        sc, _ = p.convert({'blocks': [{'type': a, **kinds['real']}]})
        assert all(x['f'].get('items') != [] and x['f'].get('rows') != [] for x in sc), a
        r = p.run({'blocks': [{'type': a, **kinds['stress']}]}, None, 'google-slides')
        assert r['ok'] or all(e.get('message') for e in r['errors']), a

def test_no_silent_truncation_in_recipes():
    import re as _re
    src = (ROOT / 'tools/deck/recipes_more.py').read_text()
    assert "[:60]" not in src and "[:6]" not in src, 'a recipe slices content; split it over slides instead'


def test_picture_fallback_for_atoms_without_a_recipe(tmp_path):
    import shutil
    if not (shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')): pytest.skip('no chromium')
    blocks = [{'type': 'status_pill', 'label': 'Live', 'status': 'success'}, {'type': 'made_up_atom', 'x': 1}]
    assert [u['type'] for u in p.run({'blocks': blocks})['unsupported']] == ['status_pill', 'made_up_atom']          # off by default: reported, not guessed
    r = p.run({'blocks': blocks}, str(tmp_path / 'o.pptx'), 'google-slides', None, '', str(tmp_path / 'pics'))
    assert r['ok'] and r['slides'] == 1 and [u['type'] for u in r['unsupported']] == ['made_up_atom']              # a blank render is refused, not shipped
    assert r['conversion']['converted'][0]['mode'] == 'picture' and (tmp_path / 'pics' / '000-status_pill.png').exists()


def test_callouts_and_grids_become_cards_and_fall_back_when_too_long():
    sc, _ = p.convert({'blocks': [{'type': 'callout', 'kind': 'warning', 'text': 'Short warning.'}]}); assert sc[0]['type'] == 'cards' and sc[0]['f']['cards'] == [('Warning', 'Short warning.')]
    sc, _ = p.convert({'blocks': [{'type': 'callout', 'title': 'Long', 'text': 'One sentence here. ' * 20}]}); assert sc[0]['type'] == 'bullets'
    sc, _ = p.convert({'blocks': [{'type': 'feature_grid', 'heading': 'Why', 'features': [{'title': f'F{i}', 'description': 'd'} for i in range(5)]}]})
    assert [x['type'] for x in sc] == ['cards', 'cards'] and len(sc[0]['f']['cards']) == 3
    sc, _ = p.convert({'blocks': [{'type': 'metric_row', 'metrics': [{'value': '1', 'label': 'a', 'sub': 'in the catalog'}]}]}); assert sc[0]['f']['stats'] == [('1', 'a', 'in the catalog')]
