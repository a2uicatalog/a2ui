"""Contract sweep runner (I75): Gemini adds data-cb + data-key to a batch of atoms in both twins; code gates the result.

Per batch, the Python renderer of each atom (plus its own helpers) and its GAS twin go to Gemini with the contract
spec and the atom's sample, kind and key hint. Edits are exact find/replace (each find must occur once). The gate is
tests/test_contract_sweep.py with A2UI_SWEEP_ATOMS=<batch>, plus the atoms' own tests and the cross-atom checks;
failures go back for up to --rounds. An atom still failing at the end is put back and left pending. Atoms that pass
are marked keyed in tests/fixtures/contract_sweep.json.

    python scripts/contract_keys.py run --atoms a,b,c [--rounds 3]
    python scripts/contract_keys.py run-all [--size 8] [--rounds 3] [--atoms a,b,c]
    python scripts/contract_keys.py rebase-sha [--atoms a,b,c]

run-all commits once per batch that keyed something; nothing is ever pushed.
"""
import argparse
import glob
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = 'renderers/web_article.py'
GASDIR = 'apps-script-surface/gas-wired-renderer'
FIX = 'tests/fixtures/contract_sweep.json'
UNREAD = 'tests/schema_fields_unread_baseline.json'
PYTHON = '/home/ck/a2ui/.venv/bin/python'
GEMINI = ('type=gemini-enterprise;project=179011472094;region=global;model=gemini-3.8-flash;'
          'account=a2uitestbench@krygier.co.uk;thinking=low')
TRAILER = 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'
ALWAYS = ['tests/test_gas_twins.py', 'tests/test_surface_parity.py', 'tests/test_schema_fields_read.py']

SPEC = """BUILD CONTRACT (owner-approved, a2uicatalog, MIT). Add it to each atom below, in BOTH its Python renderer and its GAS
(Apps Script) twin:
- data-cb="<kind>" on each element that shows ONE DATA ITEM of the atom's collection (a row, a card, a step, a tile, a
  bar, a node...), and on that item's separate text label if it has one (kind "label"). Use the kind given for the atom.
- data-key="<key>" right after data-cb on the same element: the item's stable identity from the data (the key hint
  names the field: its id, else its name/label/title); escape it with the SAME escape helper the surrounding code uses for
  attribute text. Keys must be unique among the items of one render: where two items could share a name, keep the name
  (duplicates are the author's problem) but never use the index if any identity field exists. A label uses its item's key.
- Put ` data-cb="..." data-key="..."` as the FIRST attributes of the existing opening tag of that element (right after
  the tag name). Add nothing else: no class, no style, no wrapper elements, no reordering, no reformatting. Removing
  every ` data-cb="..."` and ` data-key="..."` must give back today's bytes exactly (a test checks a recorded hash).
- Where Python and GAS emit the same bytes today they must still do (a test compares them).
- Do not touch atoms not listed. Do not edit tests.
- NEVER key an element by a value the page must keep secret or that the user is meant to find (a quiz answer, a hidden
  card's title, a password): if the only identity is such a value, key by position ("1", "2"...) and say so in notes.
- The key must come out the same in Python and GAS for ANY input (numbers, null, nested objects, hostile strings): convert
  with the twin's own string rules (Python str() vs JS String() differ for floats, None/null, booleans) using the helpers the
  surrounding code already uses for that atom's text."""
