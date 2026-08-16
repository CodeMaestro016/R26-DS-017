import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path

df = pd.read_csv(
    "processed_data/metadata/sequences.csv"
)

# Unique pedestrians

pedestrians = (
    df["pedestrian_id"]
    .unique()
)

# 70% train

train_peds, temp_peds = train_test_split(
    pedestrians,
    test_size=0.30,
    random_state=42
)

# 15% val
# 15% test

val_peds, test_peds = train_test_split(
    temp_peds,
    test_size=0.50,
    random_state=42
)

train_df = df[
    df["pedestrian_id"].isin(train_peds)
]

val_df = df[
    df["pedestrian_id"].isin(val_peds)
]

test_df = df[
    df["pedestrian_id"].isin(test_peds)
]

output_dir = Path(
    "processed_data/metadata"
)

train_df.to_csv(
    output_dir / "train.csv",
    index=False
)

val_df.to_csv(
    output_dir / "val.csv",
    index=False
)

test_df.to_csv(
    output_dir / "test.csv",
    index=False
)

print("\nDataset Split Complete")
print("-" * 40)

print(
    f"Train: {len(train_df)}"
)

print(
    f"Validation: {len(val_df)}"
)

print(
    f"Test: {len(test_df)}"
)

print(
    "\nUnique Pedestrians"
)

print(
    f"Train: {len(train_peds)}"
)

print(
    f"Validation: {len(val_peds)}"
)

print(
    f"Test: {len(test_peds)}"
)