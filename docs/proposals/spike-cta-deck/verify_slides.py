#!/usr/bin/env python3
"""Verify a PPTX the way Google Slides actually sees it, with no clicking: upload it with conversion, read back what Google parsed, fetch a PNG
per slide, and delete the test file. Dev-time test harness only: it sends the deck to Google, so use test content.

  python verify_slides.py <deck.pptx> <out-dir> [--keep]

Auth: the service account `slides-verifier` in the project is impersonated from your gcloud account (no key file anywhere):
  gcloud auth login --account=<owner>      # once
Environment (defaults match the spike):
  A2UI_GCP_ACCOUNT  a2uicatalog@krygier.co.uk      A2UI_GCP_PROJECT  artful-patrol-502116-b7      A2UI_SA  slides-verifier
  A2UI_DRIVE_FOLDER REQUIRED: id of a folder (or the root) inside a SHARED DRIVE with the service account as Content manager. Service accounts have no
                    storage of their own (a plain upload fails with storageQuotaExceeded, and presentations.create is refused), but files that belong
                    to a Shared Drive count against no one. The converted file is created there, so you can open it.

Writes <out-dir>/slide-N.png (Google's own render), <out-dir>/parsed.json (what Slides read: shapes, text, fonts, sizes) and prints a summary.
The converted file lives in your Shared Drive; it is deleted at the end unless --keep."""
import json, os, subprocess, sys, urllib.request, urllib.parse, uuid
from pathlib import Path

ACCOUNT = os.environ.get('A2UI_GCP_ACCOUNT', 'a2uicatalog@krygier.co.uk')
PROJECT = os.environ.get('A2UI_GCP_PROJECT', 'artful-patrol-502116-b7')
SA = f"{os.environ.get('A2UI_SA', 'slides-verifier')}@{PROJECT}.iam.gserviceaccount.com"
SCOPES = 'https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/presentations'
PPTX = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
SLIDES = 'application/vnd.google-apps.presentation'

def token():
    r = subprocess.run(['gcloud', 'auth', 'print-access-token', f'--account={ACCOUNT}', f'--impersonate-service-account={SA}', f'--scopes={SCOPES}'],
                       capture_output=True, text=True, timeout=60)
    t = r.stdout.strip()
    if r.returncode or len(t) < 100: raise SystemExit('could not mint a token for the service account:\n' + (r.stderr or r.stdout)[-500:])
    return t

def call(tok, method, url, body=None, headers=None, raw=False):
    req = urllib.request.Request(url, data=body, method=method, headers={'Authorization': 'Bearer ' + tok, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=120) as r: data = r.read(); return data if raw else (json.loads(data) if data else {})
    except urllib.error.HTTPError as e:
        raise SystemExit(f'{method} {url.split("?")[0]} -> HTTP {e.code}: {e.read().decode()[:400]}')

def upload_convert(tok, path):
    """Drive multipart upload; asking for the Google Slides MIME type makes Drive convert the PPTX on import (the same conversion a user gets)."""
    b = '----a2ui' + uuid.uuid4().hex
    meta = {'name': 'a2ui-verify-' + Path(path).stem, 'mimeType': SLIDES}
    if not os.environ.get('A2UI_DRIVE_FOLDER'): raise SystemExit('set A2UI_DRIVE_FOLDER to a folder (or the root) of a Shared Drive that has the service account as Content manager: a service account has no Drive storage of its own, so it cannot create files anywhere else')
    meta['parents'] = [os.environ['A2UI_DRIVE_FOLDER']]
    meta = json.dumps(meta).encode()
    body = (f'--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'.encode() + meta + f'\r\n--{b}\r\nContent-Type: {PPTX}\r\n\r\n'.encode()
            + Path(path).read_bytes() + f'\r\n--{b}--'.encode())
    return call(tok, 'POST', 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true&fields=id,name,mimeType',
                body, {'Content-Type': f'multipart/related; boundary={b}'})

def summarise(pres):
    out = {'title': pres.get('title'), 'pageSize': pres.get('pageSize'), 'slides': []}
    for sl in pres.get('slides', []):
        els = []
        for pe in sl.get('pageElements', []):
            e = {'id': pe['objectId'], 'kind': next((k for k in ('shape', 'image', 'table', 'line', 'sheetsChart', 'video', 'elementGroup') if k in pe), 'other'),
                 'x_in': round(pe.get('transform', {}).get('translateX', 0) / 914400, 2), 'y_in': round(pe.get('transform', {}).get('translateY', 0) / 914400, 2)}
            sz = pe.get('size', {}); e['w_in'] = round(sz.get('width', {}).get('magnitude', 0) * pe.get('transform', {}).get('scaleX', 1) / 914400, 2)
            e['h_in'] = round(sz.get('height', {}).get('magnitude', 0) * pe.get('transform', {}).get('scaleY', 1) / 914400, 2)
            runs = []
            for te in pe.get('shape', {}).get('text', {}).get('textElements', []):
                tr = te.get('textRun')
                if tr and tr.get('content', '').strip():
                    st = tr.get('style', {}); runs.append({'text': tr['content'].strip()[:60], 'font': st.get('fontFamily'), 'pt': st.get('fontSize', {}).get('magnitude'), 'bold': st.get('bold', False)})
            if runs: e['runs'] = runs
            if pe.get('description'): e['alt'] = pe['description']
            els.append(e)
        out['slides'].append({'id': sl['objectId'], 'elements': els, 'notes_present': bool(sl.get('slideProperties', {}).get('notesPage'))})
    return out

def trash(tok, fid):
    """A Content manager of a Shared Drive may trash files but not delete them for good (Drive answers a permanent delete with a misleading 404),
    so move the test file to the drive's trash, which Drive empties on its own after 30 days."""
    call(tok, 'PATCH', f'https://www.googleapis.com/drive/v3/files/{fid}?supportsAllDrives=true&fields=id,trashed', json.dumps({'trashed': True}).encode(),
         {'Content-Type': 'application/json'})
    print('test file moved to the Shared Drive trash')

def main(pptx, out_dir, keep=False):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    tok = token(); f = upload_convert(tok, pptx); fid = f['id']; print(f'uploaded and converted: {f["name"]} ({fid})')
    try:
        pres = call(tok, 'GET', f'https://slides.googleapis.com/v1/presentations/{fid}')
        summ = summarise(pres); (out / 'parsed.json').write_text(json.dumps(summ, indent=1))
        for i, sl in enumerate(pres['slides'], 1):
            t = call(tok, 'GET', f'https://slides.googleapis.com/v1/presentations/{fid}/pages/{sl["objectId"]}/thumbnail?thumbnailProperties.mimeType=PNG&thumbnailProperties.thumbnailSize=LARGE')
            png = urllib.request.urlopen(t['contentUrl'], timeout=60).read(); (out / f'slide-{i}.png').write_bytes(png)
            print(f'  slide {i}: {t["width"]}x{t["height"]} px -> {out / f"slide-{i}.png"}')
        fonts = sorted({r['font'] for s in summ['slides'] for e in s['elements'] for r in e.get('runs', []) if r.get('font')})
        print('fonts as Slides read them:', fonts); print('elements per slide:', [len(s['elements']) for s in summ['slides']])
    finally:
        if not keep: trash(tok, fid)

if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if len(a) != 2: raise SystemExit(__doc__)
    main(a[0], a[1], '--keep' in sys.argv)
