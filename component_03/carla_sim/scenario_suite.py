# -*- coding: utf-8 -*-
"""
Compatibility-safe CARLA scenario suite
----------------------------------------

All six scenarios are now enabled, with explicit spawn indices for
distracted and aggressive to place them at different map locations.
Hesitant uses the same robust crosswalk-first vehicle placement as
committed (see carla_live_demo.py), just pointed at a different real
crosswalk via skip_count, since the earlier explicit-spawn-index
approach for hesitant was confirmed to sometimes land nowhere near
any real crosswalk at all.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any


# ================================================================
# MENTAL STATE MAPPING
# ================================================================

BEHAVIOR_TO_STATE = {
    'waiting': 0,
    'hesitant': 1,
    'committed': 2,
    'distracted': 3,
    'aggressive': 4,
    'jaywalk': 5,
}


# ================================================================
# SCENARIO SPECIFICATION
# ================================================================

@dataclass
class ScenarioSpec:

    id: str
    behavior: str
    description: str

    weather_preset: Optional[str] = None
    weather_custom: Optional[Dict[str, Any]] = None

    spawn_distance_m: Tuple[float, float] = (28.0, 34.0)

    lane_count: int = 2
    pedestrian_side: str = 'right'
    extra_pedestrians: int = 0
    ego_cruise_kmh: float = 30.0

    pedestrian_profile: str = 'adult'
    preferred_age: Optional[str] = None
    preferred_gender: Optional[str] = None

    visual_context: Tuple[str, ...] = ()
    background_motion: bool = False
    scenario_seed_offset: int = 0

    # Explicit spawn point index (None = use seed-based or
    # crosswalk-first placement instead)
    vehicle_spawn_index: Optional[int] = None

    @property
    def true_state(self) -> int:
        return BEHAVIOR_TO_STATE[self.behavior]


# ================================================================
# SCENARIO SUITE – ALL SIX SCENARIOS
# ================================================================

SCENARIO_SUITE = [

    ScenarioSpec(
        id='committed_crosswalk_clear_day',
        behavior='committed',
        description=(
            'Single pedestrian continuously crosses a marked '
            'crosswalk in clear daylight.'
        ),
        weather_preset='ClearNoon',
        spawn_distance_m=(32.0, 32.0),
        lane_count=2,
        pedestrian_side='right',
        extra_pedestrians=0,
        ego_cruise_kmh=30.0,
        pedestrian_profile='adult',
        visual_context=('steady_crossing', 'daylight', 'crosswalk'),
        background_motion=False,
        scenario_seed_offset=11,
        vehicle_spawn_index=None,          # crosswalk-first placement, skip_count=0
    ),

    ScenarioSpec(
        id='waiting_corner_patient_day',
        behavior='waiting',
        description=(
            'Single pedestrian remains stationary near the '
            'roadside while the vehicle approaches.'
        ),
        weather_preset='ClearNoon',
        spawn_distance_m=(32.0, 32.0),
        lane_count=2,
        pedestrian_side='right',
        extra_pedestrians=0,
        ego_cruise_kmh=30.0,
        pedestrian_profile='adult',
        visual_context=('stationary', 'non_crossing', 'daylight'),
        background_motion=False,
        scenario_seed_offset=61,
        vehicle_spawn_index=None,
    ),

    ScenarioSpec(
        id='hesitant_kerb_uncertain_day',
        behavior='hesitant',
        description=(
            'Single pedestrian lingers at the kerb with long '
            'pauses and tentative steps.'
        ),
        weather_preset='ClearNoon',
        spawn_distance_m=(32.0, 32.0),
        lane_count=2,
        pedestrian_side='right',
        extra_pedestrians=0,
        ego_cruise_kmh=30.0,
        pedestrian_profile='adult',
        visual_context=('kerb_hesitation', 'daylight', 'crosswalk'),
        background_motion=False,
        scenario_seed_offset=23,
        # No longer using an explicit spawn index -- confirmed via an
        # actual run that index 5 landed with no real crosswalk within
        # 200m and the vehicle in an unintended lane. Now uses the same
        # robust crosswalk-first placement as committed, with
        # skip_count=2 (see carla_live_demo.py) to land on a different
        # real crosswalk than committed's.
        vehicle_spawn_index=None,
    ),

    ScenarioSpec(
        id='distracted_phone_crossing_day',
        behavior='distracted',
        description=(
            'Single pedestrian crosses with irregular pace and '
            'short pauses, as if distracted.'
        ),
        weather_preset='ClearNoon',
        spawn_distance_m=(32.0, 32.0),
        lane_count=2,
        pedestrian_side='right',
        extra_pedestrians=0,
        ego_cruise_kmh=30.0,
        pedestrian_profile='adult',
        visual_context=('irregular_pace', 'daylight', 'crosswalk'),
        background_motion=False,
        scenario_seed_offset=37,
        vehicle_spawn_index=10,    # <-- force different spawn point
    ),

    ScenarioSpec(
        id='aggressive_rush_crossing_day',
        behavior='aggressive',
        description=(
            'Single pedestrian rushes across with sudden lateral '
            'zigzags.'
        ),
        weather_preset='ClearNoon',
        spawn_distance_m=(32.0, 32.0),
        lane_count=2,
        pedestrian_side='right',
        extra_pedestrians=0,
        ego_cruise_kmh=30.0,
        pedestrian_profile='adult',
        visual_context=('fast_erratic', 'daylight', 'crosswalk'),
        background_motion=False,
        scenario_seed_offset=49,
        vehicle_spawn_index=15,    # <-- force different spawn point
    ),

    ScenarioSpec(
        id='jaywalk_midblock_day',
        behavior='jaywalk',
        description=(
            'Single pedestrian crosses quickly and directly at '
            'mid‑block, away from any marked crosswalk.'
        ),
        weather_preset='ClearNoon',
        spawn_distance_m=(32.0, 32.0),
        lane_count=2,
        pedestrian_side='right',
        extra_pedestrians=0,
        ego_cruise_kmh=30.0,
        pedestrian_profile='adult',
        visual_context=('midblock_crossing', 'daylight', 'no_crosswalk'),
        background_motion=False,
        scenario_seed_offset=53,
        vehicle_spawn_index=None,
    ),
]


# ================================================================
# PUBLIC API
# ================================================================

def list_scenario_ids():
    return [s.id for s in SCENARIO_SUITE]


def get_scenario(scenario_id, rng=None):
    if scenario_id == 'random':
        raise ValueError(
            "Random scenario selection is disabled. "
            f"Please select one of: {list_scenario_ids()}"
        )
    for scenario in SCENARIO_SUITE:
        if scenario.id == scenario_id:
            return scenario
    raise ValueError(
        f"Unknown scenario id '{scenario_id}'. "
        f"Valid ids: {list_scenario_ids()}"
    )


def print_scenario_info(scenario):
    print()
    print("=" * 70)
    print("SCENARIO CONFIGURATION")
    print("=" * 70)
    print(f"Scenario ID       : {scenario.id}")
    print(f"Behavior          : {scenario.behavior}")
    print(f"True mental state : {scenario.true_state}")
    print(f"Description       : {scenario.description}")
    print("-" * 70)
    print(f"Weather           : {scenario.weather_preset}")
    print(f"Spawn distance    : {scenario.spawn_distance_m[0]:.1f} m")
    print(f"Lane count        : {scenario.lane_count}")
    print(f"Pedestrian side   : {scenario.pedestrian_side}")
    print(f"Extra pedestrians : {scenario.extra_pedestrians}")
    print(f"Ego speed         : {scenario.ego_cruise_kmh:.1f} km/h")
    print(f"Pedestrian        : {scenario.pedestrian_profile}")
    print("-" * 70)
    print("Visual context    : " + ", ".join(scenario.visual_context))
    print(f"Background motion : {scenario.background_motion}")
    print(f"Scenario seed     : {scenario.scenario_seed_offset}")
    print(f"Vehicle spawn idx : {scenario.vehicle_spawn_index}")
    print("=" * 70)
    print()


# ================================================================
# SELF TEST
# ================================================================

if __name__ == '__main__':
    print()
    print("=" * 70)
    print("CARLA SCENARIO SUITE SELF TEST")
    print("=" * 70)

    scenario_ids = list_scenario_ids()
    print("\nAvailable scenarios:")
    for i, sid in enumerate(scenario_ids, 1):
        print(f"  {i}. {sid}")

    print()
    for sid in scenario_ids:
        s = get_scenario(sid)
        print_scenario_info(s)

    states = {s.true_state for s in SCENARIO_SUITE}
    assert states == {0, 1, 2, 3, 4, 5}, "Missing mental states"
    print("All six mental states are covered.")

    targeted = [s for s in SCENARIO_SUITE if s.behavior in ('distracted', 'aggressive')]
    indices = [s.vehicle_spawn_index for s in targeted]
    assert all(i is not None for i in indices), "Missing spawn index for target scenarios"
    assert len(indices) == len(set(indices)), "Duplicate spawn indices"
    print("Spawn indices are distinct for distracted, aggressive.")

    print("\nSELF TEST PASSED")