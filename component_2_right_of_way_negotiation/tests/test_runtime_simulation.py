"""Scientific and lifecycle boundaries for the qualitative panel runner."""

# Import inspect for use in this module.
import inspect
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace

# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import write_panel_outputs from runtime_simulation.reporting for the operations below.
from runtime_simulation.reporting import write_panel_outputs
# Import _dynamic_status, _presentation_timeline, _reconsider_authority_if_safe, run_runtime_simulation,
# POLICY_PATH, NEGOTIABLE from runtime_simulation.runner for the operations below.
from runtime_simulation.runner import (_dynamic_status,
                               _presentation_timeline,
                               _reconsider_authority_if_safe,
                               run_runtime_simulation, POLICY_PATH, NEGOTIABLE)
# Import APPROACH_PATHS, build_default_schedule, validate_presentation_schedule, validate_schedule from
# runtime_simulation.schedule for the operations below.
from runtime_simulation.schedule import (APPROACH_PATHS, build_default_schedule,
                                 validate_presentation_schedule,
                                 validate_schedule)
# Import PanelDemoVisualizer from runtime_simulation.visualization for the operations below.
from runtime_simulation.visualization import PanelDemoVisualizer
# Import PanelDeterministicInferenceProvider, PRESENTATION_SELECTION_RULE from runtime_simulation.inference for
# the operations below.
from runtime_simulation.inference import (PanelDeterministicInferenceProvider,
                                  PRESENTATION_SELECTION_RULE)
# Import BrowserStatePublisher from runtime_simulation.browser_state for the operations below.
from runtime_simulation.browser_state import BrowserStatePublisher
# Import SCENARIOS, get_scenario from runtime_simulation.scenarios for the operations below.
from runtime_simulation.scenarios import SCENARIOS, get_scenario
# Import PhysicalBranchReplayRunner from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import PhysicalBranchReplayRunner
# Import CoupledNegotiationTrainingEnvironment from negotiation_training.environment for the operations below.
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
# Import FinalSelectionInferenceProvider, _load_bundle from negotiation_training.final_selection for the
# operations below.
from negotiation_training.final_selection import (
    FinalSelectionInferenceProvider, _load_bundle)


# Check selected e5 checkpoint loads and runtime critic is disabled using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_selected_e5_checkpoint_loads_and_runtime_critic_is_disabled():
    # Set (payload, bundle) to the result of _load_bundle(POLICY_PATH).
    payload, bundle = _load_bundle(POLICY_PATH)
    # Set provider to the result of FinalSelectionInferenceProvider(bundle).
    provider = FinalSelectionInferenceProvider(bundle, sampling_seed=0)
    # Require payload at 'candidate_id' equals the text 'E5'; otherwise raise AssertionError.
    assert payload["candidate_id"] == "E5"
    # Require provider.runtime_critic_enabled is the same object as False; otherwise raise AssertionError.
    assert provider.runtime_critic_enabled is False
    # Require provider.bundle.centralized_critic is the same object as None; otherwise raise AssertionError.
    assert provider.bundle.centralized_critic is None


# Check default panel duration covers the four legitimate phases using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_default_panel_duration_covers_the_four_legitimate_phases():
    # Require inspect.signature(run_runtime_simulation).parameters['duration_seconds'].default equals 220.0;
    # otherwise raise AssertionError.
    assert inspect.signature(run_runtime_simulation).parameters[
        # Supply 220.0 to the enclosing expression.
        "duration_seconds"].default == 220.0
    # Set cli to the text read from Path('run_runtime_simulation.py').
    cli = Path("run_runtime_simulation.py").read_text(encoding="utf-8")
    # Require get_scenario('default_panel').recommended_duration_seconds equals 220.0; otherwise raise
    # AssertionError.
    assert get_scenario("default_panel").recommended_duration_seconds == 220.0
    # Require the text 'scenario.recommended_duration_seconds' belongs to cli; otherwise raise AssertionError.
    assert "scenario.recommended_duration_seconds" in cli


# Check presentation scenario catalog is unique qualitative and schedule only using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_presentation_scenario_catalog_is_unique_qualitative_and_schedule_only():
    # Require the number of entries in a set of item.scenario_id for item in SCENARIOS equals the number of
    # entries in SCENARIOS; otherwise raise AssertionError.
    assert len({item.scenario_id for item in SCENARIOS}) == len(SCENARIOS)
    # Require whether every item is true in a lazy sequence of item.evidence_classification equals the text
    # 'QUALITATIVE_PRESENTATION_ONLY' for item in SCENARIOS; otherwise raise AssertionError.
    assert all(item.evidence_classification ==
               # Evaluate SCENARIOS as part of the enclosing expression.
               "QUALITATIVE_PRESENTATION_ONLY" for item in SCENARIOS)
    # Require whether every item is true in a lazy sequence of 'HELD_OUT' does not belong to item.source_type and
    # 'VALIDATION' does not belong to item.source_type for item in SCENARIOS; otherwise raise AssertionError.
    assert all("HELD_OUT" not in item.source_type and
               # Evaluate the text 'VALIDATION' does not belong to item.source_type as part of the enclosing
               # expression.
               "VALIDATION" not in item.source_type for item in SCENARIOS)
    # Set forbidden to a tuple containing the text 'action', the text 'ready', the text 'blocked', the text
    # 'winner', the text 'edge'.
    forbidden = ("action", "ready", "blocked", "winner", "edge")
    # Set fields to a set built from SCENARIOS[0].__dataclass_fields__.
    fields = set(SCENARIOS[0].__dataclass_fields__)
    # Require the negation of the result of fields.intersection(forbidden); otherwise raise AssertionError.
    assert not fields.intersection(forbidden)


# Check scenario selection changes only legal schedule and admission waves using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_scenario_selection_changes_only_legal_schedule_and_admission_waves():
    # Set scenario to the result of get_scenario(the text 'regulatory_cycle').
    scenario = get_scenario("regulatory_cycle")
    # Set schedule to the result of scenario.schedule().
    schedule = scenario.schedule()
    # Require scenario.vehicle_count equals 4; otherwise raise AssertionError.
    assert scenario.vehicle_count == 4
    # Require scenario.admission_waves equals a tuple containing a tuple containing the text 'N', the text 'E',
    # the text 'S', the text 'W'; otherwise raise AssertionError.
    assert scenario.admission_waves == (("N", "E", "S", "W"),)
    # Require a set of item.movement_path_id for rows in values from schedule equals a set containing the text
    # 'N_IN_0_STRAIGHT', the text 'E_IN_0_STRAIGHT', the text 'S_IN_0_RIGHT', the text 'W_IN_0_LEFT'; otherwise
    # raise AssertionError.
    assert {item.movement_path_id for rows in schedule.values()
            # Evaluate a set containing the text 'N_IN_0_STRAIGHT', the text 'E_IN_0_STRAIGHT', the text
            # 'S_IN_0_RIGHT', the text 'W_IN_0_LEFT' as part of the enclosing expression.
            for item in rows} == {
        "N_IN_0_STRAIGHT", "E_IN_0_STRAIGHT",
        "S_IN_0_RIGHT", "W_IN_0_LEFT"}
    # Require the text '--scenario' belongs to the text read from Path('run_runtime_simulation.py'); otherwise
    # raise AssertionError.
    assert "--scenario" in Path("run_runtime_simulation.py").read_text(
        # Supply encoding as the text 'utf-8'.
        encoding="utf-8")


# Check main demo reuses rule then verified negotiation route waves using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_main_demo_reuses_rule_then_verified_negotiation_route_waves():
    # Set scenario to the result of get_scenario(the text 'yield_negotiation_demo').
    scenario = get_scenario("yield_negotiation_demo")
    # Require scenario.evidence_classification equals the text 'QUALITATIVE_PRESENTATION_ONLY'; otherwise raise
    # AssertionError.
    assert scenario.evidence_classification == "QUALITATIVE_PRESENTATION_ONLY"
    # Require scenario.movement_waves equals a tuple containing a tuple containing the text 'N_IN_0_LEFT', the
    # text 'E_IN_0_LEFT', a tuple containing the text...; otherwise raise AssertionError.
    assert scenario.movement_waves == (
        # Include a tuple containing the text 'N_IN_0_LEFT', the text 'E_IN_0_LEFT' in this tuple.
        ("N_IN_0_LEFT", "E_IN_0_LEFT"),
        # Include a tuple containing the text 'N_IN_0_STRAIGHT', the text 'E_IN_0_STRAIGHT', the text
        # 'S_IN_0_RIGHT', the text 'W_IN_0_LEFT' in this tuple.
        ("N_IN_0_STRAIGHT", "E_IN_0_STRAIGHT",
         "S_IN_0_RIGHT", "W_IN_0_LEFT"))
    # Require scenario.admission_waves equals a tuple containing a tuple containing the text 'N', the text 'E', a
    # tuple containing the text 'N', the text 'E', the text...; otherwise raise AssertionError.
    assert scenario.admission_waves == (("N", "E"), ("N", "E", "S", "W"))
    # Set schedule to the result of validate_presentation_schedule(the result of scenario.schedule()).
    schedule = validate_presentation_schedule(scenario.schedule())
    # Require the sum of the result of map(len, values from schedule) equals 6; otherwise raise AssertionError.
    assert sum(map(len, schedule.values())) == 6
    # Set raw to the result of
    # Path('runtime_simulation/scenario_catalog.json').read_text(encoding='utf-8').lower().
    raw = Path("runtime_simulation/scenario_catalog.json").read_text(encoding="utf-8").lower()
    # Iterate over a tuple containing the text 'mappo_action', the text 'winner', the text 'ready_vehicle_ids',
    # the text 'blocked_vehicle_ids',..., binding each item to forbidden.
    for forbidden in ("mappo_action", "winner", "ready_vehicle_ids",
                      "blocked_vehicle_ids", "effective_graph"):
        # Require forbidden does not belong to raw; otherwise raise AssertionError.
        assert forbidden not in raw


