from pathlib import Path
import cv2
import numpy as np


class ImageLoader:
    """
    Utility class for loading video frames.
    """

    def __init__(self, frame_root: str):

        self.frame_root = Path(frame_root)

    def load_frame(
        self,
        video: str,
        frame_number: int,
        dataset_set: str = "set01"
    ) -> np.ndarray:

        image_path = (
            self.frame_root /
            dataset_set /
            video /
            f"frame_{frame_number:06d}.jpg"
        )

        image = cv2.imread(str(image_path))

        if image is None:
            raise FileNotFoundError(
                f"Image not found:\n{image_path}"
            )

        return image

    def frame_exists(
        self,
        video: str,
        frame_number: int,
        dataset_set: str = "set01"
    ) -> bool:

        image_path = (
            self.frame_root /
            dataset_set /
            video /
            f"frame_{frame_number:06d}.jpg"
        )

        return image_path.exists()