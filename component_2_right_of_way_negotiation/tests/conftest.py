"""Keep component-relative test assets reproducible from the workspace root."""
import os
from pathlib import Path
import pytest

@pytest.fixture(scope="module",autouse=True)
def component_working_directory():
    previous=Path.cwd()
    os.chdir(Path(__file__).resolve().parents[1])
    try:
        yield
    finally:
        os.chdir(previous)