# Check panel argmax selects highest probability feasible semantic action using the setup, calls, and assertions
# below.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_panel_argmax_selects_highest_probability_feasible_semantic_action(
        # Declare monkeypatch as input parameter.
        monkeypatch):
    # Define Distribution to group the state and operations declared below.
    # Instances expose the attributes and methods implemented in this class.
    class Distribution:
        # Set probabilities to a tensor built from a list containing 0.1, 0.9.
        probabilities = torch.tensor([0.1, 0.9])

        # Apply staticmethod as a decorator to configure the following definition.
        @staticmethod
        # Evaluate action index using the inputs and processing steps below.
        # Input index: the supplied index.
        # Output: a tensor built from the negative of 0.1053605.
        def evaluate_action_index(index):
            # Require index equals 1; otherwise raise AssertionError.
            assert index == 1
            # Return a tensor built from the negative of 0.1053605 to the caller.
            return torch.tensor(-0.1053605)

    # Set policy to the result of SimpleNamespace().
    policy = SimpleNamespace(distribution_for=lambda context: (None,
                                                                # Include the result of Distribution() in this tuple.
                                                                Distribution()))
    # Set provider to the result of object.__new__(PanelDeterministicInferenceProvider).
    provider = object.__new__(PanelDeterministicInferenceProvider)
    # Set provider.bundle to the result of SimpleNamespace().
    provider.bundle = SimpleNamespace(policy=policy)
    # Set provider.policy_parameter_identity to a tuple containing the text 'FROZEN_E5'.
    provider.policy_parameter_identity = ("FROZEN_E5",)
    # Set context to the result of SimpleNamespace().
    context = SimpleNamespace(
        # Supply decision_role as the result of SimpleNamespace().
        # Supply ego_id as the text 'N02'.
        # Supply value as the text 'PROPOSER'.
        decision_role=SimpleNamespace(value="PROPOSER"), ego_id="N02",
        # Supply claim_identity as a tuple containing the text 'S01', the text 'N02'.
        # Supply proposal_id as None.
        claim_identity=("S01", "N02"), proposal_id=None,
        # Supply action_names as a tuple containing the text 'KEEP_CLAIM', the text 'RELINQUISH_CLAIM'.
        action_names=("KEEP_CLAIM", "RELINQUISH_CLAIM"),
        # Supply action_feasibility_mask as a tensor built from a list containing True, True.
        action_feasibility_mask=torch.tensor([True, True]))
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr("runtime_simulation.inference.tensor_snapshot",
                        # Declare value as input parameter.
                        lambda value: ("DISPLAY_ONLY_SNAPSHOT",))
    # Set sample to the result of provider._sample(context, a tuple containing the text 'B', a tuple containing
    # the text 'E', a tuple containing...).
    sample = provider._sample(context, ("B",), ("E",), ("S",), None)
    # Require sample.selected_semantic_action equals the text 'RELINQUISH_CLAIM'; otherwise raise AssertionError.
    assert sample.selected_semantic_action == "RELINQUISH_CLAIM"
    # Require sample.behavior_probability_vector equals the result of pytest.approx(a tuple containing 0.1, 0.9);
    # otherwise raise AssertionError.
    assert sample.behavior_probability_vector == pytest.approx((0.1, 0.9))
    # Require sample.provenance at 'argmax_used' is the same object as True; otherwise raise AssertionError.
    assert sample.provenance["argmax_used"] is True
    # Require sample.provenance at 'selection_rule' equals PRESENTATION_SELECTION_RULE; otherwise raise
    # AssertionError.
    assert sample.provenance["selection_rule"] == PRESENTATION_SELECTION_RULE


# Check browser state publisher is atomic display only and returns nothing using the setup, calls, and assertions
# below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_browser_state_publisher_is_atomic_display_only_and_returns_nothing(
        # Declare tmp_path as input parameter.
        tmp_path):
    # Set vehicle to the result of SimpleNamespace().
    vehicle = SimpleNamespace(
        # Declare _ as input parameter.
        getIDList=lambda: ("DYNAMIC_AV",), getPosition=lambda _: (4.0, 5.0),
        # Declare _, _ as input parameters.
        getAngle=lambda _: 90.0, getSpeed=lambda _: 2.5,
        # Declare _, _ as input parameters.
        getLength=lambda _: 4.8, getWidth=lambda _: 1.8)
    # Set target to tmp_path joined with the path segment 'runtime' joined with the path segment 'live_state.json'.
    target = tmp_path / "runtime" / "live_state.json"
    # Set publisher to the result of BrowserStatePublisher(target, the result of SimpleNamespace()).
    publisher = BrowserStatePublisher(
        # Supply frequency_hz as 10.
        # Supply vehicle as vehicle.
        target, SimpleNamespace(vehicle=vehicle), frequency_hz=10)
    # Set result to the result of publisher.publish().
    result = publisher.publish(
        # Supply simulation_time as 1.0.
        simulation_time=1.0,
        # Store a dictionary containing min_x, max_x, min_y, max_y under 'bounds'.
        # Store 0 under 'min_x'.
        # Store 10 under 'max_x'.
        map_state={"bounds": {"min_x": 0, "max_x": 10,
                              # Store 0 under 'min_y'.
                              # Store 10 under 'max_y'.
                              "min_y": 0, "max_y": 10}},
        # Supply running as True.
        # Supply status as the text 'NEGOTIATING'.
        # Supply participants as a tuple containing the text 'DYNAMIC_AV'.
        running=True, status="NEGOTIATING", participants=("DYNAMIC_AV",),
        # Supply ready as an empty tuple.
        # Supply blocked as an empty tuple.
        # Supply force as True.
        ready=(), blocked=(), force=True)
    # Set payload to the decoded data produced by json.loads from the text read from target.
    payload = json.loads(target.read_text(encoding="utf-8"))
    # Require result is the same object as None and payload at 'display_only' is the same object as True;
    # otherwise raise AssertionError.
    assert result is None and payload["display_only"] is True
    # Require payload['vehicles'][0] at 'display_state' equals the text 'NEGOTIATING'; otherwise raise
    # AssertionError.
    assert payload["vehicles"][0]["display_state"] == "NEGOTIATING"
    # Require payload['vehicles'][0] at 'front_bumper_x' equals 4.0; otherwise raise AssertionError.
    assert payload["vehicles"][0]["front_bumper_x"] == 4.0
    # Require payload['vehicles'][0] at 'length_m' equals 4.8; otherwise raise AssertionError.
    assert payload["vehicles"][0]["length_m"] == 4.8
    # Require payload['vehicles'][0] at 'width_m' equals 1.8; otherwise raise AssertionError.
    assert payload["vehicles"][0]["width_m"] == 1.8
    # Require the text 'paths' does not belong to payload; otherwise raise AssertionError.
    assert "paths" not in payload
    # Require the negation of whether target.with_suffix('.json.tmp') exists; otherwise raise AssertionError.
    assert not target.with_suffix(".json.tmp").exists()


# Apply 'ready,blocked,expected' as a decorator to configure the following definition.
@pytest.mark.parametrize("ready,blocked,expected", (
    # Include a tuple containing a tuple containing the text 'DYNAMIC_AV', an empty tuple, the text 'READY' in
    # this tuple.
    (("DYNAMIC_AV",), (), "READY"),
    # Include a tuple containing an empty tuple, a tuple containing the text 'DYNAMIC_AV', the text 'BLOCKED' in
    # this tuple.
    ((), ("DYNAMIC_AV",), "BLOCKED")))
# Check planner permission color precedes mappo participation using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Input ready: the supplied ready.
# Input blocked: the supplied blocked.
# Input expected: the supplied expected.
# Output: no explicit value; normal completion returns None.
def test_planner_permission_color_precedes_mappo_participation(
        # Declare tmp_path, ready, blocked, expected as input parameters.
        tmp_path, ready, blocked, expected):
    # Set vehicle to the result of SimpleNamespace().
    vehicle = SimpleNamespace(
        # Declare _ as input parameter.
        getIDList=lambda: ("DYNAMIC_AV",), getPosition=lambda _: (4.0, 5.0),
        # Declare _, _ as input parameters.
        getAngle=lambda _: 90.0, getSpeed=lambda _: 2.5,
        # Declare _, _ as input parameters.
        getLength=lambda _: 4.8, getWidth=lambda _: 1.8)
    # Set target to tmp_path joined with the path segment 'live_state.json'.
    target = tmp_path / "live_state.json"
    # Set publisher to the result of BrowserStatePublisher(target, the result of SimpleNamespace()).
    publisher = BrowserStatePublisher(target, SimpleNamespace(vehicle=vehicle))
    # Call publisher.publish with the supplied arguments.
    publisher.publish(
        # Store an empty dictionary under 'bounds'.
        simulation_time=1.0, map_state={"bounds": {}}, running=True,
        # Supply status as the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE'.
        status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
        # Supply participants as a tuple containing the text 'DYNAMIC_AV'.
        # Supply ready as ready.
        # Supply blocked as blocked.
        participants=("DYNAMIC_AV",), ready=ready, blocked=blocked,
        # Supply mappo_invocation as the text 'AUTHORIZED'.
        # Supply force as True.
        mappo_invocation="AUTHORIZED", force=True)
    # Set item to json.loads(target.read_text(encoding='utf-8'))['vehicles'] at 0.
    item = json.loads(target.read_text(encoding="utf-8"))["vehicles"][0]
    # Require item at 'display_state' equals expected; otherwise raise AssertionError.
    assert item["display_state"] == expected
    # Require item at 'execution_state' equals expected; otherwise raise AssertionError.
    assert item["execution_state"] == expected
    # Require item at 'negotiation_involvement' is the same object as True; otherwise raise AssertionError.
    assert item["negotiation_involvement"] is True


