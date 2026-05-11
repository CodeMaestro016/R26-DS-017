# Complete Vehicle A automatic edge pipeline

from vehicles.vehicle_A.identify_and_label import identify_vehicle_A_knowledge
from vehicles.vehicle_A.rl_agent_A import dqn_agent_decision
from vehicles.vehicle_A.knowledge_package_creation import create_knowledge_package
from shared.importance_score import add_importance_scores

from global_verfication_server.global_verification import send_to_global_server


def run_vehicle_A_pipeline(image_path):
    print("\nRunning Vehicle A Edge Pipeline...\n")

    detections = identify_vehicle_A_knowledge(image_path)

    print("Step 1: Knowledge labeling completed")

    candidates = add_importance_scores(image_path, detections)

    print("Step 2: Importance scoring completed")

    final_outputs = []
    knowledge_packages = []
    verified_packages = []
    rl_feedbacks = []

    for item in candidates:
        action = dqn_agent_decision(item)
        item["agent_action"] = action

        if action == "SHARE":
            item["next_step"] = "SEND_TO_GLOBAL_SERVER"

            package = create_knowledge_package(item)
            knowledge_packages.append(package)

            verified_package, rl_reward = send_to_global_server(package)

            verified_packages.append(verified_package)

            rl_feedbacks.append({
                "package_id": package["package_id"],
                "sign_number": item["sign_number"],
                "agent_action": action,
                "rl_reward": rl_reward
            })

        else:
            item["next_step"] = "IGNORE"

        final_outputs.append(item)

    print("Step 3: DQN agent decision completed")
    print("Step 4: Knowledge package sharing completed")
    print("Step 5: Global verification completed")

    return {
        "detections": detections,
        "agent_outputs": final_outputs,
        "knowledge_packages": knowledge_packages,
        "verified_packages": verified_packages,
        "rl_feedbacks": rl_feedbacks
    }