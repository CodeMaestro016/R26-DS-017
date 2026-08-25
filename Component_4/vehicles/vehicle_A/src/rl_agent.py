# vehicles/vehicle_A/src/rl_agent.py
# Vehicle A RL Agent
# Decision only: SHARE or IGNORE

import os
import random
from collections import deque

import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim


# ==========================================================
# ACTIONS
# ==========================================================

IGNORE = 0
SHARE = 1


# ==========================================================
# DQN NETWORK
# ==========================================================

class DQNNetwork(nn.Module):
    """
    DQN model for RL decision.

    Input state:
        [
            importance_score,
            label_status_encoded,
            has_red,
            has_blue,
            has_white,
            has_black,
            shape_encoded,
            text_encoded
        ]

    Output:
        Q-value for IGNORE
        Q-value for SHARE
    """

    def __init__(
        self,
        state_size=8,
        action_size=2
    ):
        super(DQNNetwork, self).__init__()

        self.network = nn.Sequential(
            nn.Linear(state_size, 64),
            nn.ReLU(),

            nn.Linear(64, 64),
            nn.ReLU(),

            nn.Linear(64, action_size)
        )

    def forward(self, state):
        return self.network(state)


# ==========================================================
# RL AGENT
# ==========================================================

class VehicleARLAgent:
    """
    Vehicle A RL agent.

    This agent does not classify signs.
    This agent does not create knowledge packages.

    The agent decides:

        SHARE or IGNORE

    After SHARE, the global verification server returns
    a reward. The reward is used to continue training this
    existing local DQN model.
    """

    def __init__(
        self,
        model_path,
        learning_rate=0.0001,
        gamma=0.99,
        batch_size=32,
        replay_memory_size=5000,
        target_update_frequency=10
    ):
        self.state_size = 8
        self.action_size = 2

        self.model_path = os.path.abspath(
            model_path
        )

        self.learning_rate = float(
            learning_rate
        )

        self.gamma = float(
            gamma
        )

        self.batch_size = int(
            batch_size
        )

        self.target_update_frequency = int(
            target_update_frequency
        )

        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        # Main DQN model used for decisions and learning.
        self.model = DQNNetwork(
            state_size=self.state_size,
            action_size=self.action_size
        ).to(self.device)

        # Target network used to calculate stable targets.
        self.target_model = DQNNetwork(
            state_size=self.state_size,
            action_size=self.action_size
        ).to(self.device)

        # Load the existing pretrained model.
        self.load_model(
            self.model_path
        )

        # Copy pretrained weights to target network.
        self.target_model.load_state_dict(
            self.model.state_dict()
        )

        self.target_model.eval()

        # Optimizer for local incremental learning.
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=self.learning_rate
        )

        # Smooth L1 loss is commonly used for DQN.
        self.loss_function = nn.SmoothL1Loss()

        # Replay memory stores:
        # state, action, reward, next_state, done.
        self.replay_memory = deque(
            maxlen=int(
                replay_memory_size
            )
        )

        self.training_step_count = 0

    # ======================================================
    # LOAD TRAINED MODEL
    # ======================================================

    def load_model(self, model_path):
        """
        Load the existing trained RL model.
        """

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"RL model not found: {model_path}"
            )

        checkpoint = torch.load(
            model_path,
            map_location=self.device
        )

        # Supports the current raw state_dict format.
        if (
            isinstance(checkpoint, dict)
            and "model_state_dict" in checkpoint
        ):
            model_state_dict = checkpoint[
                "model_state_dict"
            ]
        else:
            model_state_dict = checkpoint

        self.model.load_state_dict(
            model_state_dict
        )

        self.model.eval()

        print(
            "RL Agent model loaded:",
            model_path
        )

    # ======================================================
    # SAVE UPDATED MODEL
    # ======================================================

    def save_model(self):
        """
        Save the locally updated DQN model.

        The model is saved as a raw state_dict so it remains
        compatible with the existing loading method and the
        original pretrained model format.
        """

        model_directory = os.path.dirname(
            self.model_path
        )

        os.makedirs(
            model_directory,
            exist_ok=True
        )

        torch.save(
            self.model.state_dict(),
            self.model_path
        )

    # ======================================================
    # GET SHARE / IGNORE DECISION
    # ======================================================

    def get_decision(self, state):
        """
        Get SHARE / IGNORE decision.

        Returns:
            action_number, action_text
        """

        state = self.validate_state(
            state
        )

        state_tensor = torch.FloatTensor(
            state
        ).unsqueeze(0).to(
            self.device
        )

        self.model.eval()

        with torch.no_grad():
            q_values = self.model(
                state_tensor
            )

        action = int(
            torch.argmax(
                q_values,
                dim=1
            ).item()
        )

        return (
            action,
            action_to_text(action)
        )

    # ======================================================
    # VALIDATE STATE
    # ======================================================

    def validate_state(self, state):
        """
        Validate that the RL state has exactly eight values.
        """

        state = np.asarray(
            state,
            dtype=np.float32
        ).reshape(-1)

        if len(state) != self.state_size:
            raise ValueError(
                "RL state must contain exactly "
                f"{self.state_size} values. "
                f"Received: {len(state)}"
            )

        if not np.all(
            np.isfinite(state)
        ):
            raise ValueError(
                "RL state contains invalid values."
            )

        return state

    # ======================================================
    # STORE EXPERIENCE
    # ======================================================

    def remember(
        self,
        state,
        action,
        reward,
        next_state,
        done
    ):
        """
        Store one RL transition in replay memory.

        Transition:
            state
            action
            reward
            next_state
            done
        """

        state = self.validate_state(
            state
        )

        next_state = self.validate_state(
            next_state
        )

        action = int(action)
        reward = float(reward)
        done = bool(done)

        if action not in {
            IGNORE,
            SHARE
        }:
            raise ValueError(
                f"Invalid RL action: {action}"
            )

        self.replay_memory.append(
            (
                state.copy(),
                action,
                reward,
                next_state.copy(),
                done
            )
        )

    # ======================================================
    # RECEIVE GLOBAL REWARD
    # ======================================================

    def receive_feedback(
        self,
        state,
        action,
        reward,
        next_state=None,
        done=True
    ):
        """
        Receive reward returned by the global verification
        server and continue training the local RL model.

        For the current one-step knowledge-sharing decision:

            state
                -> SHARE
                -> global verification
                -> reward
                -> episode ends

        Therefore:
            next_state = current state
            done = True
        """

        state = self.validate_state(
            state
        )

        if next_state is None:
            next_state = state.copy()

        next_state = self.validate_state(
            next_state
        )

        action = int(action)
        reward = float(reward)
        done = bool(done)

        self.remember(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done
        )

        loss = self.train_step()

        # Save the existing model after the local update.
        self.save_model()

        return {
            "status": "LOCAL_RL_AGENT_UPDATED",
            "action": action,
            "action_text": action_to_text(
                action
            ),
            "reward": reward,
            "loss": (
                round(loss, 6)
                if loss is not None
                else None
            ),
            "replay_memory_size": len(
                self.replay_memory
            ),
            "training_steps": (
                self.training_step_count
            ),
            "model_path": self.model_path
        }

    # ======================================================
    # DQN LOCAL TRAINING
    # ======================================================

    def train_step(self):
        """
        Perform one DQN training update using replay memory.

        The method starts learning immediately using the
        available experiences. Once replay memory contains
        at least batch_size records, it samples a full batch.
        """

        if len(self.replay_memory) == 0:
            return None

        current_batch_size = min(
            self.batch_size,
            len(self.replay_memory)
        )

        batch = random.sample(
            self.replay_memory,
            current_batch_size
        )

        states = np.asarray(
            [
                experience[0]
                for experience in batch
            ],
            dtype=np.float32
        )

        actions = np.asarray(
            [
                experience[1]
                for experience in batch
            ],
            dtype=np.int64
        )

        rewards = np.asarray(
            [
                experience[2]
                for experience in batch
            ],
            dtype=np.float32
        )

        next_states = np.asarray(
            [
                experience[3]
                for experience in batch
            ],
            dtype=np.float32
        )

        dones = np.asarray(
            [
                experience[4]
                for experience in batch
            ],
            dtype=np.float32
        )

        states_tensor = torch.tensor(
            states,
            dtype=torch.float32,
            device=self.device
        )

        actions_tensor = torch.tensor(
            actions,
            dtype=torch.long,
            device=self.device
        ).unsqueeze(1)

        rewards_tensor = torch.tensor(
            rewards,
            dtype=torch.float32,
            device=self.device
        )

        next_states_tensor = torch.tensor(
            next_states,
            dtype=torch.float32,
            device=self.device
        )

        dones_tensor = torch.tensor(
            dones,
            dtype=torch.float32,
            device=self.device
        )

        self.model.train()

        # Current Q-value for the selected action.
        current_q_values = self.model(
            states_tensor
        )

        selected_q_values = (
            current_q_values.gather(
                1,
                actions_tensor
            ).squeeze(1)
        )

        # Calculate target Q-values.
        with torch.no_grad():
            next_q_values = (
                self.target_model(
                    next_states_tensor
                )
            )

            maximum_next_q_values = (
                next_q_values.max(
                    dim=1
                )[0]
            )

            target_q_values = (
                rewards_tensor
                + self.gamma
                * maximum_next_q_values
                * (1.0 - dones_tensor)
            )

        loss = self.loss_function(
            selected_q_values,
            target_q_values
        )

        self.optimizer.zero_grad()

        loss.backward()

        # Prevent unstable gradient values.
        torch.nn.utils.clip_grad_norm_(
            self.model.parameters(),
            max_norm=1.0
        )

        self.optimizer.step()

        self.training_step_count += 1

        # Periodically update the target network.
        if (
            self.training_step_count
            % self.target_update_frequency
            == 0
        ):
            self.update_target_model()

        self.model.eval()

        return float(
            loss.item()
        )

    # ======================================================
    # UPDATE TARGET NETWORK
    # ======================================================

    def update_target_model(self):
        """
        Copy current DQN weights to the target network.
        """

        self.target_model.load_state_dict(
            self.model.state_dict()
        )

        self.target_model.eval()


