from pathlib import Path
from typing import Literal

from app.workflow.state import DeploymentState


def route_after_plan(state:DeploymentState) -> Literal["build","blocked"]:
    
    report = state["inspection_report"]
    plan = state["deployment_plan"]

    repo_path = Path(report["local_path"])

    dockerfile_exists = any(
        (repo_path / name).is_file()
        for name in ("Dockerfile", "dockerfile")
    )

    if not dockerfile_exists:
        return "blocked"

    
    if plan.get("deployment_method") == "needs_investigation":
        return "blocked"

    return "build"



def route_after_build(state: DeploymentState) -> Literal["start_container","failed"]:
    if state.get("build_result", {}).get("success"):
        return "start_container"

    return "failed"


def route_after_start(state: DeploymentState) -> Literal["health","failed"]:
    return "health" if state.get("status") == "running" else "failed"