"""
Train the Bayesian Semantic Network.
"""

from pathlib import Path

from utils.bayesian_network import (
    BayesianSemanticNetwork
)


DATA_PATH = Path(
    "datasets/processed/bayesian/"
    "train_bayesian.csv"
)

MODEL_PATH = Path(
    "outputs/phase4/"
    "bayesian_semantic_network.pkl"
)


def main():

    print("=" * 70)
    print("TRAIN BAYESIAN SEMANTIC NETWORK")
    print("=" * 70)

    network = BayesianSemanticNetwork()

    network.fit(
        data=DATA_PATH,
        equivalent_sample_size=1.0
    )

    network.save(
        MODEL_PATH
    )

    print()
    print("Bayesian Network trained successfully.")

    print(f"Model saved to: {MODEL_PATH}")

    print()
    print("Nodes:")
    print(list(network.model.nodes()))

    print()
    print("Edges:")

    for edge in network.model.edges():
        print(f"  {edge[0]} -> {edge[1]}")

    print()
    print("Model valid:")
    print(network.model.check_model())

    print()
    print("=" * 70)
    print("LEARNED CPDs")
    print("=" * 70)

    network.print_cpds()


if __name__ == "__main__":
    main()