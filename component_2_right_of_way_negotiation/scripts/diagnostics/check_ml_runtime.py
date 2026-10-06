"""Hardware-safe optional ML runtime capability report."""

from ml_runtime_capability import detect_ml_runtime


def main():
    result = detect_ml_runtime()
    print("ML Runtime Capability Check")
    print(f"  Operating system: {result.operating_system}")
    print(f"  Machine architecture: {result.machine_architecture}")
    print(f"  Python version: {result.python_version}")
    print(f"  Python executable: {result.python_executable}")
    print(f"  NumPy available: {result.numpy_available}")
    print(f"  ONNX Runtime available: {result.onnxruntime_available}")
    print(f"  ONNX Runtime version: {result.onnxruntime_version}")
    print(f"  PyTorch installed: {result.pytorch_installed}")
    print(f"  PyTorch version: {result.pytorch_version}")
    print(f"  PyTorch import successful: {result.pytorch_import_successful}")
    print(f"  PyTorch CPU execution test: {result.pytorch_cpu_test}")
    print(f"  CUDA available (informational only): {result.cuda_available_informational}")
    if result.pytorch_error:
        print(f"  PyTorch error: {result.pytorch_error}")
    print("  TensorFlow required by project: False")
    print("  CUDA required by project: False")
    print(
        "  Local GNN development capability: "
        f"{result.local_gnn_development_capability}"
    )
    print(
        "  Recommended execution strategy: "
        f"{result.recommended_execution_strategy}"
    )


if __name__ == "__main__":
    main()