# ==========================================================
# ENCODING FUNCTIONS
# ==========================================================

def encode_label_status(label_status):
    """
    RARE = 0.5
    NEW  = 1.0
    KNOWN = 0.0
    """

    label_status = str(
        label_status
    ).upper()

    if label_status == "RARE":
        return 0.5

    if label_status == "NEW":
        return 1.0

    return 0.0


def encode_colors(colors):
    """
    Convert extracted color list to numeric values.

    Example:
        ['black', 'white', 'red', 'gray']

    Output:
        has_red, has_blue, has_white, has_black
    """

    if colors is None:
        colors = []

    colors = [
        str(color).lower()
        for color in colors
    ]

    has_red = (
        1.0
        if "red" in colors
        else 0.0
    )

    has_blue = (
        1.0
        if "blue" in colors
        else 0.0
    )

    has_white = (
        1.0
        if "white" in colors
        else 0.0
    )

    has_black = (
        1.0
        if "black" in colors
        else 0.0
    )

    return (
        has_red,
        has_blue,
        has_white,
        has_black
    )


def encode_shape(shape):
    """
    Shape encoding:
        unknown   = 0.0
        polygon   = 0.5
        rectangle = 0.6
        square    = 0.7
        triangle  = 0.8
        octagon   = 0.9
        circle    = 1.0
    """

    shape = str(
        shape
    ).lower()

    shape_map = {
        "unknown": 0.0,
        "polygon": 0.5,
        "rectangle": 0.6,
        "square": 0.7,
        "triangle": 0.8,
        "octagon": 0.9,
        "circle": 1.0
    }

    return shape_map.get(
        shape,
        0.0
    )