SPEC_SINGLE = """BUILD CONTRACT (owner-approved, a2uicatalog, MIT). Each atom below shows ONE visual unit. Add the contract to
each, in BOTH its Python renderer and its GAS (Apps Script) twin:
- data-cb="<kind>" on the ROOT element of the atom's render (the outermost element it emits; if it emits several
  siblings, the one that carries the content). The kind is ALWAYS "node" for the root of a single-unit atom (never tile, bar, link,
  branch or label), whatever kind the atom header shows.
- data-key="<key>" right after data-cb on the same element: the unit's identity from the data (the key hint names the
  field); where the block has no identity field the key hint is the atom type itself, written as a literal string.
  Escape a data value with the SAME escape helper the surrounding code uses for attribute text.
- Put ` data-cb="..." data-key="..."` as the FIRST attributes of the existing opening tag of that element (right after
  the tag name). Add nothing else: no class, no style, no wrapper elements, no reordering, no reformatting. Removing
  every ` data-cb="..."` and ` data-key="..."` must give back today's bytes exactly (a test checks a recorded hash).
- Where Python and GAS emit the same bytes today they must still do (a test compares them).
- Do not touch atoms not listed. Do not edit tests. Edit only what this atom alone renders: a helper that other atoms
  also call stays untouched (put the attributes where this atom's own code builds the root tag).
- NEVER key by a value the page must keep secret or that the user is meant to find (a quiz answer, a password).
- The key must come out the same in Python and GAS for ANY input (numbers, null, nested objects, hostile strings): convert
  with the twin's own string rules (Python str() vs JS String() differ for floats, None/null, booleans) using the helpers the
  surrounding code already uses for that atom's text.
- USE THE EXISTING KEY HELPERS: Python `_ck(value, "atom_name")` and GAS `_ckey(value, 'atom_name')` (they return the value
  if it is a non-empty string, else the atom-name literal, already escaped). Write data-key="{_ck(b.get("field"), "atom_name")}"
  in Python f-strings (or the concatenation equivalent) and the same through _ckey in GAS. Never key by a secret or hidden
  value (quiz answer, password, hidden reveal): use _ck(None, "atom_name") / _ckey(null, 'atom_name')."""
FORMAT = """Answer with ONE JSON object and nothing else (no code fences):
{"edits": [{"atom": "<the atom this edit keys>", "file": "<path as given in a FILE header>", "find": "<exact text copied from that file>", "replace": "<new text>"}],
 "notes": "<per atom: element keyed and key field; any atom you could not key and why>"}
Each find must be copied character for character and occur EXACTLY ONCE in its file (include enough context). Edits
apply in order; keep them minimal."""


def _wa():
    sys.path.insert(0, ROOT)
    import renderers.web_article as wa
    return wa


def unwrap(f):
    """The function under any decorator closures."""
    for _ in range(6):
        cells = [c.cell_contents for c in (getattr(f, '__closure__', None) or []) if inspect.isfunction(getattr(c, 'cell_contents', None))]
        if not cells:
            break
        f = cells[0]
    return f


def py_def(text, name, occ=0):
    """The occ-th top-level `def name(` in text (a name defined twice: the later one is the live one)."""
    ms = list(re.finditer(r'^def %s\(' % re.escape(name), text, re.M))
    if len(ms) <= occ:
        return ''
    m = ms[occ]
    n = re.search(r'^(?=def |class |@|[A-Za-z_][\w.\[\]\'"]* *=|_RENDERERS|for |if )', text[m.end():], re.M)
    return text[m.start(): m.end() + (n.start() if n else 0)]


def _where(f):
    """(file relative to the repo, occurrence index of `def name(` in it) for the LIVE function object."""
    path = os.path.relpath(inspect.getsourcefile(f))
    line = inspect.getsourcelines(f)[1]
    text = open(path).read()
    occ = sum(1 for m in re.finditer(r'^def %s\(' % re.escape(f.__name__), text, re.M) if text.count('\n', 0, m.start()) + 1 < line)
    return path, occ


def py_names(atom):
    """The atom's live renderer and its own helpers, as (file, occurrence, name); text is read from the file each round."""
    wa = _wa()
    pysrc = open(PY).read()
    f = unwrap(wa._RENDERERS[atom])
    try:
        body = inspect.getsource(f)
    except (OSError, TypeError):
        return []
    n_parts, seen = 1, {f.__name__}
    names = [(*_where(f), f.__name__)]
    for h in dict.fromkeys(re.findall(r'\b(_[a-z][a-z0-9_]*)\(', body)):
        g = getattr(wa, h, None)
        if h in seen or not inspect.isfunction(g) or pysrc.count(h + '(') > 3:   # a helper other atoms call stays out: editing it moves their bytes
            continue
        try:
            s = inspect.getsource(g)
        except (OSError, TypeError):
            continue
        if s.count('\n') <= 160 and '<' in s:
            n_parts += 1; seen.add(h); names.append((*_where(g), h))
        if n_parts > 7:
            break
    return names


def gas_files():
    return {os.path.join(GASDIR, f): open(os.path.join(GASDIR, f)).read() for f in os.listdir(GASDIR) if f.endswith('.gs')}


