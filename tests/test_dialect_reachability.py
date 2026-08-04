"""Nothing the wired dialect lets you DECLARE may be inert.

DECLARED 2026-08-04, after two bugs of one shape reached Curtis in a single
session — both found by clicking a button and reporting that nothing happened:

  - `host:message` was declared and dispatched, but sat inside
    _a2uiActionTransport's `type.indexOf('mcp:') === 0` gate, which excludes
    every verb that is not a tool call. It reached no handler at all.
  - `onRowClick` was declared, its listener attached, and _a2uiBindRowClicks
    read a `data-row-json` attribute NO ATOM EMITTED. Inert for its whole life.

Same shape both times: a declaration that validates, backed by a mechanism that
does not exist end to end.

tests/test_wired_binding.py cannot see either. It asks "does the wired element
render a control the binder can attach to?" — and in both cases the element was
fine. The plumbing behind it was not.

That test asserts a given payload works. THIS one asserts the DIALECT has no
dead ends: that anything an author could declare is backed by something real.
The difference is between catching what someone wired, and catching what someone
COULD wire and would find inert.

Expectations are parsed from source, never restated — a hardcoded list goes
stale and then fails for the one reason that is never interesting.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

HANDLED_ELSEWHERE = object()   # a prop served outside the else-if dispatch

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "apps-script-surface" / "gas-wired-renderer" / "A2UIState.html"
BUNDLE = ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html"


# ── source-derived expectations ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def state_src():
    return STATE.read_text()


@pytest.fixture(scope="module")
def declarable_verbs(state_src):
    """Every action `type` a payload may declare and expect to be routed.

    Three sources, because the transport grew three ways of recognising one:
    the mcp: allowlist, the gas: sheet map, and bare `type === '...'` specials.
    A verb reachable by none of these is one an author can write and never see
    execute.
    """
    verbs = set()
    for block in re.findall(r"var (?:MCP_)?VERBS?\s*=\s*\{(.*?)\};", state_src, re.S):
        verbs |= set(re.findall(r"'([a-z]+:[a-z_]+)'\s*:", block))
    verbs |= set(re.findall(r"type === '([a-z]+:[a-z_]+)'", state_src))
    assert verbs, "parsed no verbs out of A2UIState.html — the dispatch shape changed"
    return sorted(verbs)


@pytest.fixture(scope="module")
def wire_prop_selectors(state_src):
    """{output wire prop -> the selector or attribute its binder branch reads}.

    Read out of the binder itself so the day someone teaches it a new control,
    this test learns it in the same commit.
    """
    props = set()
    m = re.search(r"var OUTPUT_WIRE_PROPS\s*=\s*\{(.*?)\};", state_src, re.S)
    assert m, "OUTPUT_WIRE_PROPS not found — update this parser, do not hardcode"
    props = set(re.findall(r"(\w+)\s*:\s*1", m.group(1)))

    def branch_body(prop):
        """Just THIS prop's branch — up to the next one.

        Bounding matters: an unbounded window runs into the following
        `else if (prop === ...)` and attributes the neighbour's selector to this
        prop. The first run of this test did exactly that and reported
        onRowClick looking for onSearch's element, which would have sent someone
        to fix a binder that was fine.
        """
        m = re.search(r"prop === '%s'\)\s*\{" % prop, state_src)
        if not m:
            # Not every prop is served by the else-if chain. onAssign and
            # onFlightClick are read directly off layoutEl.wire elsewhere in the
            # engine, which is a legitimate second mechanism — "has no branch"
            # and "has no handler" are different claims and only the second is a
            # bug. Treat any real read of wire.<prop> as handled.
            if re.search(r"wire\.%s\b" % prop, state_src):
                return HANDLED_ELSEWHERE
            return None
        rest = state_src[m.end():]
        nxt = re.search(r"\}\s*else if \(prop ===", rest)
        return rest[:nxt.start()] if nxt else rest[:1200]

    def helper_body(fn):
        m = re.search(r"function %s\(" % re.escape(fn), state_src)
        if not m:
            return ""
        rest = state_src[m.end():]
        nxt = re.search(r"\n(?:function |// ───)", rest)
        return rest[:nxt.start()] if nxt else rest[:1500]

    out = {}
    for prop in props:
        body = branch_body(prop)
        if body is None:
            out[prop] = (None, None)
            continue
        if body is HANDLED_ELSEWHERE:
            # Handled, but by reading layoutEl.wire.<prop> directly rather than
            # through the else-if chain. There is no selector to check, and that
            # is not a defect — only an unhandled prop is.
            out[prop] = ("handled-elsewhere", None)
            continue
        sel = re.search(r"querySelector(?:All)?\('([^']+)'\)", body)
        if sel:
            out[prop] = ("selector", sel.group(1))
            continue
        # branches that delegate to a helper which reads a data- attribute
        helper = re.search(r"\b(_a2ui\w+)\(", body)
        if helper:
            hb = helper_body(helper.group(1))
            attr = re.search(r"getAttribute\('(data-[\w-]+)'\)", hb)
            if attr:
                out[prop] = ("attribute", attr.group(1))
                continue
            qs = re.search(r"querySelector(?:All)?\('([^']+)'\)", hb)
            if qs:
                out[prop] = ("selector", qs.group(1))
                continue
        out[prop] = (None, None)          # binder branch not understood
    return out


# ── atom sweep, shared with the bundle suite's approach ──────────────────────

@pytest.fixture(scope="module")
def renderer_sources():
    """Every renderer .gs, concatenated.

    Satisfiability is judged against SOURCE, not against rendered output. The
    first cut rendered every atom and asked whether the markup appeared — and
    reported four dead props that were nothing of the kind: the atoms emitting
    them threw on the generic stub props, were skipped by the try/catch, and
    their markup never entered the corpus. Absence of evidence became evidence
    of absence, which is the one failure mode a gate must not have.

    Grepping source cannot miss an emitter for want of the right props. It can
    in principle match a commented-out line — a far quieter wrong answer than
    telling someone to fix a binder that works.
    """
    d = ROOT / "apps-script-surface" / "gas-wired-renderer"
    src = "\n".join(f.read_text() for f in sorted(d.glob("*.gs")))
    # COMMENTS STRIPPED FIRST. Verified necessary the moment it was written: with
    # the data-row-json emit deliberately removed, this still passed — because
    # the explanatory comment ABOVE the emit mentions the attribute, and a
    # comment describing a mechanism is not that mechanism. Documentation that
    # satisfies a gate is the quietest possible false green.
    src = re.sub(r"/\*[\s\S]*?\*/", "", src)
    src = re.sub(r"^\s*//.*$", "", src, flags=re.M)
    return src


@pytest.fixture(scope="module")
def all_atom_markup():
    """Every registered atom rendered once, concatenated.

    One Node invocation for the whole catalogue — the same shape
    test_mcp_apps_bundle.py's sweep uses, asked a different question.
    """
    raw = BUNDLE.read_text()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", raw, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]][0]
    with tempfile.TemporaryDirectory() as td:
        drv = Path(td) / "d.js"
        drv.write_text("global.window = global;\n" + core + """
