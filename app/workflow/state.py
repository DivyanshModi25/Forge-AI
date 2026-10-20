from typing import TypedDict



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