GAS_END = r"^(?:_RENDERERS\[|function |var |// ───)"


def _gas_block(text, atom):
    ms = list(re.finditer(r"^_RENDERERS\[['\"]%s['\"]\]\s*=" % re.escape(atom), text, re.M))
    if not ms:
        return None
    m = ms[-1]
    rest = text[m.end():]
    n = re.search(GAS_END, rest, re.M)
    return text[m.start(): m.end() + (n.start() if n else min(len(rest), 20000))]


def gas_names(atom, gas=None):
    """(file, [helper names]) for the atom's GAS block; the text is read from the file as it is now, each round."""
    gas = gas if gas is not None else gas_files()
    allgas = '\n'.join(gas.values())
    for path, s in gas.items():
        body = _gas_block(s, atom)
        if body is None:
            continue
        helpers = []
        for h in dict.fromkeys(re.findall(r'\b(_[a-zA-Z][A-Za-z0-9_]*)\(', body)):
            d = re.search(r'^function %s\(' % re.escape(h), s, re.M)
            if not d or allgas.count(h + '(') > 3:
                continue
            e = re.search(GAS_END, s[d.end():], re.M)
            src = s[d.start(): d.end() + (e.start() if e else 0)]
            if src.count('\n') <= 160 and '<' in src:
                helpers.append(h)
        return path, helpers
    return None, []


def gas_text(text, atom, helpers):
    body = _gas_block(text, atom)
    if body is None:
        return ''
    out = [body]
    for h in helpers:
        d = re.search(r'^function %s\(' % re.escape(h), text, re.M)
        if d:
            e = re.search(GAS_END, text[d.end():], re.M)
            out.append(text[d.start(): d.end() + (e.start() if e else 0)])
    return '\n'.join(out)


def related(atoms):
    """The test files that name one of these atoms (quoted), plus the cross-atom checks; {file: [atoms it names]}."""
    out = {}
    for t in sorted(glob.glob('tests/test_*.py')):
        if t.endswith('test_contract_sweep.py') or t.endswith('test_contract_keys.py'):
            continue
        s = open(t).read()
        hit = [x for x in atoms if re.search(r'["\']%s["\']' % re.escape(x), s)]
        if hit or t in ALWAYS:
            out[t] = hit or list(atoms)
    return out


def accept_now_read(atoms, detail, unread=UNREAD):
    """test_schema_fields_read says "now read, so delete from <baseline>: {atom: [fields]}" when a renderer starts reading a
    declared field: an improvement the test asks to record. Do it for this batch's atoms only; True if anything changed."""
    m = re.search(r'now read, so delete from tests/schema_fields_unread_baseline.json:\s*(?:E\s+)?(\{.*?\n(?:E\s+)?\})', detail, re.S)
    if not m:
        return False
    try:
        got = json.loads(re.sub(r'(?m)^E\s+', '', m.group(1)))   # the E prefix is pytest's
    except ValueError:
        return False
    base = json.load(open(unread)); changed = False
    for a, fields in got.items():
        if a in atoms and a in base:
            base[a] = [f for f in base[a] if f not in fields]
            if not base[a]:
                del base[a]
            changed = True
    if changed:
        json.dump(base, open(unread, 'w'), indent=1, sort_keys=True); open(unread, 'a').write('\n')
    return changed


def _test_body(f, name):
    """The test's name, then the source of its function in file f when there is one (a name like test_body names its atom)."""
    try:
        text = open(f).read()
    except OSError:
        return name
    m = re.search(r'^(?:async )?def %s\(' % re.escape(name), text, re.M)
    if not m:
        return name
    start = text.find('\n', m.end()) + 1 or len(text)
    n = re.search(r'^(?=[^\s)])', text[start:], re.M)   # the next line at column 0 that is not the signature's close
    return name + '\n' + text[m.start():start + (n.start() if n else len(text))]


