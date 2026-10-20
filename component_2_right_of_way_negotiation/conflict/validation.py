"""Write network-derived conflict catalogues for validation and research QA."""

# Import csv for use in this module.
import csv
# Import Path from pathlib for the operations below.
from pathlib import Path


# Write conflict catalogues using the inputs and processing steps below.
# Input path_manager: the supplied path manager.
# Input zone_manager: the supplied zone manager.
# Input output_directory: the supplied output directory.
# Output: a tuple containing path_file, zone_file.
def write_conflict_catalogues(path_manager, zone_manager, output_directory):
    # Set output_directory to the result of Path(output_directory).
    output_directory = Path(output_directory)
    # Create the directory requested by output_directory.
    output_directory.mkdir(parents=True, exist_ok=True)
    # Set path_file to output_directory joined with the path segment 'conflict_map_paths.csv'.
    path_file = output_directory / "conflict_map_paths.csv"
    # Set zone_file to output_directory joined with the path segment 'conflict_zone_catalogue.csv'.
    zone_file = output_directory / "conflict_zone_catalogue.csv"

    # Set path_rows to the result of path_manager.catalogue_rows().
    path_rows = path_manager.catalogue_rows()
    # Enter the result of path_file.open(the text 'w') as stream and run the enclosed operations within that
    # context.
    with path_file.open("w", newline="", encoding="utf-8") as stream:
        # Set writer to the result of csv.DictWriter(stream).
        writer = csv.DictWriter(stream, fieldnames=(
            "path_id", "incoming_lane", "outgoing_lane", "manoeuvre",
            "geometry_point_count",
        ))
        # Call writer.writeheader with the supplied arguments.
        writer.writeheader()
        # Call writer.writerows with the supplied arguments.
        writer.writerows(path_rows)

    # Set zone_rows to the result of zone_manager.catalogue_rows().
    zone_rows = zone_manager.catalogue_rows()
    # Enter the result of zone_file.open(the text 'w') as stream and run the enclosed operations within that
    # context.
    with zone_file.open("w", newline="", encoding="utf-8") as stream:
        # Set writer to the result of csv.DictWriter(stream).
        writer = csv.DictWriter(stream, fieldnames=(
            "zone_id", "first_path_id", "second_path_id",
            "topological_relationship", "conflict_type", "physical_overlap",
            "coordinated_conflict", "geometry_type",
        ))
        # Call writer.writeheader with the supplied arguments.
        writer.writeheader()
        # Call writer.writerows with the supplied arguments.
        writer.writerows(zone_rows)
    # Return a tuple containing path_file, zone_file to the caller.
    return path_file, zone_file
