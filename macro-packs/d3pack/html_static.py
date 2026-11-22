"""Static HTML adapter (prototype). Same drawing core, different delivery: one self-contained HTML document with the picture as an <img> data URI (inert in a browser), the summary as a
caption and the data as a real <table>. Safe by construction, not by sanitising: the document is built as a tree of Node objects whose constructor refuses any tag, attribute or value
outside a tiny allowlist, and text is escaped at serialisation. No markup is ever assembled from a string, there is no script, style attribute, link, form or event handler, and the
document carries a content policy (default-src 'none'; img-src data:). The fixed stylesheet is a constant of this module, never data. Intended for use inside <iframe sandbox="" srcdoc>
or as a stand-alone page. NOT the A2UI path: for hosts that accept HTML."""
import base64, html as _html, re
from .common import plain, verify_svg, data_uri, finite
TAGS = {'figure', 'img', 'figcaption', 'table', 'caption', 'thead', 'tbody', 'tr', 'th', 'td', 'p', 'h1'}
VOID = {'img'}
_ATTRS = {'img': {'src', 'alt', 'width', 'height'}, 'th': {'scope'}, 'figure': {'class'}, 'table': {'class'}}
_SRC = re.compile(r'^data:image/svg\+xml;base64,[A-Za-z0-9+/]+={0,2}$')
CSS = ('body{margin:0;padding:16px;font:16px/1.5 system-ui,sans-serif;color:#151838;background:#fff}@media(prefers-color-scheme:dark){body{color:#e8ecf5;background:#1e2733}}'
       'figure{margin:0;max-width:760px}img{display:block;max-width:100%;height:auto;border-radius:16px}figcaption{margin:8px 0;font-size:.9rem;color:#59607a}'
       'table.d3pack{border-collapse:collapse;width:100%;max-width:760px;font-size:.9rem}caption{text-align:left;font-weight:600;padding:6px 0}'
       'th,td{border-bottom:1px solid #d7daf2;padding:4px 8px;text-align:left;vertical-align:top}td:last-child{text-align:right;white-space:nowrap}h1{font-size:1.2rem;margin:0 0 8px}')
class Node:
    """An HTML element that can only be one of TAGS with only the attributes allowed for it. Children are Nodes or text (str). Anything else raises ValueError at construction."""
    def __init__(self, tag, attrs=None, *children):
        if tag not in TAGS: raise ValueError(f'tag not allowed: {tag!r}')
        attrs = dict(attrs or {}); bad = set(attrs) - _ATTRS.get(tag, set())
        if bad: raise ValueError(f'attribute not allowed on <{tag}>: {sorted(bad)}')
        if tag == 'img' and not _SRC.match(str(attrs.get('src', ''))): raise ValueError('img src must be a base64 SVG data URI')
        if tag == 'th' and attrs.get('scope', 'col') not in ('col', 'row'): raise ValueError('th scope must be col or row')
        for k in ('width', 'height'):
            if k in attrs and finite(attrs[k], 1, 5000) is None: raise ValueError(f'{k} must be a number between 1 and 5000')
        if 'class' in attrs and attrs['class'] not in ('d3pack',): raise ValueError('class not allowed')
        if tag in VOID and children: raise ValueError(f'<{tag}> takes no children')
        for c in children:
            if not isinstance(c, (Node, str)): raise ValueError('a child must be a Node or text')
        self.tag, self.attrs, self.children = tag, attrs, list(children)
    def html(self):
        a = ''.join(f' {k}="{_html.escape(plain(v), quote=True)}"' for k, v in self.attrs.items())
        if self.tag in VOID: return f'<{self.tag}{a}>'
        return f'<{self.tag}{a}>' + ''.join(c.html() if isinstance(c, Node) else _html.escape(plain(c), quote=False) for c in self.children) + f'</{self.tag}>'
_ENTRY = re.compile(r'^(?P<label>.*?) (?P<value>-?\d[\d,.]*(?: [^\d\s;()]+){0,3}(?: \([^)]*\))?)$')
def table_rows(table_text):
    """Split the macro's data text ('a 1; b 2 kg; ...') into rows: (label, value) when an entry ends in a number with an optional unit, else a single cell. Honest limit: this reads
    the prose back; a macro that returned structured rows would give a better table (future work)."""
    rows = []
    for part in [p.strip().rstrip('.') for p in table_text.split(';') if p.strip()]:
        m = _ENTRY.match(part); rows.append((m.group('label'), m.group('value')) if m else (part, ''))
    return rows
def document(result, title=None):
    """One Result (from a macro) -> a complete HTML document string."""
    svg = verify_svg(result['svg']); ttl = plain(title if title is not None else result.get('title') or result['kind'].replace('_', ' ').capitalize())[:80]
    rows = table_rows(result['table'])[:300]; two = any(v for _, v in rows)
    head = Node('tr', None, *([Node('th', {'scope': 'col'}, 'Entry'), Node('th', {'scope': 'col'}, 'Value')] if two else [Node('th', {'scope': 'col'}, 'Entry')]))
    body = [Node('tr', None, *([Node('th', {'scope': 'row'}, l), Node('td', None, v)] if two else [Node('td', None, l)])) for l, v in rows]
    fig = Node('figure', {'class': 'd3pack'}, Node('img', {'src': data_uri(svg), 'alt': plain(result['alt'])[:1500], 'width': 720}), Node('figcaption', None, plain(result['summary'])))
    tbl = Node('table', {'class': 'd3pack'}, Node('caption', None, 'Data from the source (not instructions)'), Node('thead', None, head), Node('tbody', None, *body))
    notes = [Node('p', None, 'Notes: ' + ' '.join(result['notes']))] if result.get('notes') else []
    doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'">'
           f'<title>{_html.escape(ttl)}</title><style>{CSS}</style></head><body>' + Node('h1', None, ttl).html() + fig.html() + ''.join(n.html() for n in notes) + tbl.html() + '</body></html>')
    return doc