def encode_text(text_status):
    """
    text_present = 1.0
    None         = 0.0
    """

    if text_status == "text_present":
        return 1.0

    return 0.0


def normalize_importance_score(
    importance_score
):
    importance_score = float(
        importance_score
    )

    if importance_score < 0.0:
        return 0.0

    if importance_score > 1.0:
        return 1.0

    return importance_score


# ==========================================================
# BUILD RL STATE
# ==========================================================

def build_rl_state(
    importance_score,
    label_status,
    colors,
    shape,
    text_status
):
    """
    Build RL state from current pipeline outputs.

    Example:
        importance_score = 0.6075
        label_status = "RARE"
        colors = ['black', 'white', 'red', 'gray']
        shape = "octagon"
        text_status = "text_present"

    Output:
        [0.6075, 0.5, 1, 0, 1, 1, 0.9, 1]
    """

    (
        has_red,
        has_blue,
        has_white,
        has_black
    ) = encode_colors(
        colors
    )

    state = np.array(
        [
            normalize_importance_score(
                importance_score
            ),
            encode_label_status(
                label_status
            ),
            has_red,
            has_blue,
            has_white,
            has_black,
            encode_shape(
                shape
            ),
            encode_text(
                text_status
            )
        ],
        dtype=np.float32
    )

    return state


def action_to_text(action):
    if action == SHARE:
        return "SHARE"

    return "IGNORE"