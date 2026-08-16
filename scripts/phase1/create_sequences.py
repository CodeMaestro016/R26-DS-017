import pandas as pd
from pathlib import Path

# ==========================================
# Configuration
# ==========================================

WINDOW = 30
STRIDE = 15

# ==========================================
# Load annotations
# ==========================================

df = pd.read_csv(
    "processed_data/metadata/annotations.csv"
)

# Remove irrelevant labels
df = df[df["cross"] != "crossing-irrelevant"].copy()

# Sort by video → pedestrian → frame
df = df.sort_values(
    ["video", "id", "frame"]
)

# ==========================================
# Generate Sequences
# ==========================================

sequences = []
sequence_id = 0

for (video, pedestrian), group in df.groupby(["video", "id"]):

    group = group.reset_index(drop=True)

    if len(group) < WINDOW:
        continue

    for start in range(
        0,
        len(group) - WINDOW + 1,
        STRIDE
    ):

        window = group.iloc[start:start + WINDOW]

        frame_list = window["frame"].astype(str).tolist()

        sequences.append({

            "sequence_id": sequence_id,

            "video": video,

            "pedestrian_id": pedestrian,

            "start_frame": int(window.iloc[0]["frame"]),

            "end_frame": int(window.iloc[-1]["frame"]),

            "frames": "|".join(frame_list),

            "label": window.iloc[-1]["cross"]

        })

        sequence_id += 1

# ==========================================
# Save
# ==========================================

output_dir = Path(
    "processed_data/metadata"
)

output_dir.mkdir(
    parents=True,
    exist_ok=True
)

sequence_df = pd.DataFrame(sequences)

sequence_df.to_csv(
    output_dir / "sequences.csv",
    index=False
)

print("=" * 50)
print("Sequence Generation Complete")
print("=" * 50)

print(f"\nTotal Sequences : {len(sequence_df)}")

print("\nLabel Distribution\n")
print(sequence_df["label"].value_counts())

print("\nSaved To")
print(output_dir / "sequences.csv")