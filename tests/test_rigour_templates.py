"""tools/rigour, tested: what is drawn rests on standing, verbatim-grounded slots; gaps are reported, never filled;
the simplest sufficient artifact is chosen; and the Python status always matches the toulmin_argument atom's."""
import copy
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, 'tools', 'rigour')
sys.path[:0] = [TOOL, ROOT]
from rigour import argument, bom as boms, builders, provenance   # noqa: E402
from reading import extract as ex, pipeline   # noqa: E402
from renderers import web_article as atoms   # noqa: E402

FIX = os.path.join(TOOL, 'fixtures')
read = lambda n: open(os.path.join(FIX, n + '.html'), encoding='utf-8').read()


def atom_status(rec):
    h = atoms._RENDERERS['toulmin_argument'](rec)
    return re.search(r'border:1\.5px solid #[0-9a-f]{6};color:#[0-9a-f]{6};">([A-Z ]+)<', h).group(1)


# ---- the three outcomes -------------------------------------------------------------------------------------------

def test_a_described_architecture_becomes_a_diagram():
    r = pipeline.run(read('remote_access'))
    assert r['built'] == 'motion_arch'
    assert r['graph']['chain'] == ['laptop', 'vpn client', 'remote access gateway', 'internal network']
    assert [d['b'] for d in r['graph']['deps']] == ['identity provider']                # a dependency, not a layer
    assert [z['label'] for z in r['graph']['zones']] == ['Your device']                 # only the stated boundary
    assert r['provenance'] == []
    assert any('proxy' in g for g in r['gaps'])
    assert any('which side of that boundary the remote access gateway sits on' in g for g in r['gaps'])


def test_names_without_connections_fall_back_to_a_list_and_a_gap():
    r = pipeline.run(read('names_only'))
    assert r['built'] == 'bullet_list (names only)'
    assert r['gates'] == {'motion_arch': 'REBUTTED', 'layer_stack': 'REBUTTED'}
    assert r['gaps'] == ['the article names 3 components (vpn client, remote access gateway, identity provider) but never says how they connect']


def test_device_names_alone_draw_nothing():
    r = pipeline.run('<h2>App errors</h2><p>Open the app on your laptop or phone and restart it.</p>')
    assert r['block'] is None and r['built'].startswith('nothing to draw') and r['gaps'] == []


def test_a_lone_chain_is_drawn_as_the_simpler_stack():
    r = pipeline.run(read('mail_chain'))
    assert r['built'] == 'layer_stack (simplest form)'
    assert any(x['applies'] and 'reads more clearly as a stack' in x['text'] for x in r['gate']['rebuttals'])


# ---- nothing invented ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize('name', ['remote_access', 'mail_chain'])
def test_every_drawn_label_comes_from_the_article_or_a_declared_rule(name):
    src = read(name); r = pipeline.run(src); text = r['article']['text'].lower(); b = r['block']
    labels = [n['label'] for n in b.get('nodes', [])] + [l['name'] for l in b.get('layers', [])]
    assert labels and all(l.lower() in text for l in labels), labels
    rule_labels = {x['label'] for x in ex.RULES['relations']}
    assert all(e['label'] in rule_labels for e in b.get('edges', []))
    assert all(g['label'] in {z['label'] for z in ex.RULES['zones']} for g in b.get('groups', []))
    assert b.get('label', b.get('title', '')).startswith(ex.heading(src))


def test_an_invented_or_unsupported_element_is_caught():
    r = pipeline.run(read('remote_access'))
    rebutted = next(s['id'] for s in r['article']['slots'] if s['fallback'])
    findings = provenance.check(r['elements'] + [dict(what='node', label='Firewall', grounds=[]),
                                                 dict(what='node', label='Backup gateway', grounds=[rebutted]),
                                                 dict(what='edge', label='x -> y', grounds=['s99'])], r['slot_status'])
    assert findings == ["node 'Firewall' rests on no slot", f"node 'Backup gateway' rests on slot {rebutted}, which is REBUTTED",
                        "edge 'x -> y' rests on unknown slot s99"]


