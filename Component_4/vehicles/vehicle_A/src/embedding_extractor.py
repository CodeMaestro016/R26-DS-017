# ==========================================================
# vehicles/vehicle_A/src/embedding_extractor.py
#
# Step 4: Common Model-Independent Embedding Extraction
#
# IMPORTANT:
# - Same extractor must be used by Vehicle A/B/C
#   and Global Verification DB.
# - NO CNN is used.
# - This embedding is independent of each vehicle's CNN.
# - Embedding size = 4068.
# - Global DB uses the EXACT SAME implementation.
#
# Feature dimensions:
#   Grayscale : 1024
#   Edge      : 1024
#   Colour    : 256
#   HOG       : 1764
#   ----------------
#   Total     : 4068
#
# HOG implementation:
#   skimage.feature.hog
# ==========================================================


import cv2
import numpy as np

try:
    from skimage.feature import hog

    SKIMAGE_HOG_AVAILABLE = True

except ImportError:

    SKIMAGE_HOG_AVAILABLE = False


# ==========================================================
# CONFIGURATION
# ==========================================================

IMAGE_SIZE = 64

# MUST MATCH GLOBAL DATABASE
EMBEDDING_VERSION = "common_sign_embedding_v2"


# ==========================================================
# FEATURE WEIGHTS
#
# MUST MATCH GLOBAL DATABASE CREATION
# ==========================================================

GRAYSCALE_WEIGHT = 0.20
EDGE_WEIGHT = 0.20
COLOUR_WEIGHT = 0.30
HOG_WEIGHT = 0.30


# ==========================================================
# EXPECTED FEATURE DIMENSIONS
# ==========================================================

GRAYSCALE_DIM = 1024
EDGE_DIM = 1024
COLOUR_DIM = 256
HOG_DIM = 1764

EXPECTED_EMBEDDING_LENGTH = (
    GRAYSCALE_DIM
    + EDGE_DIM
    + COLOUR_DIM
    + HOG_DIM
)


# ==========================================================
# HOG CONFIGURATION
#
# IMPORTANT:
# These parameters must be IDENTICAL to the
# global database creation code.
#
# 64x64 image
# pixels_per_cell = 8x8
# cells_per_block = 2x2
# orientations = 9
#
# This produces:
#
# 7 x 7 blocks
# 2 x 2 cells/block
# 9 orientations
#
# 7*7*2*2*9 = 1764
# ==========================================================

HOG_ORIENTATIONS = 9

HOG_PIXELS_PER_CELL = (
    8,
    8
)

HOG_CELLS_PER_BLOCK = (
    2,
    2
)


# ==========================================================
# EMBEDDING EXTRACTOR
# ==========================================================

