"""One number, one wire version, everywhere on the public site.

An outside reviewer found the guide hub saying "545 published components" in one copy and "500+" in its film, the home page
saying "550+ atoms", and llms.txt saying both "474 typed atoms" and "573 atoms" while 573 were published. The same hub's film
letter showed "version": "v1.0" where the v1.0 spec's wire const is "1.0".

scripts/gen_atom_count.py owns the typed claims in source files and deploy.yml runs it with --check. These tests are the second
net: they scan the BUILT public outputs (public/**/*.html, *.md, *.txt, *.json, except blog posts and the gallery) so a page
that nobody listed in CLAIMS cannot say a different total either.

  1. Every "<3-digit>[+] [typed|published|UI|atomic] atoms|components" must equal the published count, with no plus sign.
     A per-surface or per-renderer figure must be written "X of N" (N the exact total), which this accepts because the
     hit is then "N atoms" / "N components". A dated measurement (a test run with its own atom count) goes in
     scripts/count_allowlist.txt, one line each with a reason.
  2. No public page or Markdown twin contains "version": "v1.0" (plain, JSON-escaped, or HTML-entity forms).

Source of truth: len(components) of public/catalogue/a2ui-atoms-v1.json, the same figure gen_atom_count.py uses.
"""
import fnmatch
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ALLOWLIST = ROOT / "scripts" / "count_allowlist.txt"

SKIP_DIRS = {"blog", "gallery"}          # posts and the gallery are dated records, not statements of today's catalogue
EXTS = {".html", ".md", ".txt", ".json"}

# The claim is  \b\d{3}\+?\s+(typed |published |UI |atomic )?(atoms|components)\b  (and the hyphenated "573-atom vocabulary").
# Running that regex over the 600 MB of public/parts shards takes over a minute, so the scan finds each "atoms"/"components"
# word first (fast, literal) and tests only the 64 characters in front of it. Same matches, a few seconds in all.
WORD_RE = re.compile(r"(atoms|components|atom|component)\b")
# up to three words may sit between the number and the noun ("573 typed A2UI components", "550+ published A2UI atoms")
NUM_RE = re.compile(r"\b(\d{3})(\+?)")
GAP_RE = re.compile(r"(?:\s+[A-Za-z0-9.-]+){0,3}\s+$")
WINDOW = 64
VERSION_RES = [
    re.compile(r"""["']version["']\s*:\s*["']v1\.0["']"""),                  # plain JSON / Python
    re.compile(r"""\\+["']version\\+["']\s*:\s*\\+["']v1\.0"""),              # JSON inside a JSON string
    re.compile(r"""&quot;version&quot;\s*:\s*&quot;v1\.0&quot;"""),           # HTML-escaped code sample
    re.compile(r"""&#0?34;version&#0?34;\s*:\s*&#0?34;v1\.0"""),
    re.compile(r"""\bversion["']?\s*[:=]\s*["']v1\.0["']"""),
]


def _claims(text):
    """Yield (number, plus, matched_text) for every total-looking claim in text."""
    for w in WORD_RE.finditer(text):
        i = w.start()
        lo = max(0, i - WINDOW)
        window = text[lo:i]
        singular = w.group(1) in ("atom", "component")
        best = None
        for m in NUM_RE.finditer(window):
            rest = window[m.end():]
            # "573-atom vocabulary" needs the singular word; "573 atoms" and "573 typed A2UI components" the plural
            if (singular and rest == "-") or (not singular and GAP_RE.match(rest)):
                best = m          # keep the number nearest the noun: in "550 of 573 atoms" the claim is 573, 550 is the part
        if best:
            yield best.group(1), best.group(2), text[lo + best.start():w.end()]


def published_count():
    return len(json.loads((PUBLIC / "catalogue" / "a2ui-atoms-v1.json").read_text(encoding="utf-8"))["components"])


