"""Collision checker for arch_motion SVGs. Measures the REAL geometry in Chromium (getBBox for text, getPointAtLength
sampling for every edge path), so it checks the fonts the browser actually used, not the macro's width estimates.

Needs the ids the macro writes: g<i> group (dashed outline + header text), n<i> node, e<i> edge (paths + label rect/text),
m<j>e<i> message chip j riding edge i.  Run: python3 check_layout.py file1.svg [file2.svg ...]

Fails (counted per file) on:
  overlap      two boxes overlap (node, edge-label, chip, group header text), > 0.5 px each way
  text-out     a text runs outside its own box (node / label / chip rect, group outline) or outside the viewBox
  line-through an edge line passes through another edge's label or chip, through a node it does not connect, or through a group header
  border       a node, label or chip box straddles a group outline
  detached     a chip is more than 12 px from its own edge line, or a label more than 16 px
  hug          an edge runs within 5 px of a group outline for more than 40 px
  font         a font-size under 12 px
  leader       (informational, not a failure) a chip that could not sit next to its edge and is joined to it by a leader line;
               a leader that crosses a box is a line-through failure
"""
import json, re, sys
from playwright.sync_api import sync_playwright

JS = r"""
() => {
  const svg = document.querySelector('svg');
  const out = {vb: svg.getAttribute('viewBox').split(' ').map(Number), items: []};
  const own = el => { let p = el.parentElement; while (p && p !== svg) { if (p.id) return p.id; p = p.parentElement; } return ''; };
  for (const el of svg.querySelectorAll('rect,text,path,circle')) {
    const b = el.getBBox();
    const it = {tag: el.tagName, own: own(el), x: b.x, y: b.y, w: b.width, h: b.height, fs: parseFloat(el.getAttribute('font-size') || '0'),
                txt: el.tagName === 'text' ? el.textContent : '', opac: el.getAttribute('fill-opacity')};
    if (el.tagName === 'path') {
      const L = el.getTotalLength(); const pts = [];
      for (let s = 0; s <= L; s += 2) { const q = el.getPointAtLength(s); pts.push([q.x, q.y]); }
      it.pts = pts;
    }
    out.items.push(it);
  }
  return out;
}
"""


def measure(paths):
    res = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        pg = b.new_page()
        for f in paths:
            pg.set_content('<body style="margin:0">' + open(f).read() + '</body>')
            res[f] = pg.evaluate(JS)
        b.close()
    return res


def ov(a, b, tol=0.5):
    return min(a[2], b[2]) - max(a[0], b[0]) > tol and min(a[3], b[3]) - max(a[1], b[1]) > tol


def inside(inner, outer, tol=1.0):
    return inner[0] >= outer[0] - tol and inner[1] >= outer[1] - tol and inner[2] <= outer[2] + tol and inner[3] <= outer[3] + tol


def box(it):
    return (it['x'], it['y'], it['x'] + it['w'], it['y'] + it['h'])


def dist_pt_box(p, b):
    dx = max(b[0] - p[0], 0, p[0] - b[2]); dy = max(b[1] - p[1], 0, p[1] - b[3])
    return (dx * dx + dy * dy) ** 0.5


