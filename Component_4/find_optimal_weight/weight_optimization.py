# ============================================================
# find_suitable_weight.py
#
# Data-driven selection of a suitable Visual/Novelty weight
#
# Purpose:
#   Identify a suitable contribution of Visual Prominence
#   and Novelty for the Importance Score.
#
# IMPORTANT:
#   This experiment identifies a suitable weight from the
#   available validation data. It does NOT claim that the
#   selected weight is mathematically optimal or universally
#   optimal.
# ============================================================

import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr

# ============================================================
# 1. LOAD VALIDATION DATA
# ============================================================

DATA_PATH = "find_optimal_weight/validation_data.csv"

df = pd.read_csv(DATA_PATH)

print("=" * 70)
print("DATA-DRIVEN IMPORTANCE WEIGHT SELECTION")
print("=" * 70)

print(f"\nTotal validation samples : {len(df)}")

print("\nClassification distribution:")
print(df["classification_status"].value_counts())

# ============================================================
# 2. REQUIRED COLUMNS
# ============================================================

required_columns = [
    "visual_norm",
    "novelty_norm",
    "reward",
    "classification_status"
]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

# ============================================================
# 3. REMOVE INVALID VALUES
# ============================================================

df = df.dropna(
    subset=[
        "visual_norm",
        "novelty_norm",
        "reward",
        "classification_status"
    ]
).copy()

print(f"\nValid samples used: {len(df)}")

# ============================================================
# 4. EXTRACT DATA
# ============================================================

visual = df["visual_norm"].to_numpy()
novelty = df["novelty_norm"].to_numpy()
reward = df["reward"].to_numpy()
status = df["classification_status"].to_numpy()

# ============================================================
# 5. CREATE SIMPLE REWARD TARGET
#
# Positive reward = successful knowledge-sharing outcome
# Non-positive reward = unsuccessful / undesirable outcome
# ============================================================

reward_success = (reward > 0).astype(int)

print("\nReward distribution:")
print(f"Positive reward     : {np.sum(reward_success)}")
print(f"Non-positive reward : {np.sum(reward_success == 0)}")

# ============================================================
# 6. TEST ALL WEIGHTS
#
# Visual + Novelty = 1
#
# 0.00/1.00
# 0.01/0.99
# ...
# 1.00/0.00
# ============================================================

print("\n" + "=" * 70)
print("EXHAUSTIVE WEIGHT SEARCH")
print("=" * 70)

print(
    "Testing Visual weights from 0.00 to 1.00 "
    "with Novelty = 1 - Visual..."
)

results = []