# Check latest mappo participation survives later execution frame using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_latest_mappo_participation_survives_later_execution_frame(tmp_path):
    # Set vehicle to the result of SimpleNamespace().
    vehicle = SimpleNamespace(
        # Declare _ as input parameter.
        getIDList=lambda: ("DYNAMIC_AV",), getPosition=lambda _: (4.0, 5.0),
        # Declare _, _ as input parameters.
        getAngle=lambda _: 90.0, getSpeed=lambda _: 2.5,
        # Declare _, _ as input parameters.
        getLength=lambda _: 4.8, getWidth=lambda _: 1.8)
    # Set target to tmp_path joined with the path segment 'live_state.json'.
    target = tmp_path / "live_state.json"
    # Set publisher to the result of BrowserStatePublisher(target, the result of SimpleNamespace()).
    publisher = BrowserStatePublisher(target, SimpleNamespace(vehicle=vehicle))
    # Call publisher.publish with the supplied arguments.
    publisher.publish(
        # Store an empty dictionary under 'bounds'.
        simulation_time=1.0, map_state={"bounds": {}}, running=True,
        # Supply status as the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE'.
        status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
        # Supply participants as a tuple containing the text 'DYNAMIC_AV'.
        # Supply ready as a tuple containing the text 'DYNAMIC_AV'.
        participants=("DYNAMIC_AV",), ready=("DYNAMIC_AV",),
        # Supply mappo_invocation as the text 'AUTHORIZED'.
        # Supply force as True.
        mappo_invocation="AUTHORIZED", force=True)
    # Call publisher.publish with the supplied arguments.
    publisher.publish(
        # Store an empty dictionary under 'bounds'.
        simulation_time=2.0, map_state={"bounds": {}}, running=True,
        # Supply status as the text 'EXECUTING'.
        # Supply participants as an empty tuple.
        # Supply ready as a tuple containing the text 'DYNAMIC_AV'.
        status="EXECUTING", participants=(), ready=("DYNAMIC_AV",),
        # Supply mappo_invocation as the text 'NOT_REQUIRED'.
        # Supply force as True.
        mappo_invocation="NOT_REQUIRED", force=True)
    # Set item to json.loads(target.read_text(encoding='utf-8'))['vehicles'] at 0.
    item = json.loads(target.read_text(encoding="utf-8"))["vehicles"][0]
    # Require item at 'display_state' equals the text 'READY'; otherwise raise AssertionError.
    assert item["display_state"] == "READY"
    # Require item at 'negotiation_involvement' is the same object as True; otherwise raise AssertionError.
    assert item["negotiation_involvement"] is True


# Check vehicle explainability uses real ego local runtime outputs only using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_vehicle_explainability_uses_real_ego_local_runtime_outputs_only():
    # Set prediction to a dictionary containing primary, secondary, fused_label, status.
    prediction = {"primary": {"label": "LEFT", "confidence": 0.91},
                  # Store None under 'secondary'.
                  # Store the text 'LEFT' under 'fused_label'.
                  "secondary": None, "fused_label": "LEFT",
                  "status": "MODEL_EVALUABLE"}
    # Set ldm to the result of SimpleNamespace().
    ldm = SimpleNamespace(
        # Store an empty dictionary under 'E01'.
        # Store a dictionary containing is_observed, position_history, intention_prediction under 'N01'.
        tracks={"E01": {}, "N01": {
            # Store True under 'is_observed'.
            # Store a tuple containing 1, 2, 3 under 'position_history'.
            "is_observed": True, "position_history": (1, 2, 3),
            # Store prediction under 'intention_prediction'.
            "intention_prediction": prediction}},
        # Store a tuple containing a dictionary containing target_track_id under 'edges'.
        # Store the text 'N01' under 'target_track_id'.
        current_conflict_graph={"edges": ({"target_track_id": "N01"},)},
        # Supply current_encoded_graph_observation as the result of SimpleNamespace().
        current_encoded_graph_observation=SimpleNamespace(
            # Store 2 under 'node_count'.
            dashboard_summary=lambda: {"node_count": 2,
                                       # Store 8 under 'node_feature_dimension'.
                                       "node_feature_dimension": 8}))
    # Set observations to the result of SimpleNamespace().
    observations = SimpleNamespace(get_ldm=lambda vehicle_id: ldm)
    # Set plan to the result of SimpleNamespace().
    plan = SimpleNamespace(ready_vehicle_ids=(), blocked_vehicle_ids=("E01",))
    # Set constraint to the result of SimpleNamespace().
    constraint = SimpleNamespace(vehicle_id="E01",
                                 # Supply requested_speed_cap_mps as 2.4.
                                 requested_speed_cap_mps=2.4)
    # Set evidence to the result of BrowserStatePublisher._vehicle_evidence(the text 'E01', a dictionary
    # containing speed, accel, observations, a tuple containing a...).
    evidence = BrowserStatePublisher._vehicle_evidence(
        # Store 3.2 under 'speed'.
        # Store the negative of 1.1 under 'accel'.
        "E01", {"speed": 3.2, "accel": -1.1}, observations,
        # Store the text 'E01' under 'ego_id'.
        # Store a tuple containing a dictionary containing yielding_vehicle_id, priority_vehicle_id under
        # 'joint_precedence_edges'.
        ({"ego_id": "E01", "joint_precedence_edges": (
            # Store the text 'E01' under 'yielding_vehicle_id'.
            {"yielding_vehicle_id": "E01",
             # Store the text 'N01' under 'priority_vehicle_id'.
             "priority_vehicle_id": "N01"},)},), plan, (constraint,),
        # Store the text 'E01' under 'ego_id'.
        # Store the text 'PROPOSER' under 'decision_role'.
        ({"ego_id": "E01", "decision_role": "PROPOSER",
          "selected_action": "RELINQUISH_CLAIM"},))
    # Require evidence at 'speed_mps' equals 3.2; otherwise raise AssertionError.
    assert evidence["speed_mps"] == 3.2
    # Require evidence at 'acceleration_mps2' equals the negative of 1.1; otherwise raise AssertionError.
    assert evidence["acceleration_mps2"] == -1.1
    # Require evidence['local_perception'] at 'observed_vehicle_ids' equals a tuple containing the text 'N01';
    # otherwise raise AssertionError.
    assert evidence["local_perception"]["observed_vehicle_ids"] == ("N01",)
    # Require evidence['local_intention_predictions'][0] at 'label' equals the text 'LEFT'; otherwise raise
    # AssertionError.
    assert evidence["local_intention_predictions"][0]["label"] == "LEFT"
    # Require evidence['planner'] at 'state' equals the text 'BLOCKED'; otherwise raise AssertionError.
    assert evidence["planner"]["state"] == "BLOCKED"
    # Require evidence['control'] at 'speed_cap_mps' equals 2.4; otherwise raise AssertionError.
    assert evidence["control"]["speed_cap_mps"] == 2.4
    # Require the text 'route' does not belong to the result of json.dumps(evidence).lower(); otherwise raise
    # AssertionError.
    assert "route" not in json.dumps(evidence).lower()


# Check finished browser frame preserves last inspectable evidence using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_finished_browser_frame_preserves_last_inspectable_evidence(tmp_path):
    # Set vehicle to the result of SimpleNamespace().
    vehicle = SimpleNamespace(
        # Declare _ as input parameter.
        getIDList=lambda: ("E01",), getPosition=lambda _: (1.0, 2.0),
        # Declare _, _ as input parameters.
        getAngle=lambda _: 90.0, getSpeed=lambda _: 3.0,
        # Declare _, _ as input parameters.
        getLength=lambda _: 4.8, getWidth=lambda _: 1.8)
    # Set target to tmp_path joined with the path segment 'live_state.json'.
    target = tmp_path / "live_state.json"
    # Set publisher to the result of BrowserStatePublisher(target, the result of SimpleNamespace()).
    publisher = BrowserStatePublisher(target, SimpleNamespace(vehicle=vehicle))
    # Set plan to the result of SimpleNamespace().
    plan = SimpleNamespace(ready_vehicle_ids=("E01",), blocked_vehicle_ids=())
    # Call publisher.publish with the supplied arguments.
    publisher.publish(
        # Store an empty dictionary under 'bounds'.
        simulation_time=1.0, map_state={"bounds": {}}, running=True,
        # Store a dictionary containing position, angle_degrees, length, width, speed, accel under 'E01'.
        status="READY", ready=("E01",), scientific_states={"E01": {
            # Store a tuple containing 1.0, 2.0 under 'position'.
            # Store 90.0 under 'angle_degrees'.
            # Store 4.8 under 'length'.
            "position": (1.0, 2.0), "angle_degrees": 90.0, "length": 4.8,
            # Store 1.8 under 'width'.
            # Store 3.0 under 'speed'.
            # Store 0.2 under 'accel'.
            "width": 1.8, "speed": 3.0, "accel": 0.2}}, plan=plan,
        # Store the text 'PLAN_INVALIDATED' under 'event'.
        events=({"event": "PLAN_INVALIDATED"},), force=True)
    # Call publisher.publish with the supplied arguments.
    publisher.publish(
        # Store an empty dictionary under 'bounds'.
        simulation_time=2.0, map_state={"bounds": {}}, running=False,
        # Supply status as the text 'FINISHED'.
        # Supply completed as 1.
        # Supply scheduled as 1.
        # Supply force as True.
        status="FINISHED", completed=1, scheduled=1, force=True)
    # Set payload to the decoded data produced by json.loads from the text read from target.
    payload = json.loads(target.read_text(encoding="utf-8"))
    # Require payload at 'running' is the same object as False and payload at 'status' equals the text 'FINISHED';
    # otherwise raise AssertionError.
    assert payload["running"] is False and payload["status"] == "FINISHED"
    # Require payload at 'vehicles' equals an empty list; otherwise raise AssertionError.
    assert payload["vehicles"] == []
    # Require payload['completed_vehicles'][0] at 'acceleration_mps2' equals 0.2; otherwise raise AssertionError.
    assert payload["completed_vehicles"][0]["acceleration_mps2"] == 0.2
    # Require payload at 'events' equals a list containing a dictionary containing event; otherwise raise
    # AssertionError.
    assert payload["events"] == [{"event": "PLAN_INVALIDATED"}]


