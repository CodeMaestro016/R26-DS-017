"""Evidence-backed presentation sections for the Component 2 detail page."""

import json

from nicegui import ui

from socialmind_drive_showcase.config import COMPONENT2_ROOT
from socialmind_drive_showcase.pages.component2_results import results_panel
from socialmind_drive_showcase.services.folder_service import open_predefined_folder
from socialmind_drive_showcase.ui.reusable import section_heading


DECISION_STEPS = (
    ("01", "OBSERVE", "What vehicles can I currently detect?", "Ego-local detections"),
    ("02", "REMEMBER", "Local Dynamic Map", "Tracks, confidence, observation history"),
    ("03", "PREDICT", "GRU intention prediction", "LEFT / RIGHT / STRAIGHT / UNKNOWN"),
    ("04", "FIND PHYSICAL CONFLICTS", "Can movement paths overlap?", "Physical conflict-zone relationship"),
    ("05", "CHECK TIMING / REACHABILITY", "When could each vehicle enter and clear?", "Spatial-only / temporal / unresolved"),
    ("06", "APPLY TRAFFIC RULES", "Who has a mandatory yield obligation?", "Regulatory assessment"),
    ("07", "BUILD PRECEDENCE GRAPH", "A → B means A yields to B", "Directed regulatory graph"),
    ("08", "NEGOTIATE IF NEEDED", "Only for an eligible unresolved order", "Semantic precedence claims"),
    ("09", "PLAN", "Deterministic execution permission", "READY / BLOCKED"),
    ("10", "EXECUTE", "SUMO-safe physical constraints", "Controller request"),
)

IMPLEMENTATION_MAP = (
    ("SUMO vehicle state", "environment.py", "SUMOEnv.get_vehicles()"),
    ("Ego-local perception", "perception_interface.py", "PerceptionInterface.generate_observations()"),
    ("Local Dynamic Map", "observation.py", "LocalDynamicMap / ObservationManager"),
    ("Movement paths", "conflict/map_path_manager.py", "MapPathManager"),
    ("Physical conflict zones", "conflict/conflict_zone_manager.py", "ConflictZoneManager"),
    ("Temporal / reachability reasoning", "conflict/occupancy_assessor.py", "ConflictZoneOccupancyAssessor"),
    ("Traffic rules", "traffic_rules/rule_engine.py", "TrafficRuleEngine"),
    ("Precedence graph + cycle analysis", "negotiation_learning/precedence_graph.py", "RegulatoryPrecedenceGraphBuilder"),
    ("Execution planner", "negotiation_execution/planner.py", "ConflictZoneExecutionPlanner"),
    ("Physical controller", "negotiation_execution/controller.py", "build_sumo_native_speed_constraint()"),
)


def load_research_evidence():
    """Read only stable, auditable scientific deployment artifacts."""
    selection_root = COMPONENT2_ROOT / "results" / "final_mappo_selection_v2"
    validation = json.loads((selection_root / "comparison" /
                             "candidate_validation_summary.json").read_text(encoding="utf-8"))
    selected = json.loads((selection_root / "selected_configuration.json").read_text(encoding="utf-8"))
    deployment = json.loads((COMPONENT2_ROOT / "models" / "intention" /
                             "deployment_manifest_onnx.json").read_text(encoding="utf-8"))
    rows = {}
    for candidate in ("E5", "E10", "E15"):
        record = validation["candidates"][candidate]
        rows[candidate] = record["summary"][
            "mean_replication_total_team_travel_time_seconds"]
    return {
        "validation": rows,
        "selected": selected["selected_candidate_id"],
        "held_out_used_for_selection": selected["held_out_used_for_selection"],
        "globally_optimal_claim": selected["globally_optimal_claim"],
        "runtime": deployment["runtime"],
        "verification_passed": deployment["verification"]["all_checks_passed"],
        "models_retrained": deployment["models_retrained_in_cell_24"],
    }


