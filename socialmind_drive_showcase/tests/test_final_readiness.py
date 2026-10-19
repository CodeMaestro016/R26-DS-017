"""Presentation reliability and read-only scientific evidence boundaries."""
import json
import os
import socket
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace
import pytest
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
from socialmind_drive_showcase.services.live_state_reader import read_live_state, runtime_status_label, discharge_label
from socialmind_drive_showcase.services import evaluation_reader as evidence

def component(tmp_path):
    return SimpleNamespace(live=True,working_directory=tmp_path,launch_command=("{python}","runtime.py"))

def test_old_frame_is_not_presented_as_current_launch(tmp_path):
    path=tmp_path/'live.json'
    path.write_text(json.dumps(dict(running=True,simulation_time=90)))
    os.utime(path,(100,100))
    assert not read_live_state(path,started_after=101)['available']
    state=read_live_state(path,started_after=99,clock=lambda:102)
    assert state['available'] and state['payload']['simulation_time']==90

@pytest.mark.parametrize('raw',['[]','null','{"simulation_time":NaN}','{'])
def test_malformed_or_nonfinite_telemetry_is_unavailable(tmp_path,raw):
    path=tmp_path/'live.json';path.write_text(raw)
    assert not read_live_state(path)['available']

@pytest.mark.parametrize('status',['FAILED','LAUNCHING','STOPPING'])
def test_process_failure_or_startup_overrides_old_running_frame(status):
    assert runtime_status_label(status,{'payload':{'running':True}})==status

def test_incomplete_discharge_is_not_labelled_complete():
    assert 'INCOMPLETE' in discharge_label(dict(completed=0,scheduled=16))
    assert discharge_label(dict(completed=16,scheduled=16))=='SCENARIO COMPLETE'
    assert 'UNAVAILABLE' in discharge_label({})
    assert runtime_status_label('RUNNING',{'stale':True})=='STALE TELEMETRY'

class Process:
    pid=12345
    def __init__(self):
        self.done=threading.Event();self.code=0
    def poll(self):return self.code if self.done.is_set() else None
    def wait(self,timeout=None):
        if not self.done.wait(timeout):raise subprocess.TimeoutExpired('fake',timeout)
        return self.code
    def terminate(self):self.code=-15;self.done.set()
    def kill(self):self.terminate()

def test_stop_during_process_creation_is_owned_and_not_lost(tmp_path,monkeypatch):
    launcher=ComponentLauncher(component(tmp_path));entered=threading.Event();release=threading.Event();process=Process();commands=[]
    def popen(command,**kwargs):
        commands.append((command,kwargs));entered.set()
        assert release.wait(2)
        return process
    monkeypatch.setattr(subprocess,'Popen',popen)
    monkeypatch.setattr(launcher,'_terminate_owned_tree',lambda owned:owned.terminate())
    assert launcher.launch(('--scenario','congested_four_approach'))
    assert entered.wait(2)
    assert not launcher.launch()
    assert launcher.request_stop(.1)
    release.set();launcher._worker.join(3)
    assert not launcher._worker.is_alive()
    assert launcher.stop_forced and launcher.status=='READY'
    assert process.poll() is not None and launcher._process is None
    assert commands[0][0][2:4]==['--scenario','congested_four_approach']
    assert commands[0][1]['shell'] is False
    assert not launcher._stop_request_path.exists()

def test_old_stop_timer_cannot_terminate_a_new_run(tmp_path,monkeypatch):
    launcher=ComponentLauncher(component(tmp_path));launcher.run_id='new';launcher.status='RUNNING';launcher._process=Process()
    monkeypatch.setattr(launcher,'_terminate_owned_tree',lambda p:pytest.fail('Stale stop timer targeted new run'))
    launcher._force_after_grace('old',.1)

def test_repeated_launches_have_distinct_logs_and_owned_tokens(tmp_path,monkeypatch):
    def popen(*args,**kwargs):
        process=Process();process.done.set();return process
    monkeypatch.setattr(subprocess,'Popen',popen)
    launcher=ComponentLauncher(component(tmp_path));ids=[];logs=[]
    for _ in range(2):
        assert launcher.launch();launcher._worker.join(2)
        assert launcher.status=='FINISHED'
        ids.append(launcher.run_id);logs.append(launcher.log_path)
    assert len(set(ids))==len(set(logs))==2

def test_startup_os_error_is_failed_not_finished(tmp_path,monkeypatch):
    def fail(*args,**kwargs):raise FileNotFoundError('Missing runtime/model asset')
    monkeypatch.setattr(subprocess,'Popen',fail)
    launcher=ComponentLauncher(component(tmp_path));assert launcher.launch();launcher._worker.join(2)
    assert launcher.status=='FAILED' and 'Missing runtime/model asset' in launcher.error

def test_shutdown_stops_only_owned_process_and_prevents_relaunch(tmp_path,monkeypatch):
    process=Process()
    monkeypatch.setattr(subprocess,'Popen',lambda *args,**kwargs:process)
    launcher=ComponentLauncher(component(tmp_path))
    monkeypatch.setattr(launcher,'_terminate_owned_tree',lambda owned:owned.terminate())
    assert launcher.launch()
    launcher.shutdown(.1)
    assert process.poll() is not None or launcher._process is None
    assert not launcher.launch()

