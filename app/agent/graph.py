import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from app.tools.langchain_tools import inspect_github_repository

from langgraph.graph import MessagesState,StateGraph,START
from langgraph.prebuilt import ToolNode, tools_condition



load_dotenv()

# 1. Configure the model and its available tools
model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    temperature=0,
    max_retries=1,
    timeout=60,
)

tools = [inspect_github_repository]
model_with_tools = model.bind_tools(tools)


# define model node
def call_model(state:MessagesState):
    response = model_with_tools.invoke(state["messages"])
    return {"messages":[response]}


# 3. build the graph

builder = StateGraph(MessagesState)

builder.add_node("agent",call_model)
builder.add_node("tools",ToolNode(tools))

builder.add_edge(START,"agent")

builder.add_conditional_edges("agent",tools_condition)

builder.add_edge("tools","agent")

graph = builder.compile()





# 4. run the graph

def request_inspection(github_url:str):
    return graph.invoke({
        "messages": [
            (
                "system",
                "You are Forge, a software deployment assistant. "
                "Inspect repositories before planning deployment. "
                "Base your conclusions on tool results, not guesses.",
            ),
            (
                "human",
                f"Inspect this repository before deployment: {github_url}",
            )
        ]
    })



if __name__ == "__main__":
    url = input("GitHub repository URL: ").strip()
    result = request_inspection(url)

    print("\nForge's final answer:\n")
    print(f"result: {result} \n\n")
    print(result["messages"][-1].content)