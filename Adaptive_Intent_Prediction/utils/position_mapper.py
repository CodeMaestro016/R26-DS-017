"""
Position Mapper

Converts pedestrian image coordinates into normalized
semantic position states.

Output states:
    Horizontal: left, center, right
    Vertical: top, middle, bottom
"""


class PositionMapper:

    def __init__(
        self,
        horizontal_bins=3,
        vertical_bins=3
    ):
        """
        Initialize the position mapper.

        Parameters
        ----------
        horizontal_bins : int
            Number of horizontal regions.

        vertical_bins : int
            Number of vertical regions.
        """

        if horizontal_bins != 3:
            raise ValueError(
                "Current implementation supports "
                "exactly 3 horizontal regions."
            )

        if vertical_bins != 3:
            raise ValueError(
                "Current implementation supports "
                "exactly 3 vertical regions."
            )

        self.horizontal_bins = horizontal_bins
        self.vertical_bins = vertical_bins

    def normalize(
        self,
        center_x,
        center_y,
        image_width,
        image_height
    ):
        """
        Normalize pixel coordinates into the range [0, 1].

        Returns
        -------
        tuple
            x_norm, y_norm
        """

        if image_width <= 0:
            raise ValueError(
                "image_width must be greater than zero."
            )

        if image_height <= 0:
            raise ValueError(
                "image_height must be greater than zero."
            )

        x_norm = float(center_x) / float(image_width)
        y_norm = float(center_y) / float(image_height)

        # Protect against slightly invalid annotation values
        x_norm = max(0.0, min(1.0, x_norm))
        y_norm = max(0.0, min(1.0, y_norm))

        return x_norm, y_norm

    def map_horizontal(self, x_norm):
        """
        Convert normalized x-coordinate into a horizontal state.
        """

        if not 0.0 <= x_norm <= 1.0:
            raise ValueError(
                "x_norm must be between 0 and 1."
            )

        if x_norm < (1.0 / 3.0):
            return "left"

        if x_norm < (2.0 / 3.0):
            return "center"

        return "right"

    def map_vertical(self, y_norm):
        """
        Convert normalized y-coordinate into a vertical state.
        """

        if not 0.0 <= y_norm <= 1.0:
            raise ValueError(
                "y_norm must be between 0 and 1."
            )

        if y_norm < (1.0 / 3.0):
            return "top"

        if y_norm < (2.0 / 3.0):
            return "middle"

        return "bottom"

    def map(
        self,
        center_x,
        center_y,
        image_width,
        image_height
    ):
        """
        Map pedestrian center coordinates into semantic position states.

        Returns
        -------
        dict
            Normalized coordinates and semantic position states.
        """

        x_norm, y_norm = self.normalize(
            center_x=center_x,
            center_y=center_y,
            image_width=image_width,
            image_height=image_height
        )

        horizontal = self.map_horizontal(x_norm)
        vertical = self.map_vertical(y_norm)

        return {
            "x_norm": x_norm,
            "y_norm": y_norm,
            "horizontal": horizontal,
            "vertical": vertical
        }