import json

from app.workflow.graph import deployment_graph


def main():
    github_url = input("GitHub repository URL: ").strip()

    input_state = {
        "github_url": github_url,
        "image_tag": "forge-managed-app:latest",
        "container_name": "forge-managed-app",
        "port": 8080,
    }

    print("\n--- Starting Forge workflow ---\n")

    final_state = {}

    for update in deployment_graph.stream(
        input_state,
        stream_mode="updates",
    ):
        for node_name, node_update in update.items():
            print(f"\n--- Node: {node_name} ---")
            print(json.dumps(node_update, indent=2, default=str))

            final_state.update(node_update)

    print("\n--- Execution result ---")
    print("Status:", final_state.get("status", "unknown"))
    print("Error:", final_state.get("error"))

    print(
        "Build:",
        json.dumps(final_state.get("build_result"), indent=2, default=str),
    )

    print(
        "Health:",
        json.dumps(final_state.get("health_result"), indent=2, default=str),
    )


if __name__ == "__main__":
    main()