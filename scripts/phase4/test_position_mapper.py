"""
Test Position Mapper
"""

from utils.position_mapper import PositionMapper


def main():

    mapper = PositionMapper()

    result = mapper.map(
        center_x=922.5,
        center_y=820.0,
        image_width=1920,
        image_height=1080
    )

    print("=" * 50)
    print("Position Mapper Test")
    print("=" * 50)

    print("Normalized X :", result["x_norm"])
    print("Normalized Y :", result["y_norm"])
    print("Horizontal   :", result["horizontal"])
    print("Vertical     :", result["vertical"])


if __name__ == "__main__":
    main()