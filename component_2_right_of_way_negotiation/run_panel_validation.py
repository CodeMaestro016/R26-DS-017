"""Legacy CLI alias; prefer run_targeted_validation.py."""
# Import main from run_targeted_validation for the operations below.
from run_targeted_validation import main
# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
