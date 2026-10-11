import os
import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage

from app.tools.langchain_tools import inspect_github_repository


load_dotenv()

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL","gpt-4.1-mini"),
    temperature=0,
    max_retries=1,
    timeout=60
)


tools = [inspect_github_repository]

model_with_tools = model.bind_tools(tools)


def request_inspection(github_url:str):
    messages = [
        (
            "system",
            "You are Forge, a software deployment assistant. "
            "When asked to inspect a repository, use the "
            "inspect_github_repository tool. Base your conclusions "
            "on its results, not guesses.",
        ),
        (
            "human",
            f"Inspect this repository before deployment: {github_url}",
        ),
    ]

    print(f"message:{messages} \n\n")

    # Step 1: Ask the model what to do
    response = model_with_tools.invoke(messages)
    messages.append(response)

    print(f"response: {response} \n\n")

    print(f"message:{messages} \n\n")


    # Step 2: Execute each tool requested by the model

    available_tools = {
        inspect_github_repository.name: inspect_github_repository
    }


    for tool_call in response.tool_calls:
        tool = available_tools[tool_call["name"]]
        result = tool.invoke(tool_call["args"])

        print(f"tool:{tool} \n\n")

        print(f"result for the loop: {result} \n\n")

        messages.append(
            ToolMessage(
                content=json.dumps(result),
                tool_call_id = tool_call["id"]
            )
        )

        print(f"new messages list: {messages} \n\n")

    # Step 3: Give the tool results back to the model
    final_response = model.invoke(messages)

    return final_response








if __name__ == "__main__":
    url = input("GitHub repository URL: ").strip()

    response = request_inspection(url)

    print("AI response:")
    print(response.content)

    print("Requested tool calls:")
    print(response.tool_calls)