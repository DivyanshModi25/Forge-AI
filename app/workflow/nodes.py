import subprocess

from app.workflow.state import DeploymentState
from app.tools.repository_inspector import inspect_repository
from app.agent.planner import create_deployment_plan
from app.tools.docker_tools import build_docker_image
from app.tools.health_check import check_health




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

