"""CPU inference, student retrieval and a self-contained browser report."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import threading
import time

START = time.perf_counter()
import numpy as np
import psutil

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rebuild-db', action='store_true', help='Recompute database descriptors on CPU')
    parser.add_argument('--cached', action='store_true', help='Use cached queries; no neural inference')
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--radius', type=float, default=25, help='Evaluation radius in metres, not similarity threshold')
    parser.add_argument('--out', default='output/attempt01')
    parser.add_argument('--implementation', default='student.py')
    args = parser.parse_args()
    if args.radius <= 0 or args.threads < 1:
        parser.error('radius and threads must be positive')
    impl_path = Path(args.implementation)
    if not impl_path.is_absolute():
        impl_path = ROOT / impl_path
    spec = importlib.util.spec_from_file_location('submission', impl_path)
    submission = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(submission)
    # Fail before inference if student code has not been completed.
    probe = submission.find_top_k(np.array([1., 0.]), np.eye(2), 1)
    if np.asarray(probe).shape != (1,):
        raise ValueError('find_top_k must return one-dimensional indices')
    submission.recall_at_k(np.array([[0]]), np.array([[True]]), 1)
    manifest_path = ROOT / 'data/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    records = manifest['records']
    db = [r for r in records if r['group'] == 'database']
    queries = [r for r in records if r['group'] != 'database']
    assert set(r['id'] for r in db).isdisjoint(r['id'] for r in queries)
    for record in records:
        if digest(ROOT / 'data' / record['image']) != record['sha256']:
            raise ValueError('Image checksum mismatch: ' + record['image'])
    weights = ROOT / 'weights/resnet18-gem_nclt.pth'
    signature = dict(manifest_sha256=digest(manifest_path), weights_sha256=digest(weights),
                     preprocess='PIL bilinear RGB 320x192; ImageNet mean/std; L2 normalization',
                     model_sha256=digest(ROOT/'model.py'), backbone_sha256=digest(ROOT/'third_party/opr_resnet.py'))
    cache_path = ROOT / 'data/descriptors.npz'
    cache = None
    if cache_path.exists():
        with np.load(cache_path, allow_pickle=False) as loaded:
            if json.loads(str(loaded['signature'])) == signature:
                cache = {k: loaded[k].copy() for k in ['database', 'queries']}
    if args.cached and (cache is None or args.rebuild_db):
        raise ValueError('Matching cache missing, or --cached combined with --rebuild-db')
    process = psutil.Process()
    baseline = process.memory_info().rss
    peaks = [baseline]
    stop = threading.Event()
    def monitor():
        while not stop.wait(.02):
            peaks.append(process.memory_info().rss)
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    timings = {}
    versions = dict(numpy=np.__version__, python=platform.python_version())
    inference_times = []
    if not args.cached:
        mark = time.perf_counter()
        from model import load_model, describe
        import torch
        import torchvision
        model = load_model(weights, args.threads)
        versions.update(torch=torch.__version__, torchvision=torchvision.__version__)
        timings['model_import_and_load_s'] = time.perf_counter() - mark
        mark = time.perf_counter()
        describe(model, ROOT/'data'/db[0]['image'])
        timings['warmup_s'] = time.perf_counter() - mark
        def extract(rows, label):
            values = []
            for i, record in enumerate(rows):
                start = time.perf_counter()
                values.append(describe(model, ROOT/'data'/record['image']))
                inference_times.append(time.perf_counter()-start)
                if (i+1) % 25 == 0:
                    print(f'{label}: {i+1}/{len(rows)}', flush=True)
            return np.stack(values)
        mark = time.perf_counter()
        database = extract(db, 'database') if args.rebuild_db or cache is None else cache['database']
        timings['database_s'] = time.perf_counter()-mark
        mark = time.perf_counter()
        query_desc = extract(queries, 'queries')
        timings['queries_s'] = time.perf_counter()-mark
        np.savez_compressed(cache_path, database=database, queries=query_desc, signature=json.dumps(signature))
    else:
        database, query_desc = cache['database'], cache['queries']
    mark = time.perf_counter()
    predictions = np.stack([submission.find_top_k(q, database, 5) for q in query_desc])
    if predictions.shape != (len(queries), 5) or predictions.dtype.kind not in 'iu':
        raise ValueError('Expected integer indices with shape (number of queries, 5)')
    if (predictions < 0).any() or (predictions >= len(db)).any():
        raise ValueError('Index outside database')
    if any(len(set(row)) != 5 for row in predictions):
        raise ValueError('Repeated indices in top-5')
    timings['search_s'] = time.perf_counter()-mark
    db_xy = np.array([r['xy'] for r in db])
    query_xy = np.array([r['xy'] for r in queries])
    distances = np.linalg.norm(query_xy[:, None] - db_xy[None], axis=-1)
    positives = distances <= args.radius
    eligible = positives.any(axis=1)
    metrics = {}
    for group in ['all', 'day', 'night']:
        mask = np.array([group == 'all' or q['group'] == group for q in queries])
        valid = mask & eligible
        metrics[group] = dict(queries=int(mask.sum()), evaluated=int(valid.sum()), without_match=int((mask & ~eligible).sum()))
        for k in (1, 5):
            metrics[group][f'recall@{k}'] = float(submission.recall_at_k(predictions[valid], positives[valid], k)) if valid.any() else None
    results = []
    for i, q in enumerate(queries):
        results.append(dict(query=q, eligible=bool(eligible[i]),
                            nearest_gt=int(distances[i].argmin()),
                            nearest_gt_m=float(distances[i].min()),
                            matches=[dict(index=int(j), metres=float(distances[i,j]),
                                          similarity=float(query_desc[i] @ database[j]),
                                          correct=bool(positives[i,j])) for j in predictions[i]]))
    stop.set(); thread.join()
    memory = process.memory_info()
    peak = max(max(peaks), getattr(memory, 'peak_wset', 0))
    timings['pipeline_before_report_s'] = time.perf_counter()-START
    if inference_times:
        timings.update(per_image_median_s=float(np.median(inference_times)), per_image_p95_s=float(np.percentile(inference_times,95)))
    report = dict(mode='cached descriptors; NO inference' if args.cached else 'CPU float32 neural inference',
                  database_recomputed=bool(not args.cached and (args.rebuild_db or cache is None)),
                  database_count=len(db), query_count=len(queries), radius_m=args.radius,
                  peak_process_rss_mib=peak/1024**2, baseline_rss_mib=baseline/1024**2,
                  memory_method='Process RSS sampled every 20 ms, max with Windows peak working set when available; excludes other applications.',
                  cpu=platform.processor(), logical_cpus=os.cpu_count(), threads=args.threads,
                  os=platform.platform(), versions=versions, timings=timings, metrics=metrics,
                  signature=signature, database=db, results=results)
    out = Path(args.out)
    if not out.is_absolute(): out = ROOT/out
    out.mkdir(parents=True, exist_ok=True)
    from visualization import render
    render(report, ROOT/'data', out)
    report['timings']['total_with_report_s'] = time.perf_counter()-START
    report['peak_process_rss_mib'] = max(report['peak_process_rss_mib'], getattr(process.memory_info(), 'peak_wset', process.memory_info().rss)/1024**2)
    (out/'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['database','results','signature']}, ensure_ascii=False, indent=2))
    print('Report:', out/'index.html', flush=True)


if __name__ == '__main__':
    main()