def test_default_rolling_and_sixteen_vehicle_scenarios_exist():
    from socialmind_drive_showcase.pages.component2_live_view import SELECTABLE_SCENARIOS, SCENARIO_BY_ID
    choices={s['scenario_id'] for s in SELECTABLE_SCENARIOS}
    assert 'default_panel' in SCENARIO_BY_ID and 'default_panel' not in choices
    assert 'congested_four_approach' in choices and len(choices)==5
    assert SCENARIO_BY_ID['congested_four_approach']['vehicle_count']==16

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))

def archive(tmp_path):
    manifest=dict(protocol_id='FROZEN_TEST',scenarios=[dict(scenario_id='case',continuous=False)],
        methods=['PROPOSED_MAPPO','RULES_ONLY','RULE_PLUS_FCFS'],seeds=[101])
    frozen=dict(manifest=manifest,manifest_hash=evidence._digest(manifest));save(tmp_path/'manifest.json',frozen)
    schedule={'N':[{'requested':0}]};schedule_hash=evidence._digest(schedule)
    record=dict(run_id='record',suite='final',scenario_id='case',seed=None,method='PROPOSED_MAPPO',
        classification='SAFE_DEGRADATION',manifest_hash=frozen['manifest_hash'],schedule_hash=schedule_hash,
        metrics=dict(total_vehicles_completed=0,total_vehicles_scheduled=4,mean_travel_time_seconds=None))
    provenance=dict(manifest_hash=frozen['manifest_hash'],schedule_hash=schedule_hash,schedule=schedule)
    directory=tmp_path/'runs/record'
    save(directory/'result.json',record);save(directory/'result.sha256.json',dict(result_hash=evidence._digest(record)))
    save(directory/'provenance.json',provenance);save(directory/'provenance.sha256.json',dict(provenance_hash=evidence._digest(provenance)))
    return record

def test_verified_partial_final_count_does_not_recompute_smoke_values(tmp_path):
    raw=archive(tmp_path)
    payload=dict(schema_version=1,suite='smoke',episode_count=9,groups=[dict(metrics={'completion_rate':{'mean':.37}})])
    path=tmp_path/'latest/aggregate.json';save(path,payload);before=path.read_bytes()
    result=evidence.read_evaluation(path)
    assert result['payload']==payload and path.read_bytes()==before
    verified=result['verification']
    assert verified['verified']==1 and verified['expected']==3 and verified['missing']==2
    assert verified['classification_counts']=={'SAFE_DEGRADATION':1}
    assert not verified['complete'] and verified['runs'][0]==raw
    assert verified['runs'][0]['metrics']['mean_travel_time_seconds'] is None
    assert result['plots_root']==path.parent/'plots'

def test_corrupted_or_interrupted_record_is_never_counted_as_verified(tmp_path):
    archive(tmp_path)
    (tmp_path/'runs/record/provenance.json').write_text('{}')
    (tmp_path/'runs/interrupted').mkdir()
    verified=evidence.verify_archive(tmp_path)
    assert verified['verified']==0 and verified['missing']==3
    assert verified['verification_errors'] and verified['unfinished_archive_directories']

def test_busy_port_has_actionable_error_without_launching_server(monkeypatch):
    from socialmind_drive_showcase import app as server
    monkeypatch.setattr(server,'run_showcase',lambda **kw:pytest.fail('Busy port should not launch'))
    with socket.socket() as occupied:
        occupied.bind(('127.0.0.1',0));occupied.listen()
        with pytest.raises(SystemExit) as error:
            server.main(['--server-only','--port',str(occupied.getsockname()[1])])
    assert error.value.code==2

def test_missing_desktop_dependency_is_explicit(monkeypatch):
    from socialmind_drive_showcase import app as server
    monkeypatch.setattr(server.importlib.util,'find_spec',lambda name:None)
    with pytest.raises(SystemExit) as error:server.main([])
    assert error.value.code==2

def test_missing_frozen_checkpoint_refuses_real_command_without_spawn(tmp_path,monkeypatch):
    model=SimpleNamespace(live=True,working_directory=tmp_path,launch_command=('{python}','run_runtime_simulation.py'))
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('Missing checkpoint must not start a process'))
    launcher=ComponentLauncher(model)
    assert not launcher.launch() and launcher.status=='FAILED'
    assert 'Missing frozen model asset' in launcher.error
    assert launcher.started_at is not None and launcher.exit_code is None

def test_missing_sumo_refuses_real_command_without_spawn(tmp_path,monkeypatch):
    import socialmind_drive_showcase.services.component_launcher as module
    model=SimpleNamespace(live=True,working_directory=tmp_path,launch_command=('{python}','run_runtime_simulation.py'))
    monkeypatch.setattr(module.shutil,'which',lambda name:None)
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('Missing SUMO must not start a process'))
    launcher=ComponentLauncher(model)
    assert not launcher.launch() and launcher.status=='FAILED'
    assert 'not on PATH' in launcher.error
