"""
Test Semantic Mapper
"""

from utils.semantic_mapper import SemanticMapper


def main():

    print("=" * 60)
    print("Semantic Mapper Test")
    print("=" * 60)

    mapper = SemanticMapper()

    result = mapper.map(
        speed=10.0,
        center_x=922.5,
        center_y=820.0,
        image_width=1920,
        image_height=1080,
        occlusion="medium"
    )

    for key, value in result.items():
        print(f"{key:12}: {value}")


if __name__ == "__main__":
    main()