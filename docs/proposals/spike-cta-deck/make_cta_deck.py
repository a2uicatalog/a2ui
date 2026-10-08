#!/usr/bin/env python3
"""Spike for docs/proposals/presentation-templates.md: one hand-built call-to-action slide for the A2UI Catalog.

Built the way the proposal describes: a real title placeholder, shapes added in reading order, alt text, speaker notes,
brand colours taken from atoms/brand-tokens.yaml (dark theme, oklch converted to sRGB), text sizes at or above an 18 pt floor,
and a text-fit check that uses real font metrics. It then READS THE FILE BACK to lint it and to draw a rough preview PNG,
because this machine has no PowerPoint or LibreOffice. The preview is our own approximation, not how PowerPoint or Slides draw it.

  python make_cta_deck.py <out.pptx> [<preview.png>]        (needs python-pptx, qrcode, pillow)
"""
import sys, math, re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.lang import MSO_LANGUAGE_ID
import qrcode
from PIL import Image, ImageDraw, ImageFont

URL = 'https://a2uicatalog.ai'
FONT = 'Roboto'            # brand stack; in Google Slides. Falls back on machines without it (see the fit margin)
FONT_FILES = {False: '/usr/share/fonts/chromeos/roboto/Roboto-Regular.ttf', True: '/usr/share/fonts/chromeos/roboto/Roboto-Bold.ttf'}
FLOOR_PT = 18
SAFETY = 0.88              # use at most 88% of a box's measured capacity so a wider fallback font still fits

