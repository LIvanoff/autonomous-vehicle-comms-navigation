#!/usr/bin/env python3
"""Provided headless visualizer: bag -> PNGs + GIF + HTML. Does not change points."""
import argparse
from pathlib import Path
import html
import json
import numpy as np
import rosbag
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from PIL import Image
from cloud_io import read_xyz


def save_cloud_image(xyz, path, title='', radius=30):
    """Ready function usable after read_xyz(msg); no display, OpenGL or X11."""
    valid = np.isfinite(xyz).all(axis=1)
    p = xyz[valid]
    p = p[np.linalg.norm(p, axis=1) <= radius]
    p = p[::max(1, int(np.ceil(len(p) / 18000)))]
    fig = plt.figure(figsize=(12, 9), dpi=100, facecolor='#f7f9fc')
    fig.suptitle(title, fontsize=15)
    colors = np.clip(p[:, 2], -5, 5) if len(p) else []
    for idx, (a, b, name) in enumerate([(0, 1, 'Сверху: XY'), (0, 2, 'Сбоку: XZ'), (1, 2, 'Спереди: YZ')], 1):
        ax = fig.add_subplot(2, 2, idx)
        ax.scatter(p[:, a], p[:, b], c=colors, s=.55, cmap='viridis', vmin=-5, vmax=5, rasterized=True)
        ax.set(xlim=(-radius, radius), ylim=(-radius, radius), xlabel='XYZ'[a]+' [м]', ylabel='XYZ'[b]+' [м]', title=name)
        ax.set_aspect('equal', adjustable='box')
        ax.axhline(0, color='#53657e', lw=.6); ax.axvline(0, color='#53657e', lw=.6)
        ax.grid(alpha=.2)
    ax = fig.add_subplot(2, 2, 4, projection='3d')
    ax.scatter(p[:, 0], p[:, 1], p[:, 2], c=colors, s=.6, cmap='viridis', vmin=-5, vmax=5)
    ax.set(xlim=(-radius, radius), ylim=(-radius, radius), zlim=(-radius, radius), xlabel='X [м]', ylabel='Y [м]', zlabel='Z [м]', title='3D: камера фиксирована')
    ax.view_init(elev=23, azim=-55)
    # Focal ships matplotlib 3.1; set_box_aspect appeared in 3.3.
    if hasattr(ax, 'set_box_aspect'): ax.set_box_aspect((1, 1, 1))
    fig.tight_layout(rect=(0, 0, 1, .96))
    fig.savefig(str(path)); plt.close(fig)


def render_bag(bag_path, output, topic='/points_raw', step=1.0, radius=30):
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    entries = []; start = None; next_sample = 0.; count = 0; last = None
    with rosbag.Bag(str(bag_path)) as bag:
        for _, msg, t in bag.read_messages(topics=[topic]):
            if start is None: start = t.to_sec()
            elapsed = t.to_sec() - start; last = elapsed; count += 1
            if elapsed + 1e-6 < next_sample: continue
            filename = 'frame_{:03d}.png'.format(len(entries))
            save_cloud_image(read_xyz(msg), out/filename,
                             '{} | t={:.2f} c | {}'.format(topic, elapsed, msg.header.frame_id), radius)
            entries.append({'file': filename, 't': elapsed})
            next_sample += step
    if not entries: raise ValueError('No PointCloud2 messages on '+topic)
    images = [Image.open(out/e['file']).convert('RGB') for e in entries]
    durations = [max(20, int(1000*(entries[i+1]['t']-entries[i]['t']))) for i in range(len(entries)-1)]
    durations.append(max(20, int(1000*step)))
    images[0].save(out/'animation.gif', save_all=True, append_images=images[1:], duration=durations, loop=0)
    for im in images: im.close()
    body = ''.join('<p>t={:.2f} с</p><img src="{}" loading="lazy">'.format(e['t'], e['file']) for e in entries)
    (out/'index.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><title>Просмотр облака</title><style>body{font:18px Segoe UI,sans-serif;max-width:1200px;margin:25px auto;background:#f7f9fc}img{width:100%}code{font-family:Consolas}</style><h1>Облако точек: '+html.escape(topic)+'</h1><p>Фиксированные оси, одинаковый масштаб. Цвет — координата Z от −5 до +5 м. Для просмотра выбираются точки в радиусе '+str(radius)+' м; в выходном бэге точки не прореживаются. GIF — временная выборка, не каждый скан.</p><img src="animation.gif">'+body+'</html>', encoding='utf-8')
    (out/'preview.json').write_text(json.dumps({'messages': count, 'span_s': last, 'sampled_frames': len(entries), 'topic': topic}, indent=2))
    print('Preview:', out/'index.html', 'messages:', count, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('bag'); parser.add_argument('--out', required=True)
    parser.add_argument('--topic', default='/points_raw')
    parser.add_argument('--step', type=float, default=1.)
    parser.add_argument('--radius', type=float, default=30.)
    args = parser.parse_args()
    if args.step <= 0 or args.radius <= 0: parser.error('step/radius must be positive')
    render_bag(args.bag, args.out, args.topic, args.step, args.radius)
