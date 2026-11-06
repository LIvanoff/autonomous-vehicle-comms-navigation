"""Download a deterministic, small ITLP-Campus subset, with attribution in SOURCES.md."""
import concurrent.futures
import csv
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.request

from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parent
BASE = 'https://huggingface.co/datasets/OPR-Project/ITLP-Campus-Outdoor/resolve/main/'
TRACKS = [('07_2023-10-04-day', 'database'),
          ('05_2023-08-15-day', 'day'), ('08_2023-10-11-night', 'night')]


def fetch(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=40) as response:
                return response.read()
        except Exception:
            if attempt == 4:
                raise
            time.sleep(attempt + 1)


def main():
    (ROOT / 'data/images').mkdir(parents=True, exist_ok=True)
    records = []
    for track, group in TRACKS:
        csv_path = ROOT / 'data' / (track + '.csv')
        if not csv_path.exists():
            csv_path.write_bytes(fetch(BASE + track + '/track.csv'))
        rows = list(csv.DictReader(csv_path.read_text().splitlines()))
        # Sampling fixed before inference. No selection by model success.
        indices = range(0, len(rows), 2) if group == 'database' else np.linspace(0, len(rows)-1, 30, dtype=int)
        for idx in indices:
            row = rows[idx]
            name = f'{track}_{row["front_cam_ts"]}.jpg'
            records.append(dict(id=name[:-4], group=group, track=track,
                                image='images/' + name,
                                source=BASE + track + '/front_cam/' + row['front_cam_ts'] + '.png',
                                xy=[float(row['tx']), float(row['ty'])], row=int(idx)))

    def download(record):
        path = ROOT / 'data' / record['image']
        if not path.exists():
            content = fetch(record['source'])
            with Image.open(io.BytesIO(content)) as image:
                image.convert('RGB').resize((640, 360), Image.Resampling.LANCZOS).save(path, quality=90)
        record['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        return record

    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i, record in enumerate(pool.map(download, records), 1):
            if i % 25 == 0:
                print(f'{i}/{len(records)} images; {time.perf_counter()-start:.1f}s', flush=True)
    manifest = dict(dataset='ITLP-Campus Outdoor', license='CC BY 4.0',
                    modifications='Front camera only; deterministic subsample; resized 640x360 JPEG quality=90.',
                    sampling='Database every second row; 30 evenly spaced queries per independent track.',
                    records=records)
    (ROOT / 'data/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    print(f'Done: {len(records)} images, {time.perf_counter()-start:.1f}s', flush=True)


if __name__ == '__main__':
    main()