for w_visual in np.arange(0.00, 1.01, 0.01):

    w_visual = round(float(w_visual), 2)
    w_novelty = round(1.00 - w_visual, 2)

    # --------------------------------------------------------
    # Importance Score
    # --------------------------------------------------------

    importance = (
        w_visual * visual
        +
        w_novelty * novelty
    )

    # --------------------------------------------------------
    # METRIC 1:
    # Spearman correlation with observed reward
    #
    # Measures whether higher importance generally
    # corresponds to higher/lower reward.
    # We use absolute value because either direction
    # may appear in the empirical data.
    # --------------------------------------------------------

    try:
        reward_corr, reward_p = spearmanr(
            importance,
            reward
        )

        if np.isnan(reward_corr):
            reward_corr = 0.0

    except Exception:
        reward_corr = 0.0

    # --------------------------------------------------------
    # METRIC 2:
    # Reward prediction AUC
    #
    # Measures how well importance distinguishes
    # positive-reward from non-positive-reward samples.
    # --------------------------------------------------------

    if len(np.unique(reward_success)) == 2:

        try:
            reward_auc = roc_auc_score(
                reward_success,
                importance
            )

            # Because AUC < 0.5 can simply mean the
            # relationship is reversed, use the better
            # directional interpretation.
            reward_auc_adjusted = max(
                reward_auc,
                1.0 - reward_auc
            )

        except Exception:
            reward_auc = np.nan
            reward_auc_adjusted = 0.5

    else:
        reward_auc = np.nan
        reward_auc_adjusted = 0.5

    # --------------------------------------------------------
    # METRIC 3:
    # RARE + NEW vs KNOWN
    #
    # This is a secondary criterion.
    # It checks whether importance gives higher values
    # to knowledge that is not already known.
    # --------------------------------------------------------

    known_mask = status == "KNOWN"
    rare_new_mask = np.isin(
        status,
        ["RARE", "NEW"]
    )

    if (
        np.sum(known_mask) > 0
        and
        np.sum(rare_new_mask) > 0
    ):

        known_importance = importance[known_mask]
        rare_new_importance = importance[rare_new_mask]

        mean_known = np.mean(known_importance)
        mean_rare_new = np.mean(rare_new_importance)

        separation = (
            mean_rare_new - mean_known
        )

        # AUC: KNOWN=0, RARE/NEW=1

        binary_labels = np.concatenate([
            np.zeros(len(known_importance)),
            np.ones(len(rare_new_importance))
        ])

        binary_scores = np.concatenate([
            known_importance,
            rare_new_importance
        ])

        try:
            auc_known_vs_rare_new = roc_auc_score(
                binary_labels,
                binary_scores
            )

            auc_known_vs_rare_new = max(
                auc_known_vs_rare_new,
                1.0 - auc_known_vs_rare_new
            )

        except Exception:
            auc_known_vs_rare_new = 0.5

    else:

        mean_known = np.nan
        mean_rare_new = np.nan
        separation = np.nan
        auc_known_vs_rare_new = 0.5

    # --------------------------------------------------------
    # METRIC 4:
    # Importance distribution
    # --------------------------------------------------------

    importance_mean = np.mean(importance)
    importance_std = np.std(importance)

    # --------------------------------------------------------
    # STORE RESULTS
    # --------------------------------------------------------

    results.append({

        "visual_weight": w_visual,

        "novelty_weight": w_novelty,

        "reward_spearman":
            reward_corr,

        "reward_auc":
            reward_auc,

        "reward_auc_adjusted":
            reward_auc_adjusted,

        "mean_known":
            mean_known,

        "mean_rare_new":
            mean_rare_new,

        "known_vs_rare_new_separation":
            separation,

        "known_vs_rare_new_auc":
            auc_known_vs_rare_new,

        "importance_mean":
            importance_mean,

        "importance_std":
            importance_std
    })

# ============================================================
# 7. RESULTS DATAFRAME
# ============================================================

results_df = pd.DataFrame(results)

# ============================================================
# 8. NORMALIZED RANKING
#
# Primary:
#   Reward relationship
#
# Secondary:
#   Known vs Rare/New separation
# ============================================================

results_df["rank_reward_auc"] = (
    results_df["reward_auc_adjusted"]
    .rank(ascending=False)
)

results_df["rank_reward_corr"] = (
    results_df["reward_spearman"]
    .abs()
    .rank(ascending=False)
)

results_df["rank_known_rare_new"] = (
    results_df["known_vs_rare_new_auc"]
    .rank(ascending=False)
)

# Average rank

results_df["average_rank"] = (
    results_df[
        [
            "rank_reward_auc",
            "rank_reward_corr",
            "rank_known_rare_new"
        ]
    ]
    .mean(axis=1)
)

# ============================================================
# 9. BEST WEIGHTS BY INDIVIDUAL METRICS
# ============================================================

best_reward_auc = results_df.loc[
    results_df["reward_auc_adjusted"].idxmax()
]

best_reward_corr = results_df.loc[
    results_df["reward_spearman"].abs().idxmax()
]

best_known_rare_new = results_df.loc[
    results_df["known_vs_rare_new_auc"].idxmax()
]

# ============================================================
# 10. FINAL SUITABLE WEIGHT
# ============================================================