def attribute_failures(out, atoms, rel, returncode=1, locate=None):
    """The atoms a pytest run's failures belong to. A failure is pinned to the atom its test id or line names, else (for a
    cross-atom check) to the atoms its message names, else to the atoms its file names; a collection or syntax error with no
    FAILED line fails the whole batch (it once passed as "no failures"). A Python syntax error that locate(file, line) can
    place inside one atom's code fails that atom alone: every other error in the run is its consequence."""
    if locate:
        at = {locate(f, int(n)) for f, n in re.findall(r'File "([^"]+)", line (\d+)\n(?:E?\s+.*\n)*?E?\s*(?:Indentation|Syntax|Tab)Error', out)}
        at = {a for a in at if a}
        if at:
            return at
    fails = set()
    for line in re.findall(r'^(?:FAILED|ERROR) .*$', out, re.M):
        named = [x for x in atoms if re.search(r'[\[\-]%s\]|\b%s\b' % (re.escape(x), re.escape(x)), line)]
        if named:
            fails.update(named); continue
        f = line.split()[1].split('::')[0]
        e_named = [x for x in atoms if re.search(r'(?m)^E .*\b%s\b' % re.escape(x), out)]
        if f in ALWAYS and e_named:   # a cross-atom check names its atoms in the message (schema fields, parity, twins)
            fails.update(e_named); continue
        body = _test_body(f, line.split()[1].split('::')[-1].split('[')[0].split(' ')[0])
        b_named = [x for x in atoms if re.search(r'["\']%s["\']|\b_render_%s\b|\btest_%s\b' % ((re.escape(x),) * 3), body)]
        if b_named:   # the failing test's own code names its atoms: a file that names the whole batch must not fail it all
            fails.update(b_named); continue
        fails.update(rel.get(f, atoms) if 'test_contract_sweep' not in f else [])
    if returncode != 0 and not fails:
        fails = set(atoms)
    return fails


def gate(atoms, locate=None, fast=False):
    """The sweep gate for these atoms, then their own tests and the cross-atom checks. fast: the sweep and the cross-atom
    checks only (a repair round); the atoms' own test files run once, on the edits that survive."""
    subprocess.run([PYTHON, 'scripts/gen_mcp_apps_bundle.py'], capture_output=True)
    rel = {f: a for f, a in related(atoms).items() if not fast or f in ALWAYS}
    r = subprocess.run(['timeout', '1500', 'systemd-run', '--user', '--scope', '-q', '-p', 'MemoryMax=3G', '-p', 'MemorySwapMax=0', '-E',
                        'A2UI_SWEEP_ATOMS=' + ','.join(atoms), PYTHON, '-m', 'pytest', '-q', '--no-header', '-p', 'no:cacheprovider',
                        '-k', 'not registered and not well_formed', 'tests/test_contract_sweep.py'] + list(rel), capture_output=True, text=True)
    out = r.stdout + r.stderr
    fails = attribute_failures(out, atoms, rel, r.returncode, locate)
    detail = '\n'.join(l for l in out.splitlines() if l.startswith(('E ', 'FAILED', 'ERROR')))[:10000]
    if 'now read, so delete from' in detail and accept_now_read(atoms, detail):
        return gate(atoms, locate, fast)   # the baseline now records the newly read field: judge the batch again
    if r.returncode != 0 and not detail:
        detail = '\n'.join('E ' + l for l in out.splitlines()[-25:])
    summary = ([l.strip('= ') for l in out.splitlines() if re.search(r'\d+ (?:passed|failed|error)', l)] or ['(no summary)'])[-1]
    return sorted(fails), summary, detail


def apply(edits, files, scope=None):
    """Apply find/replace edits. A find must occur once; one that repeats is applied inside the atom's live definition
    (scope(atom, file, text) -> spans) when it occurs once there. Returns (applied count, refusals, files touched)."""
    refused, done, touched = [], 0, set()
    for e in edits:
        f = e.get('file', '')
        if f not in files:
            refused.append('file not allowed: %r' % f); continue
        s = open(f).read()
        c = s.count(e.get('find', ''))
        if c > 1 and scope:
            for a0, b0 in scope(e.get('atom'), f, s):
                if s[a0:b0].count(e['find']) == 1:
                    s = s[:a0] + s[a0:b0].replace(e['find'], e['replace'], 1) + s[b0:]
                    open(f, 'w').write(s); done += 1; touched.add(f); c = -1
                    break
            if c == -1:
                continue
        if c != 1 or not e.get('find'):
            refused.append('%s: find occurs %d times: %r' % (f, c, e.get('find', '')[:120])); continue
        open(f, 'w').write(s.replace(e['find'], e['replace'], 1)); done += 1; touched.add(f)
    return done, refused, touched


