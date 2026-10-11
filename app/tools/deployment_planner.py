from typing import Literal

from pydantic import BaseModel,Field

class DeploymentStep(BaseModel):
    action:str = Field(
        description="A specific deployment action"
    )
    reason:str = Field(
        description="Why this action is needed"
    )


class DeploymentPlan(BaseModel):
    framework:str = Field(
        description="Detected application framework on runtime"
    )

    deployment_method: Literal[
        "docker",
        "existing_docker",
        "platform_specific",
        "needs_investigation",
    ]

    steps:list[DeploymentStep] = Field(
        description="Ordered steps needed for deployment."
    )

    risks:list[str] = Field(
        description="Potential deployment problems or security risks."
    )

    missing_information: list[str] = Field(
        description="Information needed before deployment can proceed."
    )

    requires_human_approval: bool = Field(
        description="Whether a person must approve before execution."
    )