def analyse(data):
    vb = (0, 0, data['vb'][2], data['vb'][3])
    items = data['items']
    groups, nodes, labels, chips, headers, edge_pts, edge_ends, texts, leaders = {}, {}, {}, {}, {}, {}, {}, [], {}
    for it in items:
        o = it['own']
        if it['tag'] == 'text':
            texts.append(it)
        if o.startswith('g'):
            if it['tag'] == 'path': groups[o] = box(it)
            elif it['tag'] == 'text': headers[o] = box(it)
        elif o.startswith('n') and it['tag'] == 'rect' and o not in nodes:
            nodes[o] = box(it)
        elif o.startswith('e'):
            if it['tag'] == 'rect': labels[o] = box(it)
            elif it['tag'] == 'path' and it['pts']:
                edge_pts.setdefault(o, []).extend(it['pts']); edge_ends.setdefault(o, []).extend([it['pts'][0], it['pts'][-1]])
        elif o.startswith('m') and it['tag'] == 'rect':
            chips[o] = box(it)
        elif o.startswith('m') and it['tag'] == 'path':
            leaders[o] = it['pts']
    # which nodes each edge connects: the nodes its first/last sample touch (within 3 px)
    ends = {}
    for e, pts in edge_pts.items():
        ends[e] = {n for n, b in nodes.items() for p in edge_ends[e] if dist_pt_box(p, b) < 4}
    probs = []
    boxes = [(k, 'node', b) for k, b in nodes.items()] + [(k, 'label', b) for k, b in labels.items()] + \
            [(k, 'chip', b) for k, b in chips.items()] + [(k, 'header', b) for k, b in headers.items()]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if ov(boxes[i][2], boxes[j][2]):
                probs.append(('overlap', f'{boxes[i][1]} {boxes[i][0]} x {boxes[j][1]} {boxes[j][0]}'))
    for t in texts:
        tb = box(t); o = t['own']
        if not inside(tb, vb, 0): probs.append(('text-out', f'"{t["txt"]}" outside viewBox'))
        host = nodes.get(o) if o.startswith('n') else labels.get(o) if o.startswith('e') else chips.get(o) if o.startswith('m') else groups.get(o)
        if host and not inside(tb, host, 0.5):
            probs.append(('text-out', f'"{t["txt"]}" outside its {o} box by {max(host[0]-tb[0], tb[2]-host[2], host[1]-tb[1], tb[3]-host[3]):.1f}px'))
        if t['fs'] and t['fs'] < 12: probs.append(('font', f'"{t["txt"]}" {t["fs"]}px'))
    for e, pts in edge_pts.items():
        num = e[1:]
        hits = {}
        for p in pts:
            for k, kind, b in boxes:
                sb = (b[0] + 1.5, b[1] + 1.5, b[2] - 1.5, b[3] - 1.5)
                if not (sb[0] < p[0] < sb[2] and sb[1] < p[1] < sb[3]): continue
                if kind == 'label' and k == e: continue
                if kind == 'chip' and k.endswith('e' + num): continue
                if kind == 'node' and k in ends[e]: continue
                hits[(kind, k)] = hits.get((kind, k), 0) + 1
        for (kind, k), c in hits.items():
            if c >= 2: probs.append(('line-through', f'edge {e} through {kind} {k} ({c * 2}px)'))
        hug = 0
        for p in pts:
            near = False
            for gb in groups.values():
                inx = gb[0] - 5 <= p[0] <= gb[2] + 5; iny = gb[1] - 5 <= p[1] <= gb[3] + 5
                if (inx and iny) and (min(abs(p[0] - gb[0]), abs(p[0] - gb[2])) < 5 or min(abs(p[1] - gb[1]), abs(p[1] - gb[3])) < 5):
                    # crossing the border is fine; running along it is not: count only points whose neighbourhood is also near
                    near = True
            hug = hug + 1 if near else 0
            if hug == 21:
                probs.append(('hug', f'edge {e} runs along a group outline for > 40 px'))
    for k, kind, b in boxes:
        if kind == 'header': continue
        for g, gb in groups.items():
            if ov(b, gb, 0) and not inside(b, gb, 0):
                probs.append(('border', f'{kind} {k} straddles group {g}'))
    for k, b in chips.items():
        e = 'e' + k.split('e')[1]
        d = min((dist_pt_box(p, b) for p in edge_pts.get(e, [])), default=1e9)
        if d > 12:
            lp = leaders.get(k, [])
            dl = min((((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5 for p in lp for q in edge_pts.get(e, [])), default=1e9)
            if dl <= 3:
                probs.append(('leader', f'chip {k} is {d:.0f}px from edge {e}, joined by a leader line'))
                crossed = set()
                for p in lp:
                    for kk, kind, bb in boxes:
                        sibling = kind == 'chip' and kk.split('e')[1] == k.split('e')[1]   # a leader may run behind a chip of its own edge
                        if kk != k and not sibling and bb[0] + 2 < p[0] < bb[2] - 2 and bb[1] + 2 < p[1] < bb[3] - 2:
                            crossed.add((kind, kk))
                for kind, kk in sorted(crossed):
                    probs.append(('line-through', f'leader of {k} through {kind} {kk}'))
            else:
                probs.append(('detached', f'chip {k} is {d:.0f}px from edge {e}'))
    for k, b in labels.items():
        d = min((dist_pt_box(p, b) for p in edge_pts.get(k, [])), default=1e9)
        if d > 16: probs.append(('detached', f'label {k} is {d:.0f}px from its edge'))
    return probs


if __name__ == '__main__':
    files = sys.argv[1:]
    verbose = '-v' in files
    files = [f for f in files if f != '-v']
    data = measure(files)
    total = 0
    cats = ['overlap', 'text-out', 'line-through', 'border', 'detached', 'hug', 'font', 'leader']
    print(f'{"file":34} ' + ' '.join(f'{c:>12}' for c in cats) + '  total')
    for f in files:
        probs = analyse(data[f])
        total += sum(1 for p in probs if p[0] != 'leader')
        cnt = {c: sum(1 for p in probs if p[0] == c) for c in cats}
        print(f'{f.rsplit("/", 1)[-1]:34} ' + ' '.join(f'{cnt[c]:12}' for c in cats) + f'  {sum(1 for p in probs if p[0] != "leader")}')
        if verbose:
            for p in probs: print('    ', *p)
    print('TOTAL problems:', total)
    sys.exit(1 if total else 0)
