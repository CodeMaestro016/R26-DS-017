# CARLA client connection

import carla

from carla_app.config.simulation_config import (
    CARLA_HOST,
    CARLA_PORT,
)


class CarlaClient:
    """
    Handles the connection between the research project
    and the CARLA server.
    """

    def __init__(self, host=CARLA_HOST, port=CARLA_PORT, timeout=10.0):
        self.host = host
        self.port = port
        self.timeout = timeout

        self.client = None
        self.world = None

    def connect(self):
        """
        Connect to the CARLA server.

        Returns:
            carla.World: The currently loaded CARLA world.
        """

        self.client = carla.Client(self.host, self.port)
        self.client.set_timeout(self.timeout)

        self.world = self.client.get_world()

        return self.world

    def get_client(self):
        """
        Return the active CARLA client.
        """

        return self.client

    def get_world(self):
        """
        Return the currently connected CARLA world.
        """

        if self.world is None:
            raise RuntimeError(
                "CARLA world is not available. "
                "Call connect() first."
            )

        return self.world

    def load_world(self, map_name):
        """
        Load a specific CARLA map.

        Args:
            map_name (str): CARLA map name.

        Returns:
            carla.World: Newly loaded world.
        """

        if self.client is None:
            raise RuntimeError(
                "CARLA client is not connected. "
                "Call connect() first."
            )

        self.world = self.client.load_world(map_name)

        return self.world

    def set_weather(self, weather):
        """
        Apply weather settings to the current world.

        Args:
            weather (dict): Weather configuration dictionary.
        """

        world = self.get_world()

        weather_parameters = carla.WeatherParameters(
            cloudiness=weather.get("cloudiness", 0.0),
            precipitation=weather.get("precipitation", 0.0),
            precipitation_deposits=weather.get(
                "precipitation_deposits", 0.0
            ),
            wind_intensity=weather.get(
                "wind_intensity", 0.0
            ),
            sun_azimuth_angle=weather.get(
                "sun_azimuth_angle", 0.0
            ),
            sun_altitude_angle=weather.get(
                "sun_altitude_angle", 70.0
            ),
            fog_density=weather.get("fog_density", 0.0),
            fog_distance=weather.get("fog_distance", 0.0),
            fog_falloff=weather.get("fog_falloff", 0.0),
            wetness=weather.get("wetness", 0.0),
            scattering_intensity=weather.get(
                "scattering_intensity", 1.0
            ),
            mie_scattering_scale=weather.get(
                "mie_scattering_scale", 0.0
            ),
            rayleigh_scattering_scale=weather.get(
                "rayleigh_scattering_scale", 0.0331
            ),
        )

        world.set_weather(weather_parameters)

    def disconnect(self):
        """
        Clear local CARLA references.

        CARLA itself is managed by the CARLA server process.
        """

        self.world = None
        self.client = None
