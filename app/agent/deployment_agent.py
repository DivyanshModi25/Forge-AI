import json
from typing import TypedDict
from pathlib import Path
import subprocess

from langgraph.graph import StateGraph, START, END

from app.agent.planner import create_deployment_plan

from app.tools.repository_inspector import inspect_repository
from app.tools.docker_tools import build_docker_image
from app.tools.health_check import check_health


class DeploymentState(TypedDict, total=False):
    github_url: str
    inspection_report: dict
    deployment_plan: dict
    image_tag: str
    container_name: str
    port: int
    build_result: dict
    health_result: dict
    status: str
    error: str


def inspect_node(state: DeploymentState) -> dict:
    report = inspect_repository(state['github_url'])

    return {
        "inspection_report":report,
    }

def planning_node(state:DeploymentState) -> dict:
    plan = create_deployment_plan(state['inspection_report'])

    return {
        "deployment_plan": plan.model_dump()
    }


def route_after_plan(state:DeploymentState) -> str:
    
    report = state["inspection_report"]
    plan = state["deployment_plan"]

    dockerfile = Path(report["local_path"])/"Dockerfile" or Path(report["local_path"])/"dockerfile"

    if not dockerfile.is_file():
        return "blocked"

    if plan.get("deployment_method") == "needs_investigation":
        return "blocked"

    return "build"



def docker_build_node(state:DeploymentState) -> dict:

    report = state["inspection_report"]

    docker_image_build_result = build_docker_image(
        report["local_path"],
        state["image_tag"]
    )

    return {"build_result": docker_image_build_result}



def start_container_node(state:DeploymentState) -> dict:
    name = state["container_name"]
    port = state["port"]
    image = state["image_tag"]

    existing = subprocess.run(
        ["docker", "container", "inspect", name],
        capture_output=True,
        text=True,
        check=False,
    )

    if existing.returncode == 0:
        return {
            "status": "blocked",
            "error": f"Container {name} already exists.",
        }

    result = subprocess.run(
        [
            "docker", "run", "-d",
            "--name", name,
            "-p", f"127.0.0.1:{port}:80",
            image,
        ],

        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    if result.returncode != 0:
        return {
            "status": "failed",
            "error": result.stderr[-3000:],
        }

    return {"status": "running"}



def health_check_node(state:DeploymentState) -> dict:
    result = check_health(
        f"http://127.0.0.1:{state['port']}",
        timeout_seconds=30,
    )

    return {
        "health_result": result,
        "status": "success" if result["healthy"] else "failed",
    }

def failure_node(state: DeploymentState) -> dict:
    return {
        "status": state.get("status", "failed"),
        "error": state.get(
            "error",
            "Deployment could not proceed.",
        ),
    }





builder = StateGraph(DeploymentState)


builder.add_node("inspect",inspect_node)
builder.add_node("plan",planning_node)
builder.add_node("image_build",docker_build_node)
builder.add_node("start_container",start_container_node)
builder.add_node("health",health_check_node)
builder.add_node("failed",failure_node)



builder.add_edge(START,"inspect")
builder.add_edge("inspect","plan")

builder.add_conditional_edges(
    "plan",
    route_after_plan,
    {
        "build":"image_build",
        "blocked":"failed"
    }
)

def route_after_build(state: DeploymentState) -> str:
    if state["build_result"].get("success"):
        return "start_container"
    return "failed"


builder.add_conditional_edges(
    "image_build",
    route_after_build,
    {
        "start_container": "start_container",
        "failed": "failed",
    },
)


def route_after_start(state: DeploymentState) -> str:
    return "health" if state.get("status") == "running" else "failed"


builder.add_conditional_edges(
    "start_container",
    route_after_start,
    {
        "health": "health",
        "failed": "failed",
    },
)


builder.add_edge("health", END)
builder.add_edge("failed", END)



deployment_graph = builder.compile()



if __name__ == "__main__":

    github_url = input("GitHub repository URL: ").strip()

    input_state = {
        "github_url": github_url,
        "image_tag": "forge-managed-app:latest",
        "container_name": "forge-managed-app",
        "port": 8080,
    }

    print("\n--- Starting deployment workflow ---\n")

    final_state = {}

    try:
        for update in deployment_graph.stream(
            input_state,
            stream_mode="updates",
        ):
            for node_name, node_update in update.items():
                print(f"\n--- Node executed: {node_name} ---")

                # Show the state update returned by this node.
                print(json.dumps(node_update, indent=2, default=str))

                # Preserve updates so we can display the final result.
                final_state.update(node_update)

        print("\n--- Execution result ---")
        print("Status:", final_state.get("status", "unknown"))
        print("Build:", json.dumps(
            final_state.get("build_result"),
            indent=2,
            default=str,
        ))
        print("Health:", json.dumps(
            final_state.get("health_result"),
            indent=2,
            default=str,
        ))
        print("Error:", final_state.get("error"))

    except Exception as exc:
        print(f"\nWorkflow crashed: {type(exc).__name__}: {exc}")
        raise