def test_a_fabricated_quote_does_not_stand():
    rec = argument.record('t', 'c', [dict(quote='Most disconnects are caused by outdated router firmware.')], 'w',
                          excerpt=ex.text_of(read('remote_access')))
    assert argument.status(rec) == 'UNVERIFIED GROUNDS'


def test_a_fallback_sentence_is_rebutted_and_never_drawn():
    r = pipeline.run(read('remote_access'))
    fb = [s for s in r['article']['slots'] if s['fallback']]
    assert len(fb) == 1 and r['slot_status'][fb[0]['id']] == 'REBUTTED'
    assert 'backup gateway' not in str(r['block']).lower()


def test_an_ambiguous_short_name_stays_unresolved():
    assert ex.resolve('gateway', ['remote access gateway', 'mail gateway']) == ('gateway', 'sourced')
    assert ex.resolve('gateway', ['remote access gateway']) == ('remote access gateway', 'derived')


def test_a_name_only_seen_in_a_fallback_is_never_an_alias_target():
    r = pipeline.run(read('remote_access'))
    assert all(s['a'] != 'backup gateway' for s in r['article']['slots'] if not s['fallback'])


# ---- clarity rules ------------------------------------------------------------------------------------------------

WORDS = 'alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo'.split()


def chain_article(names):
    return '<h2>Chain</h2><p>' + ' '.join(f'The {a} connects to the {b}.' for a, b in zip(names, names[1:])) + \
           '</p><p>The ' + names[1] + ' authenticates you against the ' + names[0] + ' vault before it starts.</p>'


def test_too_many_nodes_falls_back_to_the_stack():
    r = pipeline.run(chain_article(WORDS))                                     # 11 nodes + a dependency
    assert r['gates']['motion_arch'] == 'REBUTTED' and r['built'].startswith('layer_stack')
    assert any(x['applies'] and 'too many to read' in x['text'] for x in r['gate']['rebuttals'])


def test_labels_too_long_for_one_row_fall_back_to_the_stack():
    long_names = [f'{w} {w} {w} {w} service component' for w in WORDS[:5]]
    r = pipeline.run(chain_article(long_names))
    assert any(x['applies'] and 'cannot fit on one row' in x['text'] for x in r['gate']['rebuttals'])
    assert r['built'].startswith('layer_stack')


def test_every_declared_clarity_rule_must_be_evaluated():
    with pytest.raises(ValueError, match='not evaluated'):
        boms.gate(boms.load('motion_arch'), [], dict(min_nodes=False), '')


def test_the_layout_fits_every_label():
    r = pipeline.run(read('remote_access')); W = r['block']['w']
    for n in r['block']['nodes']:
        assert n['w'] / 100 * W >= builders.NODE_PX + builders.CHAR_PX * len(n['label']) - 1, n['label']


# ---- parity and determinism ---------------------------------------------------------------------------------------

def test_python_status_matches_the_atom_for_every_record():
    recs = []
    for n in ('remote_access', 'names_only', 'mail_chain'):
        r = pipeline.run(read(n)); recs += r['slot_records'] + [r['gate']]
    weird = copy.deepcopy(recs[0]); weird['grounds'] = [dict(quote='not there'), None, 5]
    recs += [weird, dict(type='toulmin_argument'), dict(type='toulmin_argument', claim='c', grounds=[dict(quote='x')], source_excerpt='x')]
    for rec in recs:
        assert argument.status(rec) == atom_status(rec), rec.get('title')


def test_the_pipeline_is_deterministic():
    a, b = pipeline.run(read('remote_access')), pipeline.run(read('remote_access'))
    assert a['block'] == b['block'] and a['gaps'] == b['gaps']