var out = [];
Object.keys(_RENDERERS).forEach(function (t) {
  try {
    out.push(_RENDERERS[t]({
      // Enough shape that row/option/item-driven atoms actually emit rows.
      rows: [{ id: 'r0', a: 'x' }], items: [{ label: 'l', value: 'v' }],
      columns: [{ key: 'a', label: 'A' }],
      options: [{ label: 'o', value: 'v' }], data: [{ a: 1 }],
      label: 'l', title: 't', text: 'x', name: 'n', flights: [{ id: 'f' }],
      steps: [{ label: 's' }], value: '', checked: false
    }));
  } catch (e) { /* atoms needing richer input are covered by the bundle suite */ }
});
process.stdout.write(out.join('\\n'));
""")
        r = subprocess.run(["node", str(drv)], capture_output=True, text=True, timeout=180)
        assert r.returncode == 0, r.stderr[-2000:]
        return r.stdout


def _satisfied_in_source(src, kind, needle):
    """Does any renderer emit something this binder branch could attach to?"""
    if kind == "attribute":
        return needle in src
    if kind != "selector":
        return False
    for part in [x.strip() for x in needle.split(",")]:
        if part.startswith("["):                        # [data-foo]
            if part.strip("[]") in src:
                return True
            continue
        tag = re.split(r"[:\[]", part)[0].strip()
        if " " in tag:
            tag = tag.split()[-1]
        if re.search(r"<%s\b" % re.escape(tag), src):
            return True
    return False


def _satisfied(markup, kind, needle):
    if kind == "attribute":
        return (needle + "=") in markup
    if kind != "selector":
        return False
    for part in needle.split(","):
        part = part.strip()
        if part.startswith("["):                       # [data-foo]
            return (part.strip("[]") + "=") in markup
        neg = ":not([type=checkbox])" in part
        tag = re.split(r"[:\[]", part)[0].strip()
        if " " in tag:                                  # descendant selector
            tag = tag.split()[-1]
        for m in re.finditer(r"<%s\b([^>]*)>" % re.escape(tag), markup):
            if neg and "checkbox" in m.group(1):
                continue
            if part.strip("[]").startswith("data-") and part.strip("[]") not in m.group(1):
                continue
            return True
    return False


# ── sweep 1: every verb reaches a handler ────────────────────────────────────

def test_every_declarable_verb_reaches_a_handler(declarable_verbs, state_src):
    """A verb an author can write must not fall through to the refusal branch."""
    unreachable = []
    for verb in declarable_verbs:
        prefix_gated = verb.startswith("mcp:") and "type.indexOf('mcp:')" in state_src
        special = ("type === '%s'" % verb) in state_src
        in_gas_map = re.search(r"'%s'\s*:" % re.escape(verb), state_src) is not None
        if not (prefix_gated or special or in_gas_map):
            unreachable.append(verb)
    assert not unreachable, (
        "verbs a payload may declare that reach no handler — they would refuse with "
        "the generic fallback, which is how host:message shipped inert:\n  "
        + "\n  ".join(unreachable))


def test_non_tool_verbs_are_dispatched_before_the_mcp_gate(state_src):
    """The specific trap host:message fell into, made structural.

    _a2uiActionTransport opens with an `mcp:` PREFIX gate. Any verb that is not
    a tool call must be handled BEFORE it, or it is skipped entirely and lands
    in the GAS fallback. Position is the whole contract here.
    """
    gate = state_src.index("type.indexOf('mcp:')")
    for verb in re.findall(r"type === '([a-z]+:[a-z_]+)'", state_src):
        if verb.startswith("mcp:"):
            continue
        at = state_src.index("type === '%s'" % verb)
        assert at < gate, (
            f"'{verb}' is dispatched AFTER the mcp: prefix gate, so it can never "
            f"match — the verb does not start with 'mcp:' and the gate skips the "
            f"whole block. Move it above the gate.")


# ── sweep 2: every wire prop is satisfiable by some atom ─────────────────────

def test_every_wire_prop_has_a_binder_branch(wire_prop_selectors):
    """A declared prop with no branch in the binder is a no-op wire."""
    orphaned = [p for p, (kind, _) in wire_prop_selectors.items() if kind is None]
    assert not orphaned, (
        "OUTPUT_WIRE_PROPS entries whose binder branch this test could not find. "
        "Either they have no branch (a no-op wire), or the dispatch shape changed "
        "and the parser needs updating — check which before touching either:\n  "
        + "\n  ".join(sorted(orphaned)))


def test_every_wire_prop_is_satisfiable_by_some_atom(wire_prop_selectors, renderer_sources):
    """The onRowClick bug, generalised.

    A binder looking for markup no atom emits is a wire that validates, attaches,
    and never fires. Fix by EMITTING what the binder wants, or by removing the
    prop — a documented wire that cannot work is worse than an absent one. Do not
    add an allowlist of known-dead props; that turns this gate into a record of
    things nobody fixed.
    """
    dead = []
    for prop, (kind, needle) in sorted(wire_prop_selectors.items()):
        if kind is None or kind == "handled-elsewhere":
            continue                       # no selector to satisfy
        if not _satisfied_in_source(renderer_sources, kind, needle):
            dead.append(f"{prop} -> nothing emits {needle!r}")
    assert not dead, (
        "wire props no atom can satisfy — declarable, documented and INERT:\n  "
        + "\n  ".join(dead))


# ── negative controls: a gate that cannot fail is worth nothing ──────────────

def test_the_verb_sweep_can_fail(state_src):
    fake = "invented:verb_that_does_not_exist"
    prefix_gated = fake.startswith("mcp:") and "type.indexOf('mcp:')" in state_src
    special = ("type === '%s'" % fake) in state_src
    in_map = re.search(r"'%s'\s*:" % re.escape(fake), state_src) is not None
    assert not (prefix_gated or special or in_map), (
        "a verb present nowhere in the transport was judged reachable — the "
        "reachability check is not checking anything")


def test_the_wire_sweep_can_fail(all_atom_markup):
    assert not _satisfied(all_atom_markup, "attribute", "data-nothing-emits-this"), (
        "an attribute no atom emits was judged satisfied — the satisfiability "
        "check is not checking anything")
    assert _satisfied(all_atom_markup, "selector", "button"), (
        "the check cannot find <button>, which many atoms emit — it is broken "
        "in the direction that produces false green")
