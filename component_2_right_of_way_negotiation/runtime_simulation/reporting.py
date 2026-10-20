"""Presentation-only JSON and Markdown reporting."""

# Import Path from pathlib for the operations below.
from pathlib import Path
# Import datetime, timezone from datetime for the operations below.
from datetime import datetime, timezone
# Import re for use in this module.
import re

# Import atomic_write_json from negotiation_training.controlled_pilot for the operations below.
from negotiation_training.controlled_pilot import atomic_write_json


# Write panel outputs using the inputs and processing steps below.
# Input result: the supplied result.
# Input output_dir: the supplied output dir.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def write_panel_outputs(result, output_dir="results/runtime_simulation"):
    # Set root to the result of Path(output_dir).
    # Create the directory requested by root.
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(root / "latest_runtime_simulation.json", result)
    # Call write_presentation_run_summary with the supplied arguments.
    write_presentation_run_summary(result, root / "presentation_runs")
    # Set metrics to result at 'metrics'.
    metrics = result["metrics"]
    # Set lines to a list containing the text '# Runtime Simulation Summary', the text '', the text '**Evidence
    # classification:**...
    lines = ["# Runtime Simulation Summary", "",
             "**Evidence classification:** QUALITATIVE_PRESENTATION_ONLY", "",
             "This visualization is not validation, held-out evaluation, model "
             "selection, or replacement quantitative evidence.", "",
             "| Metric | Value |", "|---|---:|"]
    # Iterate over a tuple containing the text 'presentation_vehicles_scheduled', the text
    # 'presentation_vehicles_completed', the text..., binding each item to key.
    for key in ("presentation_vehicles_scheduled",
                "presentation_vehicles_completed", "unfinished_vehicles",
                "negotiation_events", "mappo_decision_epochs",
                "rule_resolved_events", "renegotiation_events",
                "safe_hold_activations", "collisions",
                "blocked_zone_violations", "maximum_negotiation_participants"):
        # Append formatted text built from the embedded values to lines.
        lines.append(f"| {key} | {metrics[key]} |")
    # Iterate over a tuple containing the text 'total_vehicles_scheduled', the text 'total_vehicles_spawned', the
    # text..., binding each item to key.
    for key in ("total_vehicles_scheduled", "total_vehicles_spawned", "total_vehicles_completed",
                "maximum_simultaneous_active_vehicles", "maximum_simultaneously_moving_vehicles",
                "maximum_per_approach_queue_depth", "centralized_critic_runtime_calls",
                "decentralized_execution", "centralized_execution_graph_used_for_control"):
        # Run this branch when key belongs to metrics.
        if key in metrics:
            # Append formatted text built from the embedded values to lines.
            lines.append(f"| {key} | {metrics[key]} |")
    # Update lines to its current value plus a list containing the text '', formatted text built from the embedded
    # values.
    lines += ["", f"Policy hash unchanged: {result['policy_hash_unchanged']}"]
    # Write the supplied text to (root / 'latest_runtime_simulation_summary.md').
    (root / "latest_runtime_simulation_summary.md").write_text(
        # Supply encoding as the text 'utf-8'.
        "\n".join(lines) + "\n", encoding="utf-8")


