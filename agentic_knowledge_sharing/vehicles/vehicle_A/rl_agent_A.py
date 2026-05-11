# Temporary rule-based agent for Vehicle A
# Later this can be replaced by trained RL/DQN agent.
'''
def rule_based_agent_decision(item):
    importance_score = item["importance_score"]
    color = item["color"]
    shape = item["shape"]

    # Share highly important signs
    if importance_score >= 0.5:
        return "SHARE"

    # Share visually safety-related sign patterns
    if color in ["red", "yellow"] and shape in ["triangle", "circle", "octagon"]:
        return "SHARE"

    return "IGNORE"

'''

# Trained DQN Agent for Vehicle A

import os
import torch
import torch.nn as nn
import numpy as np

MODEL_PATH = "Models/dqn_agent_A.pth"

COLOR_CODES = {
    "unknown": 0,
    "red": 1,
    "blue": 2,
    "yellow": 3,
    "green": 4,
    "white": 5,
    "black": 6
}

SHAPE_CODES = {
    "unknown": 0,
    "triangle": 1,
    "circle": 2,
    "square": 3,
    "rectangle": 4,
    "octagon": 5,
    "pentagon": 6,
    "star_or_complex": 7
}


class DQN(nn.Module):
    def __init__(self, input_size=3, output_size=2):
        super(DQN, self).__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, output_size)
        )

    def forward(self, x):
        return self.network(x)


model = DQN(input_size=3, output_size=2)

if os.path.exists(MODEL_PATH):
    checkpoint = torch.load(MODEL_PATH, map_location=torch.device("cpu"))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    print("Trained DQN model loaded successfully")
else:
    model = None
    print("DQN model not found. Using fallback rule-based agent.")


def encode_state(item):
    importance = float(item.get("importance_score", 0))

    color = str(item.get("color", "unknown")).lower()
    shape = str(item.get("shape", "unknown")).lower()

    color_code = COLOR_CODES.get(color, 0)
    shape_code = SHAPE_CODES.get(shape, 0)

    color_norm = color_code / 6.0
    shape_norm = shape_code / 7.0

    state = np.array(
        [importance, color_norm, shape_norm],
        dtype=np.float32
    )

    return torch.tensor(state).unsqueeze(0)


def rule_based_agent_decision(item):
    importance_score = item["importance_score"]
    color = item["color"]
    shape = item["shape"]

    if importance_score >= 0.5:
        return "SHARE"

    if color in ["red", "yellow"] and shape in ["triangle", "circle", "octagon"]:
        return "SHARE"

    return "IGNORE"


def dqn_agent_decision(item):
    if model is None:
        return rule_based_agent_decision(item)

    state = encode_state(item)

    with torch.no_grad():
        q_values = model(state)

    action = torch.argmax(q_values).item()

    if action == 1:
        return "SHARE"

    return "IGNORE"


# Keep old function name so edge_pipeline.py does not break
def rule_based_agent_decision(item):
    return dqn_agent_decision(item)