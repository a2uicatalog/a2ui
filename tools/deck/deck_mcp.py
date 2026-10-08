#!/usr/bin/env python3
"""A thin MCP server (stdio, newline-delimited JSON-RPC) over deck_build. No model, no network: three tools, the same code as the CLI.
  deck_schema    the layouts and their fields
  deck_validate  check a deck (XML or film-style JSON) and return every error with its slide and field
  deck_build     build the PPTX; returns the report and the file (written to out_dir, and base64 when return_base64 is true)
Register it:  claude mcp add deck -- python /path/to/deck_mcp.py"""
import sys, json, base64, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import deck_build as db

INPUT = {'type': 'string', 'description': 'the deck: XML (<deck><slide layout=...>) or JSON {"scenes":[...]} using the film scene fields'}
TOOLS = [
    dict(name='deck_schema', description='List the slide layouts (title, bullets, stats, quote, cta), their fields and limits, the targets and the film-only scenes.',
         inputSchema=dict(type='object', properties={})),
    dict(name='deck_validate', description='Check a deck without building it. Returns ok, errors (slide, field, exact message) and warnings.',
         inputSchema=dict(type='object', required=['deck'], properties=dict(deck=INPUT, skip_film_only=dict(type='boolean')))),
    dict(name='deck_build', description='Build a PPTX from a deck. Same input, same bytes. Set target to google-slides for the tight layout; omitted means the safe "any" layout.',
         inputSchema=dict(type='object', required=['deck'], properties=dict(deck=INPUT, target=dict(type='string', enum=sorted(db.k.TARGETS)), skip_film_only=dict(type='boolean'),
                                                                        out_dir=dict(type='string', description='where to write deck.pptx and slide previews; default a temp dir'),
                                                                        return_base64=dict(type='boolean')))),
]

def call(name, a):
    if name == 'deck_schema': return db.schema()
    if name == 'deck_validate': return db.run(a['deck'], skip_film_only=bool(a.get('skip_film_only')))
    if name == 'deck_build':
        d = Path(a.get('out_dir') or tempfile.mkdtemp(prefix='deck-')); d.mkdir(parents=True, exist_ok=True)
        rep = db.run(a['deck'], str(d / 'deck.pptx'), a.get('target'), bool(a.get('skip_film_only')), str(d / 'preview'))
        if a.get('return_base64') and 'file' in rep: rep['base64'] = base64.b64encode(Path(rep['file']).read_bytes()).decode()
        return rep
    raise KeyError(name)

def handle(m):
    meth, mid = m.get('method'), m.get('id')
    if meth == 'initialize':
        return dict(protocolVersion=m['params'].get('protocolVersion', '2025-03-26'), capabilities=dict(tools={}), serverInfo=dict(name='deck_build', version='0.1.0'))
    if meth == 'tools/list': return dict(tools=TOOLS)
    if meth == 'tools/call':
        try: out = call(m['params']['name'], m['params'].get('arguments') or {}); bad = isinstance(out, dict) and out.get('ok') is False
        except KeyError as e: return dict(content=[dict(type='text', text=f'unknown tool {e}')], isError=True)
        except SystemExit as e: return dict(content=[dict(type='text', text=str(e))], isError=True)
        return dict(content=[dict(type='text', text=json.dumps(out, indent=1))], isError=False)
    if meth == 'ping': return {}
    if mid is None: return None                                              # notifications get no reply
    raise ValueError(f'method not found: {meth}')

def main():
    for line in sys.stdin:
        if not line.strip(): continue
        m = json.loads(line)
        try: res = handle(m); msg = None if res is None else dict(jsonrpc='2.0', id=m.get('id'), result=res)
        except Exception as e: msg = dict(jsonrpc='2.0', id=m.get('id'), error=dict(code=-32601, message=str(e)))
        if msg: print(json.dumps(msg), flush=True)

if __name__ == '__main__': main()
