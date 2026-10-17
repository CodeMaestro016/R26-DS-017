import numpy as np

from utils.image_loader import ImageLoader
from utils.annotation_loader import AnnotationLoader
from utils.cropper import PedestrianCropper

from utils.feature_extractor import AppearanceFeatureExtractor
from utils.spatial import SpatialFeatureExtractor
from utils.motion import MotionFeatureExtractor
from utils.feature_fusion import FeatureFusion


class SequenceFeatureExtractor:

    def __init__(
        self,
        frame_root,
        annotation_csv,
        dataset_set="set01"
    ):

        self.dataset_set = dataset_set

        self.image_loader = ImageLoader(frame_root)

        self.annotation_loader = AnnotationLoader(
            annotation_csv
        )

        self.cropper = PedestrianCropper()

        self.appearance = AppearanceFeatureExtractor()

        self.spatial = SpatialFeatureExtractor()

        self.motion = MotionFeatureExtractor()

        self.fusion = FeatureFusion()

    def extract(self, sequence_row):

        video = sequence_row["video"]

        pedestrian = sequence_row["pedestrian_id"]

        frame_numbers = [
            int(f)
            for f in sequence_row["frames"].split("|")
        ]

        feature_sequence = []

        previous_spatial = None

        for frame in frame_numbers:

            # ----------------------------------
            # Load Image
            # ----------------------------------

            try:

                image = self.image_loader.load_frame(
                    video=video,
                    frame_number=frame,
                    dataset_set=self.dataset_set
                )

            except Exception:

                return None

            # ----------------------------------
            # Load Annotation
            # ----------------------------------

            ann = self.annotation_loader.get_annotation(
                video=video,
                frame=frame,
                pedestrian_id=pedestrian
            )

            if ann is None:
                return None

            bbox = (
                ann["x1"],
                ann["y1"],
                ann["x2"],
                ann["y2"]
            )

            # ----------------------------------
            # Crop
            # ----------------------------------

            try:

                crop = self.cropper.crop(
                    image,
                    bbox
                )

            except Exception:

                return None

            if crop is None:
                return None

            # ----------------------------------
            # Appearance
            # ----------------------------------

            try:

                appearance = self.appearance.extract(
                    crop
                )

            except Exception:

                return None

            # ----------------------------------
            # Spatial
            # ----------------------------------

            spatial = self.spatial.extract(
                bbox
            )

            # ----------------------------------
            # Motion
            # ----------------------------------

            if previous_spatial is None:

                motion = np.zeros(
                    4,
                    dtype=np.float32
                )

            else:

                motion = self.motion.extract(
                    previous_spatial,
                    spatial
                )

            previous_spatial = spatial

            # ----------------------------------
            # Feature Fusion
            # ----------------------------------

            feature = self.fusion.fuse(
                appearance,
                spatial,
                motion
            )

            feature_sequence.append(feature)

        feature_sequence = np.asarray(
            feature_sequence,
            dtype=np.float32
        )

        # ----------------------------------
        # Fixed Sequence Validation
        # ----------------------------------

        if feature_sequence.shape[0] != len(frame_numbers):

            return None

        return feature_sequence