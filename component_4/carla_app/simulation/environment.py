# CARLA environment manager

import carla

from carla_app.config.simulation_config import (
    MAP_NAME,
    WEATHER,
    SYNCHRONOUS_MODE,
    FIXED_DELTA_SECONDS,
)


class CarlaEnvironment:
    """
    Manages the CARLA simulation environment.
    """

    def __init__(self, carla_client):
        self.carla_client = carla_client
        self.world = None

    def setup(self):
        """
        Load the configured map, apply weather and configure
        simulation settings.

        Returns:
            carla.World: Configured CARLA world.
        """

        # Load the configured map.
        self.world = self.carla_client.load_world(MAP_NAME)

        # Apply configured weather.
        self.carla_client.set_weather(WEATHER)

        # Configure simulation settings.
        self._configure_simulation_settings()

        return self.world

    def _configure_simulation_settings(self):
        """
        Configure CARLA world settings.
        """

        if self.world is None:
            raise RuntimeError(
                "CARLA world is not available. "
                "Call setup() first."
            )

        settings = self.world.get_settings()

        settings.synchronous_mode = SYNCHRONOUS_MODE

        if SYNCHRONOUS_MODE:
            settings.fixed_delta_seconds = FIXED_DELTA_SECONDS
        else:
            settings.fixed_delta_seconds = None

        self.world.apply_settings(settings)

    def get_world(self):
        """
        Return the configured CARLA world.
        """

        if self.world is None:
            raise RuntimeError(
                "CARLA environment has not been set up yet."
            )

        return self.world

    def get_map(self):
        """
        Return the currently loaded CARLA map.
        """

        return self.get_world().get_map()

    def tick(self):
        """
        Advance the simulation by one frame.

        This is used only when synchronous mode is enabled.
        """

        if self.world is None:
            raise RuntimeError(
                "CARLA environment has not been set up yet."
            )

        if SYNCHRONOUS_MODE:
            return self.world.tick()

        return None

    def restore_settings(self):
        """
        Restore CARLA to asynchronous mode.

        This is useful when shutting down the simulation.
        """

        if self.world is None:
            return

        settings = self.world.get_settings()

        settings.synchronous_mode = False
        settings.fixed_delta_seconds = None

        self.world.apply_settings(settings)

    def cleanup(self):
        """
        Clean up the environment configuration.
        """

        if self.world is not None:
            self.restore_settings()

        self.world = None
