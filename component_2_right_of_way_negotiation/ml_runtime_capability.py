"""Standard-library-only detection for optional neural dependencies."""

from dataclasses import asdict, dataclass
import importlib.util
import platform
import sys


@dataclass(frozen=True)
class MLRuntimeCapability:
    operating_system: str
    machine_architecture: str
    python_version: str
    python_executable: str
    numpy_available: bool
    onnxruntime_available: bool
    onnxruntime_version: str
    pytorch_installed: bool
    pytorch_version: str
    pytorch_import_successful: bool
    pytorch_cpu_test: str
    pytorch_error: str | None
    cuda_available_informational: bool | None
    local_gnn_development_capability: str
    recommended_execution_strategy: str

    def to_dict(self):
        return asdict(self)


def _module_available(name):
    return importlib.util.find_spec(name) is not None


def detect_ml_runtime():
    """Detect optional PyTorch safely; never installs or changes packages."""
    numpy_available = _module_available("numpy")
    onnx_available = _module_available("onnxruntime")
    onnx_version = "NOT_INSTALLED"
    if onnx_available:
        import onnxruntime
        onnx_version = onnxruntime.__version__

    torch_installed = _module_available("torch")
    torch_version = "NOT_INSTALLED"
    import_successful = False
    cpu_test = "NOT_TESTED"
    error_text = None
    cuda_available = None
    if torch_installed:
        try:
            import torch
            torch_version = torch.__version__
            import_successful = True
            value = torch.tensor([1.0], device="cpu") + 1.0
            cpu_test = "PASS" if (
                value.device.type == "cpu"
                and bool(torch.isfinite(value).all())
                and value.item() == 2.0
            ) else "FAIL"
            cuda_available = bool(torch.cuda.is_available())
        except (ImportError, OSError, RuntimeError) as error:
            error_text = f"{type(error).__name__}: {error}"
            cpu_test = "FAIL"

    if import_successful and cpu_test == "PASS":
        capability = "SUPPORTED"
        strategy = "LOCAL_CPU_PYTORCH"
    elif not torch_installed:
        capability = "PYTORCH_NOT_INSTALLED"
        strategy = "COLAB_TRAINING_ONNX_LOCAL_INFERENCE"
    else:
        capability = "PYTORCH_IMPORT_FAILED"
        strategy = "COLAB_TRAINING_ONNX_LOCAL_INFERENCE"

    return MLRuntimeCapability(
        platform.system(), platform.machine(), platform.python_version(),
        sys.executable, numpy_available, onnx_available, onnx_version,
        torch_installed, torch_version, import_successful, cpu_test,
        error_text, cuda_available, capability, strategy,
    )