# Check publisher retains completed vehicle final snapshot and trace using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_publisher_retains_completed_vehicle_final_snapshot_and_trace(tmp_path):
    # Set vehicle_ids to a list containing the text 'E01'.
    vehicle_ids = ["E01"]
    # Set vehicle to the result of SimpleNamespace().
    vehicle = SimpleNamespace(
        # Declare _ as input parameter.
        getIDList=lambda: tuple(vehicle_ids), getPosition=lambda _: (1.0, 2.0),
        # Declare _, _ as input parameters.
        getAngle=lambda _: 90.0, getSpeed=lambda _: 3.0,
        # Declare _, _ as input parameters.
        getLength=lambda _: 4.8, getWidth=lambda _: 1.8)
    # Set target to tmp_path joined with the path segment 'live.json'.
    target = tmp_path / "live.json"
    # Set publisher to the result of BrowserStatePublisher(target, the result of SimpleNamespace()).
    publisher = BrowserStatePublisher(target, SimpleNamespace(vehicle=vehicle))
    # Set plan to the result of SimpleNamespace().
    plan = SimpleNamespace(ready_vehicle_ids=("E01",), blocked_vehicle_ids=())
    # Set state to a dictionary containing E01.
    state = {"E01": {"position": (1.0, 2.0), "angle_degrees": 90.0,
                     # Store 4.8 under 'length'.
                     # Store 1.8 under 'width'.
                     # Store 3.0 under 'speed'.
                     "length": 4.8, "width": 1.8, "speed": 3.0,
                     # Store the negative of 0.2 under 'accel'.
                     "accel": -0.2}}
    # Call publisher.publish with the supplied arguments.
    publisher.publish(simulation_time=1, map_state={"bounds": {}}, running=True,
                      # Supply status as the text 'READY'.
                      # Supply scientific_states as state.
                      # Supply plan as plan.
                      status="READY", scientific_states=state, plan=plan,
                      # Supply force as True.
                      force=True)
    # Clear the stored entries in vehicle_ids.
    vehicle_ids.clear()
    # Call publisher.publish with the supplied arguments.
    publisher.publish(simulation_time=2, map_state={"bounds": {}}, running=True,
                      # Supply status as the text 'NO_ACTIVE_CONFLICT'.
                      # Supply scientific_states as an empty dictionary.
                      # Supply plan as plan.
                      status="NO_ACTIVE_CONFLICT", scientific_states={}, plan=plan,
                      # Supply force as True.
                      force=True)
    # Set payload to the decoded data produced by json.loads from the text read from target.
    payload = json.loads(target.read_text(encoding="utf-8"))
    # Require payload['completed_vehicles'][0] at 'id' equals the text 'E01'; otherwise raise AssertionError.
    assert payload["completed_vehicles"][0]["id"] == "E01"
    # Require payload['completed_vehicles'][0] at 'display_state' equals the text 'CLEARED'; otherwise raise
    # AssertionError.
    assert payload["completed_vehicles"][0]["display_state"] == "CLEARED"
    # Set history to the result of publisher.presentation_vehicle_history().
    history = publisher.presentation_vehicle_history()
    # Require history['process_traces']['E01'][-1] at 'stage' equals the text 'COMPLETED'; otherwise raise
    # AssertionError.
    assert history["process_traces"]["E01"][-1]["stage"] == "COMPLETED"


# Check presentation summary writer distinguishes stopped from completed using the setup, calls, and assertions
# below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_presentation_summary_writer_distinguishes_stopped_from_completed(tmp_path):
    # Import write_presentation_run_summary from runtime_simulation.reporting for the operations below.
    from runtime_simulation.reporting import write_presentation_run_summary
    # Set base to a dictionary containing presentation_scenario_id, started_at_utc, ended_at_utc,...
    base = {"presentation_scenario_id": "regulatory_cycle",
            "started_at_utc": "start", "ended_at_utc": "end",
            # Store 12.5 under 'actual_simulation_time_seconds'.
            "actual_simulation_time_seconds": 12.5,
            # Store True under 'policy_hash_unchanged'.
            # Store an empty list under 'events'.
            # Store an empty list under 'diagnostics'.
            "policy_hash_unchanged": True, "events": [], "diagnostics": [],
            # Store a dictionary containing final_snapshots, process_traces under 'presentation_vehicle_history'.
            # Store an empty tuple under 'final_snapshots'.
            "presentation_vehicle_history": {"final_snapshots": (),
                                               # Store an empty dictionary under 'process_traces'.
                                               "process_traces": {}},
            # Store a dictionary of key mapped to 0 for key in a tuple containing the text
            # 'presentation_vehicles_scheduled', the text 'presentation_vehicles_completed', the text... under
            # 'metrics'.
            "metrics": {key: 0 for key in (
                "presentation_vehicles_scheduled",
                "presentation_vehicles_completed", "unfinished_vehicles",
                "collisions", "blocked_zone_violations", "negotiation_events",
                "mappo_decision_epochs", "rule_resolved_events",
                "renegotiation_events")}}
    # Set stopped to a dictionary built from base.
    stopped = dict(base, presentation_run_id="stopped",
                   # Supply run_status as the text 'USER_STOPPED'.
                   run_status="USER_STOPPED")
    # Set target to the result of write_presentation_run_summary(stopped, tmp_path).
    target = write_presentation_run_summary(stopped, tmp_path)
    # Set payload to the decoded data produced by json.loads from the text read from target.
    payload = json.loads(target.read_text(encoding="utf-8"))
    # Require payload at 'run_status' equals the text 'USER_STOPPED'; otherwise raise AssertionError.
    assert payload["run_status"] == "USER_STOPPED"
    # Require payload['metrics'] at 'presentation_vehicles_completed' equals 0; otherwise raise AssertionError.
    assert payload["metrics"]["presentation_vehicles_completed"] == 0
    # Require payload at 'evidence_classification' equals the text 'QUALITATIVE_PRESENTATION_ONLY'; otherwise
    # raise AssertionError.
    assert payload["evidence_classification"] == "QUALITATIVE_PRESENTATION_ONLY"
    # Require payload at 'validation_evidence' is the same object as False; otherwise raise AssertionError.
    assert payload["validation_evidence"] is False


# Check live timeline retains real mappo event evidence after later rule event using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_live_timeline_retains_real_mappo_event_evidence_after_later_rule_event():
    # Set authorized to a dictionary containing timestamp, status, mappo_invocation, participants,
    # original_regulatory_graph,...
    authorized = {"timestamp": 10.0, "status": "NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
                  # Store the text 'AUTHORIZED' under 'mappo_invocation'.
                  # Store a tuple containing the text 'E01', the text 'N01' under 'participants'.
                  "mappo_invocation": "AUTHORIZED", "participants": ("E01", "N01"),
                  # Store a tuple containing a tuple containing the text 'E01', the text 'N01' under
                  # 'original_regulatory_graph'.
                  "original_regulatory_graph": (("E01", "N01"),),
                  # Store a tuple containing a tuple containing the text 'edge', the text 'RELINQUISH_CLAIM' under
                  # 'proposer_actions'.
                  "proposer_actions": (("edge", "RELINQUISH_CLAIM"),),
                  # Store a tuple containing a tuple containing the text 'proposal', the text
                  # 'ACCEPT_RELINQUISHMENT' under 'responder_actions'.
                  "responder_actions": (("proposal", "ACCEPT_RELINQUISHMENT"),),
                  # Store an empty tuple under 'effective_coordination_graph'.
                  "effective_coordination_graph": (),
                  # Store a tuple containing the text 'E01' under 'ready_vehicle_ids'.
                  # Store a tuple containing the text 'N01' under 'blocked_vehicle_ids'.
                  "ready_vehicle_ids": ("E01",), "blocked_vehicle_ids": ("N01",),
                  # Store a tuple containing a dictionary containing ego_id under 'policy_factor_diagnostics'.
                  # Store the text 'E01' under 'ego_id'.
                  "policy_factor_diagnostics": ({"ego_id": "E01"},)}
    # Set later_rule to a dictionary built from authorized.
    later_rule = dict(authorized, timestamp=20.0,
                      # Supply status as the text 'REGULATORY_ORDER_RESOLVED'.
                      status="REGULATORY_ORDER_RESOLVED",
                      # Supply mappo_invocation as the text 'NOT_REQUIRED'.
                      mappo_invocation="NOT_REQUIRED",
                      # Supply proposer_actions as an empty tuple.
                      # Supply responder_actions as an empty tuple.
                      proposer_actions=(), responder_actions=())
    # Set timeline to the result of _presentation_timeline(a tuple containing authorized, later_rule, an empty
    # tuple).
    timeline = _presentation_timeline((authorized, later_rule), ())
    # Require timeline[-1] at 'mappo_invocation' equals the text 'NOT_REQUIRED'; otherwise raise AssertionError.
    assert timeline[-1]["mappo_invocation"] == "NOT_REQUIRED"
    # Set saved to timeline at 0.
    saved = timeline[0]
    # Require saved at 'mappo_invocation' equals the text 'AUTHORIZED'; otherwise raise AssertionError.
    assert saved["mappo_invocation"] == "AUTHORIZED"
    # Require saved at 'original_graph' equals a tuple containing a tuple containing the text 'E01', the text
    # 'N01'; otherwise raise AssertionError.
    assert saved["original_graph"] == (("E01", "N01"),)
    # Require saved at 'proposer_actions' and saved at 'responder_actions'; otherwise raise AssertionError.
    assert saved["proposer_actions"] and saved["responder_actions"]
    # Require saved at 'ready' equals a tuple containing the text 'E01' and saved at 'blocked' equals a tuple
    # containing the text 'N01'; otherwise raise AssertionError.
    assert saved["ready"] == ("E01",) and saved["blocked"] == ("N01",)