# ---- real documentation (Wikipedia DNS extract, CC BY-SA) ------------------------------------------------------------

def test_real_dns_extract_draws_only_what_it_states():
    r = pipeline.run(read('web_dns'))
    assert r['graph']['chain'] == ['programs', 'dns resolver', 'dns servers']
    implied = [s for s in r['article']['slots'] if s['implied']]
    assert [r['slot_status'][s['id']] for s in implied] == ['REBUTTED']                # "a query to the root servers": by whom?
    assert r['built'] == 'layer_stack (simplest form)' and r['provenance'] == []
    assert 'root servers' not in str(r['block']).lower()                               # the textbook hop is not drawn
    assert r['gaps'] == ['the article mentions a query to the root servers but never says what sends it',
                         'the article links the root servers to the authoritative servers (refers to), but never connects the root servers to the rest of the path']


# ---- the HLD artifact and its separate evidence report -------------------------------------------------------------

from reading import hld   # noqa: E402


def test_hld_hosting_is_containment_not_a_flow_step():
    h = hld.build(read('remote_access'))
    assert h['status'] == 'STANDS'
    assert not any(e['b'] == 'vpn client' and e['a'] == 'laptop' for e in h['edges'])     # not an interaction
    assert 'laptop' not in h['names']                                                     # the host is the frame
    assert [z['label'] for z in h['zones']] == ['Your laptop']
    assert 'YOUR LAPTOP' in hld.artifact_page(h)


def test_hld_inbound_roles_use_the_declared_inverse():
    rules = {r['id']: r for r in ex.RULES['relations']}
    assert all(r.get('inverse') for r in rules.values()), 'every relation declares its inverse wording'
    h = hld.build(read('remote_access'))
    roles = {row[0]: row[2] for row in hld._components(h)['rows']}
    assert 'authenticates users for Remote access gateway' in roles['Identity provider']
    assert 'receives requests from' not in roles['Identity provider']


def test_hld_marks_an_unlinked_piece_and_asks_about_it():
    h = hld.build(read('web_dns'), 'extract')
    labels = [g['label'] for g in h['block']['groups']]
    assert labels == [builders.UNLINKED]
    assert any(el['what'] == 'boundary' for el in h['elements'])
    assert 'How do the root servers connect to the rest of the design?' in h['r']['questions']
    assert not h['provenance']


def test_hld_group_labels_never_exceed_what_the_renderer_draws():
    graph = dict(names={'a': 'A', 'b': 'B'}, kinds={'a': 'app', 'b': 'server'}, title='t',
                 zones=[dict(id='z', label='x' * (builders.GROUP_LABEL_MAX + 1), members=['a'], grounds=['s1'])])
    with pytest.raises(ValueError):
        builders.hld(graph, [dict(id='s1', a='a', b='b', label='connects to', role='path')])


def test_hld_artifact_carries_no_argument_machinery_and_the_report_does():
    h = hld.build(read('web_dns'), 'extract')
    art, rep = hld.artifact_page(h), hld.report_page(h)
    for word in ('STANDS', 'REBUTTED', 'warrant', 'WARRANT'):
        assert word not in art
    assert 'STANDS' in rep and 'REBUTTED' in rep and 'report.html' in art and 'artifact.html' in rep


def test_hld_names_only_draws_nothing_and_says_why():
    h = hld.build(read('names_only'))
    assert h['status'] == 'REBUTTED' and h['block'] is None
    assert 'without guessing' in hld.artifact_page(h)


def test_abbreviations_do_not_cut_a_cited_sentence():
    s = ex.sentences('<p>Servers refer, e.g., a query for example.org is passed on. Next one.</p>')
    assert s == ['Servers refer, e.g., a query for example.org is passed on.', 'Next one.']


# ---- the explainer film template -----------------------------------------------------------------------------------

from reading import film   # noqa: E402


