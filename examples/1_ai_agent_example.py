import asyncio

from gen_ai_hub.proxy.native.openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from examples.pydantic_ai_tools import register_tools
from fastapi_agent.agents import DEFAULT_PROMPT, AIAgent, PydanticAIAgent  # noqa: F401

client = AsyncOpenAI(api_version="2024-10-21")
provider = OpenAIProvider(openai_client=client)
model = OpenAIModel(
    "gpt-4o",
    provider=provider,
)

## Option #1
## Create agent with generic AI Agent
agent = AIAgent.create(
    model=model,
    provider="pydantic_ai"
)

## Option #2
## create agent with pydantic_ai agent model
# agent = PydanticAIAgent(
#     model=model,
#     prompt=DEFAULT_PROMPT
# )

register_tools(agent)


async def main(questions):
    history = []
    for q in questions:
        res, h = await agent.chat(q, history)
        print(f"\n{res}")
        history = h

if __name__ == "__main__":
    questions = [
        "what you can do?",
        # "how much is 4 times 9 ? \n summurize the digits of the result \n multiply the new result by 10 \n show all the calculations steps",
        "how much is 4 times 9 ?",
        "summurize the digits of the result. e.g. (48 -> 4 + 8)",
        "multiply the new result by 10",
        "show all the calculations steps you made",
    ]
    asyncio.run(main(questions))
