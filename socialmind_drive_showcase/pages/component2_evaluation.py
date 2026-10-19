"""Read-only presentation of backend-authored quantitative aggregate values."""
from nicegui import ui
from socialmind_drive_showcase.services.evaluation_reader import EVALUATION_ROOT, read_evaluation
from socialmind_drive_showcase.ui.layout import page_layout
from socialmind_drive_showcase.ui.cards import metric_card

def value(x):
    return "N/A" if x is None else f"{x:.3f}" if isinstance(x, float) else str(x)

def component2_evaluation_page():
    with page_layout("components"):
        with ui.column().classes("page-shell w-full py-10"):
            ui.label("Post-Training Evaluation").classes("text-3xl font-bold")
            ui.link("Component 2 qualitative live demo", "/component/right-of-way/live")
            read = read_evaluation()
            if not read["available"]:
                ui.label(read["message"])
                ui.label("Generate the frozen backend suite using run_post_training_evaluation.py. This page only reads results.")
                return
            data = read["payload"]
            verified = read.get("verification", {})
            ui.label("Evidence: " + read.get("source_path", "N/A"))
            if verified.get("available"):
                ui.label(f'Archived final episodes: {verified["verified"]}/{verified["expected"]} verified; {verified["missing"]} missing.').classes("text-xl font-bold")
                if not verified["complete"]:
                    ui.label("INCOMPLETE EVALUATION — this is not a completed 165-episode study.").classes("text-amber-7 font-bold")
                ui.label("Verified final-archive outcomes: " + str(verified["classification_counts"]))
                if verified["verification_errors"]:
                    ui.label("Archive verification issues: " + str(verified["verification_errors"])).classes("text-red-7")
            else:
                ui.label(verified.get("message", "Verified final count unavailable")).classes("text-amber-7")
            if data.get("suite") != "final":
                ui.label(f'Saved method-comparison tables and figures below are {data.get("suite", "unclassified")} evidence ({data.get("episode_count", "N/A")} episodes), separate from final-archive counts.').classes("text-amber-7")
            elif not data.get("complete_final_matrix"):
                ui.label("Saved aggregate is partial final evidence.").classes("text-amber-7")
            ui.label(data["evidence_classification"]).classes("text-xl font-bold")
            ui.label(data["scope"])
            ui.label("Bounded SUMO simulation evidence; no real-world validation. inD supplies intention-model training provenance.")
            ui.label("Out of scope: " + ", ".join(data["out_of_scope"]))
            with ui.row().classes("w-full gap-4"):
                metric_card("Collision-free episodes", f"{data['collision_free_episodes']}/{data['episode_count']}", "verified")
                metric_card("Blocked-zone violations", data["blocked_zone_violation_count"], "block")
                metric_card("Ego-local execution", data["decentralized_execution"], "hub")
                metric_card("Critic runtime calls", data["centralized_critic_runtime_calls"], "memory")
                metric_card("Policy unchanged", data["policy_hash_unchanged"], "lock")
            ui.label("Classifications: " + str(data["classification_counts"]))
            ui.label("HARDWARE-DEPENDENT RUNTIME MEASUREMENTS. Frozen backend values; no UI edits or recomputation.")
            keys = ("total_team_travel_time_seconds", "mean_travel_time_seconds", "throughput_vehicles_per_minute",
                "completion_rate", "mean_waiting_time_seconds", "p95_waiting_time_seconds",
                "maximum_waiting_time_seconds", "approach_waiting_time_gap_seconds",
                "conflicting_pair_fcfs_inversion_rate", "maximum_simultaneous_active_vehicles",
                "maximum_negotiation_participants", "mappo_negotiation_events",
                "mappo_outcomes_accepted", "mappo_outcomes_rejected_by_safety_shield",
                "fallback_activations", "fallback_rate", "timeout", "deadlock_observed")
            columns = [{"name": k, "label": k.replace("_", " "), "field": k} for k in ("scenario", "method") + keys]
            rows = [{"row_id": g["scenario_id"] + ":" + g["method"],
                "scenario": g["scenario_id"], "method": g["method"], **{
                k: value(g.get("metrics", {}).get(k, {}).get("mean")) for k in keys}} for g in data["groups"]]
            ui.table(columns=columns, rows=rows, row_key="row_id").classes("w-full")
            for path in sorted(read.get("plots_root", EVALUATION_ROOT / "plots").glob("*.png")):
                ui.image(str(path)).classes("w-full max-w-3xl")
            ui.label("Episodes, failures and safe degradation").classes("text-xl font-bold")
            columns = [{"name": k, "label": k.replace("_", " "), "field": k} for k in (
                "run_id", "method", "scenario_id", "seed", "classification", "error", "replay_command")]
            ui.table(columns=columns, rows=data["runs"], row_key="run_id").classes("w-full")
            if verified.get("available") and verified["runs"]:
                ui.label("Checksum-verified final archive — individual episodes; no new aggregate statistics").classes("text-xl font-bold")
                final_keys = ("run_id","method","scenario_id","seed","classification","completed","scheduled","mean_travel_time_seconds","mean_waiting_time_seconds","p95_waiting_time_seconds","maximum_waiting_time_seconds","throughput_vehicles_per_minute","collision_count","blocked_zone_violation_count")
                final_rows = [{**{k:value(r.get(k)) for k in final_keys}, **{k:value(r.get("metrics",{}).get(k)) for k in final_keys if k in r.get("metrics",{})},
                    "completed":value(r["metrics"].get("total_vehicles_completed")), "scheduled":value(r["metrics"].get("total_vehicles_scheduled"))} for r in verified["runs"]]
                ui.table(columns=[{"name":k,"field":k,"label":k.replace("_"," ")} for k in final_keys],rows=final_rows,row_key="run_id").classes("w-full")
            ui.label("TTT includes scheduled demand until completion or budget censoring. Waiting is observed stopped time on incoming lanes. Fairness inversions use conflicting served pairs; timestamp ties use vehicle IDs. Missing/aborted metrics are N/A.")