@pytest.mark.parametrize('name,steps', [('fix_charger', 4), ('fix_router', 3), ('fix_pin', 4), ('fix_photos', 4), ('fix_printer', 3)])
def test_film_step_count_is_the_sources_not_a_target(name, steps):
    f = film.build(read(name))
    assert f['status'] == 'STANDS' and f['built'] == 'explainer_film'
    assert len(f['art']['steps']) == steps
    assert len(f['timeline']['scenes']) == len(f['plan'])


def test_film_over_the_ceiling_falls_back_to_a_storyboard_and_asks():
    f = film.build(read('fix_many_steps'))
    assert f['status'] == 'REBUTTED' and f['built'] == 'storyboard_list'
    assert [k for k, v in f['facts'].items() if v] == ['max_steps']
    assert any('two films' in q for q in f['questions'])


def test_film_without_a_fix_draws_nothing():
    f = film.build(read('fix_no_resolution'))
    assert f['built'] == 'open_questions_only'
    assert 'without guessing' in film.artifact_page(f)


@pytest.mark.parametrize('name', ['fix_charger', 'fix_router', 'fix_pin', 'fix_photos', 'fix_printer'])
def test_every_caption_is_the_sources_own_words_and_fits(name):
    f = film.build(read(name))
    chrome = film.boms.load('explainer_film')['chrome']
    for sid, role, c in f['shown']:
        assert argument.verified(c['source'], f['art']['text']), (sid, c['source'])
        assert not film.uncovered(c['text'], c['source']), (sid, c['text'])
        assert film.fits(c['text'], role), (sid, c['text'])
    for x in f['timing']:                                  # eyebrows are declared chrome, nothing else
        assert any(re.fullmatch(re.escape(v).replace(r'\{i\}', r'\d+').replace(r'\{n\}', r'\d+').replace(r'\{condition\}', '.+'), x['eyebrow'])
                   for v in chrome.values()), x['eyebrow']


def test_a_trim_never_keeps_the_condition_and_drops_the_action():
    f = film.build(read('fix_pin'))
    esc = f['art']['escalation']
    assert esc['text'] == 'Contact the support team for a manual identity check'
    assert esc['detail']['text'].startswith('If you do not have access')
    assert not film.dangling(dict(text='If you do not have access', trimmed=[]))
    assert film.dangling(dict(text='If you do not have access', trimmed=['contact the support team']))


def test_a_supplied_caption_must_pass_coverage():
    good = 'Restart the laptop'                                       # shorter, same words
    bad = 'Update the charger firmware on your laptop'                 # plausible, not in the document
    f = film.build(read('fix_charger'), proposals={'step2': good, 'step3': bad})
    assert f['art']['steps'][1]['text'] == good and f['art']['steps'][1].get('supplied')
    assert f['art']['steps'][2]['text'] == 'Check that the charging cable is not damaged'   # the trimmed caption stays
    assert [r['slot'] for r in f['rejected']] == ['step3'] and 'firmware' in f['rejected'][0]['missing']
    assert f['status'] == 'STANDS'


def test_film_scenes_are_timed_for_reading_and_fit_the_renderer():
    for name in ('fix_charger', 'fix_router', 'fix_pin', 'fix_photos', 'fix_printer'):
        f = film.build(read(name))
        assert all(x['words'] / (x['dur'] - 1.0) <= 3 for x in f['timing'])
        tl = f['timeline']
        assert len(tl['scenes']) <= 12 and len(tl['blocks']) <= 24 and len(tl['tracks']) <= 40 and tl['duration'] <= 90


def test_an_organisation_name_in_a_caption_needs_a_reviewer():
    src = read('fix_charger').replace('Restart the laptop completely', 'Restart the laptop completely with Contoso Helper')
    f = film.build(src)
    assert f['facts']['org_names'] and f['built'] == 'open_questions_only'
    assert any('"Contoso"' in q for q in f['questions'])


