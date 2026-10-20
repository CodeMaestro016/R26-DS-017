# vehicles/vehicle_A/src/feature_extraction.py
# Step 3: Feature Extraction - Vehicle A

import cv2
import numpy as np
from sklearn.cluster import KMeans


class FeatureExtractor:
    """
    Extract visual features from cropped traffic sign.

    Inputs:
        cropped_sign:
            Cropped traffic sign image from YOLO.

        visual_prominence:
            Already calculated in detection.py using YOLO bbox.

    Output:
        Feature dictionary for RARE / NEW signs.
    """

    def __init__(self):
        """
        Simplified BGR color ranges.
        OpenCV uses BGR format, not RGB.
        """

        self.color_ranges = {
            "red": [([0, 0, 100], [90, 90, 255])],
            "blue": [([100, 0, 0], [255, 120, 120])],
            "yellow": [([0, 100, 100], [120, 255, 255])],
            "green": [([0, 100, 0], [120, 255, 120])],
            "white": [([180, 180, 180], [255, 255, 255])],
            "black": [([0, 0, 0], [70, 70, 70])],
            "gray": [([70, 70, 70], [180, 180, 180])]
        }

    # ==========================================================
    # SHAPE EXTRACTION
    # ==========================================================

    def extract_shape(self, cropped_sign):
        """
        Detect basic traffic sign shape.

        Returns:
            circle, triangle, square, rectangle, octagon, polygon, unknown
        """

        gray = cv2.cvtColor(cropped_sign, cv2.COLOR_BGR2GRAY)

        # Smooth image to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Detect edges
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return "unknown"

        # Use largest contour as sign boundary
        contour = max(contours, key=cv2.contourArea)

        area = cv2.contourArea(contour)

        if area < 50:
            return "unknown"

        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)

        vertices = len(approx)

        if vertices == 3:
            return "triangle"

        elif vertices == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / h if h > 0 else 1

            if 0.85 <= aspect_ratio <= 1.15:
                return "square"
            else:
                return "rectangle"

        elif vertices == 8:
            return "octagon"

        elif vertices > 8:
            return "circle"

        else:
            return "polygon"

    # ==========================================================
    # COLOR EXTRACTION
    # ==========================================================

    def extract_colors(self, cropped_sign):
        """
        Detect dominant colors in cropped traffic sign.

        Returns:
            List of color names.
            Example: ["red", "white", "black"]
        """

        # Resize for faster color processing
        small = cv2.resize(cropped_sign, (50, 50))

        pixels = small.reshape(-1, 3)

        # Use KMeans to find dominant color groups
        kmeans = KMeans(
            n_clusters=5,
            n_init=10,
            random_state=42
        )

        kmeans.fit(pixels)

        labels = kmeans.labels_
        counts = np.bincount(labels)

        # Sort clusters by dominance
        sorted_indices = np.argsort(counts)[::-1]

        detected_colors = []

        for index in sorted_indices:
            color = kmeans.cluster_centers_[index]
            color_name = self.get_color_name(color)

            if color_name != "unknown" and color_name not in detected_colors:
                detected_colors.append(color_name)

        if not detected_colors:
            detected_colors.append("unknown")

        return detected_colors

    def get_color_name(self, color):
        """
        Convert BGR color value to simple color name.
        """

        b, g, r = color

        # Check defined color ranges
        for color_name, ranges in self.color_ranges.items():
            for lower, upper in ranges:
                lower = np.array(lower)
                upper = np.array(upper)

                if np.all(color >= lower) and np.all(color <= upper):
                    return color_name

        # Extra check for white / gray / black
        if abs(r - g) < 30 and abs(g - b) < 30:
            avg = (r + g + b) / 3

            if avg >= 200:
                return "white"
            elif avg <= 70:
                return "black"
            else:
                return "gray"

        return "unknown"

    # ==========================================================
    # TEXT / DIGIT PRESENCE
    # ==========================================================

    def extract_text(self, cropped_sign):
        """
        Detect whether sign contains text or digits.

        This does not read the text.
        It only checks whether text/digits are present.

        Returns:
            text_present or None
        """

        gray = cv2.cvtColor(cropped_sign, cv2.COLOR_BGR2GRAY)

        # Threshold dark text / digits
        _, thresh = cv2.threshold(
            gray,
            130,
            255,
            cv2.THRESH_BINARY_INV
        )

        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        text_regions = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            area = cv2.contourArea(contour)
            aspect_ratio = w / h if h > 0 else 0

            # Basic filter for digit/text-like regions
            if area > 30 and w > 4 and h > 6 and 0.2 <= aspect_ratio <= 2.0:
                text_regions.append((x, y, w, h))

        if len(text_regions) >= 1:
            return "text_present"

        return None

    # ==========================================================
    # EXTRACT ALL FEATURES
    # ==========================================================

    def extract_all_features(self, cropped_sign, visual_prominence):
        """
        Extract all required features.

        visual_prominence is already calculated in detection.py.
        """

        shape = self.extract_shape(cropped_sign)
        colors = self.extract_colors(cropped_sign)
        text = self.extract_text(cropped_sign)

        features = {
            "shape": shape,
            "colors": colors,
            "color_count": len(colors),
            "text": text,
            "visual_prominence": round(visual_prominence, 6)
        }

        return features