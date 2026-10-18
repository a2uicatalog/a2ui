"""Write decision blocks (reader.html, operator.html), their iframe embeds and one evidence report per document.
  python3 decision.py                        # the sample documents -> out/decision/<topic>/
  python3 decision.py doc.html [--theme theme.json] [-o out/decision]"""
import argparse
import os

import _paths
from reading import decision

TOPICS = ('fix_router', 'fix_printer', 'fix_charger', 'fix_pin', 'fix_photos')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docs', nargs='*')
    ap.add_argument('--theme')
    ap.add_argument('--preselect', type=int, help='open this case (0-based) on load, for screenshots')
    ap.add_argument('-o', '--out', default=os.path.join(_paths.OUT, 'decision'))
    a = ap.parse_args()
    for p in a.docs or [os.path.join(_paths.FIXTURES, t + '.html') for t in TOPICS]:
        topic = os.path.splitext(os.path.basename(p))[0]
        src = open(p, encoding='utf-8').read()
        d_dir = os.path.join(a.out, topic); os.makedirs(d_dir, exist_ok=True)
        for aud in ('reader', 'operator'):
            d = decision.build(src, f'the {topic.replace("_", " ")} document', aud, a.theme, a.preselect)
            open(os.path.join(d_dir, aud + '.html'), 'w', encoding='utf-8').write(decision.artifact_page(d))
            open(os.path.join(d_dir, f'embed-{aud}.html'), 'w', encoding='utf-8').write(decision.embed_page(d))
            if d['status'] == 'STANDS':
                sn = decision.snippets(d)
                for kind in ('data_uri', 'srcdoc'):
                    open(os.path.join(d_dir, f'snippet-{aud}-{kind}.html'), 'w', encoding='utf-8').write(sn[kind])
        open(os.path.join(d_dir, 'report.html'), 'w', encoding='utf-8').write(decision.report_page(d))
        print(f"{topic:<12} {d['status']:<9} cases {len(d['cases'])}  paired {len(d['paired'])}  "
              f"fired {[k for k, v in d['facts'].items() if v]}  questions {len(d['questions'])}")


if __name__ == '__main__':
    main()