# Check verified mappo tags are backed by current presentation audit only using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def test_verified_mappo_tags_are_backed_by_current_presentation_audit_only():
    # Set audit_path to the result of Path(the text 'runtime_simulation/scenario_audit_current.json').
    audit_path = Path("runtime_simulation/scenario_audit_current.json")
    # Set audit to the decoded data produced by json.loads from the text read from audit_path.
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    # Require audit at 'validation_or_held_out_consumed' equals 0; otherwise raise AssertionError.
    assert audit["validation_or_held_out_consumed"] == 0
    # Set observed to a dictionary of item at 'scenario_id' mapped to item for item in audit at 'scenarios'.
    observed = {item["scenario_id"]: item for item in audit["scenarios"]}
    # Iterate over SCENARIOS, binding each item to scenario.
    for scenario in SCENARIOS:
        # Run this branch when scenario.verified_tag equals the text 'MAPPO NEGOTIATION'.
        if scenario.verified_tag == "MAPPO NEGOTIATION":
            # Require observed[scenario.scenario_id] at 'mappo_authorized_events' is at least 1; otherwise raise
            # AssertionError.
            assert observed[scenario.scenario_id]["mappo_authorized_events"] >= 1
    # Require observed['rule_resolved_two'] at 'mappo_authorized_events' equals 0; otherwise raise AssertionError.
    assert observed["rule_resolved_two"]["mappo_authorized_events"] == 0


# Check scenario inputs cannot set scientific outcomes using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_scenario_inputs_cannot_set_scientific_outcomes():
    # Set raw to the result of
    # Path('runtime_simulation/scenario_catalog.json').read_text(encoding='utf-8').lower().
    raw = Path("runtime_simulation/scenario_catalog.json").read_text(encoding="utf-8").lower()
    # Iterate over a tuple containing the text 'negotiation_status', the text 'mappo_action', the text
    # 'effective_graph', the text..., binding each item to forbidden.
    for forbidden in ("negotiation_status", "mappo_action", "effective_graph",
                      "ready_vehicle_ids", "blocked_vehicle_ids", "winner"):
        # Require forbidden does not belong to raw; otherwise raise AssertionError.
        assert forbidden not in raw


# Check no training optimizer or backward path exists in panel runner using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_no_training_optimizer_or_backward_path_exists_in_panel_runner():
    # Set source to the result of inspect.getsource(run_runtime_simulation).lower().
    source = inspect.getsource(run_runtime_simulation).lower()
    # Require the text 'optimizer.step' does not belong to source; otherwise raise AssertionError.
    assert "optimizer.step" not in source
    # Require the text 'zero_grad' does not belong to source; otherwise raise AssertionError.
    assert "zero_grad" not in source
    # Require the text '.backward(' does not belong to source; otherwise raise AssertionError.
    assert ".backward(" not in source
    # Require the text 'training_operations' belongs to source and the text 'parameter_updates' belongs to source;
    # otherwise raise AssertionError.
    assert "training_operations" in source and "parameter_updates" in source


# Check policy hash contract is checked before and after using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_policy_hash_contract_is_checked_before_and_after():
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Require the text 'policy_hash_before' belongs to source and the text 'policy_hash_after' belongs to source;
    # otherwise raise AssertionError.
    assert "policy_hash_before" in source and "policy_hash_after" in source
    # Require the text 'SELECTED_POLICY_HASH_CHANGED_DURING_PANEL_DEMO' belongs to source; otherwise raise
    # AssertionError.
    assert "SELECTED_POLICY_HASH_CHANGED_DURING_PANEL_DEMO" in source


# Check exactly one sumo start and close are in runner lifecycle using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_exactly_one_sumo_start_and_close_are_in_runner_lifecycle():
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Require the result of source.count(the text 'environment.start()') equals 1; otherwise raise AssertionError.
    assert source.count("environment.start()") == 1
    # Require the result of source.count(the text 'environment.close()') equals 1; otherwise raise AssertionError.
    assert source.count("environment.close()") == 1
    # Require the text '"sumo_start_count": starts' belongs to source; otherwise raise AssertionError.
    assert '"sumo_start_count": starts' in source
    # Require the text '"sumo_close_count": closes' belongs to source; otherwise raise AssertionError.
    assert '"sumo_close_count": closes' in source


# Check schedule uses all 12 routes with one rolling slot per approach using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_schedule_uses_all_12_routes_with_one_rolling_slot_per_approach():
    # Set schedule to the result of validate_schedule(the result of build_default_schedule()).
    schedule = validate_schedule(build_default_schedule())
    # Require keys from schedule equals keys from APPROACH_PATHS; otherwise raise AssertionError.
    assert schedule.keys() == APPROACH_PATHS.keys()
    # Require the sum of the result of map(len, values from schedule) equals 12; otherwise raise AssertionError.
    assert sum(map(len, schedule.values())) == 12
    # Require whether every item is true in a lazy sequence of the number of entries in rows equals 3 for rows in
    # values from schedule; otherwise raise AssertionError.
    assert all(len(rows) == 3 for rows in schedule.values())
    # Require whether every item is true in a lazy sequence of the number of entries in {item.approach for item in
    # rows} equals 1 for rows in values from schedule; otherwise raise AssertionError.
    assert all(len({item.approach for item in rows}) == 1
               # Evaluate values from schedule as part of the enclosing expression.
               for rows in schedule.values())


# Check negotiation scope is bounded to four and unique approaches using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_negotiation_scope_is_bounded_to_four_and_unique_approaches():
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Require the text 'len(participants) > 4' belongs to source; otherwise raise AssertionError.
    assert "len(participants) > 4" in source
    # Require the text 'PANEL_NEGOTIATION_SCOPE_BOUNDARY_BREACHED' belongs to source; otherwise raise
    # AssertionError.
    assert "PANEL_NEGOTIATION_SCOPE_BOUNDARY_BREACHED" in source
    # Require the text 'slots[approach] is None' belongs to source; otherwise raise AssertionError.
    assert "slots[approach] is None" in source


# Check rule resolved state does not invoke mappo using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_rule_resolved_state_does_not_invoke_mappo():
    # Set snapshots to a tuple containing a dictionary containing negotiation_status.
    snapshots = ({"negotiation_status": "REGULATORY_ORDER_RESOLVED"},)
    # Require the result of _dynamic_status(snapshots, a tuple containing a tuple containing 'A', 'B') equals the
    # text 'REGULATORY_ORDER_RESOLVED'; otherwise raise AssertionError.
    assert _dynamic_status(snapshots, (("A", "B"),)) == (
        "REGULATORY_ORDER_RESOLVED")
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Require the text 'if status in NEGOTIABLE' belongs to source; otherwise raise AssertionError.
    assert "if status in NEGOTIABLE" in source
    # Require the text 'TRAFFIC_RULE_ORDER_ALREADY_RESOLVED' belongs to source; otherwise raise AssertionError.
    assert "TRAFFIC_RULE_ORDER_ALREADY_RESOLVED" in source


# Check negotiable cycle uses actual selected provider actions using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_negotiable_cycle_uses_actual_selected_provider_actions():
    # Require the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE' belongs to NEGOTIABLE; otherwise raise
    # AssertionError.
    assert "NEGOTIATION_REQUIRED_REGULATORY_CYCLE" in NEGOTIABLE
    # Set source to the text read from Path('runtime_simulation/runner.py').
    source = Path("runtime_simulation/runner.py").read_text(encoding="utf-8")
    # Require the text 'provider.select_joint_actions' belongs to source; otherwise raise AssertionError.
    assert "provider.select_joint_actions" in source
    # Require the text 'outcome.proposer_assignment.claim_action_assignments' belongs to source; otherwise raise
    # AssertionError.
    assert "outcome.proposer_assignment.claim_action_assignments" in source
    # Require the text 'outcome.responder_assignment.response_action_assignments' belongs to source; otherwise
    # raise AssertionError.
    assert "outcome.responder_assignment.response_action_assignments" in source


# Check incomplete actor context is diagnosed and retried using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_incomplete_actor_context_is_diagnosed_and_retried():
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Require the text 'RESPONDER_CONTEXT_INCOMPLETE' belongs to source; otherwise raise AssertionError.
    assert "RESPONDER_CONTEXT_INCOMPLETE" in source
    # Require the text 'missing_encoded_egos' belongs to source; otherwise raise AssertionError.
    assert "missing_encoded_egos" in source
    # Require the text 'Do not freeze an incomplete authority' belongs to source; otherwise raise AssertionError.
    assert "Do not freeze an incomplete authority" in source