def component2_explanation_sections():
    _decision_process()
    _runtime_inputs()
    _conflict_reasoning()
    _regulatory_reasoning()
    _mappo_semantics()
    _execution_safety()
    _implementation_map()
    _research_evidence()
    _live_results()


def _section(eyebrow, title, copy=None, dark=False):
    classes = "section c2-explainer-section w-full"
    if dark:
        classes += " section-dark"
    section = ui.element("section").classes(classes)
    section.__enter__()
    column = ui.column().classes("page-shell")
    column.__enter__()
    section_heading(eyebrow, title, copy, dark=dark)
    return section, column


def _close(section, column):
    column.__exit__(None, None, None)
    section.__exit__(None, None, None)


def _bullet(text, tone=""):
    with ui.row().classes("c2-bullet-row items-start no-wrap"):
        ui.icon("arrow_right", size="18px").classes(tone or "text-cyan-7")
        ui.label(text).classes("c2-bullet-text")


def _decision_process():
    section, column = _section(
        "DECISION PROCESS", "How One Ego AV Makes a Decision",
        "Each autonomous vehicle independently builds its local understanding before traffic rules, negotiation and physical execution.")
    with ui.element("div").classes("c2-decision-flow"):
        for number, title, question, output in DECISION_STEPS:
            with ui.element("article").classes("c2-step-card"):
                ui.label(number).classes("c2-step-number")
                ui.label(title).classes("c2-step-title")
                ui.label(question).classes("c2-step-question")
                ui.label(output).classes("c2-step-output")
    _close(section, column)


def _runtime_inputs():
    section, column = _section("RUNTIME INPUTS", "What Does Each Ego AV Actually Know?")
    with ui.element("div").classes("c2-three-grid"):
        with ui.element("article").classes("c2-explain-card"):
            ui.label("A · EGO SELF STATE").classes("c2-card-kicker")
            for value in ("position", "speed", "heading", "vehicle length / width",
                          "lane ID / lane position / lane length", "road ID",
                          "max acceleration capability", "comfortable deceleration capability",
                          "emergency deceleration capability", "maximum speed",
                          "ego's own planned manoeuvre"):
                _bullet(value)
            ui.label("The ego vehicle knows its own planned manoeuvre.").classes("c2-note")
        with ui.element("article").classes("c2-explain-card"):
            ui.label("B · OBSERVED TARGET STATE").classes("c2-card-kicker")
            for value in ("detected position, speed and heading", "vehicle dimensions",
                          "relative position and relative velocity", "range and bearing",
                          "visible fraction / occlusion evidence",
                          "lane / road context available in the simulation abstraction",
                          "observation timestamp"):
                _bullet(value)
            ui.label("LDM ADDS").classes("c2-mini-heading")
            ui.label("is_observed · confidence · position history · velocity vector · intention prediction").classes("c2-compact-copy")
            with ui.element("div").classes("c2-warning-callout"):
                ui.label("NO TARGET ROUTE TRUTH").classes("font-extrabold")
                ui.label("The operational ego pipeline does not receive another vehicle's route_id, route_index, or true future manoeuvre.")
            ui.label("The GRU predicts intention from genuine observed position history. Do not describe SUMO route truth or current SUMO acceleration as the GRU model input.").classes("c2-note")
        with ui.element("article").classes("c2-explain-card"):
            ui.label("C · STATIC DOMAIN KNOWLEDGE").classes("c2-card-kicker")
            for value in ("SUMO road-network geometry", "legal movement paths",
                          "conflict-zone catalogue", "intersection topology",
                          "regulatory profile", "deterministic traffic-rule definitions"):
                _bullet(value)
    _close(section, column)


