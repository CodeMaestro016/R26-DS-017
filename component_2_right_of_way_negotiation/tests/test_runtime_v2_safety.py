"""V2 physical admission regressions using only ego/pair inputs."""
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import pytest for use in this module.
import pytest
# Import DecentralizedEgoExecutionController, EgoExecutionContext, EgoCoordinationCommitment,
# ExecutionStateMessage from negotiation_execution for the operations below.
from negotiation_execution import (DecentralizedEgoExecutionController,
    EgoExecutionContext, EgoCoordinationCommitment, ExecutionStateMessage)
# Import ScientificEvaluationProvider from post_training_evaluation.inference for the operations below.
from post_training_evaluation.inference import ScientificEvaluationProvider
# Import FinalSelectionInferenceProvider from negotiation_training.final_selection for the operations below.
from negotiation_training.final_selection import FinalSelectionInferenceProvider
# Import PanelDeterministicInferenceProvider from runtime_simulation.inference for the operations below.
from runtime_simulation.inference import PanelDeterministicInferenceProvider


# State using the inputs and processing steps below.
# Input progress: the supplied progress.
# Output: a dictionary built from the supplied values.
def state(progress=-20.):
    # Return a dictionary built from the supplied values to the caller.
    return dict(progress=progress, width=1.8, length=5., lane_id="incoming",
        # Supply lane_position as 10.0.
        # Supply speed as 4.0.
        # Supply comfortable_deceleration_mps2 as 4.5.
        lane_position=10., speed=4., comfortable_deceleration_mps2=4.5)


# Controller using the inputs and processing steps below.
# Output: the result of DecentralizedEgoExecutionController(paths, zones).
def controller():
    # Set paths to the result of SimpleNamespace().
    paths = SimpleNamespace(paths={p: SimpleNamespace(incoming_lane_id="incoming",
        # Supply outgoing_lane_id as the text 'outgoing'.
        outgoing_lane_id="outgoing") for p in ("A", "B")},
        # Declare s, p as input parameters.
        resolve_front_bumper_path_progress=lambda s,p: (s["progress"],None,None))
    # Set zones to the result of SimpleNamespace().
    zones = SimpleNamespace(zone_record=lambda *args: dict(zone_id="CZ",
        # Supply first_path_distance_interval as a tuple containing 0.0, 10.0.
        # Supply second_path_distance_interval as a tuple containing 0.0, 10.0.
        first_path_distance_interval=(0.,10.), second_path_distance_interval=(0.,10.)))
    # Return the result of DecentralizedEgoExecutionController(paths, zones) to the caller.
    return DecentralizedEgoExecutionController(paths,zones)


# Context using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Input peer: the supplied peer.
# Input arrival: the supplied arrival.
# Input peer_arrival: the supplied peer arrival.
# Output: the result of EgoExecutionContext(ego, the result of state(), ego, 1.0).
def context(ego="A", peer="B", arrival=0., peer_arrival=0.):
    # Return the result of EgoExecutionContext(ego, the result of state(), ego, 1.0) to the caller.
    return EgoExecutionContext(ego,state(),ego,1.,peer_messages=(
        # Supply coordination_epoch as a tuple containing the text 'epoch'.
        ExecutionStateMessage(peer,peer,state(),1.,peer_arrival,coordination_epoch=("epoch",)),),
        # Supply coordination_complete as True.
        # Supply coordination_timestamp as 1.0.
        # Supply strict_admission as True.
        coordination_complete=True,coordination_timestamp=1.,strict_admission=True,
        # Supply coordination_epoch as a tuple containing the text 'epoch'.
        # Supply queue_arrival_seconds as arrival.
        coordination_epoch=("epoch",),queue_arrival_seconds=arrival)


# Check unordered pair safe holds without mappo receipt using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_unordered_pair_safe_holds_without_mappo_receipt():
    # Set d to the result of controller().decide(the result of context()).
    d=controller().decide(context())
    # Require a tuple containing d.permission, d.reason equals a tuple containing the text 'SAFE_HOLD', the text
    # 'UNORDERED_PHYSICAL_CONFLICT'; otherwise raise AssertionError.
    assert (d.permission,d.reason)==("SAFE_HOLD","UNORDERED_PHYSICAL_CONFLICT")


