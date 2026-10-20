"""GUI configuration tests that do not launch SUMO."""

# Import patch from unittest.mock for the operations below.
from unittest.mock import patch

# Import CoupledNegotiationTrainingEnvironment from negotiation_training.environment for the operations below.
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment


# Check gui configuration constructs gui sumo environment using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: handle the specified errors.
def test_gui_configuration_constructs_gui_sumo_environment():
    # Set coupled to the result of CoupledNegotiationTrainingEnvironment(the result of object()).
    coupled = CoupledNegotiationTrainingEnvironment(object(), use_gui=True)
    # Set specification to the result of type('Specification', (), {'scenario_id': 'GUI_CONSTRUCTION_TEST',
    # 'movement_path_ids': (),...().
    specification = type("Specification", (), {
        "scenario_id": "GUI_CONSTRUCTION_TEST",
        # Store an empty tuple under 'movement_path_ids'.
        "movement_path_ids": (),
        # Store an empty tuple under 'scheduled_spawn_times'.
        "scheduled_spawn_times": (),
        # Store an empty tuple under 'scheduled_spawn_steps'.
        "scheduled_spawn_steps": (),
    })()

    # Enter the result of patch(the text 'negotiation_training.environment.SUMOEnv') as sumo and run the enclosed
    # operations within that context.
    with patch("negotiation_training.environment.SUMOEnv") as sumo:
        # Set sumo.return_value.start.side_effect to the result of RuntimeError(the text
        # 'STOP_AFTER_CONSTRUCTION').
        sumo.return_value.start.side_effect = RuntimeError("STOP_AFTER_CONSTRUCTION")
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Call coupled.run_episode with the supplied arguments.
            coupled.run_episode(specification, "TEST_MANIFEST")
        # Handle RuntimeError as error using the recovery steps below.
        except RuntimeError as error:
            # Require a string built from error equals the text 'STOP_AFTER_CONSTRUCTION'; otherwise raise
            # AssertionError.
            assert str(error) == "STOP_AFTER_CONSTRUCTION"
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Raise AssertionError with the text 'Expected construction sentinel' to stop this execution path.
            raise AssertionError("Expected construction sentinel")

    # Call sumo.assert_called_once_with with the supplied arguments.
    sumo.assert_called_once_with(use_gui=True)