def _conflict_reasoning():
    section, column = _section("CONFLICT REASONING", "Where Can Vehicles Conflict — and When Does It Matter?")
    with ui.element("div").classes("c2-two-grid"):
        with ui.element("article").classes("c2-explain-card"):
            ui.label("SPATIAL CONFLICT · WHERE?").classes("c2-card-kicker")
            _mini_flow(("Ego movement path + target candidate path + vehicle width",
                        "Physical swept regions", "Geometric overlap", "Conflict Zone · CZ_xxx"))
            ui.label("Movement paths are derived from the SUMO map. ConflictZoneManager uses physical swept envelopes and Shapely geometry.").classes("c2-compact-copy")
            ui.label("PATH DETERMINES WHERE.").classes("c2-memory-line")
        with ui.element("article").classes("c2-explain-card"):
            ui.label("TEMPORAL / REACHABILITY · WHEN?").classes("c2-card-kicker")
            ui.label("Inputs").classes("c2-mini-heading")
            ui.label("path progress · zone interval · distance to entry · vehicle length · speed · acceleration · comfortable deceleration · maximum speed").classes("c2-compact-copy")
            ui.label("Outputs").classes("c2-mini-heading")
            ui.label("BEFORE_ZONE · CURRENTLY_OCCUPYING · CLEARED_ZONE · predicted entry/clear time · earliest reachable time · can stop before zone · TEMPORAL_CONFLICT / SPATIAL_ONLY / unresolved").classes("c2-compact-copy")
            ui.label("SPEED AND DYNAMICS DETERMINE WHEN.").classes("c2-memory-line")
    with ui.expansion("Technical detail", icon="functions").classes("c2-technical-expansion w-full"):
        ui.label("Z_ij = P_i ∩ P_j").classes("c2-formula")
        ui.label("The conflict zone is the physical overlap of the two swept path regions.")
        with ui.row().classes("gap-8 mt-3"):
            ui.label("Nominal timing: time = distance / speed")
            ui.label("Stopping distance: d_stop = v² / (2a)")
    _close(section, column)


def _regulatory_reasoning():
    section, column = _section("REGULATORY REASONING", "From Physical Conflict to Legal Precedence")
    with ui.element("article").classes("c2-input-strip"):
        ui.label("TrafficRuleEngine inputs / context").classes("c2-card-kicker")
        ui.label("ego movement path · target candidate movement path(s) · relative approach · physical conflict candidate relationship · DE_STVO_UNCONTROLLED_4WAY_V1").classes("c2-compact-copy")
        ui.label("Legal precedence is not selected using a speed, TTC, urgency, or vehicle-ID score.").classes("c2-note")
    with ui.element("div").classes("c2-three-grid mt-6"):
        _rule_card("DE-STVO-8-1", "Right-before-left", "At this uncontrolled equal-road junction, a conflicting vehicle approaching from the right has precedence.")
        _rule_card("DE-STVO-9-3", "Turning vs oncoming", "A turning ego yields to physically conflicting oncoming passenger traffic.")
        _rule_card("DE-STVO-9-4", "Left vs oncoming right", "A left-turning ego yields to an oncoming right-turn candidate.")
    ui.label("ACTUAL REGULATORY OUTCOMES").classes("c2-mini-heading mt-7")
    with ui.element("div").classes("c2-token-row"):
        for value in ("EGO_MUST_YIELD", "EGO_HAS_PRECEDENCE_UNDER_RULE",
                      "NO_PAIRWISE_PRECEDENCE_RULE", "UNRESOLVED_DUE_TO_TARGET_MANOEUVRE",
                      "REGULATORY_INPUT_UNRESOLVED"):
            ui.label(value).classes("c2-status-token")
    with ui.element("div").classes("c2-graph-rule mt-7"):
        ui.label("EGO_MUST_YIELD → EGO → TARGET").classes("c2-graph-example")
        ui.label("EGO_HAS_PRECEDENCE_UNDER_RULE → TARGET → EGO").classes("c2-graph-example")
        ui.label("A → B means A YIELDS TO B").classes("c2-invariant")
        ui.label("NO NUMERIC PRIORITY SCORE IS USED.").classes("c2-warning-line")
        ui.label("Vehicle IDs are used only for deterministic ordering and serialization—not legal priority.").classes("c2-compact-copy")
    with ui.element("div").classes("c2-two-grid mt-7"):
        _cycle_card("NO CYCLE", ("A → B", "B → C"), "The regulatory graph is executable. A legal/service order can be obtained; MAPPO is not required.", False)
        _cycle_card("CYCLE", ("A → B", "B → C", "C → A"), "Each vehicle depends on another vehicle. There is no simple first vehicle.", True)
    ui.label("Cycle detection technique: Strongly Connected Components (SCC)").classes("c2-note mt-4")
    _close(section, column)


