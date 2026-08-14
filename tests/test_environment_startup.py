"""SUMO startup fallback tests without launching external processes."""

from unittest.mock import patch

import pytest
import traci

from environment import SUMOEnv


def test_gui_handshake_failure_retries_identical_simulation_headless():
    environment = SUMOEnv(use_gui=True)
    with (
        patch("environment.shutil.which", side_effect=lambda name: f"C:/{name}.exe"),
        patch("environment.traci.start", side_effect=[
            traci.exceptions.FatalTraCIError("GUI closed"), None,
        ]) as start,
        patch("environment.traci.simulation.getTime", return_value=0.0),
    ):
        environment.start()

    assert start.call_count == 2
    gui_command = start.call_args_list[0].args[0]
    headless_command = start.call_args_list[1].args[0]
    assert gui_command[0] == "C:/sumo-gui.exe"
    assert headless_command[0] == "C:/sumo.exe"
    assert gui_command[1:] == headless_command[1:]


def test_headless_handshake_failure_reports_actionable_error():
    environment = SUMOEnv(use_gui=False)
    with (
        patch("environment.shutil.which", return_value="C:/sumo.exe"),
        patch("environment.traci.start", side_effect=
              traci.exceptions.FatalTraCIError("closed")),
        pytest.raises(RuntimeError, match="Headless SUMO closed"),
    ):
        environment.start()


def test_step_captures_authoritative_lifecycle_events_before_observations():
    environment = SUMOEnv()
    calls = []
    with (
        patch("environment.traci.simulationStep", side_effect=lambda: calls.append("step")),
        patch("environment.traci.simulation.getTime", side_effect=lambda: (calls.append("time"), 1.0)[1]),
        patch("environment.traci.simulation.getDepartedIDList", side_effect=lambda: (calls.append("departed"), ("AV_0",))[1]),
        patch("environment.traci.simulation.getArrivedIDList", side_effect=lambda: (calls.append("arrived"), ("AV_1",))[1]),
        patch.object(environment, "get_vehicles", side_effect=lambda: (calls.append("observations"), {})[1]),
    ):
        assert environment.step() == {}
    assert calls == ["step", "time", "departed", "arrived", "observations"]
    assert environment.lifecycle_events.timestamp == 1.0
    assert environment.lifecycle_events.departed_vehicle_ids == ("AV_0",)
    assert environment.lifecycle_events.arrived_vehicle_ids == ("AV_1",)
