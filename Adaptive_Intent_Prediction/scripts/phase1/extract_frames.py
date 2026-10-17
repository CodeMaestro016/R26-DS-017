import cv2
from pathlib import Path

video_root = Path("raw_data/videos")
output_root = Path("processed_data/frames")

for video_file in video_root.rglob("*.mp4"):

    set_name = video_file.parent.name
    video_name = video_file.stem

    save_dir = output_root / set_name / video_name
    save_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_file))

    frame_idx = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_path = save_dir / f"frame_{frame_idx:06d}.jpg"

        cv2.imwrite(str(frame_path), frame)

        frame_idx += 1

    cap.release()

    print(f"{video_name}: {frame_idx} frames")