def _mappo_semantics():
    section, column = _section("MAPPO SEMANTICS", "Learned Coordination, Deterministic Control", dark=True)
    ui.label("WHEN IS MAPPO USED?").classes("c2-mini-heading")
    with ui.element("div").classes("c2-three-grid c2-dark-grid"):
        _authorization_card("NO ACTIVE CONFLICT", "NOT REQUIRED", False)
        _authorization_card("REGULATORY ORDER ALREADY RESOLVED", "NOT REQUIRED", False)
        _authorization_card("NEGOTIABLE REGULATORY CYCLE", "MAY BE AUTHORIZED", True,
                            "Required local context must be complete")
    with ui.element("div").classes("c2-two-grid mt-7"):
        _semantic_card("PROPOSER", "KEEP_CLAIM", "RELINQUISH_CLAIM")
        _semantic_card("RESPONDER", "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT")
    with ui.element("div").classes("c2-safety-boundary"):
        ui.label("SAFETY BOUNDARY").classes("c2-card-kicker")
        ui.label("MAPPO negotiates semantic precedence claims. It does not directly output speed, acceleration, braking or steering.").classes("text-lg font-bold")
    _close(section, column)


def _execution_safety():
    section, column = _section("EXECUTION SAFETY", "From Coordination Graph to Physical Permission")
    _mini_flow(("Effective coordination graph + active vehicles + paths + zones + cleared-zone state",
                "ConflictZoneExecutionPlanner", "Per-zone permission",
                "PERMITTED → READY  ·  BLOCKED_BY_PRECEDENCE → BLOCKED",
                "Controller", "SUMO vehicle motion"), wide=True)
    ui.label("MAPPO decides semantic claims; the planner decides permission; the controller applies physical constraints.").classes("c2-invariant mt-6")
    _close(section, column)


def _implementation_map():
    section, column = _section("IMPLEMENTATION", "Trace Every Responsibility to Current Code")
    with ui.expansion("Show Implementation Map", icon="account_tree").classes("c2-implementation-map w-full"):
        with ui.element("div").classes("c2-map-table"):
            with ui.element("div").classes("c2-map-header"):
                ui.label("System responsibility")
                ui.label("Current code location")
            for responsibility, file_name, symbol in IMPLEMENTATION_MAP:
                with ui.element("div").classes("c2-map-row"):
                    ui.label(responsibility).classes("font-bold")
                    with ui.column().classes("gap-0"):
                        ui.label(file_name).classes("c2-code-path")
                        ui.label(symbol).classes("text-sm text-blue-grey-6")
    _close(section, column)


