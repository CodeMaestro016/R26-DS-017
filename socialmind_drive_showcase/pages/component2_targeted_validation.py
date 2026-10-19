"""Small read-only panel evidence section; no frontend metric calculation."""
from nicegui import ui
from socialmind_drive_showcase.services.targeted_validation_reader import read_targeted_validation

def shown(value):
    return "N/A" if value is None else str(value)

def targeted_validation_section():
    ui.label("Targeted Validation").classes("text-2xl font-bold mt-8")
    read = read_targeted_validation()
    if not read["available"]:
        ui.label(read["message"])
        return
    data = read["payload"]
    ui.label(data["evidence_classification"])
    ui.label(data["scope"])
    ui.label(data["disclaimer"])
    ui.label(data["note"])
    ui.label("Panel comment traceability").classes("text-lg font-bold")
    for item in data["traceability"]:
        ui.label(item["comment"] + " → " + item["evidence"] + " — " + item["status"])
    columns = [dict(name=k, field=k, label=k.replace("_", " ")) for k in ("case_id", "method", "evidence_version", "classification", "completed", "mean_wait", "max_wait", "mappo_calls", "fallbacks")]
    rows = []
    for index, case in enumerate(data["cases"]):
        m = case["metrics"]
        rows.append(dict(row_id=index, case_id=case["case_id"], method=case["method"], evidence_version=case.get("evidence_version"), classification=case["classification"],
            completed=shown(m.get("total_vehicles_completed")) + "/" + shown(m.get("total_vehicles_scheduled")),
            mean_wait=shown(m.get("mean_waiting_time_seconds")), max_wait=shown(m.get("maximum_waiting_time_seconds")),
            mappo_calls=shown(m.get("mappo_inference_call_count")), fallbacks=shown(m.get("fallback_activations"))))
    ui.table(columns=columns, rows=rows, row_key="row_id").classes("w-full")
    ui.label("Dense 16-Vehicle Validation: recorded fairness/time and queues").classes("text-lg font-bold")
    for dense in data["dense"]:
        ui.label(dense["case_id"] + ": " + dense["purpose"] + " — " + dense["classification"])
        ui.label(dense.get("negotiation_note", ""))
        for key, value in dense["metrics"].items():
            if key in {"total_vehicles_scheduled", "total_vehicles_spawned", "total_vehicles_completed", "maximum_simultaneous_active_vehicles", "maximum_simultaneously_moving_vehicles", "maximum_negotiation_participants", "maximum_per_approach_queue_depth", "per_approach_mean_waiting_time_seconds", "mean_waiting_time_seconds", "median_waiting_time_seconds", "p95_waiting_time_seconds", "maximum_waiting_time_seconds", "approach_waiting_time_gap_seconds", "conflicting_pair_fcfs_inversion_rate", "total_team_travel_time_seconds", "throughput_vehicles_per_minute"}:
                ui.label(key.replace("_", " ") + ": " + shown(value))
    ui.label("Limitations / failure evidence").classes("text-lg font-bold")
    for case in data["limitations"]:
        ui.label(case["case_id"] + ": " + case["classification"])
        ui.label(shown(case["metrics"].get("deadlock_cause")))
    ui.label("Recorded safety / decentralized execution evidence: " + shown(data["totals"]))
    ui.label(data["data_provenance"])
