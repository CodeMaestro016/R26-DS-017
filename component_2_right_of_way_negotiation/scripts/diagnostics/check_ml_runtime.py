"""Hardware-safe optional ML runtime capability report."""

# Import detect_ml_runtime from ml_runtime_capability for the operations below.
from ml_runtime_capability import detect_ml_runtime


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def main():
    # Set result to the result of detect_ml_runtime().
    result = detect_ml_runtime()
    # Display the text 'ML Runtime Capability Check'.
    print("ML Runtime Capability Check")
    # Display formatted text built from the embedded values.
    print(f"  Operating system: {result.operating_system}")
    # Display formatted text built from the embedded values.
    print(f"  Machine architecture: {result.machine_architecture}")
    # Display formatted text built from the embedded values.
    print(f"  Python version: {result.python_version}")
    # Display formatted text built from the embedded values.
    print(f"  Python executable: {result.python_executable}")
    # Display formatted text built from the embedded values.
    print(f"  NumPy available: {result.numpy_available}")
    # Display formatted text built from the embedded values.
    print(f"  ONNX Runtime available: {result.onnxruntime_available}")
    # Display formatted text built from the embedded values.
    print(f"  ONNX Runtime version: {result.onnxruntime_version}")
    # Display formatted text built from the embedded values.
    print(f"  PyTorch installed: {result.pytorch_installed}")
    # Display formatted text built from the embedded values.
    print(f"  PyTorch version: {result.pytorch_version}")
    # Display formatted text built from the embedded values.
    print(f"  PyTorch import successful: {result.pytorch_import_successful}")
    # Display formatted text built from the embedded values.
    print(f"  PyTorch CPU execution test: {result.pytorch_cpu_test}")
    # Display formatted text built from the embedded values.
    print(f"  CUDA available (informational only): {result.cuda_available_informational}")
    # Run this branch when result.pytorch_error.
    if result.pytorch_error:
        # Display formatted text built from the embedded values.
        print(f"  PyTorch error: {result.pytorch_error}")
    # Display the text 'TensorFlow required by project: False'.
    print("  TensorFlow required by project: False")
    # Display the text 'CUDA required by project: False'.
    print("  CUDA required by project: False")
    # Display formatted text built from the embedded values.
    print(
        "  Local GNN development capability: "
        # Evaluate {result.local_gnn_development_capability} as part of the enclosing expression.
        f"{result.local_gnn_development_capability}"
    )
    # Display formatted text built from the embedded values.
    print(
        "  Recommended execution strategy: "
        # Evaluate {result.recommended_execution_strategy} as part of the enclosing expression.
        f"{result.recommended_execution_strategy}"
    )


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
