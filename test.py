import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    temperature=0,
    max_retries=1,
    timeout=30,
)

response = model.invoke(
    "In two sentences, explain how Forge should inspect "
    "a GitHub repository before deploying it."
)

print(response.content)