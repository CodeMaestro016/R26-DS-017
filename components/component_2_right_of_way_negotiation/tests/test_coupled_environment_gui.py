"""GUI configuration tests that do not launch SUMO."""

from unittest.mock import patch

from negotiation_training.environment import CoupledNegotiationTrainingEnvironment


def test_gui_configuration_constructs_gui_sumo_environment():
    coupled = CoupledNegotiationTrainingEnvironment(object(), use_gui=True)
    specification = type("Specification", (), {
        "scenario_id": "GUI_CONSTRUCTION_TEST",
        "movement_path_ids": (),
        "scheduled_spawn_times": (),
        "scheduled_spawn_steps": (),
    })()

    with patch("negotiation_training.environment.SUMOEnv") as sumo:
        sumo.return_value.start.side_effect = RuntimeError("STOP_AFTER_CONSTRUCTION")
        try:
            coupled.run_episode(specification, "TEST_MANIFEST")
        except RuntimeError as error:
            assert str(error) == "STOP_AFTER_CONSTRUCTION"
        else:
            raise AssertionError("Expected construction sentinel")

    sumo.assert_called_once_with(use_gui=True)
