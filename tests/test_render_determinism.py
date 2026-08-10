"""Rendering the same block twice must produce byte-identical markup.

The bug this guards against cost more than it looks. Element ids were derived
from `uuid4()`, `id(b)` (a memory address) and the built-in `hash()` (randomised
per process since Python 3.3 unless PYTHONHASHSEED is pinned). Every
`catalog-rebuild` therefore rewrote ~33 files under public/atoms/ with ZERO
content change.

That is not merely untidy. It hides real changes in noise: a genuine
regeneration of the MCP Apps pages, carrying a corrected cache-bust hash, sat
uncommitted and unnoticed inside exactly that noise until someone diffed the
tree token by token. A diff you have learned to ignore is a diff that no longer
tells you anything.

Why a SUBPROCESS rather than rendering twice in-process: `hash()` randomisation
is seeded once at interpreter start, so two calls inside one test would agree
with each other no matter how broken the code is. The two runs below use
deliberately different PYTHONHASHSEED values, which is the only way to observe
the failure this test exists to catch.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent

# Rendered in a child process so PYTHONHASHSEED can differ between runs.
_CHILD = r'''
import json, sys, hashlib, yaml
sys.path.insert(0, {root!r})
sys.path.insert(0, {scripts!r})
import generate_atom_pages as gap
from renderers.web_article import _RENDERERS

atoms = yaml.safe_load(open({schema!r}))["blocks"]
out = {{}}
for atom in atoms:
    t = atom["type"]
    fn = _RENDERERS.get(t)
    if not fn:
        continue
    try:
        block = gap._EXAMPLE_BLOCKS.get(t) or json.loads(gap.example_payload(atom))
        html = fn(block)
    except Exception as exc:
        # A renderer that raises is a different test's problem; record the
        # exception TYPE so a crash can't masquerade as determinism.
        html = "ERR:" + type(exc).__name__
    out[t] = hashlib.sha256(html.encode()).hexdigest()
print(json.dumps(out, sort_keys=True))
'''


def _render_all(hashseed: str) -> dict:
    src = _CHILD.format(
        root=str(ROOT),
        scripts=str(ROOT / "scripts"),
        schema=str(ROOT / "atoms" / "schema.yaml"),
    )
    env = dict(os.environ, PYTHONHASHSEED=hashseed)
    proc = subprocess.run([sys.executable, "-c", src], capture_output=True,
                          text=True, env=env, cwd=str(ROOT), timeout=600)
    assert proc.returncode == 0, f"render child failed:\n{proc.stderr[-3000:]}"
    return json.loads(proc.stdout)


@pytest.fixture(scope="module")
def two_runs():
    return _render_all("1"), _render_all("424242")


def test_every_atom_renders_identically_under_a_different_hash_seed(two_runs):
    first, second = two_runs
    assert first, "no atoms rendered — the harness itself is broken"
    unstable = sorted(t for t in first if first[t] != second.get(t))
    assert not unstable, (
        f"{len(unstable)} atom(s) render differently across processes — a random "
        f"uid, id() or hash() has crept back in: {unstable[:20]}"
    )


def test_renderer_sources_use_the_stable_id_helpers():
    """Fast structural check, so a reintroduced call is named at the line.

    The test above catches it only if the offending atom has a usable example
    block; this one catches it regardless.
    """
    path = ROOT / "renderers" / "web_article.py"
    src = path.read_text(encoding="utf-8")

    # Read CODE, not text. The helpers' own docstrings quote the very calls
    # they replaced ("it used to be uuid4().hex[:8]"), and a plain substring
    # scan flags those — punishing the documentation for describing the bug.
    # Blanking comment and string tokens leaves executable code only.
    import io
    import tokenize
    lines = src.splitlines()
    code = list(lines)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                (r1, _), (r2, _) = tok.start, tok.end
                for r in range(r1 - 1, min(r2, len(code))):
                    code[r] = ""
    except tokenize.TokenError:  # pragma: no cover - syntax is checked elsewhere
        pytest.skip("web_article.py did not tokenize cleanly")

    offenders = []
    for i, line in enumerate(code, 1):
        stripped = line.strip()
        if not stripped or "_wa_" in line:
            continue
        # `random.Random(seed)` / `rng.random()` are fine — a SEEDED instance is
        # deterministic. Bare module-level calls draw from the shared stream.
        for bad in ("uuid4()", "random.seed(", "random.shuffle(",
                    "random.choices(", "random.random()"):
            if bad in line and not any(
                p in line for p in ("random.Random(", "rng.", "_rng.", "r_gen.")
            ):
                offenders.append(f"{i}: {stripped[:100]}")
    assert not offenders, (
        "non-deterministic RNG use in web_article.py — seed a random.Random "
        "instance from block content instead:\n  " + "\n  ".join(offenders)
    )