# Check mappo epoch count requires a non null live outcome using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_mappo_epoch_count_requires_a_non_null_live_outcome():
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Set increment to the text 'metrics["mappo_decision_epochs"] += 1'.
    increment = 'metrics["mappo_decision_epochs"] += 1'
    # Require the result of source.index(the text 'if outcome is not None:') is less than the result of
    # source.index(increment); otherwise raise AssertionError.
    assert source.index("if outcome is not None:") < source.index(increment)


# Check predeclared case is from training manifest not held out using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_predeclared_case_is_from_training_manifest_not_held_out():
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Require the text 'EXISTING_TRAINING_SIDE_ILLUSTRATIVE_CASE' belongs to source; otherwise raise
    # AssertionError.
    assert "EXISTING_TRAINING_SIDE_ILLUSTRATIVE_CASE" in source
    # Set expected to a set containing the text 'E_IN_0_STRAIGHT', the text 'N_IN_0_STRAIGHT', the text
    # 'S_IN_0_RIGHT', the text 'W_IN_0_LEFT'.
    expected = {"E_IN_0_STRAIGHT", "N_IN_0_STRAIGHT",
                "S_IN_0_RIGHT", "W_IN_0_LEFT"}
    # Set schedule to the result of build_default_schedule().
    schedule = build_default_schedule()
    # Set actual to a set of schedule[approach][index].movement_path_id for (approach, index) in a tuple
    # containing a tuple containing the text 'E', 1, a tuple containing the text 'N', 1, a tuple containing the
    # text 'S',...
    actual = {schedule[approach][index].movement_path_id
              # Evaluate a tuple containing a tuple containing the text 'E', 1, a tuple containing the text 'N',
              # 1, a tuple containing the text 'S',... as part of the enclosing expression.
              for approach, index in (("E", 1), ("N", 1),
                                      # Include a tuple containing the text 'S', 0 in this tuple.
                                      ("S", 0), ("W", 0))}
    # Require actual equals expected; otherwise raise AssertionError.
    assert actual == expected


# Check disagreement is conservatively classified and not policy authorized using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_disagreement_is_conservatively_classified_and_not_policy_authorized():
    # Set snapshots to a tuple containing a dictionary containing negotiation_status.
    snapshots = ({"negotiation_status":
                  "COMMUNICATED_PRECEDENCE_DISAGREEMENT"},)
    # Require the result of _dynamic_status(snapshots, a tuple containing a tuple containing 'A', 'B') equals the
    # text 'COMMUNICATED_PRECEDENCE_DISAGREEMENT'; otherwise raise AssertionError.
    assert _dynamic_status(snapshots, (("A", "B"),)) == (
        "COMMUNICATED_PRECEDENCE_DISAGREEMENT")
    # Require the text 'COMMUNICATED_PRECEDENCE_DISAGREEMENT' does not belong to NEGOTIABLE; otherwise raise
    # AssertionError.
    assert "COMMUNICATED_PRECEDENCE_DISAGREEMENT" not in NEGOTIABLE


# Check no hard coded winner or semantic action exists using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_no_hard_coded_winner_or_semantic_action_exists():
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Set forbidden to a tuple containing the text 'smallest', the text 'alphabetical', the text 'timeout winner',
    # the text 'outcome =...
    forbidden = ("smallest", "alphabetical", "timeout winner",
                 'outcome = "RELINQUISH_CLAIM"',
                 'outcome = "ACCEPT_RELINQUISHMENT"')
    # Require the negation of whether any item is true in a lazy sequence of item belongs to source.lower() for
    # item in forbidden sliced by :3; otherwise raise AssertionError.
    assert not any(item in source.lower() for item in forbidden[:3])
    # Require the negation of whether any item is true in a lazy sequence of item belongs to source for item in
    # forbidden sliced by 3:; otherwise raise AssertionError.
    assert not any(item in source for item in forbidden[3:])


# Check mappo never directly issues speed commands using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_mappo_never_directly_issues_speed_commands():
    # Set provider_source to the result of inspect.getsource(FinalSelectionInferenceProvider).lower().
    provider_source = inspect.getsource(
        # Supply FinalSelectionInferenceProvider to inspect.getsource.
        FinalSelectionInferenceProvider).lower()
    # Require the text 'setspeed' does not belong to provider_source; otherwise raise AssertionError.
    assert "setspeed" not in provider_source
    # Set runner_source to the result of inspect.getsource(run_runtime_simulation).
    runner_source = inspect.getsource(run_runtime_simulation)
    # Require the text 'ego_controller.constrain' belongs to runner_source; otherwise raise AssertionError.
    assert "ego_controller.constrain" in runner_source
    # Require the text 'PhysicalBranchReplayRunner._apply_control' does not belong to runner_source; otherwise
    # raise AssertionError.
    assert "PhysicalBranchReplayRunner._apply_control" not in runner_source


# Check ready blocked are audit of ego execution with native speed constraints using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_ready_blocked_are_audit_of_ego_execution_with_native_speed_constraints():
    # Set runner_source to the result of inspect.getsource(run_runtime_simulation).
    runner_source = inspect.getsource(run_runtime_simulation)
    # Set control_source to the result of inspect.getsource(PhysicalBranchReplayRunner._apply_control).
    control_source = inspect.getsource(PhysicalBranchReplayRunner._apply_control)
    # Require the text 'planner.plan' does not belong to runner_source; otherwise raise AssertionError.
    assert "planner.plan" not in runner_source
    # Require the text 'ego_controller.decide(context)' belongs to runner_source; otherwise raise AssertionError.
    assert "ego_controller.decide(context)" in runner_source
    # Require the text 'ready_vehicle_ids' belongs to runner_source; otherwise raise AssertionError.
    assert "ready_vehicle_ids" in runner_source
    # Require the text 'blocked_vehicle_ids' belongs to runner_source; otherwise raise AssertionError.
    assert "blocked_vehicle_ids" in runner_source
    # Require the text 'PRECEDENCE_SPEED_CAP' belongs to control_source; otherwise raise AssertionError.
    assert "PRECEDENCE_SPEED_CAP" in control_source
    # Require the text 'RELEASE_TO_SUMO' belongs to control_source; otherwise raise AssertionError.
    assert "RELEASE_TO_SUMO" in control_source


# Check visualization is failure isolated and has no return to control using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_visualization_is_failure_isolated_and_has_no_return_to_control():
    # Set source to the result of inspect.getsource(PanelDemoVisualizer.update).
    source = inspect.getsource(PanelDemoVisualizer.update)
    # Require the text 'setColor' belongs to source and the text 'except Exception' belongs to source; otherwise
    # raise AssertionError.
    assert "setColor" in source and "except Exception" in source
    # Require the text 'return plan' does not belong to source and the text 'setSpeed' does not belong to source;
    # otherwise raise AssertionError.
    assert "return plan" not in source and "setSpeed" not in source


# Define _FakeGUI to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class _FakeGUI:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input fail_schema: the supplied fail schema.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, fail_schema=False):
        # Set self.calls to an empty list.
        self.calls = []
        # Set self.fail_schema to fail_schema.
        self.fail_schema = fail_schema

    # Get IDList using the inputs and processing steps below.
    # Output: a tuple containing the text 'View #0'.
    def getIDList(self):
        # Append a tuple containing the text 'getIDList' to self.calls.
        self.calls.append(("getIDList",))
        # Return a tuple containing the text 'View #0' to the caller.
        return ("View #0",)

    # Set Boundary using the inputs and processing steps below.
    # Input args: the supplied args.
    # Output: no explicit value; normal completion returns None.
    def setBoundary(self, *args):
        # Append a tuple containing the text 'setBoundary' plus args to self.calls.
        self.calls.append(("setBoundary",) + args)

    # Set Offset using the inputs and processing steps below.
    # Input args: the supplied args.
    # Output: no explicit value; normal completion returns None.
    def setOffset(self, *args):
        # Append a tuple containing the text 'setOffset' plus args to self.calls.
        self.calls.append(("setOffset",) + args)

    # Set Zoom using the inputs and processing steps below.
    # Input args: the supplied args.
    # Output: no explicit value; normal completion returns None.
    def setZoom(self, *args):
        # Append a tuple containing the text 'setZoom' plus args to self.calls.
        self.calls.append(("setZoom",) + args)

    # Set Schema using the inputs and processing steps below.
    # Input args: the supplied args.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def setSchema(self, *args):
        # Append a tuple containing the text 'setSchema' plus args to self.calls.
        self.calls.append(("setSchema",) + args)
        # Run this branch when self.fail_schema.
        if self.fail_schema:
            # Raise RuntimeError with the text 'unsupported scheme' to stop this execution path.
            raise RuntimeError("unsupported scheme")


# Define _FakeVehicle to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class _FakeVehicle:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self.colors to an empty dictionary.
        self.colors = {}

    # Get IDList using the inputs and processing steps below.
    # Output: a tuple built from the text 'ABCD'.
    def getIDList(self):
        # Return a tuple built from the text 'ABCD' to the caller.
        return tuple("ABCD")

    # Set Color using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input color: the supplied color.
    # Output: no explicit value; normal completion returns None.
    def setColor(self, vehicle_id, color):
        # Set self.colors[vehicle_id] to color.
        self.colors[vehicle_id] = color


