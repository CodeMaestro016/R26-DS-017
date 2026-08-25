# global_verification_server/reward_system.py
# Reward generation after global verification


# ==========================================================
# TRAFFIC-SIGN REWARD POINTS
# ==========================================================

SIGN_REWARD_POINTS = {
    0: {
        "name": "speed_limit_20",
        "category": "PROHIBITORY",
        "points": 5.0
    },
    1: {
        "name": "speed_limit_30",
        "category": "PROHIBITORY",
        "points": 5.0
    },
    2: {
        "name": "speed_limit_50",
        "category": "PROHIBITORY",
        "points": 4.0
    },
    3: {
        "name": "speed_limit_60",
        "category": "PROHIBITORY",
        "points": 4.0
    },
    4: {
        "name": "speed_limit_70",
        "category": "PROHIBITORY",
        "points": 4.5
    },
    5: {
        "name": "speed_limit_80",
        "category": "PROHIBITORY",
        "points": 4.5
    },
    6: {
        "name": "restriction_ends_80",
        "category": "OTHER",
        "points": 2.0
    },
    7: {
        "name": "speed_limit_100",
        "category": "PROHIBITORY",
        "points": 4.5
    },
    8: {
        "name": "speed_limit_120",
        "category": "PROHIBITORY",
        "points": 4.5
    },
    9: {
        "name": "no_overtaking",
        "category": "PROHIBITORY",
        "points": 4.5
    },
    10: {
        "name": "no_overtaking_trucks",
        "category": "PROHIBITORY",
        "points": 4.5
    },
    11: {
        "name": "priority_at_next_intersection",
        "category": "DANGER",
        "points": 4.0
    },
    12: {
        "name": "priority_road",
        "category": "OTHER",
        "points": 3.5
    },
    13: {
        "name": "give_way",
        "category": "OTHER",
        "points": 4.5
    },
    14: {
        "name": "stop",
        "category": "OTHER",
        "points": 5.0
    },
    15: {
        "name": "no_traffic_both_ways",
        "category": "PROHIBITORY",
        "points": 4.5
    },
    16: {
        "name": "no_trucks",
        "category": "PROHIBITORY",
        "points": 4.0
    },
    17: {
        "name": "no_entry",
        "category": "OTHER",
        "points": 5.0
    },
    18: {
        "name": "danger",
        "category": "DANGER",
        "points": 5.0
    },
    19: {
        "name": "bend_left",
        "category": "DANGER",
        "points": 4.5
    },
    20: {
        "name": "bend_right",
        "category": "DANGER",
        "points": 4.5
    },
    21: {
        "name": "bend",
        "category": "DANGER",
        "points": 4.5
    },
    22: {
        "name": "uneven_road",
        "category": "DANGER",
        "points": 4.0
    },
    23: {
        "name": "slippery_road",
        "category": "DANGER",
        "points": 5.0
    },
    24: {
        "name": "road_narrows",
        "category": "DANGER",
        "points": 4.5
    },
    25: {
        "name": "construction",
        "category": "DANGER",
        "points": 5.0
    },
    26: {
        "name": "traffic_signal",
        "category": "DANGER",
        "points": 4.0
    },
    27: {
        "name": "pedestrian_crossing",
        "category": "DANGER",
        "points": 5.0
    },
    28: {
        "name": "school_crossing",
        "category": "DANGER",
        "points": 5.0
    },
    29: {
        "name": "cycles_crossing",
        "category": "DANGER",
        "points": 4.5
    },
    30: {
        "name": "snow",
        "category": "DANGER",
        "points": 4.0
    },
    31: {
        "name": "animals",
        "category": "DANGER",
        "points": 4.0
    },
    32: {
        "name": "restriction_ends",
        "category": "OTHER",
        "points": 2.0
    },
    33: {
        "name": "go_right",
        "category": "MANDATORY",
        "points": 4.0
    },
    34: {
        "name": "go_left",
        "category": "MANDATORY",
        "points": 4.0
    },
    35: {
        "name": "go_straight",
        "category": "MANDATORY",
        "points": 4.0
    },
    36: {
        "name": "go_right_or_straight",
        "category": "MANDATORY",
        "points": 4.0
    },
    37: {
        "name": "go_left_or_straight",
        "category": "MANDATORY",
        "points": 4.0
    },
    38: {
        "name": "keep_right",
        "category": "MANDATORY",
        "points": 3.5
    },
    39: {
        "name": "keep_left",
        "category": "MANDATORY",
        "points": 3.5
    },
    40: {
        "name": "roundabout",
        "category": "MANDATORY",
        "points": 4.0
    },
    41: {
        "name": "restriction_ends_overtaking",
        "category": "OTHER",
        "points": 2.0
    },
    42: {
        "name": "restriction_ends_overtaking_trucks",
        "category": "OTHER",
        "points": 2.0
    }
}


# ==========================================================
# REWARD THRESHOLDS
# ==========================================================