# Apply pytest.mark.parametrize('a,b', [(0.0, 0.0), (0.2, 0.1), (0.1, 0.2), (0.0, 1e-10)]) as a decorator to
# configure the following definition.
@pytest.mark.parametrize("a,b", [(0.,0.),(.2,.1),(.1,.2),(0.,.0000000001)])
# Check fallback pair is identical at both egos using the setup, calls, and assertions below.
# Input a: the supplied a.
# Input b: the supplied b.
# Output: no explicit value; normal completion returns None.
def test_fallback_pair_is_identical_at_both_egos(a,b):
    # Set ca to the result of replace(the result of context()).
    ca=replace(context(arrival=a,peer_arrival=b),mappo_receipt=True,fallback_peer_ids=("B",))
    # Set cb to the result of replace(the result of context(the text 'B', the text 'A', b, a)).
    cb=replace(context("B","A",b,a),mappo_receipt=True,fallback_peer_ids=("A",))
    # Set (da, db) to a tuple containing the result of controller().decide(ca), the result of
    # controller().decide(cb).
    da,db=controller().decide(ca),controller().decide(cb)
    # Require da.fallback_pairs equals db.fallback_pairs; otherwise raise AssertionError.
    assert da.fallback_pairs==db.fallback_pairs
    # Require a set containing da.permission, db.permission equals a set containing the text 'PERMITTED', the text
    # 'BLOCKED_BY_PRECEDENCE'; otherwise raise AssertionError.
    assert {da.permission,db.permission}=={"PERMITTED","BLOCKED_BY_PRECEDENCE"}
    # Require da.shield_rejection_reason equals db.shield_rejection_reason; equals the text
    # 'UNORDERED_PHYSICAL_CONFLICT'; otherwise raise AssertionError.
    assert da.shield_rejection_reason==db.shield_rejection_reason=="UNORDERED_PHYSICAL_CONFLICT"


# Apply dict(fallback_peer_ids=()) as a decorator to configure the following definition.
@pytest.mark.parametrize("change", [dict(mappo_receipt=False),dict(fallback_peer_ids=()),
    # Supply queue_arrival_seconds as None.
    # Supply queue_arrival_seconds as 2.0.
    dict(queue_arrival_seconds=None),dict(queue_arrival_seconds=2.)])
# Check fallback requires valid local receipt and arrivals using the setup, calls, and assertions below.
# Input change: the supplied change.
# Output: no explicit value; normal completion returns None.
def test_fallback_requires_valid_local_receipt_and_arrivals(change):
    # Set c to the result of replace(the result of context()).
    c=replace(context(),mappo_receipt=True,fallback_peer_ids=("B",))
    # Require controller().decide(replace(c, **change)).permission equals the text 'SAFE_HOLD'; otherwise raise
    # AssertionError.
    assert controller().decide(replace(c,**change)).permission=="SAFE_HOLD"


# Check mandatory edge removal is rejected without fallback using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_mandatory_edge_removal_is_rejected_without_fallback():
    # Set c to the result of replace(the result of context()).
    c=replace(context(),mappo_receipt=True,fallback_peer_ids=("B",),
        # Supply mandatory_commitments as a tuple containing the result of EgoCoordinationCommitment(the text 'A',
        # the text 'B', a tuple containing the text 'epoch').
        mandatory_commitments=(EgoCoordinationCommitment("A","B",("epoch",)),))
    # Set d to the result of controller().decide(c).
    d=controller().decide(c)
    # Require d.shield_rejection_reason equals the text 'MANDATORY_PRECEDENCE_REMOVED' and the negation of
    # d.fallback_pairs; otherwise raise AssertionError.
    assert d.shield_rejection_reason=="MANDATORY_PRECEDENCE_REMOVED" and not d.fallback_pairs
    # Require d.permission equals the text 'BLOCKED_BY_PRECEDENCE'; otherwise raise AssertionError.
    assert d.permission=="BLOCKED_BY_PRECEDENCE"


# Check stale epoch is rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_stale_epoch_is_rejected():
    # Set c to the result of replace(the result of context()).
    c=replace(context(),commitments=(EgoCoordinationCommitment("B","A",("old",)),))
    # Require controller().decide(c).reason equals the text 'COORDINATION_EPOCH_MISMATCH'; otherwise raise
    # AssertionError.
    assert controller().decide(c).reason=="COORDINATION_EPOCH_MISMATCH"