# Visual path manager using the inputs and processing steps below.
# Output: the result of SimpleNamespace().
def _visual_path_manager():
    # Set paths to a dictionary of name mapped to the result of SimpleNamespace() for (name, geometry) in
    # key/value pairs from {'N': ((300.0, 307.0), (300.0, 293.0)), 'E': ((307.0, 300.0), (293.0, 300.0))}.
    paths = {
        # Supply centerline_geometry as geometry.
        name: SimpleNamespace(centerline_geometry=geometry)
        # Evaluate key/value pairs from {'N': ((300.0, 307.0), (300.0, 293.0)), 'E': ((307.0, 300.0), (293.0,
        # 300.0))} as part of the enclosing expression.
        for name, geometry in {
            # Store a tuple containing a tuple containing 300.0, 307.0, a tuple containing 300.0, 293.0 under 'N'.
            "N": ((300.0, 307.0), (300.0, 293.0)),
            # Store a tuple containing a tuple containing 307.0, 300.0, a tuple containing 293.0, 300.0 under 'E'.
            "E": ((307.0, 300.0), (293.0, 300.0)),
        }.items()}
    # Return the result of SimpleNamespace() to the caller.
    return SimpleNamespace(paths=paths)


# Check camera uses intersection geometry and focused zoom using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_camera_uses_intersection_geometry_and_focused_zoom():
    # Set gui to the result of _FakeGUI().
    gui = _FakeGUI()
    # Set visualizer to the result of PanelDemoVisualizer(the result of SimpleNamespace()).
    visualizer = PanelDemoVisualizer(
        # Supply enabled as True.
        # Supply gui as gui.
        # Supply vehicle as the result of _FakeVehicle().
        SimpleNamespace(gui=gui, vehicle=_FakeVehicle()), enabled=True)
    # Call visualizer.configure_camera with the supplied arguments.
    visualizer.configure_camera(_visual_path_manager())
    # Require a tuple containing the text 'setOffset', the text 'View #0', 300.0, 300.0 belongs to gui.calls;
    # otherwise raise AssertionError.
    assert ("setOffset", "View #0", 300.0, 300.0) in gui.calls
    # Require a tuple containing the text 'setZoom', the text 'View #0', 2000.0 belongs to gui.calls; otherwise
    # raise AssertionError.
    assert ("setZoom", "View #0", 2000.0) in gui.calls
    # Require the negation of whether any item is true in a lazy sequence of call[0] equals 'getBoundary' for call
    # in gui.calls; otherwise raise AssertionError.
    assert not any(call[0] == "getBoundary" for call in gui.calls)


# Check camera is gui only and headless invokes no gui api using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_camera_is_gui_only_and_headless_invokes_no_gui_api():
    # Set gui to the result of _FakeGUI().
    gui = _FakeGUI()
    # Set visualizer to the result of PanelDemoVisualizer(the result of SimpleNamespace()).
    visualizer = PanelDemoVisualizer(
        # Supply enabled as False.
        # Supply gui as gui.
        # Supply vehicle as the result of _FakeVehicle().
        SimpleNamespace(gui=gui, vehicle=_FakeVehicle()), enabled=False)
    # Call visualizer.configure_camera with the supplied arguments.
    visualizer.configure_camera(_visual_path_manager())
    # Update visualizer with the supplied entries.
    visualizer.update(("A",), ("A",), (), ())
    # Require gui.calls equals an empty list; otherwise raise AssertionError.
    assert gui.calls == []


# Check unsafe programmatic schema selection is not used using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_unsafe_programmatic_schema_selection_is_not_used():
    # Set gui to the result of _FakeGUI().
    gui = _FakeGUI(fail_schema=True)
    # Set visualizer to the result of PanelDemoVisualizer(the result of SimpleNamespace()).
    visualizer = PanelDemoVisualizer(
        # Supply enabled as True.
        # Supply gui as gui.
        # Supply vehicle as the result of _FakeVehicle().
        SimpleNamespace(gui=gui, vehicle=_FakeVehicle()), enabled=True)
    # Call visualizer.configure_camera with the supplied arguments.
    visualizer.configure_camera(_visual_path_manager())
    # Require whether any item is true in a lazy sequence of call at 0 equals the text 'setZoom' for call in
    # gui.calls; otherwise raise AssertionError.
    assert any(call[0] == "setZoom" for call in gui.calls)
    # Require the negation of whether any item is true in a lazy sequence of call[0] equals 'setSchema' for call
    # in gui.calls; otherwise raise AssertionError.
    assert not any(call[0] == "setSchema" for call in gui.calls)


# Check vehicle color legend and blocked precedence are preserved using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_vehicle_color_legend_and_blocked_precedence_are_preserved():
    # Set vehicle to the result of _FakeVehicle().
    vehicle = _FakeVehicle()
    # Set visualizer to the result of PanelDemoVisualizer(the result of SimpleNamespace()).
    visualizer = PanelDemoVisualizer(
        # Supply enabled as True.
        # Supply gui as the result of _FakeGUI().
        # Supply vehicle as vehicle.
        SimpleNamespace(gui=_FakeGUI(), vehicle=vehicle), enabled=True)
    # Update visualizer with the supplied entries.
    visualizer.update(tuple("ABCD"), negotiating=("B", "D"),
                      # Supply ready as a tuple containing the text 'C', the text 'D'.
                      # Supply blocked as a tuple containing the text 'D'.
                      ready=("C", "D"), blocked=("D",))
    # Require vehicle.colors equals a dictionary containing A, B, C, D; otherwise raise AssertionError.
    assert vehicle.colors == {
        # Store PanelDemoVisualizer.BLUE under 'A'.
        "A": PanelDemoVisualizer.BLUE,
        # Store PanelDemoVisualizer.YELLOW under 'B'.
        "B": PanelDemoVisualizer.YELLOW,
        # Store PanelDemoVisualizer.GREEN under 'C'.
        "C": PanelDemoVisualizer.GREEN,
        # Store PanelDemoVisualizer.RED under 'D'.
        "D": PanelDemoVisualizer.RED}


# Check visualization contains no vehicle motion or lifecycle calls using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_visualization_contains_no_vehicle_motion_or_lifecycle_calls():
    # Set source to the text read from Path('runtime_simulation/visualization.py').
    source = Path("runtime_simulation/visualization.py").read_text(encoding="utf-8")
    # Set forbidden to a tuple containing the text 'setSpeed', the text 'slowDown', the text 'moveTo', the text
    # 'moveToXY', the text 'teleport', the...
    forbidden = ("setSpeed", "slowDown", "moveTo", "moveToXY",
                 "teleport", "vehicle.remove", "vehicle.add")
    # Require the negation of whether any item is true in a lazy sequence of token belongs to source for token in
    # forbidden; otherwise raise AssertionError.
    assert not any(token in source for token in forbidden)


# Check route truth is used only for spawn and not actor arguments using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_route_truth_is_used_only_for_spawn_and_not_actor_arguments():
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Set call to source sliced by source.index('provider.select_joint_actions'):.
    call = source[source.index("provider.select_joint_actions"):]
    # Set call to call sliced by :call.index('elif status').
    call = call[:call.index("elif status")]
    # Require the text 'route' does not belong to call and the text 'movement' does not belong to call; otherwise
    # raise AssertionError.
    assert "route" not in call and "movement" not in call
    # Require the text '"route_truth_actor_leakage": 0' belongs to source; otherwise raise AssertionError.
    assert '"route_truth_actor_leakage": 0' in source


# Check schedule and output use no held out scenario using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_schedule_and_output_use_no_held_out_scenario():
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Require the text 'ScenarioRole.HELD_OUT' does not belong to source; otherwise raise AssertionError.
    assert "ScenarioRole.HELD_OUT" not in source
    # Require the text '"held_out_scenarios_consumed": 0' belongs to source; otherwise raise AssertionError.
    assert '"held_out_scenarios_consumed": 0' in source
    # Require the text '"validation_or_held_out_search": False' belongs to source; otherwise raise AssertionError.
    assert '"validation_or_held_out_search": False' in source


# Check historical result directory is not an output target using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_historical_result_directory_is_not_an_output_target():
    # Set source to the result of inspect.getsource(write_panel_outputs).
    source = inspect.getsource(write_panel_outputs)
    # Require the text 'results/runtime_simulation' belongs to source; otherwise raise AssertionError.
    assert "results/runtime_simulation" in source
    # Require the text 'final_mappo_selection_v2' does not belong to source; otherwise raise AssertionError.
    assert "final_mappo_selection_v2" not in source
    # Require the text 'liveness_fix_validation' does not belong to source; otherwise raise AssertionError.
    assert "liveness_fix_validation" not in source