# ---- brand colours: oklch -> sRGB (atoms/brand-tokens.yaml, dark theme) ----
def oklch(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3; m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3; s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_, -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_, -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    g = lambda v: 12.92 * v if v <= 0.0031308 else 1.055 * (max(v, 0) ** (1 / 2.4)) - 0.055
    return tuple(max(0, min(255, round(g(v) * 255))) for v in rgb)
BRAND = dict(bg=oklch(.27, .025, 255), surface=oklch(.33, .025, 255), border=oklch(.42, .02, 255), text=oklch(.95, .01, 255), muted=oklch(.72, .02, 255),
             accent=oklch(.72, .16, 277), accent_ink=oklch(.15, .02, 255), accent2=oklch(.75, .12, 202), qr_bg=(255, 255, 255), qr_ink=oklch(.22, .02, 255))
rgb = lambda c: RGBColor(*c)
def lum(c):
    f = lambda v: v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    r, g, b = (f(v / 255) for v in c); return .2126 * r + .7152 * g + .0722 * b
def contrast(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True); return (x + .05) / (y + .05)

# ---- text measurement with the real font ----
def font(pt, bold): return ImageFont.truetype(FONT_FILES[bold], size=int(round(pt * 10)))       # 10 px per pt, so widths are in 1/10 pt
def width_pt(text, pt, bold): return font(pt, bold).getlength(text) / 10
def wrap(text, pt, bold, box_w_pt):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if width_pt(t, pt, bold) <= box_w_pt or not cur: cur = t
        else: lines.append(cur); cur = w
    return lines + ([cur] if cur else [])

def build(out):
    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    layout = prs.slide_layouts[5]                                # "Title Only": the headline is a real title placeholder
    s = prs.slides.add_slide(layout)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(BRAND['bg'])
    fits = []

    def text(shape, runs, pt, bold=False, color=None, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, inset=0.0):
        tf = shape.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = Inches(inset); tf.margin_top = tf.margin_bottom = Inches(inset * .6)
        p = tf.paragraphs[0]; p.alignment = align
        for t, c in runs:
            r = p.add_run(); r.text = t; r.font.size = Pt(pt); r.font.bold = bold; r.font.name = FONT; r.font.color.rgb = rgb(c or color)
            r.font.language_id = MSO_LANGUAGE_ID.ENGLISH_US
        full = ''.join(t for t, _ in runs)
        box_w = shape.width / 12700 - 2 * inset * 72; box_h = shape.height / 12700 - 2 * inset * .6 * 72
        lines = wrap(full, pt, bold, box_w * SAFETY); need = len(lines) * pt * 1.2
        fits.append((shape.name, len(lines), round(need), round(box_h), need <= box_h))
        return shape

    def box(shape_type, x, y, w, h, fill=None, line=None, name=''):
        sh = s.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h)); sh.name = name
        if fill: sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
        else: sh.fill.background()
        if line: sh.line.color.rgb = rgb(line); sh.line.width = Pt(1.25)
        else: sh.line.fill.background()
        sh.shadow.inherit = False
        return sh
    def tb(x, y, w, h, name): sh = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); sh.name = name; return sh

    # reading order = z-order = the order shapes are added
    text(tb(0.8, 0.55, 5, 0.5, 'Wordmark'), [('A2UI', BRAND['accent']), (' Catalog', BRAND['text'])], 22, True, BRAND['text'])
    t = s.shapes.title; t.name = 'Headline'; t.left, t.top, t.width, t.height = Inches(0.8), Inches(1.45), Inches(7.7), Inches(2.45)
    text(t, [('Give your agent a catalogue of interfaces it can compose', None)], 44, True, BRAND['text'], anchor=MSO_ANCHOR.TOP)
    text(tb(0.8, 3.95, 7.4, 1.15, 'Subhead'), [('500+ declarative building blocks. One open schema. Your agent describes the interface; the renderer draws it.', None)], 20, False, BRAND['muted'])
    x = 0.8
    for label in ('Open schema', 'Many surfaces', 'Built for agents'):
        w = width_pt(label, FLOOR_PT, True) / SAFETY / 72 + 0.45      # size the chip from the same margin the fit check uses
        c = box(MSO_SHAPE.ROUNDED_RECTANGLE, x, 5.15, w, 0.5, BRAND['surface'], BRAND['border'], 'Chip: ' + label)
        text(c, [(label, None)], FLOOR_PT, True, BRAND['text'], PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, 0.08); x += w + 0.2
    btn = box(MSO_SHAPE.ROUNDED_RECTANGLE, 0.8, 5.95, 3.9, 0.85, BRAND['accent'], None, 'Button: Try the catalogue')
    text(btn, [('Try the catalogue', None)], 26, True, BRAND['accent_ink'], PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, 0.1)
    btn.click_action.hyperlink.address = URL
    text(tb(4.95, 6.08, 3.6, 0.6, 'Address'), [('a2uicatalog.ai', None)], 22, True, BRAND['accent2'])
    # QR card
    card = box(MSO_SHAPE.ROUNDED_RECTANGLE, 9.05, 1.45, 3.5, 4.3, BRAND['qr_bg'], None, 'QR card')
    qr = qrcode.QRCode(border=1, box_size=12, error_correction=qrcode.constants.ERROR_CORRECT_M); qr.add_data(URL); qr.make(fit=True)
    img = qr.make_image(fill_color=BRAND['qr_ink'], back_color=BRAND['qr_bg']).convert('RGB'); img.save('/tmp/_cta_qr.png')
    pic = s.shapes.add_picture('/tmp/_cta_qr.png', Inches(9.3), Inches(1.7), Inches(3.0), Inches(3.0)); pic.name = 'QR code'
    pic._element.nvPicPr.cNvPr.set('descr', 'QR code that opens a2uicatalog.ai')
    text(tb(9.3, 4.85, 3.0, 0.6, 'QR caption'), [('Scan to open', None)], FLOOR_PT, True, BRAND['accent_ink'], PP_ALIGN.CENTER)
    card._element.nvSpPr.cNvPr.set('descr', '')                      # decorative card behind the QR code
    s.notes_slide.notes_text_frame.text = ('Call to action. Say the one thing: the agent describes the interface, the catalogue draws it. '
                                          'Point at the button or the QR code, both open a2uicatalog.ai.')
    cp = prs.core_properties; cp.title = 'A2UI Catalog: call to action (test deck)'; cp.author = 'A2UI Catalog'; cp.language = 'en-US'
    cp.created = cp.modified = __import__('datetime').datetime(2026, 10, 8, 8, 0, 0)         # fixed, so the same input gives the same file
    prs.save(out); return fits

