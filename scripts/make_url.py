#!/usr/bin/env python3
"""
make_url.py — encode an A2UI JSON payload into a safe renderer URL.

Usage:
  python3 scripts/make_url.py payloads/brevet_full.json
  python3 scripts/make_url.py payloads/brevet_full.json --renderer gem
  echo '{"blocks":[...]}' | python3 scripts/make_url.py

Large payloads (URL > 8000 chars) are automatically sent via POST and a
curl command is printed instead of a GET URL.

Renderers:
  gem    (default) a2ui-gem-renderer — supports hub, brevet_*, flashcard_deck,
                   knowledge_check, dark_hero, lms atoms, airspace atoms
  main             general a2ui renderer (older, no gzip, no brevet atoms)
"""
import sys, json, zlib, base64, argparse, subprocess, tempfile, os
from urllib.parse import quote

_dep_id = os.environ.get('GAS_DEPLOYMENT_ID', 'YOUR_DEPLOYMENT_ID')
RENDERERS = {
    'gem':  f'https://script.google.com/macros/s/{_dep_id}/exec',
    'main': f'https://script.google.com/macros/s/{_dep_id}/exec',
}

URL_LIMIT = 8000

def make_url(payload, renderer='gem'):
    raw = json.dumps(payload, ensure_ascii=False).encode()
    if renderer == 'gem':
        compressed = zlib.compress(raw, level=9, wbits=31)  # gzip
        enc = base64.urlsafe_b64encode(compressed).rstrip(b'=').decode()
    else:
        enc = quote(base64.b64encode(raw).decode(), safe='')
    return RENDERERS[renderer] + '?p=' + enc, len(raw), len(compressed if renderer == 'gem' else raw)

def emit(url):
    osc52 = f'\033]52;c;{base64.b64encode(url.encode()).decode()}\a'
    sys.stdout.write(osc52)
    sys.stdout.write(f'\033]8;;{url}\033\\{url}\033]8;;\033\\\n')
    sys.stdout.flush()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Encode A2UI payload to renderer URL')
    parser.add_argument('file', nargs='?', help='JSON payload file (default: stdin)')
    parser.add_argument('--renderer', choices=RENDERERS.keys(), default='gem',
                        help='Target renderer (default: gem)')
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            payload = json.load(f)
    else:
        payload = json.load(sys.stdin)

    url, json_len, comp_len = make_url(payload, args.renderer)
    print(f'JSON: {json_len} bytes  |  Compressed: {comp_len} bytes  |  URL: {len(url)} chars', file=sys.stderr)

    if len(url) <= URL_LIMIT:
        emit(url)
    else:
        # Payload too large for GET — write a self-submitting HTML form and open it
        print(f'URL too long ({len(url)} chars > {URL_LIMIT}), opening via POST form...', file=sys.stderr)
        raw_json = json.dumps(payload, ensure_ascii=False)
        endpoint = RENDERERS[args.renderer]
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        tmp.write(f'''<!DOCTYPE html><html><body>
<form id="f" method="POST" action="{endpoint}">
<input type="hidden" name="p" value='{raw_json.replace("'", "&#39;")}'>
</form>
<script>document.getElementById("f").submit();</script>
</body></html>''')
        tmp.close()
        subprocess.Popen(['xdg-open', f'file://{tmp.name}'])
        print(f'Opened in browser via POST.', file=sys.stderr)