# Check s01 clear releases stale authority when physically safe using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_s01_clear_releases_stale_authority_when_physically_safe():
    # Set helper to the result of SimpleNamespace().
    helper = SimpleNamespace(_plan_invalidation_reasons=
        # Evaluate CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons as part of the enclosing
        # expression.
        CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons)
    # Set old_identity to a tuple containing a tuple containing the text 'PANEL_AV_E_02', the text
    # 'PANEL_AV_N_02', the text 'PANEL_AV_S_01', the text...
    old_identity = (
        # Include a tuple containing the text 'PANEL_AV_E_02', the text 'PANEL_AV_N_02', the text 'PANEL_AV_S_01',
        # the text 'PANEL_AV_W_01' in this tuple.
        ("PANEL_AV_E_02", "PANEL_AV_N_02", "PANEL_AV_S_01",
         "PANEL_AV_W_01"),
        # Include a tuple containing a tuple containing the text 'PANEL_AV_N_02', the text 'PANEL_AV_W_01', a
        # tuple containing the text... in this tuple.
        (("PANEL_AV_N_02", "PANEL_AV_W_01"),
         # Include a tuple containing the text 'PANEL_AV_S_01', the text 'PANEL_AV_N_02' in this tuple.
         ("PANEL_AV_S_01", "PANEL_AV_N_02")), ())
    # Set new_identity to a tuple containing a tuple containing the text 'PANEL_AV_E_02', the text
    # 'PANEL_AV_N_02', the text 'PANEL_AV_W_01', a tuple...
    new_identity = (
        # Include a tuple containing the text 'PANEL_AV_E_02', the text 'PANEL_AV_N_02', the text 'PANEL_AV_W_01'
        # in this tuple.
        ("PANEL_AV_E_02", "PANEL_AV_N_02", "PANEL_AV_W_01"),
        # Include a tuple containing a tuple containing the text 'PANEL_AV_N_02', the text 'PANEL_AV_W_01' in this
        # tuple.
        (("PANEL_AV_N_02", "PANEL_AV_W_01"),),
        # Include a tuple containing a tuple containing the text 'PANEL_AV_S_01', the text 'CZ_1' in this tuple.
        (("PANEL_AV_S_01", "CZ_1"),))
    # Set authority to the result of SimpleNamespace().
    authority = SimpleNamespace(
        # Supply state_identity as old_identity.
        state_identity=old_identity,
        # Supply effective_graph as old_identity at 1.
        effective_graph=old_identity[1],
        # Supply initial_plan as the result of SimpleNamespace().
        initial_plan=SimpleNamespace(
            # Supply graph_status as the text 'EXECUTABLE'.
            graph_status="EXECUTABLE",
            # Supply ready_vehicle_ids as a tuple containing the text 'PANEL_AV_E_02', the text 'PANEL_AV_S_01',
            # the text 'PANEL_AV_W_01'.
            ready_vehicle_ids=("PANEL_AV_E_02", "PANEL_AV_S_01",
                               "PANEL_AV_W_01"),
            # Supply blocked_vehicle_ids as a tuple containing the text 'PANEL_AV_N_02'.
            blocked_vehicle_ids=("PANEL_AV_N_02",)))
    # Set safe_zones to a dictionary containing CZ_1.
    safe_zones = {"CZ_1": {"state": "CLEARED"}}

    # Set (reconsidered, reasons) to the result of _reconsider_authority_if_safe(helper, authority, new_identity,
    # safe_zones).
    reconsidered, reasons = _reconsider_authority_if_safe(
        # Supply new_identity to _reconsider_authority_if_safe.
        helper, authority, new_identity, safe_zones)

    # Require reconsidered is the same object as None; otherwise raise AssertionError.
    assert reconsidered is None
    # Require reasons equals a tuple containing the text 'ACTIVE_PARTICIPANT_SET_CHANGED', the text
    # 'RELEVANT_PRECEDENCE_GRAPH_CHANGED', the text...; otherwise raise AssertionError.
    assert reasons == (
        "ACTIVE_PARTICIPANT_SET_CHANGED",
        "RELEVANT_PRECEDENCE_GRAPH_CHANGED",
        "CONFLICT_ZONE_CLEARED")
    # Require reconsidered is the same object as None and new_identity differs from old_identity; otherwise raise
    # AssertionError.
    assert reconsidered is None and new_identity != old_identity


# Check state change defers while occupied then reconsiders when clear using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_state_change_defers_while_occupied_then_reconsiders_when_clear():
    # Set helper to the result of SimpleNamespace().
    helper = SimpleNamespace(_plan_invalidation_reasons=
        # Evaluate CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons as part of the enclosing
        # expression.
        CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons)
    # Set authority to the result of SimpleNamespace().
    authority = SimpleNamespace(
        # Supply state_identity as a tuple containing a tuple containing the text 'OLD', an empty tuple, an empty
        # tuple.
        state_identity=(("OLD",), (), ()),
        # Supply initial_plan as the result of SimpleNamespace().
        initial_plan=SimpleNamespace(
            # Supply graph_status as the text 'EXECUTABLE'.
            # Supply ready_vehicle_ids as a tuple containing the text 'OLD'.
            graph_status="EXECUTABLE", ready_vehicle_ids=("OLD",)))

    # Set (retained, reasons) to the result of _reconsider_authority_if_safe(helper, authority, a tuple containing
    # a tuple containing the text 'NEW', an empty tuple, an...).
    retained, reasons = _reconsider_authority_if_safe(
        # Supply a tuple containing a tuple containing the text 'NEW', an empty tuple, an empty tuple to
        # _reconsider_authority_if_safe.
        helper, authority, (("NEW",), (), ()),
        # Store a dictionary containing state under 'CZ_1'.
        # Store the text 'CURRENTLY_OCCUPYING' under 'state'.
        {"CZ_1": {"state": "CURRENTLY_OCCUPYING"}})
    # Require retained is the same object as authority; otherwise raise AssertionError.
    assert retained is authority
    # Require reasons equals an empty tuple; otherwise raise AssertionError.
    assert reasons == ()

    # Set (reconsidered, reasons) to the result of _reconsider_authority_if_safe(helper, retained, a tuple
    # containing a tuple containing the text 'NEW', an empty tuple, an empty...).
    reconsidered, reasons = _reconsider_authority_if_safe(
        # Supply a tuple containing a tuple containing the text 'NEW', an empty tuple, an empty tuple to
        # _reconsider_authority_if_safe.
        helper, retained, (("NEW",), (), ()),
        # Store a dictionary containing state under 'CZ_1'.
        # Store the text 'CLEARED' under 'state'.
        {"CZ_1": {"state": "CLEARED"}})
    # Require reconsidered is the same object as None; otherwise raise AssertionError.
    assert reconsidered is None
    # Require reasons equals a tuple containing the text 'ACTIVE_PARTICIPANT_SET_CHANGED'; otherwise raise
    # AssertionError.
    assert reasons == ("ACTIVE_PARTICIPANT_SET_CHANGED",)


# Check graph churn alone does not resample executable authority using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_graph_churn_alone_does_not_resample_executable_authority():
    # Set helper to the result of SimpleNamespace().
    helper = SimpleNamespace(_plan_invalidation_reasons=
        # Evaluate CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons as part of the enclosing
        # expression.
        CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons)
    # Set old_identity to a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing a
    # tuple containing the text 'A', the...
    old_identity = (("A", "B"), (("A", "B"),), ())
    # Set new_identity to a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing a
    # tuple containing the text 'B', the...
    new_identity = (("A", "B"), (("B", "A"),), ())
    # Set authority to the result of SimpleNamespace().
    authority = SimpleNamespace(
        # Supply state_identity as old_identity.
        state_identity=old_identity,
        # Supply initial_plan as the result of SimpleNamespace().
        initial_plan=SimpleNamespace(
            # Supply graph_status as the text 'EXECUTABLE'.
            # Supply ready_vehicle_ids as a tuple containing the text 'A'.
            graph_status="EXECUTABLE", ready_vehicle_ids=("A",)))

    # Set (retained, reasons) to the result of _reconsider_authority_if_safe(helper, authority, new_identity, a
    # dictionary containing CZ_1).
    retained, reasons = _reconsider_authority_if_safe(
        # Supply new_identity to _reconsider_authority_if_safe.
        helper, authority, new_identity,
        # Store a dictionary containing state under 'CZ_1'.
        # Store the text 'BEFORE_ZONE' under 'state'.
        {"CZ_1": {"state": "BEFORE_ZONE"}})

    # Require retained is the same object as authority; otherwise raise AssertionError.
    assert retained is authority
    # Require reasons equals an empty tuple; otherwise raise AssertionError.
    assert reasons == ()


# Check panel metadata is explicitly non evidentiary using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_panel_metadata_is_explicitly_non_evidentiary(tmp_path):
    # Set result to a dictionary containing policy_hash_unchanged, metrics.
    result = {"policy_hash_unchanged": True, "metrics": {
        # Evaluate a tuple containing the text 'presentation_vehicles_scheduled', the text
        # 'presentation_vehicles_completed', the text... as part of the enclosing expression.
        key: 0 for key in ("presentation_vehicles_scheduled",
        "presentation_vehicles_completed", "unfinished_vehicles",
        "negotiation_events", "mappo_decision_epochs",
        "rule_resolved_events", "renegotiation_events",
        "safe_hold_activations", "collisions", "blocked_zone_violations",
        "maximum_negotiation_participants")}}
    # Call write_panel_outputs with the supplied arguments.
    write_panel_outputs(result, tmp_path)
    # Set text to the text read from (tmp_path / 'latest_runtime_simulation_summary.md').
    text = (tmp_path / "latest_runtime_simulation_summary.md").read_text()
    # Require the text 'QUALITATIVE_PRESENTATION_ONLY' belongs to text; otherwise raise AssertionError.
    assert "QUALITATIVE_PRESENTATION_ONLY" in text
    # Require the text 'not validation' belongs to text; otherwise raise AssertionError.
    assert "not validation" in text


# Check simulation step and vehicle physics are not panel parameters using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_simulation_step_and_vehicle_physics_are_not_panel_parameters():
    # Set source to the result of inspect.getsource(run_runtime_simulation).
    source = inspect.getsource(run_runtime_simulation)
    # Require the text 'SIM_TIME_STEP' belongs to source; otherwise raise AssertionError.
    assert "SIM_TIME_STEP" in source
    # Require the negation of whether any item is true in a lazy sequence of token belongs to source for token in
    # a tuple containing 'setAccel', 'setDecel', 'setMaxSpeed', 'teleport'; otherwise raise AssertionError.
    assert not any(token in source for token in
                   # Evaluate a tuple containing the text 'setAccel', the text 'setDecel', the text 'setMaxSpeed',
                   # the text 'teleport' as part of the enclosing expression.
                   ("setAccel", "setDecel", "setMaxSpeed", "teleport"))