def parse_reply(text):
    """The reply's JSON object; fences are stripped and raw newlines inside strings are accepted (Gemini writes them)."""
    return json.loads(re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip()), strict=False)


def call_gemini(ge, cfg, prompt, waits=(60, 120, 240, 240), timeout=120):
    """ge.call_full with a per-call timeout (one retry on a timeout, then RuntimeError so the batch is put back); it waits
    longer between attempts when the endpoint says HTTP 429 or 5xx (a large batch hits quota)."""
    timeouts = 0
    for w in waits + (None,):
        try:
            return ge.call_full(cfg, prompt, max_tokens=65536, timeout=timeout)
        except RuntimeError as e:
            if w is None or not re.match(r'HTTP (429|5\d\d)', str(e)):
                raise
            print('gemini: %s; waiting %ds' % (str(e)[:40], w), flush=True)
            time.sleep(w)
        except OSError as e:   # socket.timeout, URLError
            timeouts += 1
            if timeouts > 1:
                raise RuntimeError('gemini: timed out twice (%ds): %s' % (timeout, str(e)[:60]))
            print('gemini: timeout after %ds; retrying once' % timeout, flush=True)


def run_batch(cfg_str, atom_list, rounds=3, keep_failing=False, log_dir=None):
    """One batch; returns the atoms that failed (they are left pending, their edits put back)."""
    sys.path.insert(0, os.path.join(ROOT, 'scripts'))
    import gemini_endpoint as ge
    cfg = ge.parse(cfg_str)
    fx = json.load(open(FIX))
    atoms = [x for x in atom_list if x in fx]
    log_dir = log_dir or os.path.join(tempfile.gettempdir(), 'contract_keys_runs')
    os.makedirs(log_dir, exist_ok=True)
    log = os.path.join(log_dir, time.strftime('%Y%m%d-%H%M%S') + '-' + atoms[0] + '.jsonl')
    gas = gas_files()
    files, meta = {}, {}
    for t in atoms:
        gp, gh = gas_names(t, gas)
        pn = py_names(t)
        for f, _, _ in pn:
            files[f] = 1
        if gp:
            files[gp] = 1
        meta[t] = (pn, gp, gh)
    single = all(fx[t].get('class') == 'S' for t in atoms)

    def sources(only):
        out = []
        fallback = ('(when that field is empty or missing, the key is the atom type as a literal string)' if single
                    else '(fall back to the name/label/title field when the item has no id)')
        for t in only:
            pn, gp, gh = meta[t]
            gtxt = open(gp).read() if gp else ''
            pys = '\n'.join('=== FILE %s (function %s, the live definition, as the file is NOW) ===\n%s' % (f, n, py_def(open(f).read(), n, occ)) for f, occ, n in pn)
            out.append('##### ATOM %s  kind=%s  label kind=label  key hint=%s %s\nSAMPLE BLOCK: %s\n%s\n=== FILE %s (this atom\'s GAS block only, as the file is NOW) ===\n%s' % (
                t, fx[t]['kind'], fx[t]['key'], fallback, json.dumps(fx[t]['block'], ensure_ascii=False), pys, gp, gas_text(gtxt, t, gh)))
        return out

    def scope(atom, f, text):
        """Spans of the atom's live definitions in file f, as the text is now."""
        if atom not in meta:
            return []
        pn, gp, gh = meta[atom]
        out = []
        for pf, occ, n in pn:
            if pf == f:
                d = py_def(text, n, occ)
                if d:
                    i = [m.start() for m in re.finditer(r'^def %s\(' % re.escape(n), text, re.M)][occ]
                    out.append((i, i + len(d)))
        if gp == f:
            g = gas_text(text, atom, [])
            i = text.rfind(g) if g else -1
            if i >= 0:
                out.append((i, i + len(g)))
        return out

    def locate(f, line):
        """The batch atom whose live Python definition holds this line of file f (None if no atom's)."""
        try:
            f = os.path.relpath(f)
            text = open(f).read()
        except OSError:
            return None
        pos = sum(len(l) + 1 for l in text.split('\n')[:line - 1])
        for t in atoms:
            for a0, b0 in scope(t, f, text):
                if a0 <= pos < b0:
                    return t
        return None

    files[UNREAD] = 1   # restored with the renderers if the batch is put back
    snapshot = {f: open(f).read() for f in files}
    history, total, applied = [], {'prompt': 0, 'answer': 0, 'thinking': 0}, []
    calls = 0
    t0 = time.time()
    fails, summary, detail = gate(atoms, locate, fast=True)
    for rnd in range(1, rounds + 1):
        if not fails:
            break
        todo = fails
        p = '\n\n'.join([SPEC_SINGLE if single else SPEC, 'ATOMS IN THIS CALL: ' + ', '.join(todo)] + sources(todo) +
                        (['=== THE PREVIOUS ROUND: your edits were applied (the files above already include them); the gate then said ===\n' + history[-1]] if history else []) + [FORMAT])
        try:
            r = call_gemini(ge, cfg, p)
        except RuntimeError:   # the endpoint gave up: put every file back before the batch ends
            for f, s0 in snapshot.items():
                open(f, 'w').write(s0)
            raise
        calls += 1
        u = r['usage']
        for k, uk in (('prompt', 'promptTokenCount'), ('answer', 'candidatesTokenCount'), ('thinking', 'thoughtsTokenCount')):
            total[k] += u.get(uk, 0) or 0
        if r['finish'] == 'MAX_TOKENS':
            print('round %d: cut off at the output limit' % rnd); break
        try:
            ans = parse_reply(r['reply'])
        except ValueError as e:
            print('round %d: reply not valid JSON (%s)' % (rnd, e), flush=True); history.append('Your reply was not valid JSON (%s); nothing was applied.' % e); continue
        edits = [e for e in ans.get('edits', []) if e.get('atom') in todo]
        done, refused, _ = apply(edits, files, scope)
        applied += edits
        fails, summary, detail = gate(atoms, locate, fast=True)
        print('round %d: %d edits, %d refused; gate %s; failing %s' % (rnd, done, len(refused), summary, fails), flush=True)
        with open(log, 'a') as fh:
            fh.write(json.dumps({'round': rnd, 'applied': done, 'refused': refused, 'fails': fails, 'summary': summary, 'detail': detail[:4000], 'notes': ans.get('notes', ''), 'usage': u}) + '\n')
        history.append('Refused edits:\n%s\n\nGate: %s\n%s' % ('\n'.join(refused) or '(none)', summary, detail))
    if len(fails) < len(atoms):   # the full gate, once, on what the repair rounds left passing
        f_full, summary, detail = gate(atoms, locate)
        fails = sorted(set(fails) | set(f_full))
        print('full gate %s; failing %s' % (summary, fails), flush=True)
        with open(log, 'a') as fh:
            fh.write(json.dumps({'round': 'full', 'fails': fails, 'summary': summary, 'detail': detail[:4000]}) + '\n')
    keep = [t for t in atoms if t not in fails]
    if fails and not keep_failing:   # put the files back, then replay only the passing atoms' edits, in order, and gate them again
        for f, s0 in snapshot.items():
            open(f, 'w').write(s0)
        apply([e for e in applied if e.get('atom') in keep], files, scope)
        f2, summary, _ = gate(keep, locate) if keep else ([], '', '')
        if f2:
            for f, s0 in snapshot.items():
                open(f, 'w').write(s0)
            keep = []
        print('failing atoms left pending: %s; kept: %s' % (fails, keep))
    fx = json.load(open(FIX))
    for t in keep:
        fx[t]['status'] = 'keyed'
    json.dump(fx, open(FIX, 'w'), indent=1, ensure_ascii=False)
    fails = [t for t in atoms if t not in keep]
    print('result: keyed %d of %d; gemini calls %d; tokens %s; %.0fs; log %s' % (len(atoms) - len(fails), len(atoms), calls, total, time.time() - t0, log))
    return fails


