"""What each output wire actually DELIVERS, held against what the spec claims.

DECLARED 2026-08-14, after `onRowClick` cost two working pages in a consuming
app. The binding attached perfectly; it emitted the whole clicked row where the
consumer expected an id, so every action answered "no record with that id" --
naming the one thing that was certainly not wrong.

`test_wired_binding.py` asks DID A BINDING ATTACH. That is a different question
from WHAT VALUE FLOWS, and only the first was ever asked. A payload can be
fully bound, fully rendered, and still deliver a dict into a field that wanted
a string.

The correction that matters: the shape WAS documented. spec/a2ui-state-v1.md
has said `onRowClick | Output | object` since the pilot registry was written.
The consumer got it wrong anyway, because nothing checked -- and the engine had
meanwhile grown seven more output props that never reached the spec at all.

So this is not a missing contract. It is an UNENFORCED one, drifting. The fix
is a gate over the existing document, in both directions: a prop the binder
gains without a row is an undocumented shape someone will guess wrong, and a
row the spec keeps after the binder drops it is worse -- it reads as verified.

Writing a second table elsewhere would have made it worse still. Two
hand-maintained copies of one list is the exact drift this repo has been bitten
by three times (MCP_VERBS, the parser parity pair, the frozen renderer copies).
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "apps-script-surface" / "gas-wired-renderer" / "A2UIState.html"
SPEC = ROOT / "spec" / "a2ui-state-v1.md"

# How each emitted expression is classified. Read as: the SHAPE a consumer must
# be prepared to receive, not the JS that produces it.
SHAPE_OF_EXPR = [
    (r"^null$", "null"),
    (r"\.checked$", "boolean"),
    (r"\.value$", "string"),
    (r"^payload$", "object"),
    (r"^rowData$", "object"),
    (r"^detail$", "object"),
    (r"^person$", "object"),
]


@pytest.fixture(scope="module")
def declared():
    """{prop: shape} as spec/a2ui-state-v1.md states it."""
    rows = {}
    body = SPEC.read_text()
    # Only the consolidated table in 2.2.1 -- the per-atom tables in 3.1 give
    # the same props again and would mask a drop from the complete list.
    section = body[body.index("#### 2.2.1"):body.index("### 2.3 Error Behaviour")]
    for line in section.splitlines():
        m = re.match(r"\|\s*`(\w+)`\s*\|[^|]*\|\s*(.+?)\s*\|\s*$", line)
        if not m:
            continue
        shape = m.group(2).replace("*", "").replace("`", "").strip()
        # "event (null)" -> null; "object" stays object
        if "null" in shape:
            shape = "null"
        rows[m.group(1)] = shape.split(" (")[0].strip()
    assert rows, "no table rows parsed out of the spec -- update this parser"
    return rows


@pytest.fixture(scope="module")
def binder_props():
    """Props the engine actually accepts as output wires."""
    src = STATE.read_text()
    m = re.search(r"var OUTPUT_WIRE_PROPS\s*=\s*\{(.*?)\};", src, re.S)
    assert m, "OUTPUT_WIRE_PROPS not found -- update this parser, do not hardcode"
    return set(re.findall(r"(\w+)\s*:\s*1", m.group(1)))


def test_the_spec_and_the_binder_declare_the_same_props(declared, binder_props):
    undocumented = sorted(binder_props - set(declared))
    assert not undocumented, (
        "output wire props the engine accepts but spec/a2ui-state-v1.md "
        "does not describe. A consumer has no way to learn the shape except by "
        "guessing, and the guess that cost two pages on 2026-08-14 was the "
        f"reasonable one: {undocumented}")

    stale = sorted(set(declared) - binder_props)
    assert not stale, (
        "props the spec documents that the engine no longer accepts -- a wire "
        "written against these is silently inert, and the spec says otherwise: "
        f"{stale}")


def test_every_documented_shape_matches_what_the_binder_emits(declared):
    """The claim itself, not merely that a row exists.

    Reads the argument of each bindOutput call and classifies it. A row saying
    "string" over a call that hands back an object is worse than no row, since
    it reads as verified.
    """
    src = STATE.read_text()

    # Each branch of the output-wire dispatch, and what it hands to bindOutput.
    emitted = {}
    for m in re.finditer(r"prop === '(\w+)'\)\s*\{(.*?)(?=\n      \} else if \(prop ===|\n      \}\n)",
                         src, re.S):
        prop, body = m.group(1), m.group(2)
        args = re.findall(r"bindOutput\(\s*wireExpr,\s*([^)]+?)\s*\)", body, re.S)
        # Delegated branches call a helper instead; resolve one level.
        for helper in re.findall(r"(_a2uiBind\w+)\(", body):
            hm = re.search(r"function %s\([^)]*\)\s*\{(.*?)\n\}" % helper, src, re.S)
            if hm:
                args += re.findall(r"bindOutput\(\s*(?:wireExpr,\s*)?([^;]+?)\);",
                                   hm.group(1), re.S)
        if args:
            emitted[prop] = args

    checked = []
    for prop, shape in declared.items():
        args = emitted.get(prop)
        if not args:
            continue          # handled outside the dispatch chain; see below
        for raw in args:
            expr = re.sub(r"\s+", " ", raw).strip()
            expr = re.sub(r"^wireExpr,\s*", "", expr)
            got = next((s for pat, s in SHAPE_OF_EXPR if re.search(pat, expr)), None)
            if got is None:
                continue      # an expression this classifier cannot read
            assert got == shape, (
                f"spec says {prop} emits {shape}, but the binder hands over "
                f"{expr!r} which is {got}. Fix whichever is wrong -- a consumer "
                f"reading the spec will build for {shape}.")
            checked.append(prop)

    # A gate that classifies nothing passes for free.
    assert len(set(checked)) >= 5, (
        "too few props verified against the binder -- the dispatch shape "
        f"probably changed and this parser is silently matching nothing: {sorted(set(checked))}")


def test_the_three_surprising_shapes_are_spelled_out(declared):
    """The rows that exist because someone got them wrong.

    Not a style check. Each of these contradicts the obvious assumption, and a
    table that lists them without saying so is one a reader skims past.
    """
    body = SPEC.read_text()
    assert declared["onRowClick"] == "object"
    assert declared["onSearch"] == "null"
    assert declared["onClick"] == "null"
    for needle in ("emits the ROW, not an id", "emits nothing. The query is not"):
        assert needle in body, (
            f"spec/a2ui-state-v1.md must call out {needle!r} in prose -- "
            "the table alone gets skimmed, and these are the ones that cost "
            "working pages")