# Check peer epoch is rejected and ulp arrival tie uses id using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_peer_epoch_is_rejected_and_ulp_arrival_tie_uses_id():
    # Set c to the result of replace(the result of context()).
    c=replace(context(),peer_messages=(replace(context().peer_messages[0],coordination_epoch=("old",)),))
    # Require controller().decide(c).reason equals the text 'PEER_COORDINATION_EPOCH_MISMATCH'; otherwise raise
    # AssertionError.
    assert controller().decide(c).reason=="PEER_COORDINATION_EPOCH_MISMATCH"
    # Set c to the result of replace(the result of context()).
    c=replace(context(arrival=1e-15),mappo_receipt=True,fallback_peer_ids=("B",))
    # Require controller().decide(c).fallback_pairs equals a tuple containing a tuple containing the text 'B', the
    # text 'A'; otherwise raise AssertionError.
    assert controller().decide(c).fallback_pairs==(("B","A"),)


# Check v1 write root and implicit v2 freeze are rejected using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_v1_write_root_and_implicit_v2_freeze_are_rejected(tmp_path):
    # Import Path from pathlib for the operations below.
    from pathlib import Path
    # Import protect_v1 from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import protect_v1
    # Import run_suite from post_training_evaluation.runner for the operations below.
    from post_training_evaluation.runner import run_suite
    # Set root to Path(__file__).resolve().parents at 1 joined with the path segment 'results/post_training_evaluation'.
    root=Path(__file__).resolve().parents[1]/"results/post_training_evaluation"
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match="V1_EVIDENCE_IS_READ_ONLY"):
        # Call protect_v1 with the supplied arguments.
        protect_v1(root)
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match="V2_MANIFEST_NOT_FROZEN"):
        # Call run_suite with the supplied arguments.
        run_suite("final",tmp_path)
    # Require the negation of whether (tmp_path / 'manifest.json') exists; otherwise raise AssertionError.
    assert not (tmp_path/"manifest.json").exists()


# Check follower waits before entry without actor context using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_follower_waits_before_entry_without_actor_context():
    # Set c to the result of replace(the result of context()).
    c=replace(context(),negotiation_eligible=False,coordination_complete=False)
    # Set ctl to the result of controller().
    ctl=controller()
    # Require ctl.decide(c).blocked_zones[0] sliced by :2 equals a tuple containing the text 'JUNCTION_ENTRY',
    # 20.0; otherwise raise AssertionError.
    assert ctl.decide(c).blocked_zones[0][:2]==("JUNCTION_ENTRY",20.)
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match="BLOCKED_VEHICLE_ENTERED"):
        # Call ctl.decide with the supplied arguments.
        ctl.decide(replace(c,ego_state=state(.1)))


# Check valid admission locks at native braking boundary using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_valid_admission_locks_at_native_braking_boundary():
    # Set ctl to the result of controller().
    ctl=controller()
    # Set c to the result of replace(the result of context()).
    c=replace(context(),ego_state=state(-1.),commitments=(
        # Include the result of EgoCoordinationCommitment(the text 'B', the text 'A', a tuple containing the text
        # 'epoch') in this tuple.
        EgoCoordinationCommitment("B","A",("epoch",)),))
    # Set api to the result of SimpleNamespace().
    api=SimpleNamespace(getSpeedMode=lambda _:31,getActionStepLength=lambda _:.04,getSpeedWithoutTraCI=lambda _:4.)
    # Call ctl.constrain with the supplied arguments.
    ctl.constrain(c,ctl.decide(c),api,.04)
    # Require ctl.admission_state equals the text 'COMMITTED_TO_ENTER'; otherwise raise AssertionError.
    assert ctl.admission_state=="COMMITTED_TO_ENTER"
    # Set d to the result of ctl.decide(the result of replace(c)).
    d=ctl.decide(replace(c,ego_state=state(.1),coordination_complete=False,peer_messages=()))
    # Require d.permission equals the text 'PERMITTED' and ctl.admission_state equals the text 'IN_CONFLICT_ZONE';
    # otherwise raise AssertionError.
    assert d.permission=="PERMITTED" and ctl.admission_state=="IN_CONFLICT_ZONE"


