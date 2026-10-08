#!/usr/bin/env python3
"""Build the same slide NATIVELY with the Google Slides API (create, shapes, text, links, alt text, notes), instead of uploading a PPTX for Google to
convert. The PPTX the spike already writes is the intermediate representation: this reads its shapes back and emits Slides API requests, so both routes
start from exactly the same slide and any difference is the route, not the design.

  A2UI_DRIVE_FOLDER=<shared drive folder id> python build_native_slides.py <deck.pptx> <out-dir>

What the API cannot do, as met while writing this (also listed in docs/proposals/presentation-templates.md section 19):
  - set the slide size: a new presentation is 10 x 5.625 in, so everything is scaled by 0.75 (13.333 x 7.5 in in the PPTX), fonts included
  - set text insets: text boxes keep Slides' default 0.1 in x 0.05 in, so unfilled text boxes are grown and shifted to compensate
  - draw a custom vector shape: the QR code becomes one small rectangle per run of dark modules, grouped
It can do things the import route may lose (checked against the thumbnails): exact fonts, link, alt text and notes set directly."""
import json, os, re, sys, uuid
import importlib.util
from pathlib import Path
from pptx import Presentation
HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('v', HERE / 'verify_slides.py'); v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
EMU_PT = 12700
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
IN_X, IN_Y = 7.2 * EMU_PT, 3.6 * EMU_PT          # Slides' default text insets (left/right, top/bottom)

def rgb(c): return {'rgbColor': {'red': c[0] / 255, 'green': c[1] / 255, 'blue': c[2] / 255}}
def solid(c): return {'solidFill': {'color': rgb(c)}}
def emu(x): return {'magnitude': round(x), 'unit': 'EMU'}
def oid(): return 'o' + uuid.uuid4().hex[:12]

def read_shapes(path):
    prs = Presentation(path); sl = prs.slides[0]; W = prs.slide_width; out = []
    for sh in sl.shapes:
        d = dict(name=sh.name, x=sh.left, y=sh.top, w=sh.width, h=sh.height, kind='other', alt=sh._element.xpath('.//p:cNvPr/@descr') or [''])
        d['alt'] = d['alt'][0]
        d['title'] = sh.is_placeholder
        if sh.shape_type == 5:
            d['kind'] = 'freeform'; pth = sh._element.xpath('.//a:custGeom//a:path')[0]; pw, ph = int(pth.get('w')), int(pth.get('h')); rects = []; cur = []
            for el in pth:
                tag = el.tag.split('}')[1]; pt = el.find('a:pt', NS)
                if tag == 'moveTo': cur = [(int(pt.get('x')), int(pt.get('y')))]
                elif tag == 'lnTo': cur.append((int(pt.get('x')), int(pt.get('y'))))
                elif tag == 'close' and len(cur) >= 3:
                    xs, ys = [p[0] for p in cur], [p[1] for p in cur]
                    rects.append((min(xs) / pw, min(ys) / ph, (max(xs) - min(xs)) / pw, (max(ys) - min(ys)) / ph))
            d['rects'] = rects; d['fill'] = tuple(sh.fill.fore_color.rgb)
        else:
            d['kind'] = 'title' if sh.is_placeholder else ('textbox' if sh.shape_type == 17 else 'shape')
            d['prst'] = (sh._element.xpath('.//a:prstGeom/@prst') or [''])[0]
            d['fill'] = tuple(sh.fill.fore_color.rgb) if sh.fill.type == 1 else None
            d['line'] = (tuple(sh.line.color.rgb), sh.line.width.pt) if sh.line.fill.type == 1 else None
            d['link'] = sh.click_action.hyperlink.address if sh.click_action.hyperlink.address else None
            if sh.has_text_frame and sh.text_frame.text.strip():
                tf = sh.text_frame; p0 = tf.paragraphs[0]
                d['align'] = str(p0.alignment).split('.')[-1].split(' ')[0] if p0.alignment else 'LEFT'
                d['anchor'] = (sh._element.xpath('.//a:bodyPr/@anchor') or ['t'])[0]
                d['runs'] = [(r.text, r.font.size.pt, bool(r.font.bold), tuple(r.font.color.rgb), r.font.name) for p in tf.paragraphs for r in p.runs]
    notes = sl.notes_slide.notes_text_frame.text if sl.has_notes_slide else ''
    bg = tuple(sl.background.fill.fore_color.rgb) if sl.background.fill.type == 1 else None
    return dict(shapes=out + [x for x in []], items=[None]) if False else dict(items=[], W=W, notes=notes, bg=bg, shapes=[s for s in _collect(sl)]) if False else _finish(prs, sl, notes, bg)

