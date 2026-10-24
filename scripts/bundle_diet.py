"""Lossless size reduction for the renderer bundle (scripts/gen_mcp_apps_bundle.py).

strip_js(): drops leading indentation, blank lines and full-line `//` comments, but ONLY on lines that start in plain code state.
A small scanner tracks strings, template literals (with nested ${...}), regex literals and block comments, so nothing inside a
literal is touched. Identifiers are never renamed. tests/test_bundle_diet.py proves the result has the same token stream as
the input (acorn, when available) and that node can still parse it.

pack_scene_data(): re-encodes the generated scene kit constant (SCENE_STAGE_DATA) as a shorter literal plus a decoder that rebuilds
the exact same value (see the function for the encodings). The .gs source files are untouched, so the Apps Script project and
the tests that read them are unaffected.
"""
from __future__ import annotations

import json
import re

_KW_BEFORE_REGEX = {"return", "typeof", "instanceof", "in", "of", "new", "delete", "void", "throw", "case", "do", "else", "yield", "await"}
_IDENT = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")


_TOSTRING = re.compile(r"(?<![\w$.)\]])([A-Za-z_$][\w$]*)\.toString\(\)")


def shipped_function_names(sources) -> set[str]:
    """Names of functions whose SOURCE TEXT is shipped at runtime (`name.toString()` inside a generated <script>): the
    Python twins read these from the .gs files verbatim, so they must stay byte-identical."""
    names: set[str] = set()
    for s in sources:
        names.update(m.group(1) for m in _TOSTRING.finditer(s))
    return names


def _protected_ranges(src: str, names) -> list[tuple[int, int]]:
    out = []
    for nm in names:
        m = re.search(r"^(?:function\s+|(?:var|let|const)\s+)%s\b" % re.escape(nm), src, re.M)
        if m:
            e = re.compile(r"^\}[;]?[ \t]*$", re.M).search(src, m.end())
            out.append((m.start(), e.end() if e else len(src)))
    return out


def strip_js(src: str, keep=()) -> str:
    """`keep`: names of top-level functions that must stay verbatim (see shipped_function_names)."""
    n = len(src)
    prot = _protected_ranges(src, keep)
    drops: list[tuple[int, int]] = []
    i = 0
    line_start = True          # at the start of a line in code state
    stack: list[int] = []      # brace depths to return to template mode: one entry per open ${
    depth = 0
    prev = ""                  # last significant token kind: 'op' (regex may follow) or 'val' (division follows)

    def template(pos):
        """Scan template text from pos (just after ` or }); return (new_pos, entered_expr)."""
        while pos < n:
            c = src[pos]
            if c == "\\":
                pos += 2
            elif c == "`":
                return pos + 1, False
            elif c == "$" and src.startswith("${", pos):
                return pos + 2, True
            else:
                pos += 1
        return pos, False

    while i < n:
        if line_start:
            line_start = False
            j = i
            while j < n and src[j] in " \t\r":
                j += 1
            if j >= n or src[j] == "\n" or src.startswith("//", j):
                k = src.find("\n", j)
                k = n if k < 0 else k + 1
                drops.append((i, k))            # blank or full-line comment: drop the whole line
                i = k
                line_start = True
                continue
            if j > i:
                drops.append((i, j))            # leading indentation
                i = j
        c = src[i]
        if c == "\n":
            i += 1
            line_start = True
            continue
        if c in " \t\r":
            i += 1
            continue
        if c == "/" and src.startswith("//", i):
            k = src.find("\n", i)
            i = n if k < 0 else k
            continue
        if c == "/" and src.startswith("/*", i):
            k = src.find("*/", i + 2)
            i = n if k < 0 else k + 2
            continue
        if c in "'\"":
            i += 1
            while i < n and src[i] != c:
                i += 2 if src[i] == "\\" else 1
            i += 1
            prev = "val"
            continue
        if c == "`":
            i, expr = template(i + 1)
            if expr:
                stack.append(depth)
                depth += 1
                prev = "op"
            else:
                prev = "val"
            continue
        if c == "{":
            depth += 1
            prev = "op"
            i += 1
            continue
        if c == "}":
            depth -= 1
            if stack and stack[-1] == depth:
                stack.pop()
                i, expr = template(i + 1)
                if expr:
                    stack.append(depth)
                    depth += 1
                    prev = "op"
                else:
                    prev = "val"
                continue
            prev = "val"
            i += 1
            continue
        if c == "/":
            if prev == "op":                      # regex literal
                i += 1
                in_class = False
                while i < n:
                    d = src[i]
                    if d == "\\":
                        i += 2
                        continue
                    if d == "[":
                        in_class = True
                    elif d == "]":
                        in_class = False
                    elif d == "/" and not in_class:
                        break
                    elif d == "\n":
                        break
                    i += 1
                i += 1
                while i < n and (src[i].isalnum() or src[i] == "_"):
                    i += 1
                prev = "val"
                continue
            prev = "op"
            i += 1
            continue
        m = _IDENT.match(src, i)
        if m:
            prev = "op" if m.group(0) in _KW_BEFORE_REGEX else "val"
            i = m.end()
            continue
        if c.isdigit():
            while i < n and (src[i].isalnum() or src[i] in "._"):
                i += 1
            prev = "val"
            continue
        if c in ")]":
            prev = "val"
        else:
            prev = "op"
        i += 1
    out, pos = [], 0
    for a, b in drops:
        if any(x <= a < y for x, y in prot):
            continue
        out.append(src[pos:a])
        pos = b
    out.append(src[pos:])
    return "".join(out)


