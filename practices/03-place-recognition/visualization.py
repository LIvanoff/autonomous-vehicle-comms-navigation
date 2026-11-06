"""Offline HTML report with real ITLP images and an XY map (no map service)."""
import base64
import json
from pathlib import Path


def render(report, data_dir, out, embed=True):
    content = dict(report)
    images = {}
    for record in report['database'] + [r['query'] for r in report['results']]:
        images[record['id']] = ('data:image/jpeg;base64,' + base64.b64encode((data_dir/record['image']).read_bytes()).decode()) if embed else '../data/' + record['image']
    content['images'] = images
    template = (Path(__file__).parent/'report_template.html').read_text(encoding='utf-8')
    (out/'index.html').write_text(template.replace('__REPORT_JSON__', json.dumps(content, ensure_ascii=False).replace('</', '<\\/')), encoding='utf-8')