def _finish(prs, sl, notes, bg):
    return dict(W=prs.slide_width, H=prs.slide_height, notes=notes, bg=bg, shapes=_all(sl))

def _all(sl):
    res = []
    for sh in sl.shapes: res.append(_one(sh))
    return res

def _one(sh):
    # (kept separate so read_shapes above stays readable)
    d = dict(name=sh.name, x=sh.left, y=sh.top, w=sh.width, h=sh.height, alt=(sh._element.xpath('.//p:cNvPr/@descr') or [''])[0], title=sh.is_placeholder)
    if sh.shape_type == 5:
        d['kind'] = 'freeform'; pth = sh._element.xpath('.//a:custGeom//a:path')[0]; pw, ph = int(pth.get('w')), int(pth.get('h')); rects = []; cur = []
        for el in pth:
            tag = el.tag.split('}')[1]; pt = el.find('a:pt', NS)
            if tag == 'moveTo': cur = [(int(pt.get('x')), int(pt.get('y')))]
            elif tag == 'lnTo': cur.append((int(pt.get('x')), int(pt.get('y'))))
            elif tag == 'close' and len(cur) >= 3:
                xs, ys = [p[0] for p in cur], [p[1] for p in cur]
                rects.append((min(xs) / pw, min(ys) / ph, (max(xs) - min(xs)) / pw, (max(ys) - min(ys)) / ph))
        d['rects'] = rects; d['fill'] = tuple(sh.fill.fore_color.rgb); return d
    d['kind'] = 'title' if sh.is_placeholder else ('textbox' if sh.shape_type == 17 else 'shape')
    d['prst'] = (sh._element.xpath('.//a:prstGeom/@prst') or [''])[0]
    d['fill'] = tuple(sh.fill.fore_color.rgb) if sh.fill.type == 1 else None
    d['line'] = (tuple(sh.line.color.rgb), sh.line.width.pt) if sh.line.fill.type == 1 else None
    d['link'] = sh.click_action.hyperlink.address or None
    d['runs'] = []
    if sh.has_text_frame and sh.text_frame.text.strip():
        tf = sh.text_frame; p0 = tf.paragraphs[0]
        d['align'] = str(p0.alignment).split('.')[-1].split(' ')[0] if p0.alignment else 'LEFT'
        d['anchor'] = (sh._element.xpath('.//a:bodyPr/@anchor') or ['t'])[0]
        d['runs'] = [(r.text, r.font.size.pt, bool(r.font.bold), tuple(r.font.color.rgb), r.font.name) for p in tf.paragraphs for r in p.runs]
    return d

def build(pptx, out_dir):
    created = []
    try: _build(pptx, out_dir, created)
    except BaseException:
        if created: v.trash(v.token(), created[0]); print('half-built file moved to the trash')
        raise

