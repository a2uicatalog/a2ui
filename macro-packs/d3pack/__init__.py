"""d3 macro pack: macros with the input contracts of the matching a2uicatalog d3 atoms (where an atom exists), drawing deterministic SVG in pure Python and emitting
Basic Catalog A2UI 1.0 messages. PACK maps macro name -> function; DEMOS maps demo key -> (macro name, synthetic params); card() builds a surface."""
from . import common
from .common import atom_card
from .sunburst import sunburst
from .chord import chord_diagram
from .arc import arc_diagram
from .heatmap_calendar import heatmap_calendar
from .pack import circle_pack
from .registry_hierarchy import PACK_HIERARCHY
from .registry_stats import PACK_STATS
from .registry_flow import PACK_FLOW
from .registry_networks import PACK_NETWORKS
from .registry_fields import PACK_FIELDS
from .basic_charts import bar_chart, line_chart
from .connect_four import connect_four
from .brick_build import brick_build
from .svg_lab import svg_lab
from .availability import availability
from .latency_ledger import latency_ledger
from .gauge_sla import gauge_sla
PACK = {'sunburst': sunburst, 'chord_diagram': chord_diagram, 'arc_diagram': arc_diagram, 'heatmap_calendar': heatmap_calendar, 'circle_pack': circle_pack}
for _g in (PACK_HIERARCHY, PACK_STATS, PACK_FLOW, PACK_NETWORKS, PACK_FIELDS): PACK.update(_g)
PACK.update({'bar_chart': bar_chart, 'line_chart': line_chart, 'connect_four': connect_four, 'brick_build': brick_build, 'svg_lab': svg_lab, 'availability': availability, 'latency_ledger': latency_ledger, 'gauge_sla': gauge_sla})
# demo key -> macro name, where they differ
_DEMO_MACRO = {'gauge_sla_warning': 'gauge_sla', 'gauge_sla_plain': 'gauge_sla', 'gauge_sla_bands': 'gauge_sla', 'contour_points': 'contour_plot', 'venn_two': 'venn', 'histogram_ridge': 'histogram', 'brick_house': 'brick_build', 'availability_week': 'availability', 'availability_day': 'availability', 'latency_image': 'latency_ledger', 'latency_stashed': 'latency_ledger', 'latency_buttons': 'latency_ledger', 'latency_model': 'latency_ledger', 'latency_html': 'latency_ledger', 'brick_pyramid': 'brick_build', 'brick_stairs': 'brick_build', 'connect_four_midgame': 'connect_four'}
def _demos():
    import importlib
    out = {}
    for g in ('hierarchy', 'stats', 'flow', 'networks', 'fields', 'bricks', 'booking', 'latency', 'indicators'):
        for k, p in importlib.import_module(f'{__name__}.demos_{g}').DEMOS.items():
            macro = _DEMO_MACRO.get(k, k)
            if macro not in PACK: raise KeyError(f'demo {k!r} of group {g} names no macro {macro!r}')
            out[k] = (macro, p)
    return out
class MacroError(ValueError):
    """A macro could not produce a drawing for this input: bad parameters, a policy violation, a crash or the time budget. Only this (a ValueError) escapes card()."""
TIME_BUDGET_S = 5.0
import os as _os
MEMORY_LIMIT_BYTES = int(_os.environ.get('D3PACK_MEMORY_LIMIT_BYTES', 2 << 30))   # headroom ABOVE the address space the process already has
def _isolated(fn, kwargs, budget, mem=MEMORY_LIMIT_BYTES):
    """Run fn(**kwargs) in a forked child with a wall-clock limit (killed, not interrupted) and an address-space limit. Works from any thread and stops runaway C code too.
    Results come back pickled over a pipe; exceptions come back by class name and text."""
    import multiprocessing, os, pickle, resource, time
    _t0 = time.perf_counter(); ctx = multiprocessing.get_context('fork'); rd, wr = ctx.Pipe(duplex=False)
    def child():
        try:
            try: base = int(open('/proc/self/statm').read().split()[0]) * os.sysconf('SC_PAGE_SIZE')   # address space the forked child already shares with its parent
            except (OSError, ValueError): base = 0
            resource.setrlimit(resource.RLIMIT_AS, (base + mem, base + mem)); _t = time.perf_counter(); _r = fn(**kwargs); out = ('ok', _r, (time.perf_counter() - _t) * 1000)
        except BaseException as e: out = ('err', type(e).__name__, str(e)[:300])
        try: wr.send_bytes(pickle.dumps(out))
        finally: os._exit(0)
    proc = ctx.Process(target=child, daemon=True); proc.start(); wr.close()
    try:
        if not rd.poll(budget): proc.kill(); proc.join(2); raise TimeoutError('time budget exceeded')
        try: msg = pickle.loads(rd.recv_bytes())
        except EOFError: proc.join(2); raise MemoryError('the macro process ended without a result (memory limit or crash)')
    finally:
        rd.close()
        if proc.is_alive(): proc.kill()
        proc.join(2)
    if msg[0] == 'ok':
        _tl.timing = {'total_ms': (time.perf_counter() - _t0) * 1000, 'child_ms': msg[2], 'isolated': True}; return msg[1]
    name, text = msg[1], msg[2]
    if name == 'SvgPolicyError': raise common.SvgPolicyError(text)
    if name in ('ValueError', 'MacroError'): raise ValueError(text)
    if name == 'MemoryError': raise MemoryError(text)
    raise RuntimeError(f'{name}: {text}')
