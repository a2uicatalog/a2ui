"""Render narrow SVGs at a 360 px wide viewport; report the rendered text px (computed style x CTM scale) and layout problems."""
import sys, re
from playwright.sync_api import sync_playwright
import check_layout as CL
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    pg = b.new_page(viewport={'width': 360, 'height': 800})
    for f in sys.argv[1:]:
        svg = open(f).read()
        svg = re.sub(r'width="\d+" height="\d+"', 'width="100%"', svg, 1)
        pg.set_content('<body style="margin:0;width:360px">' + svg + '</body>')
        r = pg.evaluate("""() => { const s=document.querySelector('svg'); const k=s.getBoundingClientRect().width/s.viewBox.baseVal.width;
          let m=1e9; for(const t of s.querySelectorAll('text')) m=Math.min(m, parseFloat(t.getAttribute('font-size'))*k);
          return [s.getBoundingClientRect().width, document.documentElement.scrollWidth, m]; }""")
        data = pg.evaluate(CL.JS)
        pr = [x for x in CL.analyse(data) if x[0] != 'leader']
        print(f'{f.rsplit("/",1)[-1]:32} svg_px={r[0]:.0f} page_scrollW={r[1]} min_rendered_font={r[2]:.2f}px problems={len(pr)}', pr[:3])
    b.close()
