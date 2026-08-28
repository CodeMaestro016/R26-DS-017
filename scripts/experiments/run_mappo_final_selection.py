"""CLI for the bounded final MAPPO validation-selection experiment."""

import argparse

from negotiation_training.final_selection import (
    CANDIDATE_EPOCHS, REPLICATION_COUNT, UPDATE_HORIZON,
    baseline, heldout, prepare, report, select, smoke, train, validate,
)


STAGES = ("prepare", "smoke", "train", "validate", "select", "heldout",
          "baseline", "report", "all")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run final E5/E10/E15 MAPPO validation selection.")
    parser.add_argument("--stage", required=True, choices=STAGES)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args(argv)


def _prepared_summary(protocol):
    print("Final MAPPO selection protocol prepared.\n")
    print("Candidates:")
    for candidate, epochs in CANDIDATE_EPOCHS.items():
        print(f"{candidate:<3} -> PPO epochs {epochs}")
    print(f"\nReplications: {REPLICATION_COUNT}")
    print(f"Update horizon H: {UPDATE_HORIZON}\n")
    manifests = protocol["manifests"]
    for role in ("TRAINING", "VALIDATION", "HELD_OUT_TEST"):
        print(f"{role.replace('_', ' ').title()} scenarios: "
              f"{manifests[role]['scenario_count']}")
    print("\nHeld-out locked: YES")
    print("Ready for training: YES")


def main(argv=None):
    args = parse_args(argv)
    if args.stage == "prepare":
        _prepared_summary(prepare())
    elif args.stage == "smoke":
        result = smoke()
        print(result["status"])
        print("NOT_MODEL_SELECTION_EVIDENCE")
        print("Held-out scenarios consumed: 0")
    elif args.stage == "train":
        print(train(resume=args.resume))
    elif args.stage == "validate":
        result = validate(resume=args.resume)
        print("Candidate   Mean validation TTT   Collisions   Blocked   Eligible")
        for key, item in result["candidates"].items():
            summary = item["summary"]
            print(f"{key:<11} "
                  f"{summary['mean_replication_total_team_travel_time_seconds']:<21.6f} "
                  f"{summary['collisions']:<12} "
                  f"{summary['blocked_zone_violations']:<9} "
                  f"{item['eligible']}")
    elif args.stage == "select":
        result = select()
        print("SELECTED_CONFIGURATION = " + result["selected_candidate_id"])
        print("SELECTION_BASIS = VALIDATION_ONLY")
        print("GLOBAL_OPTIMALITY_CLAIM = FALSE")
        print("HELD_OUT_CONSUMED = FALSE")
    elif args.stage == "heldout":
        print(heldout(resume=args.resume)["status"])
    elif args.stage == "baseline":
        print(baseline(resume=args.resume)["baseline_id"])
    elif args.stage == "report":
        print(report())
    else:
        protocol = prepare(); _prepared_summary(protocol)
        train(resume=args.resume)
        validate(resume=args.resume)
        select()
        heldout(resume=args.resume)
        baseline(resume=args.resume)
        report()


if __name__ == "__main__":
    main()
