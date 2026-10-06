"""Presentation-only JSON and Markdown reporting."""

from pathlib import Path
from datetime import datetime, timezone
import re

from negotiation_training.controlled_pilot import atomic_write_json


def write_panel_outputs(result, output_dir="results/panel_demo"):
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    atomic_write_json(root / "latest_panel_demo.json", result)
    write_presentation_run_summary(result, root / "presentation_runs")
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
    for key in ("total_vehicles_scheduled", "total_vehicles_spawned", "total_vehicles_completed",
                "maximum_simultaneous_active_vehicles", "maximum_simultaneously_moving_vehicles",
                "maximum_per_approach_queue_depth", "centralized_critic_runtime_calls",
                "decentralized_execution", "centralized_execution_graph_used_for_control"):
        if key in metrics:
            lines.append(f"| {key} | {metrics[key]} |")
    lines += ["", f"Policy hash unchanged: {result['policy_hash_unchanged']}"]
    (root / "latest_panel_demo_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")


def write_presentation_run_summary(result, history_root):
    """Persist immutable qualitative presentation history, never evidence."""
    root = Path(history_root); root.mkdir(parents=True, exist_ok=True)
    raw_id = result.get("presentation_run_id") or datetime.now(
        timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    run_id = re.sub(r"[^A-Za-z0-9_.-]", "_", str(raw_id))
    metrics = result["metrics"]
    history = result.get("presentation_vehicle_history", {})
    timeline = []
    for item in result.get("events", ()):
        timeline.append({"timestamp": item.get("timestamp", 0.0),
                         "event": item.get("status", "NEGOTIATION_EVENT"),
                         "mappo_invocation": item.get("mappo_invocation"),
                         "participants": item.get("participants", ()),
                         "original_graph": item.get(
                             "original_regulatory_graph", ()),
                         "proposer_actions": item.get("proposer_actions", ()),
                         "responder_actions": item.get("responder_actions", ()),
                         "effective_graph": item.get(
                             "effective_coordination_graph", ()),
                         "ready": item.get("ready_vehicle_ids", ()),
                         "blocked": item.get("blocked_vehicle_ids", ()),
                         "policy_factors": item.get(
                             "policy_factor_diagnostics", ())})
    for item in result.get("diagnostics", ()):
        if item.get("event") in {"PLAN_INVALIDATED", "RENEGOTIATION_REQUIRED",
                                  "PRESENTATION_STOP_REQUESTED",
                                  "MAPPO_INVOCATION_BLOCKED"}:
            timeline.append(dict(item))
    summary = {
        "schema": "QUALITATIVE_PRESENTATION_RUN_V1",
        "evidence_classification": "QUALITATIVE_PRESENTATION_ONLY",
        "validation_evidence": False, "held_out_evidence": False,
        "model_selection_evidence": False,
        "run_id": run_id, "run_status": result.get("run_status", "FAILED"),
        "scenario_id": result.get("presentation_scenario_id"),
        "started_at_utc": result.get("started_at_utc"),
        "ended_at_utc": result.get("ended_at_utc"),
        "simulation_time_seconds": result.get("actual_simulation_time_seconds"),
        "metrics": dict(metrics),
        "policy_hash_unchanged": result.get("policy_hash_unchanged"),
        "vehicles": history.get("final_snapshots", ()),
        "vehicle_process_traces": history.get("process_traces", {}),
        "event_timeline": sorted(timeline, key=lambda item: item.get(
            "timestamp", 0.0))}
    target = root / f"run_{run_id}.json"
    atomic_write_json(target, summary)
    atomic_write_json(root / "latest_presentation_run.json", summary)
    return target