def test_icons_are_earned_by_a_word_in_the_scene_source():
    for name in ('fix_charger', 'fix_router', 'fix_pin', 'fix_photos', 'fix_printer'):
        f = film.build(read(name))
        assert not f['facts']['icon_grounded']
        for sid, (icon, term, src) in f['icons'].items():
            assert film._term_at(src, term) is not None, (name, sid, term)
            assert icon in film.ICONS['paths']


def test_icon_choice_rules():
    assert film.icon_for('Restart your computer') == ('restart', 'restart')            # a declared leading verb wins
    assert film.icon_for('A shared network printer shows as "offline"') == ('printer', 'printer')   # compound: last word
    assert film.icon_for('What are you seeing when it disconnects?') is None             # no match, no placeholder
    assert film.icon_for('A corrupted print job is blocking the queue') == ('printer', 'print job')   # "lock" is not in "blocking"
    assert film.icon_for('Stop thinking about it') is None                               # nor "ink" in "thinking"


def test_icons_take_the_theme_colour_not_their_own():
    f = film.build(read('fix_charger'), theme={'accent2': '#12a4b6'})
    paths = [b for l in f['timeline']['blocks'] if l['type'] == 'motion_layer' for b in l['blocks'] if b['type'] == 'motion_path']
    assert paths and {p['color'] for p in paths} == {'#12a4b6'} == {f['theme']['accent2']}


# ---- the decision block ----------------------------------------------------------------------------------------------

from reading import decision   # noqa: E402


def test_decision_block_only_where_the_source_states_alternatives():
    assert decision.build(read('fix_router'))['status'] == 'STANDS'
    assert decision.build(read('fix_printer'))['status'] == 'STANDS'
    for name in ('fix_charger', 'fix_pin', 'fix_photos'):                  # steps, not a choice
        d = decision.build(read(name))
        assert d['status'] == 'REBUTTED' and d['facts']['has_branches']
        assert 'steps, not alternatives' in d['questions'][0]


@pytest.mark.parametrize('name', ['fix_router', 'fix_printer'])
def test_every_line_in_the_block_is_verbatim_and_audiences_share_them(name):
    eu, sd = decision.build(read(name), audience='reader'), decision.build(read(name), audience='operator')
    assert eu['cases'] == sd['cases'] and eu['paired'] == sd['paired']      # only the framing differs
    for c in eu['cases']:
        assert argument.verified(c['cond_source'], eu['art']['text'])
        assert any(r == 'do' for r, _ in c['lines'])
        for _, s in c['lines']:
            assert argument.verified(s, eu['art']['text']), s
    assert '>Reported<' in decision.block_html(sd) and '>Reported<' not in decision.block_html(eu)


def test_an_answer_pairs_only_when_it_contains_the_whole_condition():
    d = decision.build(read('fix_router'))
    assert set(d['paired']) == {0, 1}                                        # the third answer never says "limited connectivity"
    assert d['misses'][0][2] == ['limited', 'connectivity']
    assert any('connectivity' in q for q in d['questions'])


def test_a_missing_escalation_is_a_question_not_a_filler():
    assert decision.build(read('fix_router'))['esc'] is None
    assert any('escalated' in q for q in decision.build(read('fix_router'))['questions'])
    assert decision.build(read('fix_printer'))['esc'] is not None


def test_the_block_needs_no_script_and_both_iframe_snippets_carry_it():
    import base64, html as H
    d = decision.build(read('fix_router'))
    assert '<script' not in decision.block_html(d)                           # CSS-only: works with sandbox="" (no scripts)
    sn = decision.snippets(d)
    page = decision.embed_page(d)
    assert base64.b64decode(sn['data_uri'].split('base64,')[1].split('"')[0]).decode() == page
    assert H.unescape(sn['srcdoc'].split('srcdoc="')[1].rsplit('"', 1)[0]) == page
    assert 'sandbox=""' in sn['data_uri'] and 'sandbox=""' in sn['srcdoc']