# ---------------------------------------------------------------------------------------------------------------------------
# Scene kit data: SCENE_STAGE_DATA -> compact literal + decoder.
#
# Encodings (all lossless; tests/test_bundle_diet.py decodes the result in node and compares it to the original, key order too):
#   1. trusted_sha256 entries that repeat an entry's own sha256 are not stored; the decoder fills them in and re-sorts the keys.
#   2. the rest is serialised as compact JSON (no whitespace) and compressed with byte-pair encoding over characters: each merged
#      pair becomes one private-use-area character (U+E000 + n); the pair table is shipped as a string, 2 characters per merge.
#      This removes the SVG indentation/attribute boilerplate and the origin/licence blocks repeated across entries in one go.
#   3. the decoder is lazy (getters): nothing is expanded until a scene or clipart actually renders.
# ---------------------------------------------------------------------------------------------------------------------------

_PUA0 = 0xE000
_DATA_RE = re.compile(r"^(?P<head>.*?\bvar SCENE_STAGE_DATA = )(?P<json>\{.*\})(?P<tail>;\s*)$", re.S)

# Note: the top-level keys of SCENE_STAGE_DATA are getter-only (lazy decode); read them, never assign to them.
_DECODER = (
    "(function(){var T=%(table)s,S=%(text)s,X=[],i,c,d=null;"
    "function e(c){var n=c.charCodeAt(0)-57344;return n>=0&&n<6400?X[n]:c}"
    "for(i=0;i<T.length;i+=2)X.push(e(T.charAt(i))+e(T.charAt(i+1)));"
    "function g(){if(!d){d=JSON.parse(S.replace(/[\\uE000-\\uF8FF]/g,e));"
    "var t={},k,a=d.trusted_sha256||{};d.entries.forEach(function(r){t[r.id]=r.sha256});for(k in a)t[k]=a[k];"
    "a={};Object.keys(t).sort().forEach(function(k){a[k]=t[k]});d.trusted_sha256=a;"
    "var o={};for(k in d)o[k]=d[k];d=o}return d}"
    "var o={};%(keys)s.forEach(function(k){Object.defineProperty(o,k,{enumerable:true,get:function(){return g()[k]}})});"
    "return o})()"
)

_cache: dict[str, str] = {}


def _bpe(text: str, max_merges: int = 6000) -> tuple[str, str]:
    """Return (table, packed): table has 2 chars per merge, packed is `text` with merged pairs replaced by PUA chars."""
    from collections import Counter
    assert all(ord(c) < _PUA0 for c in text), "text already uses private-use or astral characters"
    s = text
    table: list[str] = []
    while len(table) < max_merges:
        cnt = Counter(zip(s, s[1:]))
        best = [(n, p) for p, n in cnt.most_common(300) if n >= 4]
        if not best:
            break
        done = 0
        for _, (a, b) in best:
            if len(table) >= max_merges:
                break
            if a not in s or b not in s:
                continue
            pair = a + b
            if s.count(pair) < 4:
                continue
            ch = chr(_PUA0 + len(table))
            table.append(pair)
            s = s.replace(pair, ch)
            done += 1
        if not done:
            break
    return "".join(table), s


def pack_scene_data(src: str) -> str:
    """Rewrite the generated `var SCENE_STAGE_DATA = {...};` file text into a compact literal that decodes to the same value."""
    if src in _cache:
        return _cache[src]
    m = _DATA_RE.match(src.strip() + "\n")
    assert m, "atoms_scene_data.gs: not the expected `var SCENE_STAGE_DATA = {...};` shape"
    data = json.loads(m.group("json"))
    ent = {e["id"]: e["sha256"] for e in data["entries"]}
    tr = data.get("trusted_sha256")
    keys = list(data)
    if tr is not None:
        assert list(tr) == sorted(tr), "trusted_sha256 keys are expected in sorted order"
        assert all(tr[k] == v for k, v in ent.items() if k in tr), "an entry sha differs from its trusted sha"
        assert set(ent) <= set(tr), "entries missing from trusted_sha256"
        data["trusted_sha256"] = {k: v for k, v in tr.items() if k not in ent}
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    table, packed = _bpe(text)
    js = _DECODER % {"table": json.dumps(table, ensure_ascii=False), "text": json.dumps(packed, ensure_ascii=False),
                     "keys": json.dumps(keys)}
    assert not re.search(r"</script|<!--|<script", js, re.I), "packed scene data would break out of its <script> element"
    out = m.group("head") + js + m.group("tail")
    _cache[src] = out
    return out
