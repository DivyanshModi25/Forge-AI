import json
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.tools.deployment_planner import DeploymentPlan

from app.tools.langchain_tools import inspect_github_repository

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    temperature=0,
    max_retries=1,
    timeout=60,
)


planner = model.with_structured_output(DeploymentPlan)

def create_deployment_plan(inspection_report:dict) -> DeploymentPlan:
    messages=[
        (
            "system",
            """
            You are Forge, a cautious software deployment planner.

            Create a deployment plan based only on the supplied
            repository inspection report.

            Rules:
            - Do not claim that a framework or command exists unless
              supported by the report.
            - If the report lacks sufficient evidence, use
              needs_investigation and list what must be checked.
            - Prefer existing Docker configuration when available.
            - Never include secrets or invent environment variable values.
            - Include meaningful deployment risks.
            - Require human approval before deployment execution.
            - Return a plan matching the required schema.
            """,
        ),
        (
            "human",
            "Create a deployment plan for this repository inspection report:\n"
            + json.dumps(inspection_report, indent=2),
        ),
    ]

    return planner.invoke(messages)


if __name__ == "__main__":
    github_url = input("GitHub repository URL: ").strip()

    print("\n--- Inspecting repository ---\n")

    inspection_report = inspect_github_repository.invoke({
        "github_url": github_url
    })

    print("Repository:", inspection_report["repository"])
    print("Detected manifests:", inspection_report["manifests"])

    print("\n--- Generating deployment plan ---\n")

    plan = create_deployment_plan(inspection_report)

    print(plan.model_dump_json(indent=2))
