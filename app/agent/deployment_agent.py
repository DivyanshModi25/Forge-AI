import json
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from app.tools.repository_inspector import inspect_repository
from app.agent.planner import create_deployment_plan


class DeploymentState(TypedDict, total=False):
    github_url: str
    inspection_report: dict
    deployment_plan: dict


def inspect_node(state: DeploymentState) -> dict:
    report = inspect_repository(state['github_url'])

    return {
        "inspection_report":report,
    }

def planning_node(state:DeploymentState) -> dict:
    plan = create_deployment_plan(state['inspection_report'])

    return {
        "deployment_plan":plan
    }

builder = StateGraph(DeploymentState)


builder.add_node("inspect",inspect_node)
builder.add_node("plan",planning_node)


builder.add_edge(START,"inspect")
builder.add_edge("inspect","plan")
builder.add_edge("plan",END)

deployment_graph = builder.compile()

if __name__=="__main__":
    github_url = input("enter github url")

    result = deployment_graph.invoke({
        "github_url":github_url
    })


    print("\n--- Deployment plan ---\n")

    print(result["deployment_plan"].model_dump_json(indent=2))