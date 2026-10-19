"""V2 physical admission regressions using only ego/pair inputs."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
from negotiation_execution import (DecentralizedEgoExecutionController,
    EgoExecutionContext, EgoCoordinationCommitment, ExecutionStateMessage)
from post_training_evaluation.inference import ScientificEvaluationProvider
from negotiation_training.final_selection import FinalSelectionInferenceProvider
from runtime_simulation.inference import PanelDeterministicInferenceProvider


def state(progress=-20.):
    return dict(progress=progress, width=1.8, length=5., lane_id="incoming",
        lane_position=10., speed=4., comfortable_deceleration_mps2=4.5)


def controller():
    paths = SimpleNamespace(paths={p: SimpleNamespace(incoming_lane_id="incoming",
        outgoing_lane_id="outgoing") for p in ("A", "B")},
        resolve_front_bumper_path_progress=lambda s,p: (s["progress"],None,None))
    zones = SimpleNamespace(zone_record=lambda *args: dict(zone_id="CZ",
        first_path_distance_interval=(0.,10.), second_path_distance_interval=(0.,10.)))
    return DecentralizedEgoExecutionController(paths,zones)


def context(ego="A", peer="B", arrival=0., peer_arrival=0.):
    return EgoExecutionContext(ego,state(),ego,1.,peer_messages=(
        ExecutionStateMessage(peer,peer,state(),1.,peer_arrival,coordination_epoch=("epoch",)),),
        coordination_complete=True,coordination_timestamp=1.,strict_admission=True,
        coordination_epoch=("epoch",),queue_arrival_seconds=arrival)


def test_unordered_pair_safe_holds_without_mappo_receipt():
    d=controller().decide(context())
    assert (d.permission,d.reason)==("SAFE_HOLD","UNORDERED_PHYSICAL_CONFLICT")


@pytest.mark.parametrize("a,b", [(0.,0.),(.2,.1),(.1,.2),(0.,.0000000001)])
def test_fallback_pair_is_identical_at_both_egos(a,b):
    ca=replace(context(arrival=a,peer_arrival=b),mappo_receipt=True,fallback_peer_ids=("B",))
    cb=replace(context("B","A",b,a),mappo_receipt=True,fallback_peer_ids=("A",))
    da,db=controller().decide(ca),controller().decide(cb)
    assert da.fallback_pairs==db.fallback_pairs
    assert {da.permission,db.permission}=={"PERMITTED","BLOCKED_BY_PRECEDENCE"}
    assert da.shield_rejection_reason==db.shield_rejection_reason=="UNORDERED_PHYSICAL_CONFLICT"


@pytest.mark.parametrize("change", [dict(mappo_receipt=False),dict(fallback_peer_ids=()),
    dict(queue_arrival_seconds=None),dict(queue_arrival_seconds=2.)])
def test_fallback_requires_valid_local_receipt_and_arrivals(change):
    c=replace(context(),mappo_receipt=True,fallback_peer_ids=("B",))
    assert controller().decide(replace(c,**change)).permission=="SAFE_HOLD"


def test_mandatory_edge_removal_is_rejected_without_fallback():
    c=replace(context(),mappo_receipt=True,fallback_peer_ids=("B",),
        mandatory_commitments=(EgoCoordinationCommitment("A","B",("epoch",)),))
    d=controller().decide(c)
    assert d.shield_rejection_reason=="MANDATORY_PRECEDENCE_REMOVED" and not d.fallback_pairs
    assert d.permission=="BLOCKED_BY_PRECEDENCE"


def test_stale_epoch_is_rejected():
    c=replace(context(),commitments=(EgoCoordinationCommitment("B","A",("old",)),))
    assert controller().decide(c).reason=="COORDINATION_EPOCH_MISMATCH"


def test_peer_epoch_is_rejected_and_ulp_arrival_tie_uses_id():
    c=replace(context(),peer_messages=(replace(context().peer_messages[0],coordination_epoch=("old",)),))
    assert controller().decide(c).reason=="PEER_COORDINATION_EPOCH_MISMATCH"
    c=replace(context(arrival=1e-15),mappo_receipt=True,fallback_peer_ids=("B",))
    assert controller().decide(c).fallback_pairs==(("B","A"),)


def test_v1_write_root_and_implicit_v2_freeze_are_rejected(tmp_path):
    from pathlib import Path
    from post_training_evaluation.models import protect_v1
    from post_training_evaluation.runner import run_suite
    root=Path(__file__).resolve().parents[1]/"results/post_training_evaluation"
    with pytest.raises(RuntimeError,match="V1_EVIDENCE_IS_READ_ONLY"):
        protect_v1(root)
    with pytest.raises(RuntimeError,match="V2_MANIFEST_NOT_FROZEN"):
        run_suite("final",tmp_path)
    assert not (tmp_path/"manifest.json").exists()


def test_follower_waits_before_entry_without_actor_context():
    c=replace(context(),negotiation_eligible=False,coordination_complete=False)
    ctl=controller()
    assert ctl.decide(c).blocked_zones[0][:2]==("JUNCTION_ENTRY",20.)
    with pytest.raises(RuntimeError,match="BLOCKED_VEHICLE_ENTERED"):
        ctl.decide(replace(c,ego_state=state(.1)))


def test_valid_admission_locks_at_native_braking_boundary():
    ctl=controller()
    c=replace(context(),ego_state=state(-1.),commitments=(
        EgoCoordinationCommitment("B","A",("epoch",)),))
    api=SimpleNamespace(getSpeedMode=lambda _:31,getActionStepLength=lambda _:.04,getSpeedWithoutTraCI=lambda _:4.)
    ctl.constrain(c,ctl.decide(c),api,.04)
    assert ctl.admission_state=="COMMITTED_TO_ENTER"
    d=ctl.decide(replace(c,ego_state=state(.1),coordination_complete=False,peer_messages=()))
    assert d.permission=="PERMITTED" and ctl.admission_state=="IN_CONFLICT_ZONE"


def test_valid_stopped_release_locks_before_native_step_crosses_entry():
    ctl=controller()
    c=replace(context(),ego_state=dict(state(-.001),speed=0.),commitments=(
        EgoCoordinationCommitment("B","A",("epoch",)),))
    api=SimpleNamespace(getSpeedMode=lambda _:31,getActionStepLength=lambda _:.04,
        getSpeedWithoutTraCI=lambda _:.104)
    ctl.constrain(c,ctl.decide(c),api,.04)
    assert ctl.admission_state=="COMMITTED_TO_ENTER"


def test_explicit_unresolved_pair_is_eligible_but_missing_or_mandatory_evidence_is_not():
    from runtime_simulation.runner import _eligible_fallback_pairs
    relation=dict(ego_id="A",target_id="B",regulatory_status="UNRESOLVED_DUE_TO_TARGET_MANOEUVRE",
        shared_conflict_zone_ids=("CZ",),regulatory_evidence=dict(candidate_assessments=({"regulatory_status":"NO_PAIRWISE_PRECEDENCE_RULE"},)))
    snapshots=({"unresolved_relations":(relation,)},)
    assert _eligible_fallback_pairs(("A","B"),(),snapshots,())==(("A","B"),)
    assert not _eligible_fallback_pairs(("A","B"),(),snapshots,(("A","B"),))
    assert not _eligible_fallback_pairs(("A","B"),(),({"unresolved_relations":(dict(relation,regulatory_status="REGULATORY_INPUT_UNRESOLVED"),)},),())


def test_invalid_coordination_never_activates_fallback_even_with_pair_certificate():
    c=replace(context(),coordination_complete=False,mappo_receipt=True,fallback_peer_ids=("B",))
    d=controller().decide(c)
    assert d.permission=="SAFE_HOLD" and not d.fallback_pairs


def test_scientific_sampling_is_original_method_and_panel_is_separate():
    assert ScientificEvaluationProvider._sample is FinalSelectionInferenceProvider._sample
    assert PanelDeterministicInferenceProvider._sample is not ScientificEvaluationProvider._sample


def test_event_logger_reports_actual_inference_mode(capsys):
    from runtime_simulation.runner import _print_event
    from post_training_evaluation.inference import SCIENTIFIC_SELECTION_RULE
    outcome=SimpleNamespace(proposer_assignment=SimpleNamespace(claim_action_assignments=()),
        responder_assignment=SimpleNamespace(response_action_assignments=()),effective_precedence_graph=())
    plan=SimpleNamespace(ready_vehicle_ids=(),blocked_vehicle_ids=())
    _print_event(1,1.,(),"NEGOTIATION_REQUIRED_REGULATORY_CYCLE",(),outcome,plan,0,0,
        selection_rule=SCIENTIFIC_SELECTION_RULE)
    output=capsys.readouterr().out
    assert "SEMANTIC_SELECTION_RULE = SEEDED_STOCHASTIC_MASKED_SAMPLE" in output
    assert "ARGMAX" not in output


def test_archived_replay_verifies_code_before_launching(monkeypatch,tmp_path):
    import importlib,json
    from post_training_evaluation.models import file_hash
    replay=importlib.import_module("post_training_evaluation.replay")
    snapshot=tmp_path/"snapshot"
    snapshot.mkdir()
    script=snapshot/"run_final_evaluation.py"  # Original archived entry point.
    script.write_text("# measured diagnostic code\n")
    original=file_hash(script)
    (snapshot/"snapshot_inventory.json").write_text(json.dumps({script.name:original}))
    monkeypatch.setattr(replay,"DIAGNOSTIC_SOURCE_SNAPSHOT",snapshot)
    launches=[]
    monkeypatch.setattr(replay.subprocess,"run",lambda command,**kw:launches.append(command))
    frozen={"manifest":{"source_identities":{script.name:original}}}
    replay._replay_archived_diagnostic("saved_id",tmp_path,frozen,True)
    assert len(launches)==1 and str(script) in launches[0] and "--gui" in launches[0]
    script.write_text("# altered code\n")
    with pytest.raises(RuntimeError,match="SOURCE_SNAPSHOT_MISMATCH"):
        replay._replay_archived_diagnostic("saved_id",tmp_path,frozen,True)
    assert len(launches)==1