def _files():
    for dirpath, dirnames, filenames in __import__("os").walk(PUBLIC):
        rel = Path(dirpath).relative_to(PUBLIC)
        if rel.parts and rel.parts[0] in SKIP_DIRS:
            dirnames[:] = []
            continue
        if rel.parts[:1] == ("blog",):
            continue
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix in EXTS:
                yield p


def _allowlist():
    """[(path_glob, match_text, reason)]; every entry must carry a reason."""
    out = []
    for n, line in enumerate(ALLOWLIST.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = [x.strip() for x in line.split("|")]
        assert len(parts) == 3 and all(parts), f"{ALLOWLIST.name}:{n}: need 'path_glob | matched text | reason', got {line!r}"
        out.append(tuple(parts))
    return out


def _allowed(allow, rel, hit):
    return any(fnmatch.fnmatch(rel, g) and hit == m for g, m, _ in allow)


_SCAN = {}


def _scan_public():
    """One pass over the built tree (about 600 MB, mostly public/parts shards): {rel: [(num, plus, hit)]} plus the pages with a v1.0 sample."""
    if not _SCAN:
        claims, versions = {}, []
        for p in _files():
            text = p.read_text(encoding="utf-8", errors="replace")
            rel = p.relative_to(PUBLIC).as_posix()
            c = list(_claims(text))
            if c:
                claims[rel] = c
            if "v1.0" in text and any(rx.search(text) for rx in VERSION_RES):
                versions.append(rel)
        _SCAN.update(claims=claims, versions=versions)
    return _SCAN


def find_bad_counts(n, files=None, allow=None):
    allow = _allowlist() if allow is None else allow
    bad = []
    if files is None:
        items = _scan_public()["claims"].items()
    else:
        items = [((p.relative_to(PUBLIC).as_posix() if PUBLIC in p.parents else p.name), list(_claims(p.read_text(encoding="utf-8")))) for p in files]
    for rel, found in items:
        for num, plus, hit in found:
            if num == str(n) and not plus:
                continue
            if not _allowed(allow, rel, hit):
                bad.append(f"{rel}: {hit!r} (published count is {n}, written exactly with no '+')")
    return bad


def find_bad_versions(files=None):
    if files is None:
        return list(_scan_public()["versions"])
    bad = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        if "v1.0" not in text:
            continue
        if any(rx.search(text) for rx in VERSION_RES):
            bad.append(p.relative_to(PUBLIC).as_posix() if PUBLIC in p.parents else p.name)
    return bad


def test_every_public_total_equals_the_published_count():
    n = published_count()
    assert n > 100
    bad = find_bad_counts(n)
    assert not bad, "public pages state a different atom/component total:\n  " + "\n  ".join(bad[:40]) + (
        "\nfix the generator or content (use the @@ATOMS@@ token on a guide page), or add a dated measurement to scripts/count_allowlist.txt with a reason")


def test_no_public_page_shows_version_v1_0():
    bad = find_bad_versions()
    assert not bad, "sample messages must show the v1.0 wire version \"1.0\", not \"v1.0\": " + ", ".join(bad[:40])


def test_the_scanner_catches_what_it_is_meant_to_catch(tmp_path, monkeypatch):
    import sys
    mod = sys.modules[__name__]
    monkeypatch.setattr(mod, "PUBLIC", tmp_path)
    f = tmp_path / "x.html"
    for text, ok in [("573 atoms", True), ("550+ atoms", False), ("500+ components", False), ("545 published components", False),
                     ("474 typed atoms", False), ("573+ atoms", False), ("507 of 573 components", True), ("a 573-atom vocabulary", True),
                     ("the 480-atom vocabulary", False), ("12 atoms", True)]:
        f.write_text(text)
        assert (find_bad_counts(573, [f], []) == []) is ok, text
    f.write_text("550+ atoms")
    assert find_bad_counts(573, [f], [("x.html", "550+ atoms", "dated")]) == []
    for text, bad in [('{ "version": "v1.0" }', True), ('{ \\"version\\": \\"v1.0\\" }', True), ("{ &quot;version&quot;: &quot;v1.0&quot; }", True),
                      ('{ "version": "1.0" }', False), ("the v1.0 spec", False)]:
        f.write_text(text)
        assert bool(find_bad_versions([f])) is bad, text


def test_every_allowlist_entry_has_a_reason_and_still_matches_something():
    allow = _allowlist()
    for g, m, why in allow:
        assert len(why) > 15, f"allowlist entry {g} | {m} needs a real reason"
        assert any(fnmatch.fnmatch(r, g) and any(h == m for _, _, h in found) for r, found in _scan_public()["claims"].items()), \
            f"stale allowlist entry (no longer in any page): {g} | {m}"


def test_mutated_copies_of_real_pages_are_flagged(tmp_path, monkeypatch):
    """The guard must fail when a real built page is edited to a wrong total. Works on COPIES in a temp tree; the real tree is never touched.
    (An earlier pattern allowed one modifier word, so '573 typed A2UI components' -> '550+ typed A2UI components' went unnoticed.)"""
    import shutil
    import sys
    mod = sys.modules[__name__]
    n = published_count()
    real = PUBLIC
    cases = [  # (real page, text in it, wrong text)
        ("index.html", f"{n} typed A2UI components", "550+ typed A2UI components"),
        ("index.html", f"{n} typed UI atoms", "550+ typed UI atoms"),
        ("atoms.md", f"{n} A2UI components", f"{n - 28} A2UI components"),
        ("what-is-a2ui.md", f"{n} published components", "500+ components"),
        ("llms.txt", f"({n} atoms)", "(545 atoms)"),
        ("about.md", f"**{n} atoms**", "**474 atoms**"),
    ]
    for k, (page, good, bad) in enumerate(cases):
        src = real / page
        assert good in src.read_text(encoding="utf-8"), f"{page} no longer contains {good!r}; update this test"
        root = tmp_path / f"c{k}"
        root.mkdir()
        copy = root / page
        shutil.copy(src, copy)
        copy.write_text(copy.read_text(encoding="utf-8").replace(good, bad, 1), encoding="utf-8")
        monkeypatch.setattr(mod, "PUBLIC", root)
        mod._SCAN.clear()
        try:
            flagged = find_bad_counts(n, allow=[])
        finally:
            mod._SCAN.clear()
        assert any(bad.split(" ", 1)[0].strip("(*") in f for f in flagged), f"{page}: {good!r} -> {bad!r} was not flagged ({flagged[:3]})"
    # and a wrong sample version in a copy
    root = tmp_path / "v"
    root.mkdir()
    (root / "w.html").write_text(real.joinpath("what-is-a2ui/example/index.html").read_text(encoding="utf-8").replace('&quot;version&quot;: &quot;1.0&quot;', '&quot;version&quot;: &quot;v1.0&quot;'), encoding="utf-8")
    monkeypatch.setattr(mod, "PUBLIC", root)
    mod._SCAN.clear()
    try:
        assert find_bad_versions() == ["w.html"]
    finally:
        mod._SCAN.clear()


def test_vendored_catalog_meta_schemas_are_identical():
    # tests/fixtures/a2ui_v1_0_live/README.md says the two copies are byte-identical (audit W6 found the old note claiming otherwise)
    a = (ROOT / "tests/fixtures/a2ui_v1_0_live/catalog_definition_v1_0.json").read_bytes()
    b = (ROOT / "tests/fixtures/a2ui_v1_0_spec/json/catalog_definition.json").read_bytes()
    assert a == b


def test_mcp_readme_state_catalog_size_matches_the_catalogue():
    state = json.loads((PUBLIC / "catalogue/a2ui-state-v1.json").read_text(encoding="utf-8"))
    n = len(state.get("components", {})) + len(state.get("functions", {}))
    assert f"({n} primitives)" in (ROOT / "mcp/README.md").read_text(encoding="utf-8")
