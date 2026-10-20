"""Acceptance tests for the optional, hardware-safe PyTorch boundary."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import subprocess for use in this module.
import subprocess
# Import sys for use in this module.
import sys

# Import MLRuntimeCapability from ml_runtime_capability for the operations below.
from ml_runtime_capability import MLRuntimeCapability
# Import validate_gnn_forward from scripts.validation for the operations below.
from scripts.validation import validate_gnn_forward


# Unavailable capability using the inputs and processing steps below.
# Output: the result of MLRuntimeCapability(the text 'Windows', the text 'AMD64', the text '3.13.1', the text
# 'python.exe', True, True, the...).
def unavailable_capability():
    # Return the result of MLRuntimeCapability(the text 'Windows', the text 'AMD64', the text '3.13.1', the text
    # 'python.exe', True, True, the...) to the caller.
    return MLRuntimeCapability(
        # Supply the text 'Windows' to the enclosing expression.
        "Windows", "AMD64", "3.13.1", "python.exe", True, True,
        # Supply the text '1.0' to the enclosing expression.
        "1.0", False, "NOT_INSTALLED", False, "NOT_TESTED", None,
        # Supply None to the enclosing expression.
        None, "PYTORCH_NOT_INSTALLED",
        "COLAB_TRAINING_ONNX_LOCAL_INFERENCE",
    )


# Check validator reports blocked cleanly when pytorch is missing using the setup, calls, and assertions below.
# Input capsys: the supplied capsys.
# Output: no explicit value; normal completion returns None.
def test_validator_reports_blocked_cleanly_when_pytorch_is_missing(capsys):
    # Set status to the result of validate_gnn_forward.main(the result of unavailable_capability()).
    status = validate_gnn_forward.main(unavailable_capability())
    # Set output to capsys.readouterr().out.
    output = capsys.readouterr().out
    # Require status equals the text 'PYTORCH_RUNTIME_VALIDATION_BLOCKED'; otherwise raise AssertionError.
    assert status == "PYTORCH_RUNTIME_VALIDATION_BLOCKED"
    # Require the text 'PYTORCH_RUNTIME_VALIDATION_BLOCKED' belongs to output; otherwise raise AssertionError.
    assert "PYTORCH_RUNTIME_VALIDATION_BLOCKED" in output
    # Require the text 'SUMO runtime affected: False' belongs to output; otherwise raise AssertionError.
    assert "SUMO runtime affected: False" in output
    # Require the text 'NumPy GNN input encoder affected: False' belongs to output; otherwise raise
    # AssertionError.
    assert "NumPy GNN input encoder affected: False" in output
    # Require the text 'One-node zero-edge forward pass: PASS' does not belong to output; otherwise raise
    # AssertionError.
    assert "One-node zero-edge forward pass: PASS" not in output


# Check validator reports import failure distinctly using the setup, calls, and assertions below.
# Input capsys: the supplied capsys.
# Output: no explicit value; normal completion returns None.
def test_validator_reports_import_failure_distinctly(capsys):
    # Set capability to the result of replace(the result of unavailable_capability()).
    capability = replace(
        # Supply pytorch_installed as True.
        unavailable_capability(), pytorch_installed=True,
        # Supply pytorch_version as the text 'UNKNOWN_IMPORT_FAILED'.
        # Supply pytorch_cpu_test as the text 'FAIL'.
        pytorch_version="UNKNOWN_IMPORT_FAILED", pytorch_cpu_test="FAIL",
        # Supply pytorch_error as the text 'OSError: incompatible binary'.
        pytorch_error="OSError: incompatible binary",
        # Supply local_gnn_development_capability as the text 'PYTORCH_IMPORT_FAILED'.
        local_gnn_development_capability="PYTORCH_IMPORT_FAILED",
    )
    # Call validate_gnn_forward.main with the supplied arguments.
    validate_gnn_forward.main(capability)
    # Set output to capsys.readouterr().out.
    output = capsys.readouterr().out
    # Require the text 'could not complete a local CPU import/execution check' belongs to output; otherwise raise
    # AssertionError.
    assert "could not complete a local CPU import/execution check" in output
    # Require the text 'OSError: incompatible binary' belongs to output; otherwise raise AssertionError.
    assert "OSError: incompatible binary" in output


# Check normal runtime and base package have no pytorch import using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_normal_runtime_and_base_package_have_no_pytorch_import():
    # Set root to Path(__file__).parents at 1.
    root = Path(__file__).parents[1]
    # Set main_source to the result of (root / 'main.py').read_text(encoding='utf-8').lower().
    main_source = (root / "main.py").read_text(encoding="utf-8").lower()
    # Set base_source to the result of (root / 'negotiation_learning' /
    # '__init__.py').read_text(encoding='utf-8').lower().
    base_source = (root / "negotiation_learning" / "__init__.py").read_text(
        # Supply encoding as the text 'utf-8'.
        encoding="utf-8"
    ).lower()
    # Set validator_prefix to the result of (root / 'scripts' / 'validation' /...().
    validator_prefix = (root / "scripts" / "validation" /
                        # Supply the text 'validate_gnn_forward.py' to the enclosing expression.
                        "validate_gnn_forward.py").read_text(
        # Supply encoding as the text 'utf-8'.
        encoding="utf-8"
    # Supply 0 to the enclosing expression.
    ).split("def main", 1)[0].lower()
    # Require the text 'import torch' does not belong to main_source; otherwise raise AssertionError.
    assert "import torch" not in main_source
    # Require the text 'negotiation_learning.gnn' does not belong to main_source; otherwise raise AssertionError.
    assert "negotiation_learning.gnn" not in main_source
    # Require the text 'negotiation_learning.gnn' does not belong to base_source; otherwise raise AssertionError.
    assert "negotiation_learning.gnn" not in base_source
    # Require the text 'import torch' does not belong to validator_prefix; otherwise raise AssertionError.
    assert "import torch" not in validator_prefix


# Check mandatory requirements exclude optional neural frameworks using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_mandatory_requirements_exclude_optional_neural_frameworks():
    # Set root to Path(__file__).parents at 1.
    root = Path(__file__).parents[1]
    # Set runtime to a set built from the result of (root /
    # 'requirements.txt').read_text(encoding='utf-8').split().
    runtime = set((root / "requirements.txt").read_text(encoding="utf-8").split())
    # Set optional to the text read from (root / 'requirements-training.txt').
    optional = (root / "requirements-training.txt").read_text(encoding="utf-8")
    # Require the text 'torch' does not belong to runtime; otherwise raise AssertionError.
    assert "torch" not in runtime
    # Require the text 'tensorflow' does not belong to runtime; otherwise raise AssertionError.
    assert "tensorflow" not in runtime
    # Require the text 'torch' belongs to the result of optional.split(); otherwise raise AssertionError.
    assert "torch" in optional.split()
    # Require the text 'tensorflow' does not belong to the result of optional.lower(); otherwise raise
    # AssertionError.
    assert "tensorflow" not in optional.lower()


# Check main imports when torch is forcibly unavailable using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_main_imports_when_torch_is_forcibly_unavailable():
    # Set blocker to the text 'import importlib.abc import sys class...'.
    blocker = r'''
import importlib.abc
import sys
class BlockTorch(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "torch" or fullname.startswith("torch."):
            raise ModuleNotFoundError("torch intentionally unavailable in test")
        return None
sys.meta_path.insert(0, BlockTorch())
import main
print("MAIN_IMPORT_WITHOUT_PYTORCH_PASS")
'''
    # Set result to the result of subprocess.run(a list containing sys.executable, the text '-c', blocker).
    result = subprocess.run(
        # Supply cwd as Path(__file__).parents at 1.
        [sys.executable, "-c", blocker], cwd=Path(__file__).parents[1],
        # Supply capture_output as True.
        # Supply text as True.
        # Supply timeout as 30.
        capture_output=True, text=True, timeout=30,
    )
    # Require result.returncode equals 0; otherwise raise AssertionError with result.stderr.
    assert result.returncode == 0, result.stderr
    # Require the text 'MAIN_IMPORT_WITHOUT_PYTORCH_PASS' belongs to result.stdout; otherwise raise
    # AssertionError.
    assert "MAIN_IMPORT_WITHOUT_PYTORCH_PASS" in result.stdout