def run_all(cfg, size, rounds, only=None):
    """Every pending atom in batches, one batch at a time, one commit per batch that keyed something."""
    fx = json.load(open(FIX))
    todo = [n for n, v in sorted(fx.items()) if v['status'] == 'pending' and (only is None or n in only)]
    print('%d pending atoms, batches of %d' % (len(todo), size), flush=True)
    t0 = time.time()
    for i in range(0, len(todo), size):
        b = todo[i:i + size]
        r = subprocess.run([PYTHON, os.path.join(ROOT, 'scripts/contract_keys.py'), 'run', '--gemini', cfg, '--atoms', ','.join(b), '--rounds', str(rounds)],
                           capture_output=True, text=True)
        kept = [n for n, v in json.load(open(FIX)).items() if v['status'] == 'keyed' and n in b]
        if kept:
            commit_batch(kept)
        lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
        last = lines[-2:] if any(l.startswith('result:') for l in lines[-2:]) else ['CRASHED:'] + lines[-12:]   # show a traceback in full
        print('[%4.0fs] batch %d: %s' % (time.time() - t0, i // size + 1, ' / '.join(last)), flush=True)
    fx = json.load(open(FIX))
    print('DONE: keyed %d of %d sweep atoms' % (sum(v['status'] == 'keyed' for v in fx.values()), len(fx)), flush=True)


def commit_batch(kept):
    paths = ['renderers', 'apps-script-surface', FIX, 'tests/fixtures/contract_registry.json', UNREAD,
             'public-play/renderer-bundle.html', 'public/surfaces/mcp-apps/renderer-bundle.html']
    subprocess.run(['git', '-C', ROOT, 'add'] + paths, check=True)
    subprocess.run(['git', '-C', ROOT, 'commit', '-q', '-m', 'Contract sweep: data-cb + data-key on ' + ', '.join(kept) + ' (Gemini, gated)\n\n' + TRAILER], check=True)


def rebase_sha(only=None):
    """Record both twins' baselines in STRIPPED form from the CURRENT tree (run it on a clean tree) into the fixture, for
    the given atoms or all; list atoms whose clean output already carries data-key or data-cb."""
    sys.path.insert(0, os.path.join(ROOT, 'tests')); sys.path.insert(0, ROOT)
    from test_motion_atoms import _norm
    from test_contract_sweep import _gas_isolated, _strip, _py_fresh
    import scripts.gen_mcp_apps_bundle as gen
    fx = json.load(open(FIX))
    core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", gen.build_bundle(), re.S) if "a2ui-core" in b[:300]][0]
    names = [n for n in sorted(fx) if only is None or n in only]
    gas = _gas_isolated(core, [fx[n]['block'] for n in names])
    native = {}
    for n, g in zip(names, gas):
        p = _py_fresh(fx[n]['block'])
        fx[n]['py_sha'] = hashlib.sha256(_norm(_strip(p)).encode()).hexdigest()
        fx[n]['gas_sha'] = hashlib.sha256(_norm(_strip(g)).encode()).hexdigest()
        hits = sorted(set(re.findall(r' (data-key|data-cb)=', p + g)))
        if hits:
            native[n] = hits
    json.dump(fx, open(FIX, 'w'), indent=1, ensure_ascii=False)
    print('baselines recorded for %d atoms; native contract-like attributes in clean output: %s' % (len(names), native))


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = a.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run', help='one batch')
    r.add_argument('--gemini', default=GEMINI); r.add_argument('--atoms', required=True); r.add_argument('--rounds', type=int, default=3)
    r.add_argument('--keep', action='store_true', help='debug: leave failing edits in place'); r.add_argument('--log')
    ra = sub.add_parser('run-all', help='every pending atom in batches, one commit per good batch')
    ra.add_argument('--gemini', default=GEMINI); ra.add_argument('--size', type=int, default=8); ra.add_argument('--rounds', type=int, default=3)
    ra.add_argument('--atoms', help='only these pending atoms')
    rs = sub.add_parser('rebase-sha', help='record pre-sweep baselines from the current tree')
    rs.add_argument('--atoms')
    o = a.parse_args(argv)
    os.chdir(ROOT)
    if o.cmd == 'run':
        return 1 if run_batch(o.gemini, o.atoms.split(','), o.rounds, o.keep, o.log) else 0
    if o.cmd == 'run-all':
        run_all(o.gemini, o.size, o.rounds, set(o.atoms.split(',')) if o.atoms else None)
        return 0
    rebase_sha(set(o.atoms.split(',')) if o.atoms else None)
    return 0


if __name__ == '__main__':
    sys.exit(main())
