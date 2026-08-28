from nicegui import ui

from socialmind_drive_showcase.config import COMPONENT2
from socialmind_drive_showcase.services.result_reader import (format_edge,
    read_panel_results, short_vehicle_id)
from socialmind_drive_showcase.ui.cards import metric_card


METRICS = (
    ("Presentation vehicles scheduled", "presentation_vehicles_scheduled", "event"),
    ("Presentation vehicles completed", "presentation_vehicles_completed", "task_alt"),
    ("Unfinished vehicles", "unfinished_vehicles", "pending_actions"),
    ("Negotiation events", "negotiation_events", "hub"),
    ("MAPPO decision epochs", "mappo_decision_epochs", "psychology"),
    ("Rule-resolved events", "rule_resolved_events", "gavel"),
    ("Re-negotiation events", "renegotiation_events", "sync"),
    ("Collisions", "collisions", "warning"),
    ("Blocked-zone violations", "blocked_zone_violations", "block"),
    ("Maximum participants", "maximum_negotiation_participants", "groups"),
)


@ui.refreshable
def results_panel():
    result = read_panel_results(COMPONENT2.result_path)
    if not result["available"]:
        with ui.element("div").classes("reserved-panel w-full"):
            ui.icon("insert_chart_outlined", size="48px")
            ui.label("LATEST RESULTS NOT AVAILABLE").classes("font-bold tracking-wider")
            ui.label(result["message"])
        return
    payload, metrics = result["payload"], result["metrics"]
    with ui.element("div").classes("disclaimer w-full"):
        ui.label("QUALITATIVE PRESENTATION ONLY").classes("font-extrabold tracking-wider")
        ui.label("These live panel metrics are not validation, held-out evaluation, model-selection evidence, or replacement quantitative research evidence.")
    with ui.element("div").classes("info-grid mt-6"):
        for label, key, icon in METRICS:
            metric_card(label, metrics.get(key, "—"), icon)
    with ui.element("div").classes("info-grid mt-5"):
        metric_card("Selected policy", payload.get("selected_candidate_id", "—"), "model_training")
        metric_card("Policy hash unchanged", payload.get("policy_hash_unchanged", "—"), "verified")
        metric_card("Centralized critic calls", payload.get("centralized_critic_calls", "—"), "memory")
        metric_card("Training operations", payload.get("training_operations", "—"), "school")
        metric_card("Held-out scenarios consumed", payload.get("held_out_scenarios_consumed", "—"), "science")
    event = result["latest_mappo_event"]
    if event:
        with ui.element("div").classes("result-panel mt-8"):
            ui.label("LATEST MAPPO-AUTHORIZED EVENT").classes("eyebrow")
            ui.label(event.get("status", "—")).classes("text-2xl font-bold mt-2")
            with ui.row().classes("gap-2 mt-3"):
                for participant in event.get("participants", ()):
                    ui.label(short_vehicle_id(participant)).classes("chip")
            with ui.element("div").classes("info-grid mt-7"):
                _edge_column("Original regulatory graph", event.get("original_regulatory_graph", ()))
                _action_column("Proposer actions", event.get("proposer_actions", ()))
                _action_column("Responder actions", event.get("responder_actions", ()))
                _edge_column("Effective coordination graph", event.get("effective_coordination_graph", ()))
            with ui.row().classes("mt-6 gap-8"):
                _vehicle_list("READY", event.get("ready_vehicle_ids", ()), "text-green-7")
                _vehicle_list("BLOCKED", event.get("blocked_vehicle_ids", ()), "text-red-7")


def _edge_column(title, edges):
    with ui.column().classes("info-card gap-2"):
        ui.label(title).classes("font-bold text-sm")
        for edge in edges:
            ui.label(format_edge(edge)).classes("action-card")


def _action_column(title, actions):
    with ui.column().classes("info-card gap-2"):
        ui.label(title).classes("font-bold text-sm")
        if not actions:
            ui.label("No action occurred").classes("text-blue-grey-5 text-sm")
        for subject, action in actions:
            label = (format_edge(subject) if len(subject) == 2 else
                     short_vehicle_id(subject[-2]) + " → " +
                     short_vehicle_id(subject[-1]))
            ui.label(f"{label}: {action}").classes("action-card")


def _vehicle_list(title, values, color):
    with ui.column().classes("gap-1"):
        ui.label(title).classes(f"font-extrabold {color}")
        ui.label(", ".join(short_vehicle_id(x) for x in values) or "None")
