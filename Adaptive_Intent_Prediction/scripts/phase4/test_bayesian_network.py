"""
Test Bayesian Semantic Network inference.
"""

from pathlib import Path

from utils.bayesian_network import (
    BayesianSemanticNetwork
)


MODEL_PATH = Path(
    "outputs/phase4/"
    "bayesian_semantic_network.pkl"
)


def print_result(title, evidence, result):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    print("Evidence:")

    for key, value in evidence.items():
        print(f"  {key:12}: {value}")

    print()
    print("Intention tendency probabilities:")

    for state, probability in (
        result["intention_tendency"].items()
    ):
        print(
            f"  {state:15}: "
            f"{probability:.6f}"
        )

    print()
    print("Observation reliability probabilities:")

    for state, probability in (
        result[
            "observation_reliability"
        ].items()
    ):
        print(
            f"  {state:15}: "
            f"{probability:.6f}"
        )

    print()
    print("Bayesian feature vector:")
    print(result["feature_vector"])

    print(
        "Feature dimension:",
        result["feature_vector"].shape
    )


def main():

    network = BayesianSemanticNetwork.load(
        MODEL_PATH
    )

    test_cases = [
        {
            "title":
                "Static pedestrian with low occlusion",

            "evidence": {
                "motion": "static",
                "horizontal": "center",
                "vertical": "bottom",
                "occlusion": "low"
            }
        },

        {
            "title":
                "Walking pedestrian with medium occlusion",

            "evidence": {
                "motion": "walking",
                "horizontal": "center",
                "vertical": "bottom",
                "occlusion": "medium"
            }
        },

        {
            "title":
                "Fast pedestrian with high occlusion",

            "evidence": {
                "motion": "fast",
                "horizontal": "right",
                "vertical": "bottom",
                "occlusion": "high"
            }
        }
    ]

    for test_case in test_cases:

        evidence = test_case["evidence"]

        result = network.predict(
            motion=evidence["motion"],
            horizontal=evidence["horizontal"],
            vertical=evidence["vertical"],
            occlusion=evidence["occlusion"]
        )

        print_result(
            title=test_case["title"],
            evidence=evidence,
            result=result
        )


if __name__ == "__main__":
    main()