best_overall = results_df.loc[
    results_df["average_rank"].idxmin()
]

# ============================================================
# 11. DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("BEST WEIGHT BY INDIVIDUAL CRITERIA")
print("=" * 70)

print("\nBest by Reward AUC:")
print(
    f"  Visual  = {best_reward_auc['visual_weight']:.2f}"
)
print(
    f"  Novelty = {best_reward_auc['novelty_weight']:.2f}"
)
print(
    f"  Reward AUC = "
    f"{best_reward_auc['reward_auc_adjusted']:.4f}"
)

print("\nBest by Reward Correlation:")
print(
    f"  Visual  = {best_reward_corr['visual_weight']:.2f}"
)
print(
    f"  Novelty = {best_reward_corr['novelty_weight']:.2f}"
)
print(
    f"  |Spearman| = "
    f"{abs(best_reward_corr['reward_spearman']):.4f}"
)

print("\nBest by KNOWN vs RARE/NEW:")
print(
    f"  Visual  = {best_known_rare_new['visual_weight']:.2f}"
)
print(
    f"  Novelty = {best_known_rare_new['novelty_weight']:.2f}"
)
print(
    f"  AUC = "
    f"{best_known_rare_new['known_vs_rare_new_auc']:.4f}"
)

# ============================================================
# 12. FINAL RECOMMENDATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL SUITABLE WEIGHT")
print("=" * 70)

final_visual = best_overall["visual_weight"]
final_novelty = best_overall["novelty_weight"]

print(
    f"\nVisual Weight  : {final_visual:.2f}"
)

print(
    f"Novelty Weight : {final_novelty:.2f}"
)

print(
    f"\nReward AUC     : "
    f"{best_overall['reward_auc_adjusted']:.4f}"
)

print(
    f"Reward Spearman: "
    f"{best_overall['reward_spearman']:.4f}"
)

print(
    f"KNOWN vs RARE/NEW AUC: "
    f"{best_overall['known_vs_rare_new_auc']:.4f}"
)

print(
    "\nSelection method:"
    "\n  1. Exhaustive search of all weight combinations"
    "\n  2. Reward relationship"
    "\n  3. Reward discrimination"
    "\n  4. Known vs non-known separation"
    "\n  5. Average ranking of the criteria"
)

print(
    "\nInterpretation:"
    "\nThe selected weight is a data-driven suitable"
    "\nweight for the Importance Score in this experiment."
)

# ============================================================
# 13. TOP 10 WEIGHTS
# ============================================================

print("\n" + "=" * 70)
print("TOP 10 SUITABLE WEIGHT COMBINATIONS")
print("=" * 70)

top10 = (
    results_df
    .sort_values("average_rank")
    .head(10)
)

print(
    top10[
        [
            "visual_weight",
            "novelty_weight",
            "reward_auc_adjusted",
            "reward_spearman",
            "known_vs_rare_new_auc",
            "average_rank"
        ]
    ].to_string(index=False)
)

# ============================================================
# 14. SAVE RESULTS
# ============================================================

output_path = (
    "find_optimal_weight/"
    "suitable_weight_search_results.csv"
)

results_df.to_csv(
    output_path,
    index=False
)

# Save selected weight

summary = pd.DataFrame([{
    "selected_visual_weight":
        final_visual,

    "selected_novelty_weight":
        final_novelty,

    "reward_auc":
        best_overall["reward_auc_adjusted"],

    "reward_spearman":
        best_overall["reward_spearman"],

    "known_vs_rare_new_auc":
        best_overall["known_vs_rare_new_auc"]
}])

summary.to_csv(
    "find_optimal_weight/"
    "selected_weight_summary.csv",
    index=False
)

print("\n" + "=" * 70)
print("FILES SAVED")
print("=" * 70)

print(
    "find_optimal_weight/"
    "suitable_weight_search_results.csv"
)

print(
    "find_optimal_weight/"
    "selected_weight_summary.csv"
)

print("=" * 70)