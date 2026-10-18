"""Write an explainer film (artifact.html) and its evidence report (report.html) for each problem/fix document.
  python3 film.py                                       # the sample documents -> out/film/<topic>/
  python3 film.py doc.html [--theme theme.json] [--captions proposed.json] [-o out/film]"""
import argparse
import json
import os

import _paths
from reading import film

TOPICS = ('fix_charger', 'fix_router', 'fix_pin', 'fix_photos', 'fix_printer', 'fix_no_resolution', 'fix_many_steps')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docs', nargs='*')
    ap.add_argument('--theme', help='JSON of #rrggbb colours (see rigour/theme.py)')
    ap.add_argument('--captions', help='JSON {slot id: caption} of supplied captions; each must pass the coverage check')
    ap.add_argument('-o', '--out', default=os.path.join(_paths.OUT, 'film'))
    a = ap.parse_args()
    proposals = json.load(open(a.captions)) if a.captions else None
    for p in a.docs or [os.path.join(_paths.FIXTURES, t + '.html') for t in TOPICS]:
        topic = os.path.splitext(os.path.basename(p))[0]
        f = film.build(open(p, encoding='utf-8').read(), f'the {topic.replace("_", " ")} document', proposals, a.theme)
        d = os.path.join(a.out, topic); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'artifact.html'), 'w', encoding='utf-8').write(film.artifact_page(f))
        open(os.path.join(d, 'report.html'), 'w', encoding='utf-8').write(film.report_page(f))
        fired = [k for k, v in f['facts'].items() if v]
        print(f"{topic:<17} {f['status']:<9} {f['built']:<20} steps {len(f['art']['steps'])}  scenes {len(f['timeline']['scenes']):>2}  "
              f"{f['timeline']['duration']:>5.1f}s  fired {fired}  rejected {len(f['rejected'])}")


if __name__ == '__main__':
    main()