def _build(pptx, out_dir, created):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    spec_ = _finish_read(pptx)
    folder = os.environ.get('A2UI_DRIVE_FOLDER') or sys.exit('set A2UI_DRIVE_FOLDER (a Shared Drive folder with the service account as Content manager)')
    tok = v.token()
    f = v.call(tok, 'POST', 'https://www.googleapis.com/drive/v3/files?supportsAllDrives=true&fields=id,name',
               json.dumps({'name': 'a2ui-native-' + Path(pptx).stem, 'mimeType': v.SLIDES, 'parents': [folder]}).encode(), {'Content-Type': 'application/json'})
    pid = f['id']; created.append(pid); print('created an empty Slides file natively:', f['name'], pid)
    base = f'https://slides.googleapis.com/v1/presentations/{pid}'
    pres = v.call(tok, 'GET', base); PW, PH = pres['pageSize']['width']['magnitude'], pres['pageSize']['height']['magnitude']
    s = PW / spec_['W']; print(f'page is {PW/914400:g} x {PH/914400:g} in; the PPTX slide is {spec_["W"]/914400:.3f} in wide, so scale {s:.3f} (the API cannot change the page size)')
    sid = oid(); first = pres['slides'][0]['objectId']
    v.call(tok, 'POST', base + ':batchUpdate', json.dumps({'requests': [
        {'createSlide': {'objectId': sid, 'insertionIndex': 1, 'slideLayoutReference': {'predefinedLayout': 'TITLE_ONLY'}}},
        {'deleteObject': {'objectId': first}}]}).encode(), {'Content-Type': 'application/json'})
    pres = v.call(tok, 'GET', base); slide = pres['slides'][0]
    title_el = next((e for e in slide['pageElements'] if e.get('shape', {}).get('placeholder', {}).get('type') == 'TITLE'), None)
    notes_id = slide['slideProperties']['notesPage']['notesProperties']['speakerNotesObjectId']
    R = []
    if spec_['bg']: R.append({'updatePageProperties': {'objectId': sid, 'pageProperties': {'pageBackgroundFill': solid(spec_['bg'])}, 'fields': 'pageBackgroundFill.solidFill.color'}})
    def place(x, y, w, h, comp):                            # source EMU -> target EMU, optionally growing a text box by Slides' fixed insets
        gx, gy = (IN_X, IN_Y) if comp else (0, 0)
        return {'size': {'width': emu(w * s + 2 * gx), 'height': emu(h * s + 2 * gy)},
                'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': round(x * s - gx), 'translateY': round(y * s - gy), 'unit': 'EMU'}}
    def text_reqs(obj, d):
        txt = ''.join(r[0] for r in d['runs']); q = [{'insertText': {'objectId': obj, 'insertionIndex': 0, 'text': txt}}]; i = 0
        for t, pt, bold, col, font in d['runs']:
            q.append({'updateTextStyle': {'objectId': obj, 'textRange': {'type': 'FIXED_RANGE', 'startIndex': i, 'endIndex': i + len(t)},
                      'style': {'fontFamily': font or 'Roboto', 'fontSize': {'magnitude': round(pt * s * 4) / 4, 'unit': 'PT'}, 'bold': bold, 'foregroundColor': {'opaqueColor': rgb(col)}},
                      'fields': 'fontFamily,fontSize,bold,foregroundColor'}}); i += len(t)
        al = {'LEFT': 'START', 'CENTER': 'CENTER', 'RIGHT': 'END'}.get(d.get('align', 'LEFT'), 'START')
        q.append({'updateParagraphStyle': {'objectId': obj, 'textRange': {'type': 'ALL'}, 'style': {'alignment': al, 'lineSpacing': 100}, 'fields': 'alignment,lineSpacing'}})
        return q
    for d in spec_['shapes']:
        if d['kind'] == 'title' and title_el:
            tid = title_el['objectId']; cw = title_el['size']['width']['magnitude'] * title_el['transform']['scaleX']; ch = title_el['size']['height']['magnitude'] * title_el['transform']['scaleY']
            nw, nh = d['w'] * s + 2 * IN_X, d['h'] * s + 2 * IN_Y
            R.append({'updatePageElementTransform': {'objectId': tid, 'applyMode': 'ABSOLUTE', 'transform': {'scaleX': nw / title_el['size']['width']['magnitude'], 'scaleY': nh / title_el['size']['height']['magnitude'], 'translateX': round(d['x'] * s - IN_X), 'translateY': round(d['y'] * s - IN_Y), 'unit': 'EMU'}}})
            R += text_reqs(tid, d); R.append({'updateShapeProperties': {'objectId': tid, 'shapeProperties': {'contentAlignment': 'TOP'}, 'fields': 'contentAlignment'}})
        elif d['kind'] in ('textbox', 'shape'):
            o = oid(); filled = d['fill'] is not None
            st = 'ROUND_RECTANGLE' if d['prst'] == 'roundRect' else 'RECTANGLE' if filled else 'TEXT_BOX'
            R.append({'createShape': {'objectId': o, 'shapeType': st, 'elementProperties': {'pageObjectId': sid, **place(d['x'], d['y'], d['w'], d['h'], not filled)}}})
            props = {'shapeBackgroundFill': solid(d['fill']) if filled else {'propertyState': 'NOT_RENDERED'},
                     'outline': ({'outlineFill': solid(d['line'][0]), 'weight': {'magnitude': d['line'][1] * s, 'unit': 'PT'}} if d['line'] else {'propertyState': 'NOT_RENDERED'}),
                     'contentAlignment': 'MIDDLE' if d.get('anchor') == 'ctr' else 'TOP'}
            fields = 'shapeBackgroundFill,outline,contentAlignment'
            if d['link']: props['link'] = {'url': d['link']}; fields += ',link'
            R.append({'updateShapeProperties': {'objectId': o, 'shapeProperties': props, 'fields': fields}})
            if d['runs']: R += text_reqs(o, d)
        elif d['kind'] == 'freeform':
            ids = []
            for rx, ry, rw, rh in d['rects']:
                o = oid(); ids.append(o)
                R.append({'createShape': {'objectId': o, 'shapeType': 'RECTANGLE', 'elementProperties': {'pageObjectId': sid, **place(d['x'] + rx * d['w'], d['y'] + ry * d['h'], rw * d['w'], rh * d['h'], False)}}})
                R.append({'updateShapeProperties': {'objectId': o, 'shapeProperties': {'shapeBackgroundFill': solid(d['fill']), 'outline': {'propertyState': 'NOT_RENDERED'}}, 'fields': 'shapeBackgroundFill,outline'}})
            g = oid(); R.append({'groupObjects': {'groupObjectId': g, 'childrenObjectIds': ids}})
            # The API refuses alt text on a group ("not allowed on group"), so one invisible shape the size of the QR code carries it.
            lab = oid(); R.append({'createShape': {'objectId': lab, 'shapeType': 'RECTANGLE', 'elementProperties': {'pageObjectId': sid, **place(d['x'], d['y'], d['w'], d['h'], False)}}})
            R.append({'updateShapeProperties': {'objectId': lab, 'shapeProperties': {'shapeBackgroundFill': {'propertyState': 'NOT_RENDERED'}, 'outline': {'propertyState': 'NOT_RENDERED'}}, 'fields': 'shapeBackgroundFill,outline'}})
            R.append({'updatePageElementAltText': {'objectId': lab, 'title': 'QR code', 'description': d['alt'] or 'QR code'}})
    if spec_['notes']: R.append({'insertText': {'objectId': notes_id, 'insertionIndex': 0, 'text': spec_['notes']}})
    print(f'sending {len(R)} requests in batches')
    for i in range(0, len(R), 200):
        v.call(tok, 'POST', base + ':batchUpdate', json.dumps({'requests': R[i:i + 200]}).encode(), {'Content-Type': 'application/json'})
    pres = v.call(tok, 'GET', base); (out / 'parsed.json').write_text(json.dumps(v.summarise(pres), indent=1))
    t = v.call(tok, 'GET', f'{base}/pages/{pres["slides"][0]["objectId"]}/thumbnail?thumbnailProperties.mimeType=PNG&thumbnailProperties.thumbnailSize=LARGE')
    import urllib.request; (out / 'slide-1.png').write_bytes(urllib.request.urlopen(t['contentUrl'], timeout=60).read())
    print('thumbnail ->', out / 'slide-1.png', f'({t["width"]}x{t["height"]})', '| file kept in the folder: https://docs.google.com/presentation/d/' + pid + '/edit')

def _finish_read(path):
    prs = Presentation(path); sl = prs.slides[0]
    return dict(W=prs.slide_width, H=prs.slide_height, notes=sl.notes_slide.notes_text_frame.text if sl.has_notes_slide else '',
                bg=tuple(sl.background.fill.fore_color.rgb) if sl.background.fill.type == 1 else None, shapes=_all(sl))

if __name__ == '__main__':
    if len(sys.argv) != 3: raise SystemExit(__doc__)
    build(sys.argv[1], sys.argv[2])
