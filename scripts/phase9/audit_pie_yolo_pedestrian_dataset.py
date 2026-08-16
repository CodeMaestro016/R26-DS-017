from pathlib import Path
import pandas as pd

ROOT = Path('datasets/processed/yolo_pedestrian')


def main():
    print('=' * 96)
    print('PHASE 9.5A - YOLO DATASET INTEGRITY AUDIT')
    print('=' * 96)
    manifest_path = ROOT / 'dataset_manifest.csv'
    yaml_path = ROOT / 'data.yaml'
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest = pd.read_csv(manifest_path)
    errors = []
    boxes = 0
    for row in manifest.itertuples(index=False):
        image = Path(row.output_image)
        label = Path(row.output_label)
        if not image.exists(): errors.append(f'Missing image: {image}')
        if not label.exists():
            errors.append(f'Missing label: {label}')
            continue
        text = label.read_text(encoding='utf-8').strip()
        if not text: continue
        for n, line in enumerate(text.splitlines(), 1):
            parts = line.split()
            if len(parts) != 5:
                errors.append(f'{label}:{n}: expected 5 tokens')
                continue
            cls = int(parts[0]); vals = [float(v) for v in parts[1:]]
            if cls != 0: errors.append(f'{label}:{n}: class != 0')
            if not all(0 <= v <= 1 for v in vals): errors.append(f'{label}:{n}: coord outside [0,1]')
            if vals[2] <= 0 or vals[3] <= 0: errors.append(f'{label}:{n}: non-positive size')
            boxes += 1
    train_videos = set(manifest.loc[manifest.split == 'train', 'video_key'].astype(str))
    val_videos = set(manifest.loc[manifest.split == 'val', 'video_key'].astype(str))
    overlap = sorted(train_videos & val_videos)
    if overlap: errors.append(f'Video leakage: {overlap}')
    print('Images:', len(manifest))
    print('Boxes :', boxes)
    print('Train videos:', sorted(train_videos))
    print('Val videos  :', sorted(val_videos))
    print('Video overlap:', overlap)
    print('Errors:', len(errors))
    if errors:
        for e in errors[:30]: print(' -', e)
        raise RuntimeError(f'Audit FAILED with {len(errors)} errors')
    print('Dataset YAML:')
    print(yaml_path.read_text(encoding='utf-8'))
    print('Status: PASSED')
    print('=' * 96)


if __name__ == '__main__':
    main()
