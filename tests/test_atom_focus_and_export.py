"""Focus and Export on the film demo (owner, 2 Nov: "the focus features plus gif mp4 for this particular demo").
Focus opens the live film large in a modal <dialog>; Export wires ck-70's AtomExport (vendored unmodified) through the inspector's Export tab."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import generate_atom_pages as g  # noqa: E402

FILM = {"type": "motion_arch", "description": "d", "fields": {}, "surfaces": {"works_on": ["web"]}}
STATIC = {"type": "treemap", "description": "d", "fields": {}, "surfaces": {"works_on": ["web"]}}


def _page(atom):
    return g.render_page(atom)


def test_a_film_page_has_an_accessible_focus_dialog():
    html = _page(FILM)
    assert 'id="focus-preview"' in html and 'aria-haspopup="dialog"' in html
    dlg = re.search(r'<dialog id="focus-dialog"[^>]*>', html).group(0)
    assert 'aria-label="Focused view of' in dlg                       # a named dialog
    assert 'id="focus-close"' in html and 'aria-label="Close focused view"' in html   # a visible Close button, not Esc only
    assert 'id="focus-pause"' in html and 'aria-pressed="false"' in html              # Pause is reachable inside the dialog
    assert 'id="focus-zoom"' in html and 'tabindex="0"' in html                        # Zoom 2x, and the stage is a keyboard stop to pan
    assert "showModal" in html and "dlg.close()" in html                               # native modal: focus trap, Esc, inert page


def test_focus_moves_the_film_it_does_not_clone_it_and_gives_focus_back():
    js = g.FOCUS_JS
    assert "stage.appendChild(root)" in js and "cloneNode" not in js   # one clock, one state
    assert "insertBefore(root, mark)" in js and "open.focus()" in js    # back where it was; focus returns to the Focus button
    assert "sizing" in js                                                # our own resize event must not re-enter size() (stack overflow seen once)
    assert "is-custom" in js                                             # not offered for a custom payload frame (a moved iframe would reload)


def test_a_static_page_has_no_focus_button_or_dialog():
    html = _page(STATIC)
    assert 'id="focus-preview"' not in html and "<dialog" not in html


def test_focus_dialog_css_paints_its_own_dim_and_respects_phone_width():
    html = _page(FILM)
    assert ".focus-dialog{" in html and "rgba(8,10,16,.9)" in html
    assert re.search(r"\.focus-btn\{[^}]*min-height:44px", html) and re.search(r"\.focus-close\{[^}]*min-height:44px", html)


def test_export_tab_uses_the_vendored_exporter_lazily():
    assert g.EXPORT_JS.exists()                                          # vendored: the Export tab is emitted in this build
    html = _page(FILM)
    assert 'id="export-row"' in html and 'id="panel-export"' in html
    assert html.count("/vendors/client-export/atom_export.js") == 1      # one script URL, created by the loader
    assert "<script src=\"/vendors/client-export/atom_export.js\"" not in html   # never a blocking tag: loaded on idle or first hover/focus
    assert "requestIdleCallback" in html and "pointerenter" in html and "focusin" in html


def test_export_buttons_come_from_formats_and_gif_is_capped():
    js = g.EXPORT_JS_BLOCK
    assert "X.formats(box)" in js                                        # unsupported formats get no button
    assert "opts.maxSeconds = 6" in js                                   # GIF loops are 6 s
    assert "nod: !!(nod && nod.checked)" in js                           # the nod is opt-in
    assert 'id="export-nod"' in _page(FILM) and "checked" not in re.search(r'<input type="checkbox" id="export-nod"[^>]*>', _page(FILM)).group(0)
    assert "AbortController" in js and "e.name === 'AbortError'" in js    # cancel is not a failure
    assert 'role="progressbar"' in _page(FILM) and 'aria-live="polite"' in _page(FILM)


def test_a_custom_payload_gets_a_plain_note_and_no_export_buttons():
    html = _page(FILM)
    assert "Export works on the example film. To export your own, copy the payload." in html
    assert "syncCustom" in g.EXPORT_JS_BLOCK and "box.classList.contains('is-custom')" in g.EXPORT_JS_BLOCK
    assert ".export-btns[hidden]{display:none}" in html                  # display:flex would otherwise override [hidden]


def test_the_vendored_exporter_is_byte_identical_to_ck_70s_branch():
    src = Path("/mnt/hdd2/work/film-export/public/vendors/client-export/atom_export.js")
    if not src.exists():
        return
    assert g.EXPORT_JS.read_bytes() == src.read_bytes()


def test_export_says_how_long_mp4_takes():
    html = _page(FILM)
    assert "MP4 is the whole film and can take a few minutes" in html and "GIF is the first 6 seconds" in html
    assert "hint.hidden = c" in g.EXPORT_JS_BLOCK                        # not shown beside a custom payload