def _research_evidence():
    evidence = load_research_evidence()
    section, column = _section("RESEARCH EVIDENCE", "Research Evaluation Evidence",
                               "Stable validation and deployment artifacts—not the live panel snapshot.")
    with ui.element("div").classes("c2-evidence-layout"):
        with ui.element("article").classes("c2-explain-card"):
            ui.label("CONTROLLED MAPPO VALIDATION").classes("c2-card-kicker")
            ui.label("Mean validation replication-total team travel time · lower is better").classes("c2-compact-copy")
            for candidate, value in evidence["validation"].items():
                with ui.row().classes("c2-evidence-row justify-between w-full"):
                    ui.label(candidate).classes("font-extrabold")
                    ui.label(f"{value:.6f}").classes("font-mono")
            ui.label(f"SELECTED · {evidence['selected']}").classes("c2-selected-evidence")
            ui.label("Best-performing eligible configuration among the predefined tested candidates.").classes("c2-note")
            with ui.row().classes("gap-2 flex-wrap"):
                ui.label("Validation used for selection").classes("c2-status-token")
                ui.label("Held-out not used for selection").classes("c2-status-token")
                ui.label("Not claimed globally optimal").classes("c2-status-token")
        with ui.element("article").classes("c2-explain-card"):
            ui.label("HELD-OUT INTERPRETATION").classes("c2-card-kicker")
            ui.label("The selected E5 configuration remained eligible under the recorded held-out hard safety gates. The deterministic no-learned-negotiation baseline failed one predefined held-out safety-validity gate.").classes("c2-compact-copy")
            ui.label("This does not establish that E5 was globally safer or faster than the baseline.").classes("c2-note")
        with ui.element("article").classes("c2-explain-card"):
            ui.label("INTENTION DEPLOYMENT VERIFICATION").classes("c2-card-kicker")
            for value in (evidence["runtime"]["engine"], evidence["runtime"]["execution_provider"],
                          "TensorFlow not required", "Frozen exported ONNX models",
                          "ONNX verification passed", "No retraining during export"):
                _bullet(value)
            ui.label("No intention-accuracy percentage is shown because this page does not derive one from a dedicated structured deployment-accuracy field.").classes("c2-note")
    _close(section, column)


def _live_results():
    section, column = _section("LIVE PRESENTATION", "Latest Live Results",
                               "A qualitative runtime snapshot, separate from research evaluation evidence.")
    with ui.row().classes("gap-3 mb-6"):
        ui.button("Refresh Latest Results", icon="refresh", on_click=results_panel.refresh).props("outline no-caps")
        ui.button("Open Panel Results Folder", icon="folder_open",
                  on_click=lambda: _open_folder(COMPONENT2_ROOT / "results" / "runtime_simulation")).props("flat no-caps")
        ui.button("Open Technical Project Folder", icon="source",
                  on_click=lambda: _open_folder(COMPONENT2_ROOT)).props("flat no-caps")
    results_panel()
    _close(section, column)


def _mini_flow(items, wide=False):
    with ui.element("div").classes("c2-mini-flow" + (" c2-mini-flow-wide" if wide else "")):
        for index, item in enumerate(items):
            ui.label(item).classes("c2-mini-flow-node")
            if index < len(items) - 1:
                ui.icon("arrow_forward", size="18px").classes("c2-mini-arrow")


def _rule_card(rule_id, title, copy):
    with ui.element("article").classes("c2-explain-card c2-rule-card"):
        ui.label(rule_id).classes("c2-rule-id")
        ui.label(title).classes("font-bold text-lg")
        ui.label(copy).classes("c2-compact-copy")


def _cycle_card(title, edges, copy, cycle):
    with ui.element("article").classes("c2-cycle-card" + (" is-cycle" if cycle else "")):
        ui.label(title).classes("c2-card-kicker")
        ui.label("   ".join(edges)).classes("c2-cycle-edges")
        ui.label(copy).classes("c2-compact-copy")


def _authorization_card(title, outcome, active, note=None):
    with ui.element("article").classes("c2-authorization-card" + (" is-active" if active else "")):
        ui.label(title).classes("font-bold")
        ui.icon("arrow_downward", size="18px")
        ui.label(outcome).classes("c2-auth-outcome")
        if note:
            ui.label(note).classes("text-xs text-blue-grey-3")


def _semantic_card(role, first, second):
    with ui.element("article").classes("c2-semantic-card"):
        ui.label(role).classes("c2-card-kicker")
        ui.label(first).classes("c2-action-token")
        ui.label(second).classes("c2-action-token")


def _open_folder(path):
    try:
        open_predefined_folder(path)
    except OSError as error:
        ui.notify(f"Folder could not be opened: {error}", type="negative")
