from __future__ import annotations

import argparse
import json
import os
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from PIL import Image

ANNOTATIONS = Path('datasets/processed/metadata/annotations.csv')
FRAMES_ROOT = Path('datasets/processed/frames')
DEFAULT_OUTPUT = Path('datasets/processed/yolo_pedestrian')
ALLOWED_OCCLUSIONS = {'none', 'part'}
SEED = 42


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    p.add_argument('--negative-ratio', type=float, default=0.10)
    p.add_argument('--overwrite', action='store_true')
    p.add_argument('--copy-mode', choices=['hardlink', 'copy'], default='hardlink')
    return p.parse_args()


def norm_occ(v):
    t = str(v).strip().lower()
    return {'partial': 'part', 'fully-occluded': 'full', 'partially-occluded': 'part'}.get(t, t)


def set_from_id(pid):
    prefix = str(pid).strip().split('_', 1)[0]
    if not prefix.isdigit():
        raise ValueError(f'Cannot derive PIE set from pedestrian id: {pid!r}')
    return f'set{int(prefix):02d}'


def choose_split(video_keys):
    by_set = defaultdict(list)
    for key in sorted(set(video_keys)):
        s, _ = key.split('/', 1)
        by_set[s].append(key)
    val = set()
    for s, keys in sorted(by_set.items()):
        if len(keys) < 2:
            raise RuntimeError(f'{s} needs at least 2 videos for video-level train/val split')
        val.add(sorted(keys)[-1])
    train = set(video_keys) - val
    if train & val:
        raise RuntimeError('Train/val video leakage detected')
    return train, val


def find_frame(dataset_set, video, frame):
    base = FRAMES_ROOT / dataset_set / video
    for ext in ('.jpg', '.jpeg', '.png'):
        p = base / f'frame_{int(frame):06d}{ext}'
        if p.exists():
            return p
    return None


def link_or_copy(src, dst, mode):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    if mode == 'hardlink':
        try:
            os.link(src, dst)
            return 'hardlink'
        except OSError:
            shutil.copy2(src, dst)
            return 'copy-fallback'
    shutil.copy2(src, dst)
    return 'copy'


def to_yolo(row, width, height):
    x1 = max(0.0, min(float(width), float(row.x1)))
    y1 = max(0.0, min(float(height), float(row.y1)))
    x2 = max(0.0, min(float(width), float(row.x2)))
    y2 = max(0.0, min(float(height), float(row.y2)))
    bw, bh = x2 - x1, y2 - y1
    if bw <= 1 or bh <= 1:
        raise ValueError('degenerate bbox')
    xc = (x1 + x2) / 2 / width
    yc = (y1 + y2) / 2 / height
    nw = bw / width
    nh = bh / height
    vals = (xc, yc, nw, nh)
    if not all(0 <= v <= 1 for v in vals):
        raise ValueError(f'normalized bbox outside [0,1]: {vals}')
    return f'0 {xc:.8f} {yc:.8f} {nw:.8f} {nh:.8f}', bw, bh


def frame_number(path):
    token = path.stem.replace('frame_', '', 1)
    return int(token) if token.isdigit() else None