# Check valid stopped release locks before native step crosses entry using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_valid_stopped_release_locks_before_native_step_crosses_entry():
    # Set ctl to the result of controller().
    ctl=controller()
    # Set c to the result of replace(the result of context()).
    c=replace(context(),ego_state=dict(state(-.001),speed=0.),commitments=(
        # Include the result of EgoCoordinationCommitment(the text 'B', the text 'A', a tuple containing the text
        # 'epoch') in this tuple.
        EgoCoordinationCommitment("B","A",("epoch",)),))
    # Set api to the result of SimpleNamespace().
    api=SimpleNamespace(getSpeedMode=lambda _:31,getActionStepLength=lambda _:.04,
        # Declare _ as input parameter.
        getSpeedWithoutTraCI=lambda _:.104)
    # Call ctl.constrain with the supplied arguments.
    ctl.constrain(c,ctl.decide(c),api,.04)
    # Require ctl.admission_state equals the text 'COMMITTED_TO_ENTER'; otherwise raise AssertionError.
    assert ctl.admission_state=="COMMITTED_TO_ENTER"


# Check explicit unresolved pair is eligible but missing or mandatory evidence is not using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_explicit_unresolved_pair_is_eligible_but_missing_or_mandatory_evidence_is_not():
    # Import _eligible_fallback_pairs from runtime_simulation.runner for the operations below.
    from runtime_simulation.runner import _eligible_fallback_pairs
    # Set relation to a dictionary built from the supplied values.
    relation=dict(ego_id="A",target_id="B",regulatory_status="UNRESOLVED_DUE_TO_TARGET_MANOEUVRE",
        # Store the text 'NO_PAIRWISE_PRECEDENCE_RULE' under 'regulatory_status'.
        shared_conflict_zone_ids=("CZ",),regulatory_evidence=dict(candidate_assessments=({"regulatory_status":"NO_PAIRWISE_PRECEDENCE_RULE"},)))
    # Set snapshots to a tuple containing a dictionary containing unresolved_relations.
    snapshots=({"unresolved_relations":(relation,)},)
    # Require the result of _eligible_fallback_pairs(a tuple containing the text 'A', the text 'B', an empty
    # tuple, snapshots, an empty tuple) equals a tuple containing a tuple containing the text 'A', the text 'B';
    # otherwise raise AssertionError.
    assert _eligible_fallback_pairs(("A","B"),(),snapshots,())==(("A","B"),)
    # Require the negation of the result of _eligible_fallback_pairs(a tuple containing the text 'A', the text
    # 'B', an empty tuple, snapshots, a tuple containing a...); otherwise raise AssertionError.
    assert not _eligible_fallback_pairs(("A","B"),(),snapshots,(("A","B"),))
    # Require the negation of the result of _eligible_fallback_pairs(a tuple containing the text 'A', the text
    # 'B', an empty tuple, a tuple containing a dictionary...); otherwise raise AssertionError.
    assert not _eligible_fallback_pairs(("A","B"),(),({"unresolved_relations":(dict(relation,regulatory_status="REGULATORY_INPUT_UNRESOLVED"),)},),())


# Check invalid coordination never activates fallback even with pair certificate using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_invalid_coordination_never_activates_fallback_even_with_pair_certificate():
    # Set c to the result of replace(the result of context()).
    c=replace(context(),coordination_complete=False,mappo_receipt=True,fallback_peer_ids=("B",))
    # Set d to the result of controller().decide(c).
    d=controller().decide(c)
    # Require d.permission equals the text 'SAFE_HOLD' and the negation of d.fallback_pairs; otherwise raise
    # AssertionError.
    assert d.permission=="SAFE_HOLD" and not d.fallback_pairs


# Check scientific sampling is original method and panel is separate using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_scientific_sampling_is_original_method_and_panel_is_separate():
    # Require ScientificEvaluationProvider._sample is the same object as FinalSelectionInferenceProvider._sample;
    # otherwise raise AssertionError.
    assert ScientificEvaluationProvider._sample is FinalSelectionInferenceProvider._sample
    # Require PanelDeterministicInferenceProvider._sample is a different object from
    # ScientificEvaluationProvider._sample; otherwise raise AssertionError.
    assert PanelDeterministicInferenceProvider._sample is not ScientificEvaluationProvider._sample


