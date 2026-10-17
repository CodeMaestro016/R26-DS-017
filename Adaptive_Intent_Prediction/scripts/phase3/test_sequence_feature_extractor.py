import pandas as pd

from utils.sequence_feature_extractor import SequenceFeatureExtractor

# -------------------------------------------------
# Load one sequence from train.csv
# -------------------------------------------------

train_df = pd.read_csv(
    "datasets/processed/metadata/train.csv"
)

sequence = train_df.iloc[0]

print("=" * 60)
print("Sequence Information")
print("=" * 60)

print(sequence)

print()

# -------------------------------------------------
# Create Extractor
# -------------------------------------------------

extractor = SequenceFeatureExtractor(

    frame_root="datasets/processed/frames",

    annotation_csv="datasets/processed/metadata/annotations.csv",

    dataset_set="set01"
)

# -------------------------------------------------
# Extract Features
# -------------------------------------------------

features = extractor.extract(
    sequence
)

print("=" * 60)
print("Extraction Complete")
print("=" * 60)

print()

print("Feature Shape")

print(features.shape)

print()

print("First Frame Feature Shape")

print(features[0].shape)

print()

print("First 20 Values")

print(features[0][:20])