def main():
    args = parse_args()
    if args.negative_ratio < 0:
        raise ValueError('--negative-ratio must be >= 0')
    print('=' * 106)
    print('PHASE 9.5A - BUILD PIE SET01+SET02 YOLO PEDESTRIAN DATASET')
    print('=' * 106)

    if not ANNOTATIONS.exists():
        raise FileNotFoundError(ANNOTATIONS)
    if not FRAMES_ROOT.exists():
        raise FileNotFoundError(FRAMES_ROOT)

    out = args.output
    if out.exists():
        if not args.overwrite:
            raise FileExistsError(f'{out} exists. Re-run with --overwrite to rebuild.')
        shutil.rmtree(out)
    for split in ('train', 'val'):
        (out / 'images' / split).mkdir(parents=True, exist_ok=True)
        (out / 'labels' / split).mkdir(parents=True, exist_ok=True)

    ann = pd.read_csv(ANNOTATIONS)
    required = {'video','frame','id','x1','y1','x2','y2','occlusion'}
    missing = required - set(ann.columns)
    if missing:
        raise KeyError(f'Missing columns: {sorted(missing)}')

    ann = ann.copy()
    ann['dataset_set'] = ann['id'].map(set_from_id)
    ann = ann[ann['dataset_set'].isin({'set01','set02'})].copy()
    ann['video'] = ann['video'].astype(str)
    ann['frame'] = pd.to_numeric(ann['frame'], errors='raise').astype(int)
    ann['occ'] = ann['occlusion'].map(norm_occ)
    ann['video_key'] = ann['dataset_set'] + '/' + ann['video']

    video_keys = sorted(ann['video_key'].unique())
    train_videos, val_videos = choose_split(video_keys)
    split_of = {k: 'train' for k in train_videos} | {k: 'val' for k in val_videos}

    print('TRAIN videos:')
    for k in sorted(train_videos): print(' ', k)
    print('VAL videos:')
    for k in sorted(val_videos): print(' ', k)
    print('Direct detector labels: occlusion NONE + PART')
    print('FULL: excluded from direct labels; reserved for tracking/severe-occlusion evaluation')

    all_ped_frames = defaultdict(set)
    positive_groups = {}
    for key, g in ann.groupby('video_key'):
        all_ped_frames[key] = set(g['frame'])
        allowed = g[g['occ'].isin(ALLOWED_OCCLUSIONS)]
        for f, fg in allowed.groupby('frame'):
            positive_groups[(key, int(f))] = fg.copy()

    pos_by_video = Counter(key for key, _ in positive_groups)
    rng = random.Random(SEED)
    negative_selected = []
    for key in video_keys:
        dataset_set, video = key.split('/', 1)
        base = FRAMES_ROOT / dataset_set / video
        files = []
        for ext in ('*.jpg','*.jpeg','*.png'):
            files.extend(base.glob(ext))
        candidates = []
        for p in sorted(files):
            f = frame_number(p)
            if f is not None and f not in all_ped_frames[key]:
                candidates.append((key, f, p))
        n = min(int(round(pos_by_video[key] * args.negative_ratio)), len(candidates))
        if n:
            negative_selected.extend(rng.sample(candidates, n))

    stats = defaultdict(Counter)
    occ_stats = defaultdict(Counter)
    copy_stats = Counter()
    size_cache = {}
    records = []
    problems = []
    widths, heights = [], []

    def export(key, f, rows=None, source=None, negative=False):
        split = split_of[key]
        dataset_set, video = key.split('/', 1)
        src = source or find_frame(dataset_set, video, f)
        if src is None:
            problems.append(f'MISSING FRAME: {key}/frame_{f:06d}')
            return
        if key not in size_cache:
            with Image.open(src) as im:
                size_cache[key] = im.size
        w, h = size_cache[key]
        stem = f'{dataset_set}_{video}_frame_{f:06d}'
        img_dst = out / 'images' / split / f'{stem}{src.suffix.lower()}'
        lbl_dst = out / 'labels' / split / f'{stem}.txt'
        copy_stats[link_or_copy(src, img_dst, args.copy_mode)] += 1
        lines = []
        frame_occ = Counter()
        if not negative and rows is not None:
            for row in rows.itertuples(index=False):
                try:
                    line, bw, bh = to_yolo(row, w, h)
                except Exception as exc:
                    problems.append(f'BAD BOX: {key} frame={f} ped={row.id}: {exc}')
                    continue
                lines.append(line)
                widths.append(bw); heights.append(bh)
                frame_occ[row.occ] += 1
                occ_stats[split][row.occ] += 1
        lbl_dst.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
        stats[split]['images'] += 1
        if negative:
            stats[split]['negative_images'] += 1
        else:
            stats[split]['positive_images'] += 1
            stats[split]['boxes'] += len(lines)
        records.append({
            'split': split, 'dataset_set': dataset_set, 'video': video,
            'video_key': key, 'frame': f, 'source_image': str(src),
            'output_image': str(img_dst), 'output_label': str(lbl_dst),
            'is_negative': negative, 'num_boxes': len(lines),
            'none_boxes': int(frame_occ['none']), 'part_boxes': int(frame_occ['part'])
        })

    print('Exporting positive frames...')
    for (key, f), rows in sorted(positive_groups.items()):
        export(key, f, rows=rows)
    print('Exporting true-negative frames...')
    for key, f, src in negative_selected:
        export(key, f, source=src, negative=True)

    yaml = out / 'data.yaml'
    yaml.write_text(
        f'path: {out.resolve().as_posix()}\ntrain: images/train\nval: images/val\n\nnames:\n  0: pedestrian\n',
        encoding='utf-8'
    )
    pd.DataFrame(records).to_csv(out / 'dataset_manifest.csv', index=False)
    (out / 'video_split.json').write_text(json.dumps({
        'split_unit': 'dataset_set/video', 'seed': SEED,
        'train_videos': sorted(train_videos), 'val_videos': sorted(val_videos),
        'video_overlap': sorted(train_videos & val_videos),
        'direct_detection_occlusions': ['none','part'],
        'full_policy': 'excluded from direct detector labels; reserved for tracking/severe-occlusion analysis',
        'negative_ratio': args.negative_ratio
    }, indent=2), encoding='utf-8')
    summary = {
        'stats': {s: dict(stats[s]) for s in ('train','val')},
        'occlusion_boxes': {s: dict(occ_stats[s]) for s in ('train','val')},
        'copy_modes': dict(copy_stats),
        'problem_count': len(problems),
        'bbox_pixels': {
            'min_width': min(widths) if widths else None,
            'median_width': float(pd.Series(widths).median()) if widths else None,
            'min_height': min(heights) if heights else None,
            'median_height': float(pd.Series(heights).median()) if heights else None,
        },
        'data_yaml': str(yaml)
    }
    (out / 'build_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (out / 'build_problems.txt').write_text('\n'.join(problems), encoding='utf-8')

    print('-' * 106)
    for split in ('train','val'):
        s = stats[split]
        print(f'{split.upper():5s} images={s["images"]} positive={s["positive_images"]} negative={s["negative_images"]} boxes={s["boxes"]} none={occ_stats[split]["none"]} part={occ_stats[split]["part"]}')
    print('Video overlap:', sorted(train_videos & val_videos))
    print('Problems:', len(problems))
    if widths:
        print(f'BBox width  min/median: {min(widths):.1f}/{pd.Series(widths).median():.1f}px')
        print(f'BBox height min/median: {min(heights):.1f}/{pd.Series(heights).median():.1f}px')
    print('Dataset YAML:', yaml)
    print('Summary:', out / 'build_summary.json')
    print('Problems file:', out / 'build_problems.txt')
    if train_videos & val_videos:
        raise RuntimeError('FAILED: video leakage')
    if stats['train']['boxes'] == 0 or stats['val']['boxes'] == 0:
        raise RuntimeError('FAILED: zero boxes in train or val')
    print('Status: PASSED')
    print('=' * 106)


if __name__ == '__main__':
    main()
