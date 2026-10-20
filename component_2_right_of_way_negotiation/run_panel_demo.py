"""Legacy CLI alias; prefer run_runtime_simulation.py."""
# Import main from run_runtime_simulation for the operations below.
from run_runtime_simulation import main
# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
