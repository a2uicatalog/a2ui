"""The Apps Script renderer page (/renderer/) and the rule that page numbers come from data.

Written 2026-11-13 when the page still said "501 atoms" with 573 published (550 of them on Apps
Script): the number was typed into gen_renderer_page.py, out of reach of gen_atom_count.py, and the
page was not rebuilt on deploy. Owner: "make the numbers mechanical going forward".
"""
import io
import json
import re
import subprocess
import sys
import tempfile
import tokenize
import ast
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import gen_renderer_page as page  # noqa: E402
import a2ui_v1_conformance as conformance  # noqa: E402

COUNT_CLAIM = re.compile(r"\b\d{3} (?:typed )?(?:UI )?atoms\b")


def test_page_numbers_come_from_data():
    c = page.counts()
    html = page.render()
    assert "@@" not in html
    assert f"{c['GAS_ATOMS']} of the catalog's {c['TOTAL_ATOMS']} atoms render on Apps Script" in html
    assert f"<h4>{c['GAS_ATOMS']} atoms, ready to go</h4>" in html
    assert f"A2UI v{c['PROTOCOL']}</strong>" in html and f"all {c['BASIC_N']} components" in html
    claimed = {m.split()[0] for m in COUNT_CLAIM.findall(html)}
    assert claimed <= {c["GAS_ATOMS"], c["TOTAL_ATOMS"]}, claimed


def test_v1_example_is_valid_and_renders():
    conformance.assert_conforms(page.V1_EXAMPLE,
                                conformance._validator_for("agent_to_renderer.json", permissive_extensions=False))
    import gen_mcp_apps_bundle as gen
    core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", gen.build_bundle(), re.S) if "a2ui-core" in b[:300]][0]
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core +
                     f"\nvar out = _rehydrateV1Surface({json.dumps(page.V1_EXAMPLE['createSurface'])});"
                     "\nconsole.log(JSON.stringify(renderAtoms(out.blocks, {})));")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr[-1500:]
    html = json.loads(p.stdout.strip().split("\n")[-1])
    for want in ("Hello from Apps Script", "Your name", 'data-a2ui-bind="/form/name"', "data-a2ui-action=", "Say hello"):
        assert want in html, want
    # the example printed on the page is the one tested here
    printed = page.render()
    assert '"@path": "/form/name"' in printed and '"surfaceId": "hello"' in printed


def _deploy_generators():
    wf = (ROOT / ".github/workflows/deploy.yml").read_text()
    return sorted(set(re.findall(r"python3 (scripts/[\w./-]+\.py)", wf)))


def _docstring_lines(src):
    lines = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) \
                    and isinstance(first.value.value, str):
                lines.update(range(first.lineno, first.end_lineno + 1))
    return lines


def test_no_typed_in_atom_counts_in_page_generators():
    """A page generator states counts from data: an f-string field, never a literal like "501 atoms".
    Comments and docstrings may record history; a dated article summary (a /blog/ link) may quote
    the count it was published with."""
    bad = []
    for rel in _deploy_generators():
        path = ROOT / rel
        src = path.read_text(encoding="utf-8")
        skip = _docstring_lines(src)
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type != tokenize.STRING and tok.type != getattr(tokenize, "FSTRING_MIDDLE", -1):
                continue
            for m in COUNT_CLAIM.finditer(tok.string):
                line = tok.start[0] + tok.string[:m.start()].count("\n")
                text = src.splitlines()[line - 1]
                if line in skip or "/blog/" in text:
                    continue
                bad.append(f"{rel}:{line}: {m.group(0)}")
    assert not bad, "typed-in atom counts (read them from spec.json instead):\n" + "\n".join(bad)


def test_renderer_page_is_built_on_deploy():
    assert "scripts/gen_renderer_page.py" in _deploy_generators()