VERIFICATION_THRESHOLD = 0.70
WEAK_MISMATCH_THRESHOLD = 0.50
VERY_LOW_SIMILARITY_THRESHOLD = 0.10


# ==========================================================
# REWARD CALCULATION
# ==========================================================

def calculate_verification_reward(
    similarity,
    verified_class_id=None
):
    """
    Calculate the RL reward after global verification.

    Rules:
        similarity >= 0.70
            Positive reward based on verified class points.

        0.50 <= similarity < 0.70
            Reward = -1.0

        0.10 < similarity < 0.50
            Reward = -3.0

        similarity <= 0.10
            Reward = -5.0

    Args:
        similarity:
            Cosine similarity from global verification.

        verified_class_id:
            Verified GTSRB class ID.
            Required only for positive rewards.

    Returns:
        Dictionary containing reward information.
    """

    try:
        similarity = float(similarity)
    except (TypeError, ValueError):
        return {
            "reward": -5.0,
            "reward_type": "NEGATIVE",
            "reason": "INVALID_SIMILARITY_VALUE",
            "similarity": 0.0,
            "verified_class_id": None,
            "class_name": None,
            "category": None
        }

    similarity = max(
        -1.0,
        min(1.0, similarity)
    )

    # ======================================================
    # VERIFIED KNOWLEDGE
    # ======================================================

    if similarity >= VERIFICATION_THRESHOLD:

        try:
            verified_class_id = int(
                verified_class_id
            )
        except (TypeError, ValueError):
            return {
                "reward": 1.0,
                "reward_type": "POSITIVE",
                "reason": "VERIFIED_CLASS_ID_MISSING",
                "similarity": round(similarity, 4),
                "verified_class_id": None,
                "class_name": None,
                "category": None
            }

        class_data = SIGN_REWARD_POINTS.get(
            verified_class_id
        )

        if class_data is None:
            return {
                "reward": 1.0,
                "reward_type": "POSITIVE",
                "reason": "VERIFIED_CLASS_POINTS_NOT_FOUND",
                "similarity": round(similarity, 4),
                "verified_class_id": verified_class_id,
                "class_name": None,
                "category": None
            }

        return {
            "reward": float(
                class_data["points"]
            ),
            "reward_type": "POSITIVE",
            "reason": "KNOWLEDGE_VERIFIED",
            "similarity": round(similarity, 4),
            "verified_class_id": verified_class_id,
            "class_name": class_data["name"],
            "category": class_data["category"]
        }

    # ======================================================
    # SIMILARITY BETWEEN 0.50 AND 0.70
    # ======================================================

    if similarity >= WEAK_MISMATCH_THRESHOLD:
        return {
            "reward": -1.0,
            "reward_type": "NEGATIVE",
            "reason": "SIMILARITY_BELOW_VERIFICATION_THRESHOLD",
            "similarity": round(similarity, 4),
            "verified_class_id": None,
            "class_name": None,
            "category": None
        }

    # ======================================================
    # SIMILARITY BETWEEN 0.10 AND 0.50
    # ======================================================

    if similarity > VERY_LOW_SIMILARITY_THRESHOLD:
        return {
            "reward": -3.0,
            "reward_type": "NEGATIVE",
            "reason": "LOW_SIMILARITY",
            "similarity": round(similarity, 4),
            "verified_class_id": None,
            "class_name": None,
            "category": None
        }

    # ======================================================
    # SIMILARITY 0.10 OR LOWER
    # ======================================================

    return {
        "reward": -5.0,
        "reward_type": "NEGATIVE",
        "reason": "VERY_LOW_OR_ZERO_SIMILARITY",
        "similarity": round(similarity, 4),
        "verified_class_id": None,
        "class_name": None,
        "category": None
    }


# ==========================================================
# OPTIONAL TEST
# ==========================================================

if __name__ == "__main__":

    test_cases = [
        {
            "similarity": 0.91,
            "verified_class_id": 0
        },
        {
            "similarity": 0.78,
            "verified_class_id": 5
        },
        {
            "similarity": 0.65,
            "verified_class_id": None
        },
        {
            "similarity": 0.32,
            "verified_class_id": None
        },
        {
            "similarity": 0.08,
            "verified_class_id": None
        },
        {
            "similarity": 0.0,
            "verified_class_id": None
        }
    ]

    print("=" * 60)
    print("Verification Reward System Test")
    print("=" * 60)

    for test_case in test_cases:
        result = calculate_verification_reward(
            similarity=test_case["similarity"],
            verified_class_id=test_case[
                "verified_class_id"
            ]
        )

        print()
        print(
            "Similarity        :",
            test_case["similarity"]
        )
        print(
            "Verified Class ID :",
            test_case[
                "verified_class_id"
            ]
        )
        print(
            "Reward            :",
            result["reward"]
        )
        print(
            "Reward Type       :",
            result["reward_type"]
        )
        print(
            "Reason            :",
            result["reason"]
        )

    print("=" * 60)