# Persist immutable qualitative presentation history, never evidence.
# Input result: the supplied result.
# Input history_root: the supplied history root.
# Output: target.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def write_presentation_run_summary(result, history_root):
    """Persist immutable qualitative presentation history, never evidence."""
    # Set root to the result of Path(history_root).
    # Create the directory requested by root.
    root = Path(history_root); root.mkdir(parents=True, exist_ok=True)
    # Set raw_id to 'presentation_run_id' from result; use None if absent or the result of
    # datetime.now(timezone.utc).strftime(the text '%Y%m%dT%H%M%S_%fZ').
    raw_id = result.get("presentation_run_id") or datetime.now(
        # Supply timezone.utc to datetime.now.
        timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    # Set run_id to the result of re.sub(the text '[^A-Za-z0-9_.-]', the text '_', a string built from raw_id).
    run_id = re.sub(r"[^A-Za-z0-9_.-]", "_", str(raw_id))
    # Set metrics to result at 'metrics'.
    metrics = result["metrics"]
    # Set history to 'presentation_vehicle_history' from result; use an empty dictionary if absent.
    history = result.get("presentation_vehicle_history", {})
    # Set timeline to an empty list.
    timeline = []
    # Iterate over 'events' from result; use an empty tuple if absent, binding each item to item.
    for item in result.get("events", ()):
        # Append a dictionary containing timestamp, event, mappo_invocation, participants, original_graph,
        # proposer_actions,... to timeline.
        timeline.append({"timestamp": item.get("timestamp", 0.0),
                         # Store 'status' from item; use the text 'NEGOTIATION_EVENT' if absent under 'event'.
                         "event": item.get("status", "NEGOTIATION_EVENT"),
                         # Store 'mappo_invocation' from item; use None if absent under 'mappo_invocation'.
                         "mappo_invocation": item.get("mappo_invocation"),
                         # Store 'participants' from item; use an empty tuple if absent under 'participants'.
                         "participants": item.get("participants", ()),
                         # Store 'original_regulatory_graph' from item; use an empty tuple if absent under
                         # 'original_graph'.
                         "original_graph": item.get(
                             # Supply an empty tuple to item.get.
                             "original_regulatory_graph", ()),
                         # Store 'proposer_actions' from item; use an empty tuple if absent under
                         # 'proposer_actions'.
                         "proposer_actions": item.get("proposer_actions", ()),
                         # Store 'responder_actions' from item; use an empty tuple if absent under
                         # 'responder_actions'.
                         "responder_actions": item.get("responder_actions", ()),
                         # Store 'effective_coordination_graph' from item; use an empty tuple if absent under
                         # 'effective_graph'.
                         "effective_graph": item.get(
                             # Supply an empty tuple to item.get.
                             "effective_coordination_graph", ()),
                         # Store 'ready_vehicle_ids' from item; use an empty tuple if absent under 'ready'.
                         "ready": item.get("ready_vehicle_ids", ()),
                         # Store 'blocked_vehicle_ids' from item; use an empty tuple if absent under 'blocked'.
                         "blocked": item.get("blocked_vehicle_ids", ()),
                         # Store 'policy_factor_diagnostics' from item; use an empty tuple if absent under
                         # 'policy_factors'.
                         "policy_factors": item.get(
                             # Supply an empty tuple to item.get.
                             "policy_factor_diagnostics", ())})
    # Iterate over 'diagnostics' from result; use an empty tuple if absent, binding each item to item.
    for item in result.get("diagnostics", ()):
        # Run this branch when 'event' from item; use None if absent belongs to a set containing the text
        # 'PLAN_INVALIDATED', the text 'RENEGOTIATION_REQUIRED', the text 'PRESENTATION_STOP_REQUESTED',...
        if item.get("event") in {"PLAN_INVALIDATED", "RENEGOTIATION_REQUIRED",
                                  "PRESENTATION_STOP_REQUESTED",
                                  "MAPPO_INVOCATION_BLOCKED"}:
            # Append a dictionary built from item to timeline.
            timeline.append(dict(item))
    # Set summary to a dictionary containing schema, evidence_classification, validation_evidence,
    # held_out_evidence,...
    summary = {
        "schema": "QUALITATIVE_PRESENTATION_RUN_V1",
        "evidence_classification": "QUALITATIVE_PRESENTATION_ONLY",
        # Store False under 'validation_evidence'.
        # Store False under 'held_out_evidence'.
        "validation_evidence": False, "held_out_evidence": False,
        # Store False under 'model_selection_evidence'.
        "model_selection_evidence": False,
        # Store run_id under 'run_id'.
        # Store 'run_status' from result; use the text 'FAILED' if absent under 'run_status'.
        "run_id": run_id, "run_status": result.get("run_status", "FAILED"),
        # Store 'presentation_scenario_id' from result; use None if absent under 'scenario_id'.
        "scenario_id": result.get("presentation_scenario_id"),
        # Store 'started_at_utc' from result; use None if absent under 'started_at_utc'.
        "started_at_utc": result.get("started_at_utc"),
        # Store 'ended_at_utc' from result; use None if absent under 'ended_at_utc'.
        "ended_at_utc": result.get("ended_at_utc"),
        # Store 'actual_simulation_time_seconds' from result; use None if absent under 'simulation_time_seconds'.
        "simulation_time_seconds": result.get("actual_simulation_time_seconds"),
        # Store a dictionary built from metrics under 'metrics'.
        "metrics": dict(metrics),
        # Store 'policy_hash_unchanged' from result; use None if absent under 'policy_hash_unchanged'.
        "policy_hash_unchanged": result.get("policy_hash_unchanged"),
        # Store 'final_snapshots' from history; use an empty tuple if absent under 'vehicles'.
        "vehicles": history.get("final_snapshots", ()),
        # Store 'process_traces' from history; use an empty dictionary if absent under 'vehicle_process_traces'.
        "vehicle_process_traces": history.get("process_traces", {}),
        # Store the sorted values from timeline under 'event_timeline'.
        "event_timeline": sorted(timeline, key=lambda item: item.get(
            # Supply the text 'timestamp' to the enclosing expression.
            "timestamp", 0.0))}
    # Set target to root divided by formatted text built from the embedded values.
    target = root / f"run_{run_id}.json"
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(target, summary)
    # Call atomic_write_json with the supplied arguments.
    atomic_write_json(root / "latest_presentation_run.json", summary)
    # Return target to the caller.
    return target
