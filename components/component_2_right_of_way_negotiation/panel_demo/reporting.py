"""Presentation-only JSON and Markdown reporting."""

from pathlib import Path

from negotiation_training.controlled_pilot import atomic_write_json


def write_panel_outputs(result, output_dir="results/panel_demo"):
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    atomic_write_json(root / "latest_panel_demo.json", result)
    metrics = result["metrics"]
    lines = ["# Live Panel Demonstration Summary", "",
             "**Evidence classification:** QUALITATIVE_PRESENTATION_ONLY", "",
             "This visualization is not validation, held-out evaluation, model "
             "selection, or replacement quantitative evidence.", "",
             "| Metric | Value |", "|---|---:|"]
    for key in ("presentation_vehicles_scheduled",
                "presentation_vehicles_completed", "unfinished_vehicles",
                "negotiation_events", "mappo_decision_epochs",
                "rule_resolved_events", "renegotiation_events",
                "safe_hold_activations", "collisions",
                "blocked_zone_violations", "maximum_negotiation_participants"):
        lines.append(f"| {key} | {metrics[key]} |")
    lines += ["", f"Policy hash unchanged: {result['policy_hash_unchanged']}"]
    (root / "latest_panel_demo_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