import threading as _threading, time as _time
_tl = _threading.local()
def last_timing():
    """Timing of the most recent call() in THIS thread: total_ms (as the caller saw it), child_ms (compute inside the macro) and whether it ran isolated. The difference is the cost of the isolation (fork, pipe, pickle)."""
    return dict(getattr(_tl, 'timing', {}) or {})
def _run_with_budget(fn, kwargs, budget, isolate=True):
    if isolate and budget: return _isolated(fn, kwargs, budget)
    t = _time.perf_counter(); r = fn(**kwargs); ms = (_time.perf_counter() - t) * 1000; _tl.timing = {'total_ms': ms, 'child_ms': ms, 'isolated': False}; return r
def call(name, params, budget=TIME_BUDGET_S, isolate=True):
    """Run macro `name` safely. Unknown options are dropped and noted (a router or model may send fields the macro does not know); the run has a time budget; every failure
    other than a plain ValueError becomes a MacroError that names the macro and the exception class, never a stack trace. Returns the macro's {variant: Result, '_default': name}."""
    import inspect
    if name not in PACK: raise MacroError(f'unknown macro {name!r}')
    if not isinstance(params, dict): raise MacroError(f'{name}: parameters must be an object')
    fn = PACK[name]; sig = inspect.signature(fn); has_kw = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())
    ok = {k: v for k, v in params.items() if isinstance(k, str) and (has_kw or k in sig.parameters)}
    extra = sorted(str(k) for k in params if not isinstance(k, str) or k not in sig.parameters)   # keys the macro does not declare, whether it tolerates them or not
    try: res = _run_with_budget(fn, ok, budget, isolate)
    except common.SvgPolicyError as e: raise MacroError(f'{name}: output policy violation ({e})') from e
    except ValueError as e: raise MacroError(f'{name}: {e}') from e
    except TimeoutError as e: raise MacroError(f'{name}: time budget of {budget:g} s exceeded') from e
    except RecursionError as e: raise MacroError(f'{name}: input too deeply nested') from e
    except MemoryError as e: raise MacroError(f'{name}: memory limit reached') from e
    except Exception as e: raise MacroError(f'{name}: failed on this input ({type(e).__name__})') from e
    for k, r in res.items():
        if k == '_default': continue
        said = ' '.join(r['notes']); missing = [x for x in extra if x not in said]    # options the macro already named in its own notes are not repeated
        if missing:
            msg = 'Unknown option' + ('s' if len(missing) > 1 else '') + ' ignored: ' + ', '.join(common.plain(x)[:30] for x in missing) + '.'
            r['notes'] = list(r['notes']) + [msg]; r['alt'] = r['alt'] + (' ' if ' Notes: ' in r['alt'] else ' Notes: ') + msg
    return res
def card(name, title, params, surface_id='atom', budget=TIME_BUDGET_S, isolate=True):
    """Run macro `name` with `params` (the atom's own input), return (createSurface, {variant: updateDataModel}, results). Raises MacroError on any failure."""
    res = call(name, params, budget, isolate); default = res.pop('_default'); create, updates = atom_card(common.plain(title)[:80], res, default, surface_id); return create, updates, res
def note_card(title, reason, surface_id='atom'):
    """A Basic-only surface (Card > Column > Text, Text) that says why nothing was drawn. The reader gets a readable sentence instead of a blank or a stack trace."""
    comps = [{'id': 'root', 'component': 'Card', 'child': 'col'}, {'id': 'col', 'component': 'Column', 'children': ['title', 'note']},
             {'id': 'title', 'component': 'Text', 'text': common.plain(title)[:80]}, {'id': 'note', 'component': 'Text', 'variant': 'caption', 'text': 'No picture was drawn: ' + common.plain(reason)[:300]}]
    return {'version': '1.0', 'createSurface': {'surfaceId': surface_id, 'catalogId': common.BASIC, 'components': comps}}
def card_or_note(name, title, params, surface_id='atom', budget=TIME_BUDGET_S, isolate=True):
    """Like card(), but a failure returns (note surface, {}, {'error': reason}) so a service can always answer."""
    try: return card(name, title, params, surface_id, budget, isolate)
    except MacroError as e: return note_card(title, str(e), surface_id), {}, {'error': str(e)}
