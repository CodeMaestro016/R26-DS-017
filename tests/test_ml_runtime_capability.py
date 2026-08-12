"""Acceptance tests for the optional, hardware-safe PyTorch boundary."""

from dataclasses import replace
from pathlib import Path
import subprocess
import sys

from ml_runtime_capability import MLRuntimeCapability
import validate_gnn_forward


def unavailable_capability():
    return MLRuntimeCapability(
        "Windows", "AMD64", "3.13.1", "python.exe", True, True,
        "1.0", False, "NOT_INSTALLED", False, "NOT_TESTED", None,
        None, "PYTORCH_NOT_INSTALLED",
        "COLAB_TRAINING_ONNX_LOCAL_INFERENCE",
    )


def test_validator_reports_blocked_cleanly_when_pytorch_is_missing(capsys):
    status = validate_gnn_forward.main(unavailable_capability())
    output = capsys.readouterr().out
    assert status == "PYTORCH_RUNTIME_VALIDATION_BLOCKED"
    assert "PYTORCH_RUNTIME_VALIDATION_BLOCKED" in output
    assert "SUMO runtime affected: False" in output
    assert "NumPy GNN input encoder affected: False" in output
    assert "One-node zero-edge forward pass: PASS" not in output


def test_validator_reports_import_failure_distinctly(capsys):
    capability = replace(
        unavailable_capability(), pytorch_installed=True,
        pytorch_version="UNKNOWN_IMPORT_FAILED", pytorch_cpu_test="FAIL",
        pytorch_error="OSError: incompatible binary",
        local_gnn_development_capability="PYTORCH_IMPORT_FAILED",
    )
    validate_gnn_forward.main(capability)
    output = capsys.readouterr().out
    assert "could not complete a local CPU import/execution check" in output
    assert "OSError: incompatible binary" in output


def test_normal_runtime_and_base_package_have_no_pytorch_import():
    root = Path(__file__).parents[1]
    main_source = (root / "main.py").read_text(encoding="utf-8").lower()
    base_source = (root / "negotiation_learning" / "__init__.py").read_text(
        encoding="utf-8"
    ).lower()
    validator_prefix = (root / "validate_gnn_forward.py").read_text(
        encoding="utf-8"
    ).split("def main", 1)[0].lower()
    assert "import torch" not in main_source
    assert "negotiation_learning.gnn" not in main_source
    assert "negotiation_learning.gnn" not in base_source
    assert "import torch" not in validator_prefix


def test_mandatory_requirements_exclude_optional_neural_frameworks():
    root = Path(__file__).parents[1]
    runtime = set((root / "requirements.txt").read_text(encoding="utf-8").split())
    optional = (root / "requirements-training.txt").read_text(encoding="utf-8")
    assert "torch" not in runtime
    assert "tensorflow" not in runtime
    assert "torch" in optional.split()
    assert "tensorflow" not in optional.lower()


def test_main_imports_when_torch_is_forcibly_unavailable():
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
    result = subprocess.run(
        [sys.executable, "-c", blocker], cwd=Path(__file__).parents[1],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "MAIN_IMPORT_WITHOUT_PYTORCH_PASS" in result.stdout
