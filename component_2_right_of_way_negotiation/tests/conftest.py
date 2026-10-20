"""Keep component-relative test assets reproducible from the workspace root."""
# Import os for use in this module.
import os
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import pytest for use in this module.
import pytest

# Apply pytest.fixture(scope='module', autouse=True) as a decorator to configure the following definition.
@pytest.fixture(scope="module",autouse=True)
# Component working directory using the inputs and processing steps below.
# Output: yield the values produced by the yield statements below.
# Processing: handle the specified errors.
def component_working_directory():
    # Set previous to the result of Path.cwd().
    previous=Path.cwd()
    # Call os.chdir with the supplied arguments.
    os.chdir(Path(__file__).resolve().parents[1])
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Yield no value to the iterator consumer.
        yield
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Call os.chdir with the supplied arguments.
        os.chdir(previous)