def lint(path, fits):
    prs = Presentation(path); W, H = prs.slide_width, prs.slide_height; sl = prs.slides[0]; probs = []
    if not sl.shapes.title or not sl.shapes.title.text_frame.text.strip(): probs.append('no slide title')
    for sh in sl.shapes:
        if sh.left < 0 or sh.top < 0 or sh.left + sh.width > W or sh.top + sh.height > H: probs.append(f'{sh.name}: outside the slide')
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size and r.font.size.pt < FLOOR_PT: probs.append(f'{sh.name}: {r.font.size.pt} pt is under the {FLOOR_PT} pt floor')
        if sh.shape_type == 13 and not sh._element.nvPicPr.cNvPr.get('descr'): probs.append(f'{sh.name}: picture without alt text')
    shapes = [sh for sh in sl.shapes]
    rect = lambda sh: (sh.left, sh.top, sh.left + sh.width, sh.top + sh.height)
    inside = lambda a, b: a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]
    for i, a in enumerate(shapes):
        for b in shapes[i + 1:]:
            ra, rb = rect(a), rect(b)
            if ra[0] < rb[2] and rb[0] < ra[2] and ra[1] < rb[3] and rb[1] < ra[3] and not (inside(ra, rb) or inside(rb, ra)):
                probs.append(f'{a.name} overlaps {b.name}')
    probs += [f'{n}: text needs {need} pt of height, box has {have}' for n, _, need, have, ok in fits if not ok]
    pairs = [('headline on background', BRAND['text'], BRAND['bg']), ('subhead on background', BRAND['muted'], BRAND['bg']), ('chip text on chip', BRAND['text'], BRAND['surface']),
             ('button text on button', BRAND['accent_ink'], BRAND['accent']), ('address on background', BRAND['accent2'], BRAND['bg']), ('wordmark accent on background', BRAND['accent'], BRAND['bg']),
             ('QR caption on card', BRAND['accent_ink'], BRAND['qr_bg'])]
    cr = [(n, round(contrast(a, b), 2)) for n, a, b in pairs]; probs += [f'contrast {n}: {v}:1 is under 4.5' for n, v in cr if v < 4.5]
    return probs, cr

def preview(path, out):
    prs = Presentation(path); sl = prs.slides[0]; S = 100 / 914400 * 12700 / 12700   # 1 inch = 100 px
    W, H = int(prs.slide_width / 914400 * 100), int(prs.slide_height / 914400 * 100)
    im = Image.new('RGB', (W, H), BRAND['bg']); d = ImageDraw.Draw(im)
    px = lambda e: e / 914400 * 100
    for sh in sl.shapes:
        x0, y0, x1, y1 = px(sh.left), px(sh.top), px(sh.left + sh.width), px(sh.top + sh.height)
        if sh.shape_type == 13:
            from io import BytesIO; im.paste(Image.open(BytesIO(sh.image.blob)).convert('RGB').resize((int(x1 - x0), int(y1 - y0))), (int(x0), int(y0))); continue
        if sh.shape_type == 1 and sh.fill.type == 1:
            fc = tuple(sh.fill.fore_color.rgb); d.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=fc, outline=tuple(sh.line.color.rgb) if sh.line.fill.type == 1 else None, width=1)
        if sh.has_text_frame and sh.text_frame.text.strip():
            tf = sh.text_frame; ins = px(tf.margin_left); box_w = (x1 - x0) - 2 * ins; y = y0 + px(tf.margin_top)
            runs = [(r.text, r.font.size.pt, bool(r.font.bold), tuple(r.font.color.rgb)) for p in tf.paragraphs for r in p.runs]
            full = ''.join(r[0] for r in runs); pt, bold = runs[0][1], runs[0][2]
            lines = wrap(full, pt, bold, box_w * 72 / 100 * 1.0); lh = pt * 1.2 * 100 / 72
            tot = lh * len(lines)
            if tf.vertical_anchor == MSO_ANCHOR.MIDDLE: y = y0 + ((y1 - y0) - tot) / 2
            fnt = ImageFont.truetype(FONT_FILES[bold], size=int(round(pt * 100 / 72)))
            for ln in lines:
                lw = fnt.getlength(ln); xx = x0 + ins if tf.paragraphs[0].alignment != PP_ALIGN.CENTER else x0 + ((x1 - x0) - lw) / 2
                pos = 0
                for t, _, b, c in runs:                                         # colour per run, left to right
                    seg = ln[pos:pos + len(t)] if len(runs) > 1 else ln
                    if len(runs) > 1 and not seg: break
                    d.text((xx, y), seg, font=fnt, fill=c); xx += fnt.getlength(seg); pos += len(t)
                    if len(runs) == 1: break
                y += lh
    im.save(out)

if __name__ == '__main__':
    out = sys.argv[1]; fits = build(out); probs, cr = lint(out, fits)
    print('text fit:'); [print(f'  {n:34s} {l} line(s), needs {need} pt of {have} pt  {"ok" if ok else "OVERFLOW"}') for n, l, need, have, ok in fits]
    print('contrast:'); [print(f'  {n:34s} {v}:1') for n, v in cr]
    print('lint:', 'clean' if not probs else probs)
    if len(sys.argv) > 2: preview(out, sys.argv[2]); print('preview ->', sys.argv[2])
