from pathlib import Path
from typing import Dict, Optional

import pandas as pd


class AnnotationLoader:
    """
    Utility class for loading pedestrian annotations.
    """

    def __init__(self, annotation_file: str):

        self.annotation_file = Path(annotation_file)

        if not self.annotation_file.exists():
            raise FileNotFoundError(
                f"Annotation file not found:\n{self.annotation_file}"
            )

        self.df = pd.read_csv(self.annotation_file)

    def get_annotation(
        self,
        video: str,
        frame: int,
        pedestrian_id: str
    ) -> Optional[Dict]:

        sample = self.df[
            (self.df["video"] == video) &
            (self.df["frame"] == frame) &
            (self.df["id"] == pedestrian_id)
        ]

        if sample.empty:
            return None

        row = sample.iloc[0]

        return {

            "video": row["video"],

            "frame": int(row["frame"]),

            "pedestrian_id": row["id"],

            "x1": int(row["x1"]),
            "y1": int(row["y1"]),
            "x2": int(row["x2"]),
            "y2": int(row["y2"]),

            "action": row["action"],
            "cross": row["cross"],
            "look": row["look"],
            "occlusion": row["occlusion"]

        }

    def get_all_annotations(
        self,
        video: str,
        frame: int
    ):

        return self.df[
            (self.df["video"] == video) &
            (self.df["frame"] == frame)
        ]