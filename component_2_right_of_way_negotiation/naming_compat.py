"""Import aliases and immutable-path translations for the terminology migration."""
# Import importlib for use in this module.
import importlib
# Import importlib.abc for use in this module.
import importlib.abc
# Import importlib.util for use in this module.
import importlib.util
# Import sys for use in this module.
import sys
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set PACKAGES to a dictionary containing panel_demo, panel_validation, final_evaluation.
PACKAGES = {"panel_demo":"runtime_simulation", "panel_validation":"targeted_validation",
            "final_evaluation":"post_training_evaluation"}

# Define _AliasLoader to group the state and operations declared below.
# Base classes: importlib.abc.Loader.
# Instances expose the attributes and methods implemented in this class.
class _AliasLoader(importlib.abc.Loader):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input name: the supplied name.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, name):
        # Set self.name to name.
        self.name = name
    # Create module using the inputs and processing steps below.
    # Input spec: the supplied spec.
    # Output: module.
    def create_module(self, spec):
        # Set module to the result of importlib.import_module(self.name).
        module = importlib.import_module(self.name)
        # Set self.original_metadata to a tuple containing module.__spec__, module.__loader__, module.__package__.
        self.original_metadata = (module.__spec__,module.__loader__,module.__package__)
        # Return module to the caller.
        return module
    # Exec module using the inputs and processing steps below.
    # Input module: the supplied module.
    # Output: no explicit value; normal completion returns None.
    def exec_module(self, module):
        # Set (module.__spec__, module.__loader__, module.__package__) to self.original_metadata.
        module.__spec__,module.__loader__,module.__package__ = self.original_metadata

# Define _AliasFinder to group the state and operations declared below.
# Base classes: importlib.abc.MetaPathFinder.
# Instances expose the attributes and methods implemented in this class.
class _AliasFinder(importlib.abc.MetaPathFinder):
    # Find spec using the inputs and processing steps below.
    # Input fullname: the supplied fullname.
    # Input path: the path or path object supplied by the caller.
    # Input target: the supplied target.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def find_spec(self, fullname, path=None, target=None):
        # Set (first, dot, tail) to the result of fullname.partition(the text '.').
        first, dot, tail = fullname.partition(".")
        # Run this branch when the negation of dot or first does not belong to PACKAGES.
        if not dot or first not in PACKAGES:
            # Return None to the caller.
            return None
        # Set name to PACKAGES at first plus dot plus tail.
        name = PACKAGES[first]+dot+tail
        # Set spec to the result of importlib.util.find_spec(name).
        spec = importlib.util.find_spec(name)
        # Run this branch when spec is the same object as None.
        if spec is None:
            # Return None to the caller.
            return None
        # Return the result of importlib.util.spec_from_loader(fullname, the result of _AliasLoader(name)) to the
        # caller.
        return importlib.util.spec_from_loader(fullname, _AliasLoader(name),
            # Supply is_package as spec.submodule_search_locations is a different object from None.
            is_package=spec.submodule_search_locations is not None)

# Alias package using the inputs and processing steps below.
# Input old: the supplied old.
# Input new: the supplied new.
# Output: module.
# Processing: select branches using the stated conditions.
def alias_package(old, new):
    # Run this branch when the negation of whether any item is true in a lazy sequence of whether f has type
    # _AliasFinder for f in sys.meta_path.
    if not any(isinstance(f, _AliasFinder) for f in sys.meta_path):
        # Call sys.meta_path.insert with the supplied arguments.
        sys.meta_path.insert(0, _AliasFinder())
    # Set module to the result of importlib.import_module(new).
    module = importlib.import_module(new)
    # Set sys.modules[old] to module.
    sys.modules[old] = module
    # Return module to the caller.
    return module

# Resolve recorded path keys without rewriting an immutable inventory.
# Input path: the path or path object supplied by the caller.
# Output: return the value selected by the matching return branch below.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def historical_path(path):
    """Resolve recorded path keys without rewriting an immutable inventory."""
    # Set path to the result of Path(path).
    path = Path(path)
    # Set project to Path(__file__).resolve().parent.
    project = Path(__file__).resolve().parent
    # Set relative to path.
    relative = path
    # Run this branch when the result of path.is_absolute().
    if path.is_absolute():
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set relative to the result of path.relative_to(project).
            relative = path.relative_to(project)
        # Handle ValueError using the recovery steps below.
        except ValueError:
            # Return path to the caller.
            return path
    # Set base to project joined with the path segment 'results/naming_migration/pre_migration_runtime'.
    base = project / "results/naming_migration/pre_migration_runtime"
    # Run this branch when the text 'results' does not belong to relative.parts and whether (base / relative) is
    # an existing file.
    if "results" not in relative.parts and (base / relative).is_file():
        # Return base divided by relative to the caller.
        return base / relative
    # Run this branch when whether path is an existing file.
    if path.is_file():
        # Return path to the caller.
        return path
    # Set text to the result of str(path).replace(the text '\\', the text '/').
    text = str(path).replace("\\", "/")
    # Iterate over key/value pairs from PACKAGES, binding each item to (old, new).
    for old,new in PACKAGES.items():
        # Set text to the result of text.replace(new, old).
        text = text.replace(new,old)
    # Set base to Path(__file__).resolve().parent joined with the path segment
    # 'results/naming_migration/pre_migration_runtime'.
    base = Path(__file__).resolve().parent / "results/naming_migration/pre_migration_runtime"
    # Set candidate to base divided by text.
    candidate = base / text
    # Run this branch when whether candidate is an existing file.
    if candidate.is_file():
        # Return candidate to the caller.
        return candidate
    # Return path to the caller.
    return path

# Old preservation tests retain their exact-byte assertion against the archive.
# Input inventory: the supplied inventory.
# Output: whether every item is true in a lazy sequence of the result of file_hash(historical_path(path)).lower()
# equals the result of sha.lower() for (path, sha) in key/value pairs from inventory.
def assert_historical_unchanged(inventory):
    """Old preservation tests retain their exact-byte assertion against the archive."""
    # Import file_hash from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import file_hash
    # Return whether every item is true in a lazy sequence of the result of
    # file_hash(historical_path(path)).lower() equals the result of sha.lower() for (path, sha) in key/value pairs
    # from inventory to the caller.
    return all(file_hash(historical_path(path)).lower()==sha.lower() for path,sha in inventory.items())