# Check event logger reports actual inference mode using the setup, calls, and assertions below.
# Input capsys: the supplied capsys.
# Output: no explicit value; normal completion returns None.
def test_event_logger_reports_actual_inference_mode(capsys):
    # Import _print_event from runtime_simulation.runner for the operations below.
    from runtime_simulation.runner import _print_event
    # Import SCIENTIFIC_SELECTION_RULE from post_training_evaluation.inference for the operations below.
    from post_training_evaluation.inference import SCIENTIFIC_SELECTION_RULE
    # Set outcome to the result of SimpleNamespace().
    outcome=SimpleNamespace(proposer_assignment=SimpleNamespace(claim_action_assignments=()),
        # Supply responder_assignment as the result of SimpleNamespace().
        # Supply effective_precedence_graph as an empty tuple.
        # Supply response_action_assignments as an empty tuple.
        responder_assignment=SimpleNamespace(response_action_assignments=()),effective_precedence_graph=())
    # Set plan to the result of SimpleNamespace().
    plan=SimpleNamespace(ready_vehicle_ids=(),blocked_vehicle_ids=())
    # Call _print_event with the supplied arguments.
    _print_event(1,1.,(),"NEGOTIATION_REQUIRED_REGULATORY_CYCLE",(),outcome,plan,0,0,
        # Supply selection_rule as SCIENTIFIC_SELECTION_RULE.
        selection_rule=SCIENTIFIC_SELECTION_RULE)
    # Set output to capsys.readouterr().out.
    output=capsys.readouterr().out
    # Require the text 'SEMANTIC_SELECTION_RULE = SEEDED_STOCHASTIC_MASKED_SAMPLE' belongs to output; otherwise
    # raise AssertionError.
    assert "SEMANTIC_SELECTION_RULE = SEEDED_STOCHASTIC_MASKED_SAMPLE" in output
    # Require the text 'ARGMAX' does not belong to output; otherwise raise AssertionError.
    assert "ARGMAX" not in output


# Check archived replay verifies code before launching using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_archived_replay_verifies_code_before_launching(monkeypatch,tmp_path):
    # Import importlib, json for use in this module.
    import importlib,json
    # Import file_hash from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import file_hash
    # Set replay to the result of importlib.import_module(the text 'post_training_evaluation.replay').
    replay=importlib.import_module("post_training_evaluation.replay")
    # Set snapshot to tmp_path joined with the path segment 'snapshot'.
    snapshot=tmp_path/"snapshot"
    # Create the directory requested by snapshot.
    snapshot.mkdir()
    # Set script to snapshot joined with the path segment 'run_final_evaluation.py'.
    script=snapshot/"run_final_evaluation.py"  # Original archived entry point.
    # Write the supplied text to script.
    script.write_text("# measured diagnostic code\n")
    # Set original to the result of file_hash(script).
    original=file_hash(script)
    # Write the supplied text to (snapshot / 'snapshot_inventory.json').
    (snapshot/"snapshot_inventory.json").write_text(json.dumps({script.name:original}))
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(replay,"DIAGNOSTIC_SOURCE_SNAPSHOT",snapshot)
    # Set launches to an empty list.
    launches=[]
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(replay.subprocess,"run",lambda command,**kw:launches.append(command))
    # Set frozen to a dictionary containing manifest.
    frozen={"manifest":{"source_identities":{script.name:original}}}
    # Call replay._replay_archived_diagnostic with the supplied arguments.
    replay._replay_archived_diagnostic("saved_id",tmp_path,frozen,True)
    # Require the number of entries in launches equals 1 and a string built from script belongs to launches at 0
    # and the text '--gui' belongs to launches at 0; otherwise raise AssertionError.
    assert len(launches)==1 and str(script) in launches[0] and "--gui" in launches[0]
    # Write the supplied text to script.
    script.write_text("# altered code\n")
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match="SOURCE_SNAPSHOT_MISMATCH"):
        # Call replay._replay_archived_diagnostic with the supplied arguments.
        replay._replay_archived_diagnostic("saved_id",tmp_path,frozen,True)
    # Require the number of entries in launches equals 1; otherwise raise AssertionError.
    assert len(launches)==1
