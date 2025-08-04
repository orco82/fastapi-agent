import asyncio

from dotenv import load_dotenv

from examples.pydantic_ai_tools import register_tools
from fastapi_agent.agents import DEFAULT_PROMPT, AIAgent, PydanticAIAgent  # noqa: F401

load_dotenv()

## Option #1
## Create agent with generic AI Agent
agent = AIAgent.create(
    model="openai:gpt-4.1-mini",
    provider="pydantic_ai"
)

## Option #2
## create agent with pydantic_ai agent model
# agent = PydanticAIAgent(
#     model="openai:gpt-4.1-mini",
#     prompt=DEFAULT_PROMPT
# )

register_tools(agent)


async def main(questions):
    history = []
    for q in questions:
        print(f"\nQ: {q}")
        res, h = await agent.chat(q, history)
        print(f"A: {res}", end="\n\n-----\n")
        history = h


if __name__ == "__main__":
    questions = [
        "what tool do you have?",
        "how much is 4 times 9 ?",
        "summurize the digits of the result. e.g. (48 -> 4 + 8)",
        "multiply the new result by 10",
        "show all the calculations steps you made",
        "what is the weather in New York?"
    ]
    asyncio.run(main(questions))
