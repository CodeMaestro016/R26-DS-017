"""Legacy CLI alias; prefer run_post_training_evaluation.py."""
# Import main from run_post_training_evaluation for the operations below.
from run_post_training_evaluation import main
# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
