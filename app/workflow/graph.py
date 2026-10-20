from langgraph.graph import StateGraph,START,END

from app.workflow.state import DeploymentState
from app.workflow.nodes import inspect_node,planning_node,docker_build_node,start_container_node,health_check_node,failure_node
from app.workflow.routing import route_after_build,route_after_plan,route_after_start



def build_deployment_graph():

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


    builder.add_conditional_edges(
        "image_build",
        route_after_build,
        {
            "start_container": "start_container",
            "failed": "failed",
        },
    )


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



    return builder.compile()



deployment_graph = build_deployment_graph()