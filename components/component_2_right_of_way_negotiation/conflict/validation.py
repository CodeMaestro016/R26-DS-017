"""Write network-derived conflict catalogues for validation and research QA."""

import csv
from pathlib import Path


def write_conflict_catalogues(path_manager, zone_manager, output_directory):
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    path_file = output_directory / "conflict_map_paths.csv"
    zone_file = output_directory / "conflict_zone_catalogue.csv"

    path_rows = path_manager.catalogue_rows()
    with path_file.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=(
            "path_id", "incoming_lane", "outgoing_lane", "manoeuvre",
            "geometry_point_count",
        ))
        writer.writeheader()
        writer.writerows(path_rows)

    zone_rows = zone_manager.catalogue_rows()
    with zone_file.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=(
            "zone_id", "first_path_id", "second_path_id",
            "topological_relationship", "conflict_type", "physical_overlap",
            "coordinated_conflict", "geometry_type",
        ))
        writer.writeheader()
        writer.writerows(zone_rows)
    return path_file, zone_file
