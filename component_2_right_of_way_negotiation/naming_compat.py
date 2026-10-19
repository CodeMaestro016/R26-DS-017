"""Import aliases and immutable-path translations for the terminology migration."""
import importlib
import importlib.abc
import importlib.util
import sys
from pathlib import Path

PACKAGES = {"panel_demo":"runtime_simulation", "panel_validation":"targeted_validation",
            "final_evaluation":"post_training_evaluation"}

class _AliasLoader(importlib.abc.Loader):
    def __init__(self, name):
        self.name = name
    def create_module(self, spec):
        module = importlib.import_module(self.name)
        self.original_metadata = (module.__spec__,module.__loader__,module.__package__)
        return module
    def exec_module(self, module):
        module.__spec__,module.__loader__,module.__package__ = self.original_metadata

class _AliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        first, dot, tail = fullname.partition(".")
        if not dot or first not in PACKAGES:
            return None
        name = PACKAGES[first]+dot+tail
        spec = importlib.util.find_spec(name)
        if spec is None:
            return None
        return importlib.util.spec_from_loader(fullname, _AliasLoader(name),
            is_package=spec.submodule_search_locations is not None)

def alias_package(old, new):
    if not any(isinstance(f, _AliasFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _AliasFinder())
    module = importlib.import_module(new)
    sys.modules[old] = module
    return module

def historical_path(path):
    """Resolve recorded path keys without rewriting an immutable inventory."""
    path = Path(path)
    project = Path(__file__).resolve().parent
    relative = path
    if path.is_absolute():
        try:
            relative = path.relative_to(project)
        except ValueError:
            return path
    base = project / "results/naming_migration/pre_migration_runtime"
    if "results" not in relative.parts and (base / relative).is_file():
        return base / relative
    if path.is_file():
        return path
    text = str(path).replace("\\", "/")
    for old,new in PACKAGES.items():
        text = text.replace(new,old)
    base = Path(__file__).resolve().parent / "results/naming_migration/pre_migration_runtime"
    candidate = base / text
    if candidate.is_file():
        return candidate
    return path

def assert_historical_unchanged(inventory):
    """Old preservation tests retain their exact-byte assertion against the archive."""
    from post_training_evaluation.models import file_hash
    return all(file_hash(historical_path(path)).lower()==sha.lower() for path,sha in inventory.items())
