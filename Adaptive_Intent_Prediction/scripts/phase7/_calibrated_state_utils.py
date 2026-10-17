from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


def _walk_for_key(obj, keys):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower() in keys:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    pass
        for value in obj.values():
            found = _walk_for_key(value, keys)
            if found is not None:
                return found

    elif isinstance(obj, list):
        for value in obj:
            found = _walk_for_key(value, keys)
            if found is not None:
                return found

    return None


def load_deployment_temperature_and_threshold():
    candidates = [
        Path("outputs/phase6/final_test/uncertainty_deployment_config.json"),
        Path("outputs/phase6/uncertainty_deployment_config.json"),
        Path("outputs/phase6/final_test/final_uncertainty_summary.json"),
        Path("outputs/phase6/temperature_calibration.json"),
    ]

    payloads = []

    for path in candidates:
        if path.exists():
            payloads.append(
                (
                    path,
                    json.loads(path.read_text(encoding="utf-8")),
                )
            )

    if not payloads:
        raise FileNotFoundError(
            "Could not find Phase-6 deployment/calibration JSON files."
        )

    temperature_keys = {
        "temperature",
        "temperature_value",
        "optimal_temperature",
        "calibration_temperature",
    }

    threshold_keys = {
        "mc_threshold",
        "frozen_mc_threshold",
        "decision_threshold",
        "crossing_threshold",
        "calibrated_mc_threshold",
        "threshold",
    }

    temperature = None
    threshold = None
    temperature_source = None
    threshold_source = None

    for path, payload in payloads:
        if temperature is None:
            found = _walk_for_key(payload, temperature_keys)
            if found is not None:
                temperature = found
                temperature_source = str(path)

        if threshold is None:
            found = _walk_for_key(payload, threshold_keys)
            if found is not None:
                threshold = found
                threshold_source = str(path)

    if temperature is None:
        raise KeyError(
            "Could not find the frozen Phase-6 temperature in JSON outputs."
        )

    if threshold is None:
        raise KeyError(
            "Could not find the frozen calibrated MC decision threshold "
            "in Phase-6 JSON outputs."
        )

    if temperature <= 0:
        raise ValueError(f"Invalid temperature: {temperature}")

    if not (0.0 < threshold < 1.0):
        raise ValueError(f"Invalid MC threshold: {threshold}")

    return (
        float(temperature),
        float(threshold),
        temperature_source,
        threshold_source,
    )


def calibrate_probability(probability, temperature):
    p = np.asarray(probability, dtype=np.float64)
    p = np.clip(p, 1e-7, 1.0 - 1e-7)

    logit = np.log(p / (1.0 - p))
    calibrated = 1.0 / (1.0 + np.exp(-(logit / temperature)))

    return calibrated.astype(np.float32)


def confidence_from_probability(probability):
    p = np.asarray(probability, dtype=np.float32)
    return np.maximum(p, 1.0 - p).astype(np.float32)


def normalized_binary_entropy(probability):
    p = np.asarray(probability, dtype=np.float64)
    p = np.clip(p, 1e-7, 1.0 - 1e-7)

    entropy = -(
        p * np.log(p)
        + (1.0 - p) * np.log(1.0 - p)
    )

    return (entropy / math.log(2.0)).astype(np.float32)


def decision_margin_uncertainty(probability):
    p = np.asarray(probability, dtype=np.float32)
    return (
        1.0 - 2.0 * np.abs(p - 0.5)
    ).clip(0.0, 1.0).astype(np.float32)
