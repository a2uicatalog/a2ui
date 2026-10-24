"""scripts/bundle_diet.py: the renderer bundle's lossless size reduction must not change what the code or the data mean."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import bundle_diet  # noqa: E402
import gen_mcp_apps_bundle as gen  # noqa: E402

NODE = shutil.which("node")
KEEP = bundle_diet.shipped_function_names([f.read_text() for f in gen.renderer_files()])
pytestmark = pytest.mark.skipif(not NODE, reason="node not installed")


def test_strip_js_touches_only_code_state_lines():
    src = (
        "function f() {\n"
        "    // a full-line comment\n"
        "\n"
        "    var t = `line one\n"
        "    // not a comment, inside a template\n"
        "      ${ [1].map((x) => `\n"
        "   // nested template text\n"
        "${x}`).join('') } end`;\n"
        "    var s = 'a\\\n"
        "    // continued string';\n"
        "    var r = /['\"`\\/]\\/\\//g;\n"
        "    var d = a / b / c; // trailing comment stays\n"
        "    /* block\n"
        "    // still block */\n"
        "    return `x`;\n"
        "}\n"
    )
    out = bundle_diet.strip_js(src)
    assert "full-line comment" not in out
    for keep in ("    // not a comment, inside a template\n", "   // nested template text\n", "    // continued string'",
                 "var r = /['\"`\\/]\\/\\//g;", "var d = a / b / c; // trailing comment stays", "// still block */"):
        assert keep in out, keep
    assert "\n\n" not in out
    assert out.count("\n    ") == 4 and "\n    var" not in out    # only template/string/block-comment lines keep their indent
    assert len(out) < len(src)


def _tokens(path):
    p = subprocess.run([NODE, str(ROOT / "scripts" / "bundle_diet_tokens.mjs"), str(path)], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr[-800:]
    return p.stdout.strip()


def test_every_bundled_source_keeps_an_identical_token_stream_after_stripping(tmp_path):
    """acorn tokenises the original and the stripped text: same token types and values (strings, template parts, regexes by pattern
    and flags), comments aside. Needs node's acorn (Debian nodejs ships it at /usr/share/nodejs/acorn); where it is missing the test
    skips, so a CI runner without it does not check this, only the local runs and the render proof do."""
    files = [f for f in gen.renderer_files() if f.name != "atoms_scene_data.gs"] + [gen.QRCODEGEN_PATH]
    for name in gen.PARTIALS:
        (tmp_path / (name + ".orig.js")).write_text(gen.partial_body(name))
        files.append(tmp_path / (name + ".orig.js"))
    for f in files:
        a = _tokens(f)
        if a == "NOACORN":
            pytest.skip("acorn not available")
        (tmp_path / "stripped.js").write_text(bundle_diet.strip_js(f.read_text(), KEEP))
        assert _tokens(tmp_path / "stripped.js") == a, f.name


def test_scene_data_decodes_to_exactly_the_original_value():
    orig = (gen.RENDERER_DIR / "atoms_scene_data.gs").read_text()
    packed = bundle_diet.pack_scene_data(orig)
    assert len(packed) < len(orig) * 0.2
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "a.js").write_text(orig)
        (Path(td) / "b.js").write_text(bundle_diet.strip_js(packed))
        (Path(td) / "eq.js").write_text(
            "const fs=require('fs'),vm=require('vm'),assert=require('assert');"
            "function load(p){const c=vm.createContext({});vm.runInContext(fs.readFileSync(p,'utf8')+'\\nthis.D=SCENE_STAGE_DATA;',c);return c.D;}"
            "const a=load(__dirname+'/a.js'),b=load(__dirname+'/b.js');"
            "assert.deepStrictEqual(Object.keys(a),Object.keys(b));"
            "assert.strictEqual(JSON.stringify(a),JSON.stringify(b));"          # same values, same key order, at every depth
            "for(const k of Object.keys(a)) assert.deepEqual(a[k],b[k]);"
            "assert.strictEqual(JSON.stringify(Object.keys(a.trusted_sha256)),JSON.stringify(Object.keys(b.trusted_sha256)));"
            "console.log('ok')")
        p = subprocess.run([NODE, str(Path(td) / "eq.js")], capture_output=True, text=True, timeout=120)
        assert p.returncode == 0 and p.stdout.strip() == "ok", p.stderr[-1200:]


def test_the_bundle_core_script_still_parses():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]][0]
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "core.js").write_text(core)
        p = subprocess.run([NODE, "--check", str(Path(td) / "core.js")], capture_output=True, text=True, timeout=120)
        assert p.returncode == 0, p.stderr[-800:]


def test_functions_shipped_as_source_text_stay_verbatim_in_the_bundle():
    """_moStudioObj, _brickKit, _brickMount, _geoLib, _A2UI_V1_RUNTIME ... are serialised with .toString() and re-read from the .gs by the
    Python twins: the bundle must hold their exact original text."""
    assert {"_moStudioObj", "_brickKit", "_brickMount", "_geoLib", "_A2UI_V1_RUNTIME"} <= KEEP
    bundle = gen.build_bundle()
    for f in gen.renderer_files():
        src = f.read_text()
        for nm in KEEP:
            m = re.search(r"^(?:function\s+|var\s+)%s\b.*?^\}[;]?[ \t]*$" % re.escape(nm), src, re.S | re.M)
            if m:
                assert m.group(0) in bundle, nm


def test_packed_scene_data_cannot_close_its_script_element():
    packed = bundle_diet.pack_scene_data((gen.RENDERER_DIR / "atoms_scene_data.gs").read_text())
    assert not re.search(r"</script|<!--|<script", packed, re.I)
