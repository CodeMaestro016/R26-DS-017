"""SUMO startup fallback tests without launching external processes."""

# Import patch from unittest.mock for the operations below.
from unittest.mock import patch

# Import pytest for use in this module.
import pytest
# Import traci for use in this module.
import traci

# Import SUMOEnv from environment for the operations below.
from environment import SUMOEnv


# Check gui handshake failure retries simulation headless without gui settings using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_gui_handshake_failure_retries_simulation_headless_without_gui_settings():
    # Set environment to the result of SUMOEnv().
    environment = SUMOEnv(use_gui=True)
    # Enter the result of patch(the text 'environment.shutil.which'); the result of patch(the text
    # 'environment.traci.start') as start; the result of patch(the text 'environment.traci.simulation.getTime')
    # and run the enclosed operations within that context.
    with (
        # Declare name as input parameter.
        patch("environment.shutil.which", side_effect=lambda name: f"C:/{name}.exe"),
        # Supply side_effect as a list containing the result of traci.exceptions.FatalTraCIError(the text 'GUI
        # closed'), None.
        patch("environment.traci.start", side_effect=[
            # Include the result of traci.exceptions.FatalTraCIError(the text 'GUI closed') in this list.
            traci.exceptions.FatalTraCIError("GUI closed"), None,
        # Evaluate start as part of the enclosing expression.
        ]) as start,
        # Supply return_value as 0.0.
        patch("environment.traci.simulation.getTime", return_value=0.0),
    ):
        # Call environment.start with the supplied arguments.
        environment.start()

    # Require start.call_count equals 2; otherwise raise AssertionError.
    assert start.call_count == 2
    # Set gui_command to start.call_args_list[0].args at 0.
    gui_command = start.call_args_list[0].args[0]
    # Set headless_command to start.call_args_list[1].args at 0.
    headless_command = start.call_args_list[1].args[0]
    # Require gui_command at 0 equals the text 'C:/sumo-gui.exe'; otherwise raise AssertionError.
    assert gui_command[0] == "C:/sumo-gui.exe"
    # Require headless_command at 0 equals the text 'C:/sumo.exe'; otherwise raise AssertionError.
    assert headless_command[0] == "C:/sumo.exe"
    # Require the text '--gui-settings-file' belongs to gui_command; otherwise raise AssertionError.
    assert "--gui-settings-file" in gui_command
    # Require the text '--gui-settings-file' does not belong to headless_command; otherwise raise AssertionError.
    assert "--gui-settings-file" not in headless_command
    # Set settings_index to the result of gui_command.index(the text '--gui-settings-file').
    settings_index = gui_command.index("--gui-settings-file")
    # Require the result of gui_command[settings_index + 1].endswith(the text 'panel_real_world.xml'); otherwise
    # raise AssertionError.
    assert gui_command[settings_index + 1].endswith("panel_real_world.xml")
    # Require gui_command sliced by 1:settings_index equals headless_command sliced by 1:; otherwise raise
    # AssertionError.
    assert gui_command[1:settings_index] == headless_command[1:]


# Check headless handshake failure reports actionable error using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_headless_handshake_failure_reports_actionable_error():
    # Set environment to the result of SUMOEnv().
    environment = SUMOEnv(use_gui=False)
    # Enter the result of patch(the text 'environment.shutil.which'); the result of patch(the text
    # 'environment.traci.start'); the result of pytest.raises(RuntimeError) and run the enclosed operations within
    # that context.
    with (
        # Supply return_value as the text 'C:/sumo.exe'.
        patch("environment.shutil.which", return_value="C:/sumo.exe"),
        # Supply side_effect as the result of traci.exceptions.FatalTraCIError(the text 'closed').
        patch("environment.traci.start", side_effect=
              # Evaluate the result of traci.exceptions.FatalTraCIError(the text 'closed') as part of the
              # enclosing expression.
              traci.exceptions.FatalTraCIError("closed")),
        # Supply match as the text 'Headless SUMO closed'.
        pytest.raises(RuntimeError, match="Headless SUMO closed"),
    ):
        # Call environment.start with the supplied arguments.
        environment.start()


# Check step captures authoritative lifecycle events before observations using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_step_captures_authoritative_lifecycle_events_before_observations():
    # Set environment to the result of SUMOEnv().
    environment = SUMOEnv()
    # Set calls to an empty list.
    calls = []
    # Enter the result of patch(the text 'environment.traci.simulationStep'); the result of patch(the text
    # 'environment.traci.simulation.getTime'); the result of patch(the text
    # 'environment.traci.simulation.getDepartedIDList');... and run the enclosed operations within that context.
    with (
        # Supply side_effect as a callback that returns the result of calls.append(the text 'step').
        patch("environment.traci.simulationStep", side_effect=lambda: calls.append("step")),
        # Supply side_effect as a callback that returns (calls.append('time'), 1.0) at 1.
        patch("environment.traci.simulation.getTime", side_effect=lambda: (calls.append("time"), 1.0)[1]),
        # Supply side_effect as a callback that returns (calls.append('departed'), ('AV_0',)) at 1.
        patch("environment.traci.simulation.getDepartedIDList", side_effect=lambda: (calls.append("departed"), ("AV_0",))[1]),
        # Supply side_effect as a callback that returns (calls.append('arrived'), ('AV_1',)) at 1.
        patch("environment.traci.simulation.getArrivedIDList", side_effect=lambda: (calls.append("arrived"), ("AV_1",))[1]),
        # Supply side_effect as a callback that returns (calls.append('observations'), {}) at 1.
        patch.object(environment, "get_vehicles", side_effect=lambda: (calls.append("observations"), {})[1]),
    ):
        # Require the result of environment.step() equals an empty dictionary; otherwise raise AssertionError.
        assert environment.step() == {}
    # Require calls equals a list containing the text 'step', the text 'time', the text 'departed', the text
    # 'arrived', the text 'observations'; otherwise raise AssertionError.
    assert calls == ["step", "time", "departed", "arrived", "observations"]
    # Require environment.lifecycle_events.timestamp equals 1.0; otherwise raise AssertionError.
    assert environment.lifecycle_events.timestamp == 1.0
    # Require environment.lifecycle_events.departed_vehicle_ids equals a tuple containing the text 'AV_0';
    # otherwise raise AssertionError.
    assert environment.lifecycle_events.departed_vehicle_ids == ("AV_0",)
    # Require environment.lifecycle_events.arrived_vehicle_ids equals a tuple containing the text 'AV_1';
    # otherwise raise AssertionError.
    assert environment.lifecycle_events.arrived_vehicle_ids == ("AV_1",)
