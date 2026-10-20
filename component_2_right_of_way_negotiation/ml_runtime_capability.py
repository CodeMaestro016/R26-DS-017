"""Standard-library-only detection for optional neural dependencies."""

# Import asdict, dataclass from dataclasses for the operations below.
from dataclasses import asdict, dataclass
# Import importlib.util for use in this module.
import importlib.util
# Import platform for use in this module.
import platform
# Import sys for use in this module.
import sys


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MLRuntimeCapability to group the state and operations declared below.
# Declared fields: operating_system, machine_architecture, python_version, python_executable, numpy_available,
# onnxruntime_available, onnxruntime_version, pytorch_installed, pytorch_version, pytorch_import_successful,....
# Construction and attribute behavior follow the declared decorators and base classes.
class MLRuntimeCapability:
    # Declare operating_system as str for this data structure.
    operating_system: str
    # Declare machine_architecture as str for this data structure.
    machine_architecture: str
    # Declare python_version as str for this data structure.
    python_version: str
    # Declare python_executable as str for this data structure.
    python_executable: str
    # Declare numpy_available as bool for this data structure.
    numpy_available: bool
    # Declare onnxruntime_available as bool for this data structure.
    onnxruntime_available: bool
    # Declare onnxruntime_version as str for this data structure.
    onnxruntime_version: str
    # Declare pytorch_installed as bool for this data structure.
    pytorch_installed: bool
    # Declare pytorch_version as str for this data structure.
    pytorch_version: str
    # Declare pytorch_import_successful as bool for this data structure.
    pytorch_import_successful: bool
    # Declare pytorch_cpu_test as str for this data structure.
    pytorch_cpu_test: str
    # Declare pytorch_error as str | None for this data structure.
    pytorch_error: str | None
    # Declare cuda_available_informational as bool | None for this data structure.
    cuda_available_informational: bool | None
    # Declare local_gnn_development_capability as str for this data structure.
    local_gnn_development_capability: str
    # Declare recommended_execution_strategy as str for this data structure.
    recommended_execution_strategy: str

    # To dict using the inputs and processing steps below.
    # Output: the result of asdict(self).
    def to_dict(self):
        # Return the result of asdict(self) to the caller.
        return asdict(self)


# Module available using the inputs and processing steps below.
# Input name: the supplied name.
# Output: the result of importlib.util.find_spec(name) is a different object from None.
def _module_available(name):
    # Return the result of importlib.util.find_spec(name) is a different object from None to the caller.
    return importlib.util.find_spec(name) is not None


# Detect optional PyTorch safely; never installs or changes packages.
# Output: the result of MLRuntimeCapability(the result of platform.system(), the result of platform.machine(), the
# result of...).
# Processing: select branches using the stated conditions, then handle the specified errors.
def detect_ml_runtime():
    """Detect optional PyTorch safely; never installs or changes packages."""
    # Set numpy_available to the result of _module_available(the text 'numpy').
    numpy_available = _module_available("numpy")
    # Set onnx_available to the result of _module_available(the text 'onnxruntime').
    onnx_available = _module_available("onnxruntime")
    # Set onnx_version to the text 'NOT_INSTALLED'.
    onnx_version = "NOT_INSTALLED"
    # Run this branch when onnx_available.
    if onnx_available:
        # Import onnxruntime for use in this module.
        import onnxruntime
        # Set onnx_version to onnxruntime.__version__.
        onnx_version = onnxruntime.__version__

    # Set torch_installed to the result of _module_available(the text 'torch').
    torch_installed = _module_available("torch")
    # Set torch_version to the text 'NOT_INSTALLED'.
    torch_version = "NOT_INSTALLED"
    # Set import_successful to False.
    import_successful = False
    # Set cpu_test to the text 'NOT_TESTED'.
    cpu_test = "NOT_TESTED"
    # Set error_text to None.
    error_text = None
    # Set cuda_available to None.
    cuda_available = None
    # Run this branch when torch_installed.
    if torch_installed:
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Import torch for use in this module.
            import torch
            # Set torch_version to torch.__version__.
            torch_version = torch.__version__
            # Set import_successful to True.
            import_successful = True
            # Set value to a tensor built from a list containing 1.0 plus 1.0.
            value = torch.tensor([1.0], device="cpu") + 1.0
            # Set cpu_test to the text 'PASS' when value.device.type equals the text 'cpu' and a Boolean built
            # from the result of torch.isfinite(value).all() and the result of value.item() equals 2.0, otherwise
            # the text 'FAIL'.
            cpu_test = "PASS" if (
                # Evaluate value.device.type equals the text 'cpu' and a Boolean built from the result of
                # torch.isfinite(value).all() and the result of value.item() equals 2.0 as part of the enclosing
                # expression.
                value.device.type == "cpu"
                # Evaluate a Boolean built from the result of torch.isfinite(value).all() as part of the enclosing
                # expression.
                and bool(torch.isfinite(value).all())
                # Evaluate the result of value.item() equals 2.0 as part of the enclosing expression.
                and value.item() == 2.0
            # Supply the text 'FAIL' to the enclosing expression.
            ) else "FAIL"
            # Set cuda_available to a Boolean built from the result of torch.cuda.is_available().
            cuda_available = bool(torch.cuda.is_available())
        # Handle (ImportError, OSError, RuntimeError) as error using the recovery steps below.
        except (ImportError, OSError, RuntimeError) as error:
            # Set error_text to formatted text built from the embedded values.
            error_text = f"{type(error).__name__}: {error}"
            # Set cpu_test to the text 'FAIL'.
            cpu_test = "FAIL"

    # Run this branch when import_successful and cpu_test equals the text 'PASS'.
    if import_successful and cpu_test == "PASS":
        # Set capability to the text 'SUPPORTED'.
        capability = "SUPPORTED"
        # Set strategy to the text 'LOCAL_CPU_PYTORCH'.
        strategy = "LOCAL_CPU_PYTORCH"
    # Run this branch when the negation of torch_installed.
    elif not torch_installed:
        # Set capability to the text 'PYTORCH_NOT_INSTALLED'.
        capability = "PYTORCH_NOT_INSTALLED"
        # Set strategy to the text 'COLAB_TRAINING_ONNX_LOCAL_INFERENCE'.
        strategy = "COLAB_TRAINING_ONNX_LOCAL_INFERENCE"
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Set capability to the text 'PYTORCH_IMPORT_FAILED'.
        capability = "PYTORCH_IMPORT_FAILED"
        # Set strategy to the text 'COLAB_TRAINING_ONNX_LOCAL_INFERENCE'.
        strategy = "COLAB_TRAINING_ONNX_LOCAL_INFERENCE"

    # Return the result of MLRuntimeCapability(the result of platform.system(), the result of platform.machine(),
    # the result of...) to the caller.
    return MLRuntimeCapability(
        # Supply the result of platform.python_version() to MLRuntimeCapability.
        platform.system(), platform.machine(), platform.python_version(),
        # Supply numpy_available to MLRuntimeCapability.
        sys.executable, numpy_available, onnx_available, onnx_version,
        # Supply import_successful to MLRuntimeCapability.
        torch_installed, torch_version, import_successful, cpu_test,
        # Supply cuda_available to MLRuntimeCapability.
        error_text, cuda_available, capability, strategy,
    )