class EmbeddingExtractor:

    def __init__(self):

        if not SKIMAGE_HOG_AVAILABLE:

            raise ImportError(
                "scikit-image is required for the "
                "common embedding extractor.\n\n"
                "Install using:\n"
                "pip install scikit-image"
            )

        self.embedding_version = (
            EMBEDDING_VERSION
        )

        print(
            "Embedding extractor loaded."
        )

        print(
            "Embedding method: "
            "grayscale + edge + HSV + HOG"
        )

        print(
            "HOG implementation: "
            "skimage.feature.hog"
        )

        print(
            f"Embedding version: "
            f"{self.embedding_version}"
        )

        print(
            f"Embedding length: "
            f"{EXPECTED_EMBEDDING_LENGTH}"
        )


    # ======================================================
    # NORMALIZE VECTOR
    # ======================================================

    @staticmethod
    def normalize_vector(vector):

        vector = np.asarray(
            vector,
            dtype=np.float32
        ).reshape(-1)

        if vector.size == 0:

            return None

        if not np.all(
            np.isfinite(vector)
        ):

            return None

        norm = np.linalg.norm(
            vector
        )

        if norm < 1e-12:

            return None

        return (
            vector / norm
        ).astype(
            np.float32
        )


    # ======================================================
    # PREPROCESS IMAGE
    # ======================================================

    def preprocess_image(
        self,
        cropped_sign
    ):

        if cropped_sign is None:

            print(
                "Invalid cropped sign: "
                "image is None."
            )

            return None


        if not isinstance(
            cropped_sign,
            np.ndarray
        ):

            print(
                "Invalid cropped sign: "
                "expected NumPy array."
            )

            return None


        if cropped_sign.size == 0:

            print(
                "Invalid cropped sign: "
                "image is empty."
            )

            return None


        # --------------------------------------------------
        # Grayscale -> BGR
        # --------------------------------------------------

        if len(
            cropped_sign.shape
        ) == 2:

            cropped_sign = cv2.cvtColor(
                cropped_sign,
                cv2.COLOR_GRAY2BGR
            )


        # --------------------------------------------------
        # BGRA -> BGR
        # --------------------------------------------------

        elif (
            len(cropped_sign.shape) == 3
            and cropped_sign.shape[2] == 4
        ):

            cropped_sign = cv2.cvtColor(
                cropped_sign,
                cv2.COLOR_BGRA2BGR
            )


        # --------------------------------------------------
        # Validate BGR
        # --------------------------------------------------

        elif not (
            len(cropped_sign.shape) == 3
            and cropped_sign.shape[2] == 3
        ):

            print(
                "Invalid cropped sign: "
                "unsupported image format."
            )

            return None


        # --------------------------------------------------
        # Resize to 64x64
        # --------------------------------------------------

        resized = cv2.resize(
            cropped_sign,
            (
                IMAGE_SIZE,
                IMAGE_SIZE
            ),
            interpolation=cv2.INTER_AREA
        )

        return resized


    # ======================================================
    # GRAYSCALE FEATURES
    #
    # 32 x 32 = 1024
    # ======================================================

    def extract_grayscale_features(
        self,
        image
    ):

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )


        gray_small = cv2.resize(
            gray,
            (
                32,
                32
            ),
            interpolation=cv2.INTER_AREA
        )


        features = (
            gray_small
            .astype(np.float32)
            .reshape(-1)
            / 255.0
        )


        normalized = (
            self.normalize_vector(
                features
            )
        )


        if normalized is None:

            return np.zeros(
                GRAYSCALE_DIM,
                dtype=np.float32
            )


        return normalized


    # ======================================================
    # EDGE FEATURES
    #
    # 32 x 32 = 1024
    # ======================================================

    def extract_edge_features(
        self,
        image
    ):

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )


        gray = cv2.GaussianBlur(
            gray,
            (
                3,
                3
            ),
            0
        )


        edges = cv2.Canny(
            gray,
            threshold1=50,
            threshold2=150
        )


        edge_small = cv2.resize(
            edges,
            (
                32,
                32
            ),
            interpolation=cv2.INTER_AREA
        )


        features = (
            edge_small
            .astype(np.float32)
            .reshape(-1)
            / 255.0
        )


        normalized = (
            self.normalize_vector(
                features
            )
        )


        if normalized is None:

            return np.zeros(
                EDGE_DIM,
                dtype=np.float32
            )


        return normalized


    # ======================================================
    # COLOUR FEATURES
    #
    # HSV histogram
    #
    # 16 x 16 = 256
    # ======================================================

    def extract_colour_features(
        self,
        image
    ):

        hsv = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2HSV
        )


        histogram = cv2.calcHist(
            images=[
                hsv
            ],
            channels=[
                0,
                1
            ],
            mask=None,
            histSize=[
                16,
                16
            ],
            ranges=[
                0,
                180,
                0,
                256
            ]
        )


        histogram = (
            histogram
            .astype(np.float32)
            .reshape(-1)
        )


        normalized = (
            self.normalize_vector(
                histogram
            )
        )


        if normalized is None:

            return np.zeros(
                COLOUR_DIM,
                dtype=np.float32
            )


        return normalized


    # ======================================================
    # HOG FEATURES
    #
    # 1764 dimensions
    #
    # IMPORTANT:
    # Uses skimage, NOT cv2.HOGDescriptor.
    # ======================================================

    def extract_hog_features(
        self,
        image
    ):

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )


        # --------------------------------------------------
        # EXACT SAME HOG CONFIGURATION AS GLOBAL DB
        # --------------------------------------------------

        hog_features = hog(
            gray,

            orientations=HOG_ORIENTATIONS,

            pixels_per_cell=(
                HOG_PIXELS_PER_CELL
            ),

            cells_per_block=(
                HOG_CELLS_PER_BLOCK
            ),

            block_norm="L2-Hys",

            visualize=False,

            feature_vector=True
        )


        if hog_features is None:

            return None


        hog_features = (
            np.asarray(
                hog_features,
                dtype=np.float32
            ).reshape(-1)
        )


        # --------------------------------------------------
        # Verify HOG dimension
        # --------------------------------------------------

        if len(
            hog_features
        ) != HOG_DIM:

            print(
                "ERROR: Unexpected HOG "
                f"dimension: "
                f"{len(hog_features)}"
            )

            return None


        # --------------------------------------------------
        # Normalize HOG
        # --------------------------------------------------

        normalized = (
            self.normalize_vector(
                hog_features
            )
        )


        if normalized is None:

            return None


        return normalized


    # ======================================================
    # COMPLETE EMBEDDING
    # ======================================================

    def extract_embedding(
        self,
        cropped_sign
    ):

        # --------------------------------------------------
        # PREPROCESS
        # --------------------------------------------------

        image = (
            self.preprocess_image(
                cropped_sign
            )
        )


        if image is None:

            return None


        # --------------------------------------------------
        # EXTRACT FEATURE GROUPS
        # --------------------------------------------------

        grayscale_features = (
            self.extract_grayscale_features(
                image
            )
        )


        edge_features = (
            self.extract_edge_features(
                image
            )
        )


        colour_features = (
            self.extract_colour_features(
                image
            )
        )


        hog_features = (
            self.extract_hog_features(
                image
            )
        )


        if hog_features is None:

            print(
                "Failed to extract HOG features."
            )

            return None


        # --------------------------------------------------
        # APPLY FEATURE WEIGHTS
        #
        # MUST MATCH GLOBAL DATABASE
        # --------------------------------------------------

        grayscale_features = (
            grayscale_features
            * GRAYSCALE_WEIGHT
        )


        edge_features = (
            edge_features
            * EDGE_WEIGHT
        )


        colour_features = (
            colour_features
            * COLOUR_WEIGHT
        )


        hog_features = (
            hog_features
            * HOG_WEIGHT
        )


        # --------------------------------------------------
        # CONCATENATE
        #
        # 1024
        # +1024
        # +256
        # +1764
        # =4068
        # --------------------------------------------------

        embedding = np.concatenate([
            grayscale_features,
            edge_features,
            colour_features,
            hog_features
        ])


        # --------------------------------------------------
        # SAFETY CHECK
        # --------------------------------------------------

        if len(
            embedding
        ) != EXPECTED_EMBEDDING_LENGTH:

            print(
                "ERROR: Unexpected embedding "
                f"length: "
                f"{len(embedding)}"
            )

            return None


        # --------------------------------------------------
        # FINAL L2 NORMALIZATION
        # --------------------------------------------------

        embedding = (
            self.normalize_vector(
                embedding
            )
        )


        if embedding is None:

            print(
                "Failed to normalize "
                "embedding."
            )

            return None


        return embedding.tolist()


    # ======================================================
    # GET EMBEDDING VERSION
    # ======================================================

    def get_embedding_version(
        self
    ):

        return (
            self.embedding_version
        )


    # ======================================================
    # GET EMBEDDING LENGTH
    # ======================================================

    def get_embedding_length(
        self
    ):

        return (
            EXPECTED_EMBEDDING_LENGTH
        )